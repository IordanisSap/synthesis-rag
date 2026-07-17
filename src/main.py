from dotenv import load_dotenv
import os
from src.db import ExistDB, ExistDBError
from config.loader import parse
from pathlib import Path
import logging
from src.schema.validation import get_template
from src.schema.description import produce_class_description
from src.services.ai.llm_client import call_LLM

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import HttpUrl

from src.workflows.generate_descriptions import generate_descriptions

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

descs = generate_descriptions(db, workdir, config)
print(descs)