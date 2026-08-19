import functools
from transformers import AutoTokenizer


DEFAULT_MODEL = "Qwen/Qwen3.5-9B"

@functools.lru_cache(maxsize=16)
def _get_tokenizer(model_id: str):
    """
    Loads and caches the fast tokenizer for a given Hugging Face model ID.
    The lru_cache ensures this heavy operation only runs once per model.
    """
    print(f"Loading tokenizer for {model_id} into cache...")
    return AutoTokenizer.from_pretrained(model_id, use_fast=True)

def count_tokens(text: str, model_id: str = DEFAULT_MODEL) -> int:
    """
    Returns the exact token count for any text using the specified open-weights model.
    """
    tokenizer = _get_tokenizer(model_id)
    return len(tokenizer.encode(text))