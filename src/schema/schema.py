from collections.abc import Sequence
from src.db import CollectionContents, ExistDB


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


def get_class_filepaths(db: ExistDB, collectionContents: CollectionContents) -> tuple[str, list[str]] | None:
    """
    Returns the template filepath and all data instance filepaths for a valid class folder.
    Returns None when the folder does not match the class template + instance-folder rule.
    """

    templateFile = get_template_filepath(collectionContents)
    if templateFile is None:
        return None

    instanceFolders = get_instances_filepaths(collectionContents)
    if len(instanceFolders) == 0:
        return None

    instanceFiles: list[str] = []
    for instanceFolder in instanceFolders:
        instanceFolderContent = db.list_contents(instanceFolder)
        xmlFiles = [file for file in instanceFolderContent.files if file.lower().endswith(".xml")]
        instanceFiles.extend(f"{instanceFolderContent.path}/{file}" for file in xmlFiles)

    if len(instanceFiles) == 0:
        return None

    return templateFile, instanceFiles