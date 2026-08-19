from xml.etree import ElementTree as ET

XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
EXIST_NS = "http://exist.sourceforge.net/NS/exist"
DEFAULT_XML_FIELDS_TO_TRIM = ["admin"]


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




def extract_class_names(raw_xml_string: str) -> list[str]:
    """
    Parses the raw eXist-db XML response and extracts the root tag name 
    (class name) of each returned document.
    """
    if not raw_xml_string or not raw_xml_string.strip():
        return []
        
    # Wrap in a dummy root to ensure valid XML parsing when multiple documents are returned
    safe_xml = f"<results>{raw_xml_string}</results>"
    class_names = []
    
    try:
        root = ET.fromstring(safe_xml)
        
        for element in root:
            # eXist-db's REST API sometimes wraps the output in an <exist:result> tag.
            # If we hit that wrapper, we iterate through its children instead.
            if "result" in element.tag:
                for hit in element:
                    # hit.tag might look like '{http://namespace.com}Organization'
                    # We split on '}' and take the last part to get just 'Organization'
                    class_name = hit.tag.split('}')[-1]
                    class_names.append(class_name)
            else:
                class_name = element.tag.split('}')[-1]
                class_names.append(class_name)
                
    except ET.ParseError as e:
        print(f"XML Parsing Error: {e}")
        
    return class_names


def remove_greek_tones(text: str) -> str:
    """Helper function to replicate eXist-db's tone and case insensitivity."""
    text = text.lower()
    tones = 'άέήίόύώϊϋΐΰ'
    no_tones = 'αεηιουωιυιυ'
    return text.translate(str.maketrans(tones, no_tones))

def extract_matching_fields(raw_xml_string: str, keywords: list[str]) -> list[dict]:
    """
    Parses the raw XML and extracts the fields containing the keywords.
    Returns a list of dicts with the FULL XML PATH to the field.
    """
    if not raw_xml_string or not raw_xml_string.strip():
        return []
        
    normalized_kws = [remove_greek_tones(kw.strip()) for kw in keywords if kw.strip()]
    safe_xml = f"<results>{raw_xml_string}</results>"
    extracted_data = []
    
    try:
        root = ET.fromstring(safe_xml)
        
        def walk_tree(element, current_path, class_name):
            # 1. Check the text of the current element
            if element.text and element.text.strip():
                original_text = element.text.strip()
                norm_text = remove_greek_tones(original_text)
                
                if any(kw in norm_text for kw in normalized_kws):
                    extracted_data.append({
                        "class": class_name,
                        "field_path": current_path,
                        "value": original_text
                    })
            
            for child in element:
                child_name = child.tag.split('}')[-1]
                new_path = f"{current_path}/{child_name}" if current_path else child_name
                walk_tree(child, new_path, class_name)

        def process_document(doc_root):
            class_name = doc_root.tag.split('}')[-1]
            
            for child in doc_root:
                child_name = child.tag.split('}')[-1]
                walk_tree(child, child_name, class_name)
                        
        for element in root:
            if "result" in element.tag: 
                for hit in element:
                    process_document(hit)
            else:
                process_document(element)
                
    except ET.ParseError as e:
        print(f"XML Parsing Error: {e}")
        
    return extracted_data