# from src.data_types import RecordType
from collections.abc import Sequence
from src.db import CollectionContents


class NoInstanceError(Exception):
    """No data instance exists in directory."""
    pass

def get_template(collectionContents: CollectionContents):
    """
    Returns the class template with data that can be indexed in the given path if it exists.
    Else returns None
    Assumed structure:
        - path: .../folderName
        - folderName.xml file exists in folderName and defines the template
    """
    
    folderName = collectionContents.path.split("/")[-1]
    templateFile = folderName + ".xml"
    if templateFile not in collectionContents.files:
        return None
    
    return collectionContents.path + "/" + templateFile