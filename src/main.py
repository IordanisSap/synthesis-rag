from src.db import ExistDB
from config.loader import parse
from pathlib import Path
import logging

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import HttpUrl

from src.workflows.workflows import answer_with_search_results


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

INDEX_FOLDER = config["search"]["index_path"]
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
# QUESTION = "Υπάρχουν αντικείμενα από χρυσό στο μουσείο;"
QUESTION = "πού έχουν εντοπιστεί τα αρχαιότερα κατάλοιπα ανθρώπινης παρουσίας στην πεδιάδα της Μεσαράς και πότε χρονολογούνται?"


print(list(answer_with_search_results(QUESTION, db, workdir, config, INDEX_FOLDER)))



