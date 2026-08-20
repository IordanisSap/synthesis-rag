# Synthesis-RAG
SynthesisRAG is a Retrieval-Augmented Generation (RAG) system that offers Question Answering (QA) capabilities for any information system relying on Synthesis

## How to run

First, there should be a model running locally using either ollama or vllm. For example using the model `Qwen3.5-9B`
```
vllm serve Qwen/Qwen3.5-9B --quantization fp8 --max-model-len 32768 --gpu-memory-utilization 0.9 --enforce-eager
```

You can then run the pipeline using the following 2 methods:
### Run with frontend
```
streamlit run frontend/app_streamlit.py \
    --server.address 0.0.0.0 \
    --server.port 8501 \
    --server.headless true \
```

### Run just the pipeline (main.py)
`python -m src.main`



## How to set the database and configuration

For setting the database URL create a .env file with the same structure as the one in [.env.example](.env.example) and fill in the necessary credentials.

For example:
```
EXIST_DB_URL=http://<IP>/exist/rest/db
EXIST_DB_USER=user
EXIST_DB_PASSWORD=password
```

For configuring the collection to be indexed as well as the indexing and retrieval process change the [configuration](./config/dev.toml) file accordingly. More information can be found in the [configuration README](./config/README.md)