
from src.db import ExistDB
import logging
from src.schema.field_values import build_catalog


logger = logging.getLogger(__name__)

def get_field_descriptions(db: ExistDB, workdir: str):
    return build_catalog(db, workdir)

            

    
def filter_class_fields(class_fields: dict, relevant_fields: list[str]) -> dict:
    """
    Filters the class fields based on the relevant fields.

    Args:
        class_fields (dict): The dictionary containing class fields.
        relevant_fields (list[str]): The list of relevant field names.

    Returns:
        dict: A dictionary containing only the relevant class fields.
    """
    filtered_fields = {field: description for field, description in class_fields.items() if field in relevant_fields}
    return filtered_fields