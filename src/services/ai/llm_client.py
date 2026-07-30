from ollama import ChatResponse
from ollama import chat as ollama_chat


def call_LLM(system_prompt : str, user_prompt : str, model_config) -> str:
    provider = model_config.get("provider", None)

    if not provider:
        raise ValueError("Provider is required in model_config.")

    if provider == "ollama":
        resposne = call_ollama(system_prompt, user_prompt, model_config)
        if resposne == None:
            raise RuntimeError(f"Failed to call llm with config {model_config}")
        return resposne
    
    else:
        raise ValueError(f"Provider {provider} is not supported.")
    
def call_ollama(system_prompt, user_prompt, model_config) -> str | None:
    model = model_config.get("model", None)
    if not model:
        raise ValueError("Model is required for Ollama provider.")
    
    options = {}
    
    options.update(model_config)

    response: ChatResponse = ollama_chat(
        model=model,
        options={'temperature': model_config.get('temperature', 0.1), 'num_ctx': model_config.get('num_ctx', 2048)},
        think=False,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )

    print(response.message.content)
    return response.message.content