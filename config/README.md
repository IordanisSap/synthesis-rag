# Synthesis-RAG configuration

This config file can be used to configure the following:

* Database
    * base_path: Base path of eXist-db, usually "/db"
    * workdir: The path of the collection to be indexed


* Search
    * index_path: Directory where the search index is stored/loaded from
    * workdir: ignore_tags: List of XML/HTML tags whose content should be excluded when building the index

* Generation
    * model: Identifier of the LLM used to generate responses
    * provider: Backend serving the model (e.g. "vllm", "ollama", "openai")
    * temperature: Sampling temperature for generation; lower values (e.g. 0.10) produce more deterministic, focused output
    * num_ctx: Maximum context window size, in tokens, the model can use for a request
    * num_predict: Maximum number of tokens the model will generate in its response