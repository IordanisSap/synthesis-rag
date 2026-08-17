from src.services.ai.prompts.registry import PromptBuilder, PromptTemplate
from src.services.ai.llm_client import call_LLM

def generate_xquery(context: str, question: str, classes: list[str], llm_config: dict) -> str:
    """
    Generates an XQuery based on the provided context and question.
    
    Args:
        context (str): The context or background information for the query.
        question (str): The specific question or requirement for the XQuery.
        collection_path (str): The path to the collection to query.
        llm_config (dict): The configuration for the LLM client.
    
    Returns:
        str: The generated XQuery.
    """
    system_prompt, user_prompt = PromptBuilder.build_messages(
        PromptTemplate.GENERATE_XQUERY,
        {"context": context, "classes":"\n".join(classes), "question": question}
    )

    response = call_LLM(system_prompt, user_prompt, llm_config)
    return response
