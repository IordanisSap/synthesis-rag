import xml.etree.ElementTree as ET
from src.context.field_catalog.process import postprocess_xml_fields, remove_empty_xml_fields
from src.services.ai.token_estimator import count_tokens


TOPK = 40

def search_to_ordered_classes(xml_string, available_classes):
    class_occurrences = {}
    
    root = ET.fromstring(xml_string)

    parsed_results = []

    for result in root.findall('result'):
        result_data = {
            'file': result.attrib.get('file'),
            'class': result.attrib.get('class'),
            'top-score': float(result.attrib.get('top-score', 0)),
            'total-hits': int(result.attrib.get('total-hits', 0))
        }
        parsed_results.append(result_data)

    for item in parsed_results:
        if item['class'] in available_classes:
            class_occurrences[item['class']] = class_occurrences.get(item['class'], 0) + 1

    ordered_classes = sorted(class_occurrences.items(), key=lambda x: x[1], reverse=True)
    return [cls for cls, _ in ordered_classes]

def search_to_string_hits(xml_string, available_classes):    
    root = ET.fromstring(xml_string)
    hits = []

    for result in root.findall('result'):
        result_data = {
            'file': result.attrib.get('file'),
            'class': result.attrib.get('class'),
            'top-score': float(result.attrib.get('top-score', 0)),
            'total-hits': int(result.attrib.get('total-hits', 0))
        }
        if result.attrib.get('class') in available_classes:
            hits.append(result_data)

    return hits


def search_to_string(xml_string, available_classes, fields_to_ignore, max_tokens=None, max_num=TOPK):
    root = ET.fromstring(xml_string)
    used_tokens = 0
    keep_xmls = []

    for result in root.findall('result'):
        if result.attrib.get('class') not in available_classes:
            continue

        inner_xml_string = result.text or ""
        for child in result:
            inner_xml_string += ET.tostring(child, encoding='unicode')
        final_content = inner_xml_string.strip()

        removed_irrelevant_fields = postprocess_xml_fields(final_content, max_length=1000, fields_to_ignore=fields_to_ignore)
        final = remove_empty_xml_fields(removed_irrelevant_fields)
        estimated_tokens = count_tokens(final)
        if max_tokens is not None and (used_tokens + estimated_tokens) > max_tokens:
            break
        used_tokens += estimated_tokens
        keep_xmls.append(final)
        if len(keep_xmls) >= max_num:
            break

    return keep_xmls
