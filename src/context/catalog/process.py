import argparse
import json
import re
import sys
from collections import defaultdict
from xml.etree import ElementTree as ET
import logging

from src.db import ExistDB
from src.schema import get_class_filepaths
from src.context.filtering import (
    is_noise_attribute,
    local_name,
    DEFAULT_XML_FIELDS_TO_TRIM,
    MAX_STRING_LENGTH,
)

logger = logging.getLogger(__name__)


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

    final_fields = postprocess_catalog_fields(catalogClass["fields"])
    # keys_to_keep = ["category", "dataType", "sampleValues"]
    keys_to_keep = ["dataType", "sampleValues"]

    return [
        {
            "field": f["path"], 
            **{k: f[k] for k in keys_to_keep if k in f}
        }
        for f in final_fields
    ]


def strip_fields(root, paths_to_remove: set[str]) -> None:
    """
    Removes elements/attributes whose catalog-style path is in paths_to_remove.
    Mirrors the local-name, namespace-agnostic traversal used by walk()
    in build_catalog.py, so removal stays consistent with however
    'always-empty' was computed -- including repeated elements.
    """
    removals = []  # (parent, child) pairs, detached after the walk completes

    def recurse(elem, prefix, parent):
        # 1. If this element's path is marked for removal, queue it and stop recursing
        if prefix in paths_to_remove and parent is not None:
            removals.append((parent, elem))
            return

        # 2. Check and remove attributes
        for raw_name in list(elem.attrib.keys()):
            if is_noise_attribute(raw_name):
                continue
            attr_path = f"{prefix}/@{local_name(raw_name)}"
            if attr_path in paths_to_remove:
                del elem.attrib[raw_name]

        # 3. Recurse into children
        for child in list(elem):
            child_prefix = (
                f"{prefix}/{local_name(child.tag)}" if prefix else local_name(child.tag)
            )
            recurse(child, child_prefix, elem)

    # Start recursion
    recurse(root, "", None)

    # Apply removals safely
    for parent, child in removals:
        # Check if child is still in parent (handles duplicate/repeated elements safely)
        if child in parent:
            parent.remove(child)


def prune_empty_containers(root) -> None:
    """
    Removes elements that ended up empty (no text, no children, no
    meaningful attributes) after strip_fields has run.
    """

    def is_empty(elem) -> bool:
        text_empty = not (elem.text or "").strip()
        no_children = len(elem) == 0
        no_real_attrs = not any(not is_noise_attribute(name) for name in elem.attrib)
        return text_empty and no_children and no_real_attrs

    def recurse(elem):
        to_remove = []
        for child in list(elem):
            recurse(child)
            if is_empty(child):
                to_remove.append(child)
        for child in to_remove:
            elem.remove(child)

    recurse(root)

def postprocess_xml_fields(
    xml_str: str,
    paths_to_remove: set[str] = set(DEFAULT_XML_FIELDS_TO_TRIM),
    max_length: int = MAX_STRING_LENGTH,
) -> str:
    """
    Filters out unwanted XML fields and crops long text values.
    """
    root = ET.fromstring(xml_str)
    paths_to_remove = paths_to_remove | set(DEFAULT_XML_FIELDS_TO_TRIM)

    def crop_text(text: str):
        if text is None:
            return None
        return text if len(text) <= max_length else text[:max_length] + "..."

    removals = []

    def recurse(elem, prefix, parent):
        if prefix in paths_to_remove and parent is not None:
            removals.append((parent, elem))
            return

        elem.text = crop_text(elem.text)
        elem.tail = crop_text(elem.tail)

        for raw_name in list(elem.attrib.keys()):
            if is_noise_attribute(raw_name):
                continue
            attr_path = f"{prefix}/@{local_name(raw_name)}"
            if attr_path in paths_to_remove:
                del elem.attrib[raw_name]
            else:
                elem.attrib[raw_name] = crop_text(elem.attrib[raw_name])

        for child in list(elem):
            child_prefix = f"{prefix}/{local_name(child.tag)}" if prefix else local_name(child.tag)
            recurse(child, child_prefix, elem)

    recurse(root, "", None)

    for parent, child in removals:
        if child in parent:
            parent.remove(child)

    prune_empty_containers(root)
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode")


def postprocess_catalog_fields(
    fields: list,
    paths_to_remove: set[str] = set(DEFAULT_XML_FIELDS_TO_TRIM),
    max_length: int = MAX_STRING_LENGTH,
) -> list:
    """
    Filters out unwanted catalog fields and crops long sample values.
    """
    if not isinstance(fields, list):
        return fields

    filtered_fields = [
        field_info 
        for field_info in fields 
        if field_info.get("category") != "always-empty" and field_info.get("path").split("/")[0] not in paths_to_remove
    ]

    for field_info in filtered_fields:
        if "sampleValues" in field_info and isinstance(field_info["sampleValues"], list):
            field_info["sampleValues"] = [
                value if len(value) <= max_length else value[:max_length] + "..."
                for value in field_info["sampleValues"]
            ]

    return filtered_fields