from collections.abc import Sequence
from src.db import CollectionContents


class NoInstanceError(Exception):
    """No data instance exists in directory."""
    pass

class NoTemplateError(Exception):
    """No template exists in directory."""
    pass

def get_template_filepath(collectionContents: CollectionContents) -> str | None:
    """
    Returns the class template with data that can be indexed in the given path if it exists.
    Else returns None
    Assumed structure:
        - collectionContents.path = <path>/.../<folderName>
        - folderName.xml file exists inside <folderName> and defines the template
    """
    
    folderName = collectionContents.path.split("/")[-1]
    templateFile = folderName + ".xml"
    if templateFile not in collectionContents.files:
        return None
    
    return collectionContents.path + "/" + templateFile

def get_instances_filepaths(collectionContents: CollectionContents) -> Sequence[str]:
    """
    Returns all folders containing data instances in the given path if they exist.
    Else returns None
    Assumed structure:
        - collectionContents.path = <path>/.../<folderName>
        - <folderName> contains one or more folders with data instances
    """

    if len(collectionContents.folders) == 0:
        return []
    
    return [collectionContents.path + "/" + folder for folder in collectionContents.folders]