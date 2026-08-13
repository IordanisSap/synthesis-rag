
from src.context.class_context import contextToString, trim_contexts
from src.workflows.blocks.generate_class_descriptions import generate_class_descriptions, get_class_examples, fill_class_context_fields
from src.workflows.blocks.generate_xquery import generate_xquery
from src.workflows.blocks.get_field_descriptions import build_field_descriptions
from src.workflows.blocks.answer_question import answer_question

from src.services.ai.tools import detect_relevant_classes
from src.index.index import save_to_index, load_from_index
from src.xquery.postprocessing import postprocess_xquery

from src.db import ExistDB
from src.services.ai.token_estimator import estimate_tokens


def workflow1(question: str, db: ExistDB, workdir: str, config: dict, index_folder: str):
    descs = load_from_index("class_descriptions", workdir.split("/")[-1], index_folder)
    if not descs:
        descs = generate_class_descriptions(db, workdir, config["generation"])
        save_to_index("class_descriptions", descs, workdir.split("/")[-1], index_folder)



    relevant_classes = detect_relevant_classes(
        question=question,
        class_descriptions=descs,
        llm_config=config["generation"]
    )



    contexts = get_class_examples(db, workdir, classes=relevant_classes)
    xquery = generate_xquery(context="\n".join([contextToString(context) for context in contexts]), 
                            question=question, 
                            llm_config=config["generation"])

    print(f"Raw XQuery:\n{xquery}\n")
    xquery = postprocess_xquery(xquery, config["database"])
    print(f"Postprocessed XQuery:\n{xquery}\n")
    print(db.execute_xquery(xquery))



def workflow2(question: str, db: ExistDB, workdir: str, config: dict, index_folder: str):
    class_descriptions = load_from_index("class_descriptions", workdir.split("/")[-1], index_folder)
    if not class_descriptions:
        class_descriptions = generate_class_descriptions(db, workdir, config["generation"])
        save_to_index("class_descriptions", class_descriptions, workdir.split("/")[-1], index_folder)

    field_descriptions = load_from_index("field_descriptions", workdir.split("/")[-1], index_folder)
    if not field_descriptions:
        field_descriptions = build_field_descriptions(db, workdir)
        save_to_index("field_descriptions", field_descriptions, workdir.split("/")[-1], index_folder)


    print(class_descriptions)
    relevant_classes = detect_relevant_classes(
        question=question,
        class_descriptions=class_descriptions,
        llm_config=config["generation"]
    )
    # relevant_classes = ["Person"]
    print(relevant_classes)
    relevant_classes = relevant_classes[:3]
    contexts = get_class_examples(db, workdir, classes=relevant_classes)

    contexts = [fill_class_context_fields(context, field_descriptions) for context in contexts]
    trimmed_str_contexts = trim_contexts(contexts, max_tokens=config["generation"]["num_ctx"] - 1000)

    # for context in contexts:
    #     print(f"Class: {context.name}")
    #     print(f"Template: {context.template}")
    #     print(f"Example Instances: {context.example_instances}")
    #     print(f"Field Descriptions: {context.field_descriptions}")
    #     print("\n")

    final_context = "\n".join(trimmed_str_contexts)
    # print(final_context)
    # with open("tmp_context.txt", "w", encoding="utf-8") as f:
    #     f.write(final_context)

    # print(estimate_tokens(final_context))
    # exit()
    xquery = generate_xquery(context=final_context, 
                        question=question, 
                        llm_config=config["generation"])

    print(f"Raw XQuery:\n{xquery}\n")
    xquery = postprocess_xquery(xquery, config["database"])
    print(f"Postprocessed XQuery:\n{xquery}\n")
    print(db.execute_xquery(xquery))











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
    db,
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
        # --- class descriptions ------------------------------------------
        yield PipelineEvent("status", "Loading class descriptions...")
        class_descriptions = load_from_index("class_descriptions", workdir_name, index_folder)
        if not class_descriptions:
            yield PipelineEvent("status", "No cached class descriptions found, generating them...")
            class_descriptions = generate_class_descriptions(db, workdir, config["generation"])
            save_to_index("class_descriptions", class_descriptions, workdir_name, index_folder)
        # yield PipelineEvent("result", "Class descriptions ready", data=class_descriptions)
 
        # --- field descriptions -------------------------------------------
        yield PipelineEvent("status", "Loading field descriptions...")
        field_descriptions = load_from_index("field_descriptions", workdir_name, index_folder)
        if not field_descriptions:
            yield PipelineEvent("status", "No cached field descriptions found, generating them...")
            field_descriptions = build_field_descriptions(db, workdir)
            save_to_index("field_descriptions", field_descriptions, workdir_name, index_folder)
        yield PipelineEvent("result", "Field descriptions ready")
 
        # --- relevant classes ----------------------------------------------
        yield PipelineEvent("status", "Selecting relevant classes...")
        relevant_classes = detect_relevant_classes(
            question=question,
            class_descriptions=class_descriptions,
            llm_config=config["generation"],
        )
        relevant_classes = relevant_classes[:3]
        yield PipelineEvent("result", "Relevant classes selected", data=relevant_classes)
 
        # --- context building ------------------------------------------------
        # yield PipelineEvent("status", "Fetching examples for the selected classes...")
        contexts = get_class_examples(db, workdir, classes=relevant_classes)
 
        # yield PipelineEvent("status", "Filling in field context...")
        contexts = [fill_class_context_fields(context, field_descriptions) for context in contexts]
 
        # yield PipelineEvent("status", "Trimming context to fit the model's context window...")
        trimmed_str_contexts = trim_contexts(contexts, max_tokens=config["generation"]["num_ctx"] - 1000)
        final_context = "\n".join(trimmed_str_contexts)
        # yield PipelineEvent("result", "Context ready", data=final_context)
 
        # --- xquery generation ---------------------------------------------
        yield PipelineEvent("status", "Generating XQuery...")
        xquery = generate_xquery(context=final_context, question=question, llm_config=config["generation"])
        xquery = postprocess_xquery(xquery, config["database"])
        yield PipelineEvent("result", "XQuery generated", data=xquery)
 
        # --- execution ------------------------------------------------------
        yield PipelineEvent("status", "Running query against the database...")
        db_result = db.execute_xquery(xquery)

        # --- answer generation -------------------------------------------------
        yield PipelineEvent("status", "Generating final answer...")
        answer = answer_question(context=db_result, question=question, llm_config=config["generation"])
        
        yield PipelineEvent("final", "Done", data=answer)
 
    except Exception as exc:  # noqa: BLE001 - surface any failure to the frontend
        yield PipelineEvent("error", "Pipeline failed", data=str(exc))
