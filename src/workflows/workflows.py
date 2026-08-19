
from src.db import ExistDB
from src.context.class_context import trim_contexts
from src.workflows.blocks.generate_class_descriptions import generate_class_descriptions, build_class_contexts
from src.workflows.blocks.generate_xquery import generate_xquery
from src.workflows.blocks.get_field_descriptions import build_field_descriptions
from src.workflows.blocks.answer_question import answer_question
from src.workflows.blocks.extract_keywords import extract_keywords

from src.services.ai.tools import detect_relevant_classes
from src.services.ai.token_estimator import count_tokens

from src.index.index import save_to_index, load_from_index
from src.search.search import search_to_ordered_classes, search_to_string, search_to_string_hits
from src.xquery.postprocessing import postprocess_xquery
from src.xquery.utils import has_hits
from src.context.filtering import extract_class_names, extract_matching_fields

from dataclasses import dataclass
from typing import Any, Iterator, Literal


 
RESERVED_TOKEN_NUM = 1000
@dataclass
class PipelineEvent:
    """A single event emitted by the pipeline.
 
    type:
      "status" -> a "doing X..." message, nothing to show but the text
      "result" -> a completed intermediate step, with data attached
      "error"  -> something went wrong; data holds the exception/message
      "final"  -> the pipeline is done; data holds the final answer
    """
    type: Literal["status", "result", "error", "final"]
    message: str
    data: Any = None


def answer_with_search_results(
    question: str,
    db: ExistDB,
    workdir: str,
    config: dict,
    index_folder: str,
) -> Iterator[PipelineEvent]:
    """
    Runs the full RAG pipeline, yielding a PipelineEvent after each
    meaningful step. The caller just iterates over this generator and
    renders each event as it arrives — no changes needed here when you
    swap frontends.
    """
    workdir_name = workdir.split("/")[-1]
    try:
        
        # --- Analyze classes and field descriptions -------------------------------------------
        yield PipelineEvent("status", "Loading field descriptions...")
        field_descriptions = load_from_index("field_descriptions", workdir_name, index_folder)
        if not field_descriptions:
            yield PipelineEvent("status", "No cached field descriptions found, generating them...")
            field_descriptions = build_field_descriptions(db, workdir)
            save_to_index("field_descriptions", field_descriptions, workdir_name, index_folder)
        yield PipelineEvent("status", "Field descriptions ready")

        available_classes = field_descriptions.keys()
        yield PipelineEvent("result", "Available classes", data=list(available_classes))

        yield PipelineEvent("status", "Ensuring index presence...")
        db.ensure_fulltext_index(workdir)

        yield PipelineEvent("status", "Extracting search keywords...")
        keywords = extract_keywords(question, config["generation"])
        yield PipelineEvent("result", "Extracted keywords", data=keywords)

        yield PipelineEvent("status", "Searching the database...")
        res = db.multiple_string_search(keywords, workdir, partial_match=True)
        search_xml_contexts = search_to_string(res, available_classes, max_tokens=config["generation"]["num_ctx"] - config["generation"]["num_predict"] - RESERVED_TOKEN_NUM)
        final_search_context = "\n".join(search_xml_contexts)

        hits_to_display = search_to_string_hits(res, available_classes)
        yield PipelineEvent("result", "Search hits", data=hits_to_display)

        # --- answer generation -------------------------------------------------
        yield PipelineEvent("status", "Generating final answer...")
        answer = answer_question(context=final_search_context, question=question, llm_config=config["generation"])
        yield PipelineEvent("final", "Done", data=answer)
 
    except Exception as exc:  # surface any failure to the frontend
        yield PipelineEvent("error", "Pipeline failed", data=str(exc))




# TODO: Fix after completing full text search implementation
def answer_with_xquery(
    question: str,
    db: ExistDB,
    workdir: str,
    config: dict,
    index_folder: str,
) -> Iterator[PipelineEvent]:
    """
    Runs the full RAG pipeline, yielding a PipelineEvent after each
    meaningful step. The caller just iterates over this generator and
    renders each event as it arrives — no changes needed here when you
    swap frontends.
    """
    workdir_name = workdir.split("/")[-1]
    try:
        
        # --- Analyze classes and field descriptions -------------------------------------------
        yield PipelineEvent("status", "Loading field descriptions...")
        field_descriptions = load_from_index("field_descriptions", workdir_name, index_folder)
        if not field_descriptions:
            yield PipelineEvent("status", "No cached field descriptions found, generating them...")
            field_descriptions = build_field_descriptions(db, workdir)
            save_to_index("field_descriptions", field_descriptions, workdir_name, index_folder)
        yield PipelineEvent("status", "Field descriptions ready")

        available_classes = field_descriptions.keys()

        yield PipelineEvent("status", "Ensuring index presence...")
        db.ensure_fulltext_index(workdir)

        yield PipelineEvent("status", "Extracting search keywords...")
        keywords = extract_keywords(question, config["generation"])

        # keywords = ['Δίσκος της Φαιστού']
        yield PipelineEvent("result", "Extracted keywords", data=keywords)

        yield PipelineEvent("status", "Searching the database...")
        res = db.multiple_string_search(keywords, workdir, partial_match=True)

        # --- Build context from class template and field analysis -------------------------------------------
        relevant_classes = search_to_ordered_classes(res, available_classes)
        yield PipelineEvent("result", "Relevant classes selected", data=relevant_classes)
        print(relevant_classes)
        contexts = build_class_contexts(db, workdir, field_descriptions, classes=relevant_classes)

        trimmed_str_contexts = trim_contexts(contexts, max_tokens=config["generation"]["num_ctx"] - config["generation"]["num_predict"] - RESERVED_TOKEN_NUM)
        final_context = "\n".join(trimmed_str_contexts)

        # --- xquery generation ---------------------------------------------
        yield PipelineEvent("status", "Generating XQuery...")
        xquery = generate_xquery(context=final_context, question=question, classes=relevant_classes, llm_config=config["generation"])

        yield PipelineEvent("result", "Raw XQuery generated", data=xquery)
        xquery = postprocess_xquery(xquery, config["database"])
        yield PipelineEvent("result", "Postprocessed XQuery generated", data=xquery)
        print(xquery)
 
        # --- execution ------------------------------------------------------
        yield PipelineEvent("status", "Running query against the database...")

        try:
            db_result = db.execute_xquery(xquery)

        except Exception as e:
            yield PipelineEvent("error", "XQuery execution failed", data=str(e))
            db_result = ""

        if not has_hits(db_result) or True:
            yield PipelineEvent("status", "No hits found in the database for the generated XQuery.")
            yield PipelineEvent("status", "Trying to answer with search context...")
            # --- Build alternative context from XML file contents -------------------------------------------
            search_xml_contexts = search_to_string(res, available_classes, max_tokens=config["generation"]["num_ctx"] - config["generation"]["num_predict"] - RESERVED_TOKEN_NUM)
            final_search_context = "\n".join(search_xml_contexts)
            print(count_tokens(final_search_context))
        
        else:
            yield PipelineEvent("status", "Hits found in the database for the generated XQuery.")
            final_search_context = final_context

            



        # --- answer generation -------------------------------------------------
        yield PipelineEvent("status", "Generating final answer...")
        answer = answer_question(context=final_search_context, question=question, llm_config=config["generation"])
        
        yield PipelineEvent("final", "Done", data=answer)
 
    except Exception as exc:  # surface any failure to the frontend
        yield PipelineEvent("error", "Pipeline failed", data=str(exc))