from ollama import ChatResponse
from ollama import chat as ollama_chat
from openai import OpenAI

def call_LLM(system_prompt: str, user_prompt: str, model_config) -> str:
    provider = model_config.get("provider", None)
    if not provider:
        raise ValueError("Provider is required in model_config.")

    if provider == "ollama":
        response = call_ollama(system_prompt, user_prompt, model_config)
    elif provider == "vllm":
        response = call_vllm(system_prompt, user_prompt, model_config)
    else:
        raise ValueError(f"Provider {provider} is not supported.")

    if response is None:
        raise RuntimeError(f"Failed to call llm with config {model_config}")
    return response


def call_ollama(system_prompt, user_prompt, model_config) -> str | None:
    model = model_config.get("model", None)
    if not model:
        raise ValueError("Model is required for Ollama provider.")

    response: ChatResponse = ollama_chat(
        model=model,
        options={'temperature': model_config.get('temperature', 0.1), 'num_ctx': model_config.get('num_ctx', 2048)},
        think=False,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )
    return response.message.content


def call_vllm(system_prompt, user_prompt, model_config) -> str | None:
    model = model_config.get("model", None)
    if not model:
        raise ValueError("Model is required for vLLM provider.")

    base_url = model_config.get("base_url", "http://localhost:8000/v1")
    api_key = model_config.get("api_key", "EMPTY")  # vLLM ignores this unless you set --api-key

    client = OpenAI(base_url=base_url, api_key=api_key)

    response = client.chat.completions.create(
        model=model,
        temperature=model_config.get("temperature", 0.1),
        max_tokens=model_config.get("max_tokens", 2048),
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.choices[0].message.content
    print(content)
    return content