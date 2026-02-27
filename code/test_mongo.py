from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()  # .env मधून variable load करतो

mongo_uri = os.getenv('mongodb+srv://saee:<db_password>@cluster0.62vgd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db_name = os.getenv('DB_NAME')

client = MongoClient(mongo_uri)
db = client[db_name]

print("✅ MongoDB connected successfully!")
print("📂 Available collections:", db.list_collection_names())
