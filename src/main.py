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
from src.xquery.postprocessing import set_xquery_collection

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import HttpUrl

from src.workflows.generate_descriptions import generate_descriptions, get_class_contexts
from src.workflows.generate_xquery import generate_xquery

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

# descs = generate_descriptions(db, workdir, config["generation"])
# print(descs)


contexts = get_class_contexts(db, workdir)

# xquery = generate_xquery(context="", question="Find the names of all persons working in 'ΙΤΕ'", llm_config=config["generation"])
# print(xquery)


xquery = generate_xquery(context="\n".join([build_class_xquery_context(context) for context in contexts]), 
                         question="Find the names of all persons working in 'ΙΤΕ'", 
                         llm_config=config["generation"])

xquery = set_xquery_collection(xquery, config["database"])

print(xquery)

print(db.execute_xquery(xquery))