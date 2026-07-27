from src.services.ai.tools import detect_relevant_classes

def detect_relevant_classes(question: str, class_descriptions: dict, llm_config: dict) -> list:
    """
    Detects relevant classes based on the provided question and class descriptions.

    Args:
        question (str): The question to analyze.
        class_descriptions (dict): A dictionary containing class descriptions.
        llm_config (dict): Configuration for the language model.

    Returns:
        list: A list of relevant classes.
    """
    relevant_classes = detect_relevant_classes(
        question=question,
        class_descriptions=class_descriptions,
        llm_config=llm_config
    )

    return relevant_classes


