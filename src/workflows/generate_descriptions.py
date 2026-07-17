from dotenv import load_dotenv
import os

from emoji import config
from src.db import ExistDB, ExistDBError
from config.loader import parse
from pathlib import Path
import logging
from src.schema.validation import get_template
from src.schema.description import produce_class_description
from src.services.ai.llm_client import call_LLM

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import HttpUrl

logger = logging.getLogger(__name__)

def generate_descriptions(db: ExistDB, workdir: str, config: dict):
    try:
        contents = db.list_contents(workdir)
        
        if len(contents.files) > 0:
            logger.warning('Found file in top level directory')

        descriptions = {}
        for class_folder in contents.folders:
            folder_path = f"{workdir}/{class_folder}"
            system, user = produce_class_description(db, folder_path)

            if system is not None and user is not None:
                response = call_LLM(system, user, config["generation"])
                descriptions[class_folder] = response
            
    except ExistDBError as e:
        logger.critical(f"Aborting execution due to database error: {e}")