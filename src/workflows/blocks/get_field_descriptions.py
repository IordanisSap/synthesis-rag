
from src.db import ExistDB
import logging
from src.schema.fields import build_catalog, trim_xml_fields, trim_empty_fields_catalog


logger = logging.getLogger(__name__)

def build_field_descriptions(db: ExistDB, workdir: str):
    """
    Builds a catalog of field descriptions for all classes in the given workdir.
    """
    return build_catalog(db, workdir)
