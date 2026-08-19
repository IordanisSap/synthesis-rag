"""
app_streamlit.py

Minimal chat frontend for the RAG pipeline defined in rag_pipeline.py.

Run with:
    streamlit run app_streamlit.py
"""

import streamlit as st
import sys
from pathlib import Path
 
# frontend/app_streamlit.py -> project root is one level up.
# Streamlit only puts this file's own directory (frontend/) on sys.path,
# so without this, `from src...` would fail no matter what folder you
# launch `streamlit run` from.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.workflows.workflows import answer_with_search_results





from src.db import ExistDB
from config.loader import parse
from pathlib import Path
import logging

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import HttpUrl



class ExistDBSettings(BaseSettings):
    url: HttpUrl
    user: str
    password: str
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        env_prefix="exist_db_"
    )

exist_db_settings = ExistDBSettings() # type: ignore

index_folder = ".index"

CONFIG_PATH = Path("config/dev.toml")
config = parse(CONFIG_PATH)
workdir = config["database"]["workdir"]

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs.log"),
            logging.StreamHandler() # Also print to console
        ]
    )

setup_logging()
logger = logging.getLogger(__name__)


db = ExistDB(exist_db_settings.url, exist_db_settings.user, exist_db_settings.password)

QUESTION = "Are there findings made from silver?"





# TODO: wire these up to your real objects however you currently build them
# from your_project import db, workdir, config, index_folder

st.set_page_config(page_title="Synthesis RAG Chatbot - MESSARA", page_icon="🤖")
st.title("Synthesis RAG Chatbot - MESSARA")

if "history" not in st.session_state:
    st.session_state.history = []  # list of {"role": ..., "content": ...}

# replay previous turns on rerun
for turn in st.session_state.history:
    with st.chat_message(turn["role"]):
        st.markdown(turn["content"])

question = st.chat_input("Ask a question...")

if question:
    st.session_state.history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        status_box = st.status("Working on it...", expanded=True)
        final_answer = None

        for event in answer_with_search_results(question, db, workdir, config, index_folder):
            if event.type == "status":
                status_box.write(event.message)

            elif event.type == "result":
                status_box.write(f"**{event.message}**")
                if isinstance(event.data, str):
                    # Plain strings go through code block to prevent Markdown mangling
                    status_box.code(event.data, language="xquery")
                    
                elif isinstance(event.data, (list, tuple)):
                    # Catch arrays generically. If > 5, collapse it.
                    if len(event.data) > 5:
                        with status_box.expander(f"View {len(event.data)} items", expanded=False):
                            st.write(event.data)
                    else:
                        status_box.write(event.data)
                        
                else:
                    # Fallback for dicts, ints, or anything else
                    status_box.write(event.data)


            elif event.type == "error":
                status_box.update(label="Failed", state="error", expanded=True)
                st.error(event.data)
                final_answer = "Sorry, something went wrong while answering that."

            elif event.type == "final":
                final_answer = event.data
                status_box.update(label="Done", state="complete", expanded=False)

        st.markdown(final_answer)
        st.session_state.history.append({"role": "assistant", "content": final_answer})