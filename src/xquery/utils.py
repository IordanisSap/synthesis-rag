import xml.etree.ElementTree as ET

def has_hits(xquery_result_str: str) -> bool:
    try:
        root = ET.fromstring(xquery_result_str)
        hits_str = root.attrib.get('{http://exist.sourceforge.net/NS/exist}hits', '0')
        hits = int(hits_str)
        
        return hits > 0
    except ET.ParseError:
        print("Failed to parse XML response.")
        return False