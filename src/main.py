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

from src.workflows.workflows import workflow1
from src.workflows.blocks.get_field_descriptions import get_field_descriptions
from src.workflows.blocks.trim_empty_fields import trim_empty_class_fields

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

field_descriptions = load_from_index("field_descriptions", workdir.split("/")[-1], INDEX_FOLDER)
if not field_descriptions:
    field_descriptions = get_field_descriptions(db, workdir)
    save_to_index("field_descriptions", field_descriptions, workdir.split("/")[-1], INDEX_FOLDER)


res = trim_empty_class_fields(field_descriptions["Person"]["fields"])
print(f"Trimmed Organization fields: {res}")
# QUESTION = "Can I visit Μονή Παναγίας Καλυβιανής by car?"
# QUESTION = "Find the names of all persons working in ΙΤΕ"
# workflow1(QUESTION, db, workdir, config, INDEX_FOLDER)
