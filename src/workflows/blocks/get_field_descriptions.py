
from src.db import ExistDB
import logging
from src.schema.fields import build_catalog, trim_xml_fields, trim_empty_fields_catalog


logger = logging.getLogger(__name__)

def build_field_descriptions(db: ExistDB, workdir: str):
    """
    Builds a catalog of field descriptions for all classes in the given workdir.
    """
    return build_catalog(db, workdir)


def get_class_field_descriptions(catalog: dict, className: str) -> list:
    """
    Returns a list of field descriptions for the specified classes in the given workdir.
    If no classes are specified, returns field descriptions for all classes.
    """
    if not isinstance(catalog, dict):
        logger.warning("Catalog is not a dictionary. Returning empty field descriptions.")
        return []

    if className not in catalog:
        logger.warning(f"Class '{className}' not found in catalog. Returning empty field descriptions.")
        return []

    catalogClass = catalog[className]

    if "fields" not in catalogClass or not isinstance(catalogClass["fields"], list):
        logger.warning("Catalog does not contain a valid 'fields' list. Returning empty field descriptions.")
        return []

    return trim_empty_fields_catalog(catalogClass.get("fields", []))