from src.db import ExistDB
from src.context.catalog.process import postprocess_xml_fields
from src.services.ai.token_estimator import estimate_tokens
from src.schema import get_template_filepath, NoInstanceError, get_instances_filepaths
import logging
from collections.abc import Sequence
from dataclasses import dataclass, asdict, field
from typing import Any
import json

logger = logging.getLogger(__name__)
DEFAULT_SAMPLE_COUNT = 3

@dataclass
class ClassContext:
    name: str
    template: str
    example_instances: list[str]
    field_descriptions: list[dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self, delimiter: str = "\n\n") -> dict:
        data = asdict(self)
        data['instances'] = delimiter.join(self.example_instances)
        
        return data

def get_class_context(db: ExistDB, folder_path: str, samples : int = DEFAULT_SAMPLE_COUNT):
    folder_content = db.list_contents(folder_path)
    templateFile = get_template_filepath(folder_content)

    if templateFile:
        templateFileContent = db.read_document(templateFile)
        
        # Assuming all folders contain data
        instanceFolders = get_instances_filepaths(folder_content)
        if len(instanceFolders) == 0:
            error_msg = f"No data instance exists in: {folder_content.path} \n A data instance is required to produce the class description"
            logger.error(error_msg)
            return None                 # TODO: Skip this for now, see later how templates without instances should be handled

        instanceFileContents = get_class_samples(db, instanceFolders, samples)

        return ClassContext(
            name=folder_content.path.split("/")[-1],
            template=postprocess_xml_fields(templateFileContent),
            example_instances=instanceFileContents,
        )


    else:
        logger.info(f"{folder_path} does not contain a template and will not be indexed)")
        return None
    

def get_class_samples(db: ExistDB, instance_folders: Sequence[str], samples : int = DEFAULT_SAMPLE_COUNT):
    """
    Returns a list of sample instances from the given folder path.
    """
    instanceFolderContent = db.list_contents(f"{instance_folders[0]}")

    if len(instanceFolderContent.files) == 0:
        error_msg = f"No data instance exists in: {instanceFolderContent.path} \n A data instance is required to produce the class description"
        logger.error(error_msg)
        raise NoInstanceError(error_msg)
    
    chosenSamples = instanceFolderContent.files[:samples]

    instanceFileContents = [
        postprocess_xml_fields(db.read_document(f"{instanceFolderContent.path}/{sample}"))
        for sample in chosenSamples
    ]

    return instanceFileContents


def contextToString(class_details: ClassContext) -> str:
    """
    Constructs a context string for XQuery generation based on class details.

    Args:
        class_details (ClassDescription): An instance of ClassDescription containing details about the class.

    Returns:
        str: A formatted context string for XQuery generation.
    """
    context_parts = []
    
    if class_details.name:
        context_parts.append(f"Class Name: {class_details.name}")
    
    if class_details.template:
        context_parts.append(f"Template: \n{class_details.template}")
    
    # if class_details.example_instances:
    #     instances_info = '\n'.join(class_details.example_instances)
    #     context_parts.append(f"Example Instances: \n{instances_info}")

    if class_details.field_descriptions:
        field_info = ', '.join(json.dumps(field, ensure_ascii=False) for field in class_details.field_descriptions)
        context_parts.append(f"Field Descriptions: {field_info}")
    
    context_string = "\n".join(context_parts)
    
    return context_string


MAX_CLASS_NUM = 3

def trim_contexts(contexts: list[ClassContext], max_tokens: int) -> list[str]:
    """
    Trims the contexts to fit within the specified maximum token limit.

    Args:
        contexts (list[ClassContext]): A list of ClassContext instances.
        max_tokens (int): The maximum number of tokens allowed.

    Returns:
        str: A string representation of the trimmed contexts.
    """
    trimmed_contexts = []
    total_tokens = 0

    for context in contexts:
        processed_context = trim_context(context)
        context_str = contextToString(processed_context)
        context_tokens = estimate_tokens(context_str)

        if total_tokens + context_tokens <= max_tokens and len(trimmed_contexts) < MAX_CLASS_NUM:
            trimmed_contexts.append(context_str)
            total_tokens += context_tokens
        else:
            break

    return trimmed_contexts


ENUM_MAX = 10
CONTROLLED_VOCAB_MAX = 10
FREE_TEXT_SAMPLES = 5

def trim_context(context: ClassContext) -> ClassContext:
    """
    Trims the field descriptions of a ClassContext to avoid catalog bloat.

    Args:
        context (ClassContext): An instance of ClassContext.

    Returns:
        ClassContext: A new instance of ClassContext with trimmed field descriptions.
    """

    for field in context.field_descriptions:
        if field["category"] == "enum":
            max_distinct = ENUM_MAX
        elif field["category"] == "controlled-vocab":
            max_distinct = CONTROLLED_VOCAB_MAX
        else:
            max_distinct = FREE_TEXT_SAMPLES

        field["sampleValues"] = field["sampleValues"][:max_distinct]

    return context