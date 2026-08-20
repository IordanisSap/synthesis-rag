### Run in background
```
nohup streamlit run frontend/app_streamlit.py \
    --server.address 0.0.0.0 \
    --server.port 8501 \
    --server.headless true \
    >> streamlit.log 2>&1 &
disown
```