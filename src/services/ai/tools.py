from src.services.ai.llm_client import call_LLM
from src.schema.description import ClassContext
from src.services.ai.prompts.registry import PromptBuilder, PromptTemplate

def detect_relevant_classes(question: str, class_descriptions: dict, llm_config: dict) -> list[str]:
    """
    Detects relevant classes in the given question by checking for class names in the database schema.

    Args:
        question (str): The question string to analyze.
        class_descriptions (dict): A dictionary of class descriptions to check against.
        llm_config (dict): The configuration for the LLM.

    Returns:
        List[str]: A list of relevant class names found in the question.
    """

    llm_class_context = [f"{key}: {value}" for key, value in class_descriptions.items()]
    system_prompt, user_prompt = PromptBuilder.build_messages(
        PromptTemplate.SELECT_RELEVANT_CLASSES,
        {"question": question, "classes": "\n".join(llm_class_context)}
    )
    response = call_LLM(system_prompt, user_prompt, llm_config)
    return response.strip().split(",")