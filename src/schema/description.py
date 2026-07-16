from src.db import CollectionContents, ExistDB
from src.schema.validation import get_template, NoInstanceError
import logging
from src.services.ai.prompts.registry import PromptBuilder, PromptTemplate
import xml.etree.ElementTree as ET


logger = logging.getLogger(__name__)


def produce_class_description(db: ExistDB, folder_path: str, samples : int = 3):

    def trim_for_prompt(xml_str: str) -> str:
        root = ET.fromstring(xml_str)    
        
        admin = root.find("admin")
        if admin is not None:
            root.remove(admin)
                    
        ET.indent(root, space="  ")
        
        return ET.tostring(root, encoding="unicode")


    folder_content = db.list_contents(folder_path)
    templateFile = get_template(folder_content)

    if templateFile:
        templateFileContent = db.read_document(templateFile)
        if templateFileContent is None:
            logger.error(f"Template file {templateFile} could not be read.")
            return None, None
        
        # Assuming all folders contain data
        dataFolder = folder_content.folders[0]
        instanceFolderContent = db.list_contents(f"{folder_content.path}/{dataFolder}")

        if len(instanceFolderContent.files) == 0:
            error_msg = f"No data instance exists in: {folder_content.path}/{dataFolder} \n A data instance is required to produce the class description"
            logger.error(error_msg)
            raise NoInstanceError(error_msg)

        chosenSamples = instanceFolderContent.files[:samples]

        instanceFileContents = [
            trim_for_prompt(content) for content in (
                db.read_document(f"{instanceFolderContent.path}/{sample}")
                for sample in chosenSamples
            ) if content is not None
        ]


        print(instanceFileContents[0])
        print(trim_for_prompt(templateFileContent))
        prompt_params = {
            "name": folder_content.path.split("/")[-1],
            "template": trim_for_prompt(templateFileContent),
            "instances": f"Example: {'\n\n Another Example: \n'.join(instanceFileContents)}"
        }

        # system, user = PromptBuilder.build_messages(PromptTemplate.SUMMARIZE_CLASS, prompt_params)
        # return system, user 
        return None, None
    else:
        logger.info(f"{folder_path} does not contain a template and will not be indexed)")
        return None, None
    
