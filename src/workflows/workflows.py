
from src.db import ExistDB
from src.context.class_context import trim_contexts
from src.workflows.blocks.generate_class_descriptions import generate_class_descriptions, build_class_contexts
from src.workflows.blocks.generate_xquery import generate_xquery
from src.workflows.blocks.get_field_descriptions import build_field_descriptions
from src.workflows.blocks.answer_question import answer_question
from src.workflows.blocks.extract_keywords import extract_keywords

from src.services.ai.tools import detect_relevant_classes
from src.services.ai.token_estimator import estimate_tokens

from src.index.index import save_to_index, load_from_index
from src.xquery.postprocessing import postprocess_xquery
from src.context.filtering import extract_class_names, extract_matching_fields

from dataclasses import dataclass
from typing import Any, Iterator, Literal
 
 
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
 
 
def run_rag_pipeline(
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
        # --- field descriptions -------------------------------------------
        yield PipelineEvent("status", "Loading field descriptions...")
        field_descriptions = load_from_index("field_descriptions", workdir_name, index_folder)
        if not field_descriptions:
            yield PipelineEvent("status", "No cached field descriptions found, generating them...")
            field_descriptions = build_field_descriptions(db, workdir)
            save_to_index("field_descriptions", field_descriptions, workdir_name, index_folder)
        yield PipelineEvent("status", "Field descriptions ready")

        # --- context building ------------------------------------------------
        contexts = build_class_contexts(db, workdir, field_descriptions)


        # --- class descriptions ------------------------------------------
        yield PipelineEvent("status", "Loading class descriptions...")
        class_descriptions = load_from_index("class_descriptions", workdir_name, index_folder)
        if not class_descriptions:
            yield PipelineEvent("status", "No cached class descriptions found, generating them...")
            class_descriptions = generate_class_descriptions(contexts, config["generation"])
            save_to_index("class_descriptions", class_descriptions, workdir_name, index_folder)

        yield PipelineEvent("result", "Class descriptions ready", data=[
            (cd[:20] + "...") if isinstance(cd, str) and len(cd) > 20 else cd
            for cd in class_descriptions
        ])
 
 
        # --- relevant classes ----------------------------------------------
        yield PipelineEvent("status", "Selecting relevant classes...")
        relevant_classes = detect_relevant_classes(
            question=question,
            class_descriptions=class_descriptions,
            llm_config=config["generation"],
        )
        relevant_classes = relevant_classes[:3]
        yield PipelineEvent("result", "Relevant classes selected", data=relevant_classes)
 
        trimmed_str_contexts = trim_contexts(contexts, max_tokens=config["generation"]["num_ctx"] - 1000)
        final_context = "\n".join(trimmed_str_contexts)
        print(estimate_tokens(final_context))
 
        # --- xquery generation ---------------------------------------------
        yield PipelineEvent("status", "Generating XQuery...")
        xquery = generate_xquery(context=final_context, question=question, classes=relevant_classes, llm_config=config["generation"])

        yield PipelineEvent("result", "Raw XQuery generated", data=xquery)

        xquery = postprocess_xquery(xquery, config["database"])
        yield PipelineEvent("result", "Postprocessed XQuery generated", data=xquery)
 
        # --- execution ------------------------------------------------------
        yield PipelineEvent("status", "Running query against the database...")
        db_result = db.execute_xquery(xquery)

        # --- answer generation -------------------------------------------------
        yield PipelineEvent("status", "Generating final answer...")
        answer = answer_question(context=db_result, question=question, llm_config=config["generation"])
        
        yield PipelineEvent("final", "Done", data=answer)
 
    except Exception as exc:  # surface any failure to the frontend
        yield PipelineEvent("error", "Pipeline failed", data=str(exc))




def run_rag_pipeline2(
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

        yield PipelineEvent("status", "Ensuring index presence...")
        db.ensure_fulltext_index(workdir)

        yield PipelineEvent("status", "Extracting keywords...")
        # keywords = extract_keywords(question, config["generation"])

        keywords = ['Δίσκος της Φαιστού']
        yield PipelineEvent("result", "Extracted keywords", data=keywords)

        yield PipelineEvent("status", "Searching the database...")
        res = db.multiple_string_search(keywords, workdir, partial_match=True)

        res = db.multiple_string_search_file(keywords, workdir, partial_match=True)

        print(res)
        exit()
        
        matching_fields = extract_matching_fields(res, keywords)
        print(matching_fields)
        yield PipelineEvent("result", "Extracted matching fields", data=matching_fields)

        relevant_classes = list(set(extract_class_names(res)))
        yield PipelineEvent("result", "Relevant classes selected", data=relevant_classes)

        print(relevant_classes)
        exit()

        # --- field descriptions -------------------------------------------
        yield PipelineEvent("status", "Loading field descriptions...")
        field_descriptions = load_from_index("field_descriptions", workdir_name, index_folder)
        if not field_descriptions:
            yield PipelineEvent("status", "No cached field descriptions found, generating them...")
            field_descriptions = build_field_descriptions(db, workdir)
            save_to_index("field_descriptions", field_descriptions, workdir_name, index_folder)
        yield PipelineEvent("status", "Field descriptions ready")

        contexts = build_class_contexts(db, workdir, field_descriptions, classes=relevant_classes)

        trimmed_str_contexts = trim_contexts(contexts, max_tokens=config["generation"]["num_ctx"] - 1000)
        final_context = "\n".join(trimmed_str_contexts)


        # --- xquery generation ---------------------------------------------
        yield PipelineEvent("status", "Generating XQuery...")
        xquery = generate_xquery(context=final_context, question=question, classes=relevant_classes, llm_config=config["generation"])

        yield PipelineEvent("result", "Raw XQuery generated", data=xquery)

        xquery = postprocess_xquery(xquery, config["database"])
        yield PipelineEvent("result", "Postprocessed XQuery generated", data=xquery)
 
        # --- execution ------------------------------------------------------
        yield PipelineEvent("status", "Running query against the database...")
        db_result = db.execute_xquery(xquery)

        # --- answer generation -------------------------------------------------
        yield PipelineEvent("status", "Generating final answer...")
        answer = answer_question(context=db_result, question=question, llm_config=config["generation"])
        
        yield PipelineEvent("final", "Done", data=answer)
 
    except Exception as exc:  # surface any failure to the frontend
        yield PipelineEvent("error", "Pipeline failed", data=str(exc))