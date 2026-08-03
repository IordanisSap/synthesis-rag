from xml.etree import ElementTree as ET


XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
EXIST_NS = "http://exist.sourceforge.net/NS/exist"
DEFAULT_XML_FIELDS_TO_TRIM = ["admin"]
MAX_STRING_LENGTH = 50                 # Used to crop very long strings

def local_name(tag: str) -> str:
    return tag.split("}", 1)[1] if tag.startswith("{") else tag


def is_noise_attribute(raw_name: str) -> bool:
    return raw_name.startswith(f"{{{XSI_NS}}}")

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
