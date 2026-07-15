import xml.etree.ElementTree as ET


def parseXML(string):
    root = ET.fromstring(string)
    return root