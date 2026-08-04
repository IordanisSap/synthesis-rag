import tiktoken

DEFAULT_MAX_TOKENS = 32784

def estimate_tokens(text: str) -> int:
    """
    Returns a fast token estimation for any LLM using a general, modern tokenizer.
    Uses 'o200k_base', which is highly compressed and fast for large strings.
    """
    encoding = tiktoken.get_encoding("o200k_base")
    return len(encoding.encode(text, disallowed_special=()))