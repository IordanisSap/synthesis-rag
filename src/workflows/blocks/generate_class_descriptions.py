
from src.db import ExistDB, ExistDBError
import logging
from src.schema.description import get_class_context, ClassContext
from src.services.ai.llm_client import call_LLM
from src.services.ai.prompts.registry import PromptBuilder, PromptTemplate


logger = logging.getLogger(__name__)

def generate_class_descriptions(db: ExistDB, workdir: str, llm_config: dict):
    class_contexts = get_class_contexts(db, workdir)
    descriptions = {}
    for class_context in class_contexts:
        system, user = PromptBuilder.build_messages(PromptTemplate.SUMMARIZE_CLASS, class_context.to_dict())
        response = call_LLM(system, user, llm_config)
        descriptions[class_context.name] = response
    return descriptions
            

    
def get_class_contexts(db: ExistDB, workdir: str, classes: list[str] | None = None) -> list[ClassContext]:
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
            logger.info(f"Found data class {class_context.name}")
            contexts.append(class_context)
    return contexts
            