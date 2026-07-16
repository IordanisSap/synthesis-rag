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

try:
    contents = db.list_contents(workdir)
    
    if len(contents.files) > 0:
        logger.warning('Found file in top level directory')

    for class_folder in contents.folders:
        folder_path = f"{workdir}/{class_folder}"
        system, user = produce_class_description(db, folder_path)

        if system is not None and user is not None:
            response = call_LLM(system, user, config["generation"])
            print(response)


except ExistDBError as e:
    logger.critical(f"Aborting execution due to database error: {e}")