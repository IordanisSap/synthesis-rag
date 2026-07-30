#!/usr/bin/env python3
"""
Scans an eXist-db collection for entity folders and builds a compact
field-value catalog for each one

An immediate child folder F of --root is considered an entity folder only if:
  1. It contains a resource named exactly "F.xml" (the template - all fields
     empty), directly inside F.
  2. It contains at least one subfolder that itself contains at least one
     .xml resource (the actual data instances).
Anything else (e.g. a folder with no matching template file, or a folder
whose subfolders don't have any .xml files) is skipped.

For each field/attribute path found (template U instances), it reports:
  - "always-empty"          never populated in the sample
  - "controlled-vocabulary" governed by an sps_vocabulary attribute
  - "enum"                  small, closed set of observed values
  - "free-text"             effectively unbounded (names, ids, uris, dates...)

All eXist-db access is plain HTTP GET, using the same URL pattern and the
same built-in directory-listing response (exist:collection / exist:resource)
as your existing ExistDB.list_contents /sps_vocabulary read_document methods. No XQuery
execution is used anywhere in this script.

Requires: pip install requests

Usage:
  python build_catalog.py \
      --url http://localhost:8080/exist \
      --user admin --password secret \
      --root /db/apps/messara/data \
      --output catalog.json
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from xml.etree import ElementTree as ET
import logging

from src.db import ExistDB
from src.schema.schema import get_class_filepaths

DEFAULT_XML_FIELDS_TO_TRIM = set(["admin"])

ENUM_MAX_DISTINCT_DEFAULT = 10  # hard cap on distinct values for "enum"
CONTROLLED_VOCAB_MAX_DISTINCT_DEFAULT = 10
ENUM_MAX_RATIO_DEFAULT = 0.3  # distinct/occurrences must also stay under this
FREE_TEXT_SAMPLES = 3  # how many example values to keep for free-text fields

XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
EXIST_NS = "http://exist.sourceforge.net/NS/exist"

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}:\d{2})?$")
TIME_RE = re.compile(r"^\d{2}:\d{2}:\d{2}$")
INT_RE = re.compile(r"^-?\d+$")
URI_RE = re.compile(r"^https?://")

logger = logging.getLogger(__name__)

def discover_entities(db: ExistDB, root: str, verbose: bool = True):
    """Find folders under root matching the template+data-subfolder rule."""
    entities = {}
    root_contents = db.list_contents(root)

    for folder in root_contents.folders:
        folder_path = f"{root}/{folder}"
        folder_contents = db.list_contents(folder_path)
        class_filepaths = get_class_filepaths(db, folder_contents)

        if not class_filepaths:
            if verbose:
                print(f"  skip {folder}: not a class folder")
            continue

        template_path, instance_files = class_filepaths

        entities[folder] = {
            "template": template_path,
            "instances": instance_files,
        }
        if verbose:
            print(f"  found {folder}: {len(instance_files)} instance file(s)")

    return entities


def local_name(tag: str) -> str:
    return tag.split("}", 1)[1] if tag.startswith("{") else tag


def is_noise_attribute(raw_name: str) -> bool:
    return raw_name.startswith(f"{{{XSI_NS}}}")


def walk(elem, prefix: str, doc_id: str, require_nonempty: bool, out: list):
    """Recursively collect {path, value, doc, vocab} observations from elem."""
    vocab = ""
    for raw_name, value in elem.attrib.items():
        if is_noise_attribute(raw_name):
            continue
        name = local_name(raw_name)
        value = value.strip()
        if name == "sps_vocabulary" and value:
            vocab = value
        if require_nonempty and not value:
            continue
        out.append(
            {"path": f"{prefix}/@{name}", "value": value, "doc": doc_id, "vocab": ""}
        )

    children = list(elem)
    if not children:
        text = (elem.text or "").strip()
        if not require_nonempty or text:
            out.append({"path": prefix, "value": text, "doc": doc_id, "vocab": vocab})
    else:
        for child in children:
            child_prefix = (
                f"{prefix}/{local_name(child.tag)}" if prefix else local_name(child.tag)
            )
            walk(child, child_prefix, doc_id, require_nonempty, out)


def guess_type(values):
    if not values:
        return "unknown"
    if all(DATE_RE.match(v) for v in values):
        return "date"
    if all(TIME_RE.match(v) for v in values):
        return "time"
    if all(INT_RE.match(v) for v in values):
        return "integer"
    if all(URI_RE.match(v) for v in values):
        return "uri"
    return "string"


def build_field_stats(
    template_paths, observations, enum_max_distinct, enum_max_ratio, cv_max_distinct
):
    by_path = defaultdict(list)
    for obs in observations:
        by_path[obs["path"]].append(obs)

    all_paths = set(template_paths) | set(by_path.keys())

    fields = []
    for path in sorted(all_paths):
        obs_list = by_path.get(path, [])
        values = [o["value"] for o in obs_list]
        occurrences = len(values)
        distinct = sorted(set(values))
        distinct_count = len(distinct)

        vocab_values = [o["vocab"] for o in obs_list if o["vocab"]]
        vocab_file = vocab_values[0] if vocab_values else None

        per_doc_counts = defaultdict(int)
        for o in obs_list:
            per_doc_counts[o["doc"]] += 1
        max_per_doc = max(per_doc_counts.values()) if per_doc_counts else 0

        ratio = (distinct_count / occurrences) if occurrences else 0

        if occurrences == 0:
            category = "always-empty"
        elif vocab_file:
            category = "controlled-vocabulary"
        elif distinct_count <= enum_max_distinct and ratio <= enum_max_ratio:
            category = "enum"
        else:
            category = "free-text"

        field = {
            "path": path,
            "occurrences": occurrences,
            "distinctCount": distinct_count,
            "repeatablePerDocument": max_per_doc > 1,
            "category": category,
        }
        if vocab_file:
            field["vocabularyFile"] = vocab_file
        if category == "free-text":
            field["dataType"] = guess_type(distinct)
            field["sampleValues"] = distinct[:FREE_TEXT_SAMPLES]
        if category == "enum":
            field["sampleValues"] = distinct
        if category == "controlled-vocabulary":
            field["sampleValues"] = distinct[:cv_max_distinct]

        fields.append(field)

    return fields


def build_catalog_for_entity(
    db, class_name, template_path, instance_paths, enum_max_distinct, enum_max_ratio, cv_max_distinct
):
    try:
        template_root = ET.fromstring(db.read_document_raw(template_path))
    except Exception as e:
        print(
            f"  ! skipping {class_name}: failed to read template {template_path}: {e}",
            file=sys.stderr,
        )
        return None

    template_obs = []
    walk(template_root, "", "TEMPLATE", False, template_obs)
    template_paths = {o["path"] for o in template_obs}

    observations = []
    for path in instance_paths:
        try:
            root_elem = ET.fromstring(db.read_document_raw(path))
        except Exception as e:
            print(f"    ! skipping {path}: {e}", file=sys.stderr)
            continue
        walk(root_elem, "", path, True, observations)

    fields = build_field_stats(
        template_paths, observations, enum_max_distinct, enum_max_ratio, cv_max_distinct
    )

    return {
        "class": class_name,
        "templatePath": template_path,
        "documentCount": len(instance_paths),
        "fields": fields,
    }


def build_catalog(
    db,
    root,
    enum_max_distinct=ENUM_MAX_DISTINCT_DEFAULT,
    enum_max_ratio=ENUM_MAX_RATIO_DEFAULT,
    cv_max_distinct=CONTROLLED_VOCAB_MAX_DISTINCT_DEFAULT,
    verbose=False,
):
    entities = discover_entities(db, root, verbose=verbose)
    if not entities:
        print(
            "No entity folders found matching the expected structure "
            "(Folder/Folder.xml + Folder/subfolder/*.xml)."
        )
        return {}

    catalog = {}
    for class_name, info in entities.items():
        print(f"Profiling {class_name} ({len(info['instances'])} instance file(s))...")
        catalog[class_name] = build_catalog_for_entity(
            db,
            class_name,
            info["template"],
            info["instances"],
            enum_max_distinct,
            enum_max_ratio,
            cv_max_distinct,
        )

    return catalog


def strip_fields(root, paths_to_remove: set) -> None:
    """
    Removes elements/attributes whose catalog-style path is in paths_to_remove.
    Mirrors the local-name, namespace-agnostic traversal used by walk()
    in build_catalog.py, so removal stays consistent with however
    'always-empty' was computed -- including repeated elements.
    """
    removals = []  # (parent, child) pairs, detached after the walk completes

    def recurse(elem, prefix, parent):
        for raw_name in list(elem.attrib.keys()):
            if is_noise_attribute(raw_name):
                continue
            attr_path = f"{prefix}/@{local_name(raw_name)}"
            if attr_path in paths_to_remove:
                del elem.attrib[raw_name]

        children = list(elem)
        if not children:
            if prefix in paths_to_remove and parent is not None:
                removals.append((parent, elem))
            return

        for child in children:
            child_prefix = (
                f"{prefix}/{local_name(child.tag)}" if prefix else local_name(child.tag)
            )
            recurse(child, child_prefix, elem)

    recurse(root, "", None)

    for parent, child in removals:
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


def trim_xml_fields(
    xml_str: str, paths_to_remove: set = DEFAULT_XML_FIELDS_TO_TRIM
) -> str:
    root = ET.fromstring(xml_str)
    strip_fields(root, paths_to_remove)
    prune_empty_containers(root)
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode")


def trim_empty_fields_catalog(fields: list) -> list:
    """
    Returns a list of fields with always-empty fields removed.
    """
    if not isinstance(fields, list):
        return fields

    return [
        field_info 
        for field_info in fields 
        if field_info.get("category") != "always-empty"
    ]



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

    final_fields = trim_empty_fields_catalog(catalogClass.get("fields", []))

    for field in final_fields:
        keys_to_keep = ["path", "category", "dataType", "sampleValues"]
        for key in list(field.keys()):
            if key not in keys_to_keep:
                del field[key]
    return final_fields