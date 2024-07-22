# myapp/mongodb.py
from pymongo import MongoClient

def get_db():
    client = MongoClient('mongodb://myuser:mypassword@localhost:27017/')
    db = client['mydatabase']
    return db


