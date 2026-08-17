
from src.db import ExistDB
import logging
from src.context.field_catalog.create import build_catalog


logger = logging.getLogger(__name__)

def build_field_descriptions(db: ExistDB, workdir: str):
    """
    Builds a catalog of field descriptions for all classes in the given workdir.
    """
    return build_catalog(db, workdir)
