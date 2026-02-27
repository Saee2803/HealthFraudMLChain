from pymongo import MongoClient

# 🔹 Atlas URI टाका
uri = "mongodb+srv://Saee:Saee2830@cluster1.cju5mqx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1"
client = MongoClient(uri)

# 🔹 Database आणि collection निवड
db = client["healthfraudmlchain"]      # Database नाव
collection = db["claims"]              # Collection नाव

# 🔹 एक sample document insert कर
collection.insert_one({"test": "data"})
print("Inserted!")
