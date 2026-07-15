from dotenv import load_dotenv
import os
from src.db import ExistDB
from src.utils.parser import parseXML

load_dotenv()

existdb_url = os.getenv("EXISTDB_URL")
existdb_user = os.getenv("EXISTDB_USER")
existdb_pass = os.getenv("EXISTDB_PASS")


db = ExistDB(existdb_url, existdb_user, existdb_pass)
# db.upload_directory("/mnt/10TB/iordanissapidis/synthesis/data")
contents = db.read_document("DMSCOLLECTION/MESSARA/Person/Person.xml")
print(parseXML(contents))