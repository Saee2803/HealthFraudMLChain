from pymongo import MongoClient


uri = "mongodb+srv://Saee:Saee2830@cluster1.cju5mqx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1"
client = MongoClient(uri)


db = client["healthfraudmlchain"]      
collection = db["claims"]              


collection.insert_one({"test": "data"})
print("Inserted!")
