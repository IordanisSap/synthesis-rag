
import logging
import json

from src.db import ExistDB
from src.context.class_context import get_class_context, ClassContext
from src.services.ai.llm_client import call_LLM
from src.services.ai.prompts.registry import PromptBuilder, PromptTemplate
from src.context.field_catalog.process import get_class_field_descriptions

# get_class_field_descriptions

logger = logging.getLogger(__name__)

def generate_class_descriptions(class_contexts, llm_config: dict) -> dict[str, str]:
    descriptions = {}
    for class_context in class_contexts:
        system, user = PromptBuilder.build_messages(PromptTemplate.SUMMARIZE_CLASS, {"name": class_context.name, "template": class_context.template, "fields": json.dumps(class_context.field_descriptions, ensure_ascii=False)})
        response = call_LLM(system, user, llm_config)
        descriptions[class_context.name] = response
    return descriptions
            

    
def build_class_contexts(db: ExistDB, workdir: str, field_descriptions: dict, classes: list[str] | None = None) -> list[ClassContext]:
    contents = db.list_contents(workdir)
    
    if len(contents.files) > 0:
        logger.warning('Found file in top level directory')

    contexts = []
    for class_folder in contents.folders:
        folder_path = f"{workdir}/{class_folder}"
        if classes is not None and class_folder not in classes:
            continue
        class_context = get_class_context(db, folder_path)
        if class_context is not None:
            class_context.field_descriptions = fill_class_context_fields(class_context, field_descriptions).field_descriptions
            contexts.append(class_context)
        else:
            logger.warning(f"Skipping class {class_folder} due to missing template or instances")
    return contexts


def fill_class_context_fields(classContext: ClassContext, catalog: dict) -> ClassContext:
    """
    Fills the field_descriptions of a ClassContext using the provided catalog.
    """
    class_name = classContext.name
    if class_name in catalog:
        classContext.field_descriptions = get_class_field_descriptions(catalog, class_name)
    else:
        logger.warning(f"No field descriptions found for class {class_name} in catalog.")
    return classContext