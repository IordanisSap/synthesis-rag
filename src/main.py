from dotenv import load_dotenv
import os
from src.db import ExistDB, ExistDBError
from config.loader import parse
from pathlib import Path
import logging


from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import HttpUrl
load_dotenv()
class ExistDBSettings(BaseSettings):
    url: HttpUrl  # Validates that it's a real URL
    user: str
    password: str
    
    # Automatically loads from your .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

# Instantiating the class validates everything immediately
exist_db_settings = ExistDBSettings() # type: ignore


CONFIG_PATH = Path("config/dev.toml")
config = parse(CONFIG_PATH)
workdir = config["database"]["workdir"]

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("myapp.log"),
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
        print(folder_path)
        
        sub_contents = db.list_contents(folder_path)
        
        print(sub_contents)

except ExistDBError as e:
    logger.critical(f"Aborting execution due to database error: {e}")