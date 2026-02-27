# models/user_model.py

from werkzeug.security import generate_password_hash, check_password_hash
from database.mongodb_connect import get_collection

# Register a new user
def register_user(email, password, role):
    # Check if user already exists
    users = get_collection('users')
    if users.find_one({"email": email}):
        return {"success": False, "message": "User already exists"}

    hashed_pw = generate_password_hash(password)
    user_data = {
        "email": email,
        "password": hashed_pw,
        "role": role  # "patient", "doctor", or "admin"
    }
    users.insert_one(user_data)
    return {"success": True, "message": "User registered successfully"}

# Authenticate user on login
def authenticate_user(email, password):
    users = get_collection('users')
    user = users.find_one({"email": email})
    if user and check_password_hash(user["password"], password):
        return {"success": True, "user": user}
    return {"success": False, "message": "Invalid credentials"}

# Get user role by email
def get_user_role(email):
    users = get_collection('users')
    user = users.find_one({"email": email})
    if user:
        return user.get("role")
    return None
