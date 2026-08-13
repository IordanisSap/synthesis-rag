from src.services.ai.prompts.registry import PromptBuilder, PromptTemplate
from src.services.ai.llm_client import call_LLM

def answer_question(context: str, question: str, llm_config: dict) -> str:
    """
    Generates an answer based on the provided context and question.
    
    Args:
        context (str): The context or background information.
        question (str): The specific question or requirement for the answer.
        llm_config (dict): The configuration for the LLM client.
    
    Returns:
        str: The generated answer.
    """
    system_prompt, user_prompt = PromptBuilder.build_messages(
        PromptTemplate.RESPOND_TO_QUESTION,
        {"context": context, "question": question}
    )
    
    response = call_LLM(system_prompt, user_prompt, llm_config)
    return response
