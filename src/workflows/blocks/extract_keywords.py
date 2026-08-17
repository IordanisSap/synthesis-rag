from src.services.ai.prompts.registry import PromptBuilder, PromptTemplate
from src.services.ai.llm_client import call_LLM

def extract_keywords(question: str, llm_config: dict) -> list[str]:
    """
    Extracts keywords from the provided question.
    
    Args:
        question (str): The question for keyword extraction.
        llm_config (dict): The configuration for the LLM client.
    
    Returns:
        str: The extracted keywords.
    """
    system_prompt, user_prompt = PromptBuilder.build_messages(
        PromptTemplate.EXTRACT_KEYWORDS,
        {"question": question}
    )
    
    response = call_LLM(system_prompt, user_prompt, llm_config)
    keywords = [keyword.strip() for keyword in response.split(",") if keyword.strip()]
    return keywords
