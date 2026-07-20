import xml.etree.ElementTree as ET


DEFAULT_XML_FIELDS_TO_TRIM = ["admin"]
def trim_xml_fields(xml_str: str, fields = DEFAULT_XML_FIELDS_TO_TRIM) -> str:
    """
    Removes specified fields from the XML string.
    """
    root = ET.fromstring(xml_str)    
    
    for field in fields:
        elem = root.find(field)
        if elem is not None:
            root.remove(elem)
                
    ET.indent(root, space="  ")
    
    return ET.tostring(root, encoding="unicode")