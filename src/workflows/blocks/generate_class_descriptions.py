
from src.db import ExistDB
import logging
from src.context.class_context import get_class_context, ClassContext
from src.services.ai.llm_client import call_LLM
from src.services.ai.prompts.registry import PromptBuilder, PromptTemplate
from src.context.catalog.process import get_class_field_descriptions


logger = logging.getLogger(__name__)

def generate_class_descriptions(db: ExistDB, workdir: str, llm_config: dict) -> dict[str, str]:
    class_contexts = get_class_examples(db, workdir)
    descriptions = {}
    for class_context in class_contexts:
        system, user = PromptBuilder.build_messages(PromptTemplate.SUMMARIZE_CLASS, class_context.to_dict())
        response = call_LLM(system, user, llm_config)
        descriptions[class_context.name] = response
    return descriptions
            

    
def get_class_examples(db: ExistDB, workdir: str, classes: list[str] | None = None) -> list[ClassContext]:
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