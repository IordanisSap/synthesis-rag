

import os
import json
from typing import Any


def save_to_index(key: str, value: Any, collection: str, index_folder: str) -> None:
    """
    Save a key-value pair to the index folder as a JSON file.
    """
    os.makedirs(index_folder, exist_ok=True)
    
    file_path = os.path.join(index_folder, f"{collection}.json")
    
    data = {}
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
    
    data[key] = value
    
    with open(file_path, 'w') as f:
        json.dump(data, f)
    

def load_from_index(key: str, collection: str, index_folder: str) -> Any:
    """
    Load a value from the index folder based on the key.
    """
    file_path = os.path.join(index_folder, f"{collection}.json")
    
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    return data.get(key, None)