from dotenv import load_dotenv
import os
from src.db import ExistDB, ExistDBError
from config.loader import parse
from pathlib import Path
import logging
from src.schema.schema import get_template_filepath
from src.services.ai.llm_client import call_LLM
from src.schema.description import get_class_context, ClassContext
from src.xquery.build_context import build_class_xquery_context
from src.xquery.postprocessing import postprocess_xquery

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import HttpUrl

from src.workflows.workflows import workflow1, workflow2

from src.index.index import save_to_index, load_from_index

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

INDEX_FOLDER = ".index"

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

workflow2("Find the names of all persons working in ΙΤΕ", db, workdir, config, INDEX_FOLDER)


# QUESTION = "Can I visit Μονή Παναγίας Καλυβιανής by car?"
# QUESTION = "Find the names of all persons working in ΙΤΕ"
# workflow1(QUESTION, db, workdir, config, INDEX_FOLDER)
