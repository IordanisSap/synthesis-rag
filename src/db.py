import requests
from requests.auth import HTTPBasicAuth
import os
import xml.etree.ElementTree as ET
import logging
from pydantic import HttpUrl,BaseModel, Field

logger = logging.getLogger(__name__)


class CollectionContents(BaseModel):
    path: str
    folders: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)

class ExistDBError(Exception):
    """Custom exception for eXist-db API errors."""
    pass

class ExistDB:
    def __init__(self, url: HttpUrl, username: str, password: str):
        self.url = url
        self.auth = HTTPBasicAuth(username, password)
        
    def read_document(self, filename: str) -> str:
        """
        Reads a document
        """
        url = f"{self.url}/{filename.removeprefix('/db')}"
        response = requests.get(url, auth=self.auth)
        
        if response.status_code == 200:
            logger.info(f"--- Read: {filename} ---")
            return response.text
        else:
            logger.error(f"Failed to read: {response.status_code} - {response.text}")
            raise ExistDBError(f"Failed to read document: {response.status_code} - {response.text}")

    def read_document_raw(self, filename: str) -> bytes:
        url = f"{self.url}/{filename.removeprefix('/db').lstrip('/')}"
        response = requests.get(url, auth=self.auth)
        if response.status_code == 200:
            return response.content
        raise RuntimeError(f"Failed to read {filename}: {response.status_code} - {response.text}")


    def execute_xquery(self, xquery: str) -> str:
            """
            Executes an XQuery against the eXist-db instance using form data.
            """
            response = requests.post(
                f"{self.url}/rest", 
                auth=self.auth, 
                data={"_query": xquery} 
            )
            
            if response.status_code == 200:
                logger.info("--- XQuery executed successfully ---")
                return response.text
            else:
                logger.error(f"Failed to execute XQuery: {response.status_code} - {response.text}")
                raise ExistDBError(f"Failed to execute XQuery: {response.status_code} - {response.text}")

    def list_contents(self, path: str = "") -> CollectionContents:
        """
        Lists available folders (collections) and files (resources) in a given path.
        """
        clean_path = path.removeprefix('/db').strip('/') if path else ""
        target_url = f"{self.url}/{clean_path}" if clean_path else str(self.url)
        
        response = requests.get(target_url, auth=self.auth)
        
        if response.status_code != 200:
            error_msg = f"Failed to list contents: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise ExistDBError(error_msg)
            
        try:
            root = ET.fromstring(response.content)
            namespace = {'exist': 'http://exist.sourceforge.net/NS/exist'}
            
            main_collection = root.find('exist:collection', namespace)
            
            if main_collection is None:
                error_msg = f"Could not find collection data in the response for path: {path}"
                logger.error(error_msg)
                raise ExistDBError(error_msg)
            
            collection_name = main_collection.get('name')

            if collection_name is None:
                error_msg = f"Main collection missing 'name' attribute for path: {path}"
                logger.error(error_msg)
                raise ExistDBError(error_msg)
            
            # Extract sub-collections (folders) and resources (files)
            folders = [
                name for col in main_collection.findall('exist:collection', namespace)
                if (name := col.get('name')) is not None
            ]
            
            files = [
                name for res in main_collection.findall('exist:resource', namespace)
                if (name := res.get('name')) is not None
            ]
            
            return CollectionContents(
                path=collection_name,
                folders=folders,
                files=files
            )
            
        except ET.ParseError as e:
            error_msg = "Error: Could not parse the XML response from eXist-db."
            logger.error(error_msg)
            raise ExistDBError(error_msg) from e
        



    def upload_directory(self, local_path: str):
        """
        Walks through the local directory and uploads all files to eXist-db.
        Missing collections are automatically created.
        """

        def put_file(local_file_path: str, remote_url: str):
            logger.info(f"Uploading: {local_file_path}")
            
            headers = {}
            if local_file_path.lower().endswith('.xml'):
                headers['Content-Type'] = 'application/xml'
            else:
                headers['Content-Type'] = 'application/octet-stream'
                
            with open(local_file_path, 'rb') as file_data:
                response = requests.put(
                    remote_url, 
                    auth=self.auth, 
                    data=file_data, 
                    headers=headers
                )
                
            if response.status_code in [200, 201]:
                logger.info(f"  -> Success! (Status: {response.status_code})")
            else:
                logger.error(f"  -> Failed: {response.status_code} - {response.text}")
                    
        if not os.path.exists(local_path):
            logger.error(f"Error: The path '{local_path}' does not exist.")
            return

        for root, _, files in os.walk(local_path):
            for file_name in files:
                local_file_path = os.path.join(root, file_name)
                
                # Maintain the exact folder structure
                relative_path = os.path.relpath(local_file_path, local_path)
                
                remote_file_path = relative_path.replace(os.sep, '/')
                remote_url = f"{self.url}/{remote_file_path}"
                
                put_file(local_file_path, remote_url)





