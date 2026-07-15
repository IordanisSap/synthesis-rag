import requests
from requests.auth import HTTPBasicAuth
import os


class ExistDB:
    def __init__(self, url, username, password):
        self.url = url
        self.auth = HTTPBasicAuth(username, password)

    def upload_directory(self, local_path):
        """
        Walks through the local directory and uploads all files to eXist-db.
        Missing collections are automatically created.
        """

        def put_file(local_file_path, remote_url):
            print(f"Uploading: {local_file_path}")
            
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
                print(f"  -> Success! (Status: {response.status_code})")
            else:
                print(f"  -> Failed: {response.status_code} - {response.text}")
                    
        if not os.path.exists(local_path):
            print(f"Error: The path '{local_path}' does not exist.")
            return

        for root, dirs, files in os.walk(local_path):
            for file_name in files:
                local_file_path = os.path.join(root, file_name)
                
                # Maintain the exact folder structure
                relative_path = os.path.relpath(local_file_path, local_path)
                
                remote_file_path = relative_path.replace(os.sep, '/')
                remote_url = f"{self.url}/{remote_file_path}"
                
                put_file(local_file_path, remote_url)

        
    def read_document(self, filename):
        """
        Reads a document
        """
        url = f"{self.url}/{filename}"
        response = requests.get(url, auth=self.auth)
        
        if response.status_code == 200:
            print(f"--- Content of {filename} ---")
            print(response.text)
            return response.text
        else:
            print(f"Failed to read: {response.status_code} - {response.text}")


