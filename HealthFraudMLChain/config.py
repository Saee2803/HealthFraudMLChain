"""
Configuration module for HealthFraudMLChain
Uses environment variables for security in production
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file (if exists)
load_dotenv()

# MongoDB connection
MONGO_URI = os.environ.get(
    "MONGODB_URI",
    os.environ.get("MONGO_URI", "mongodb://localhost:27017/healthfraud")
)

# Flask secret key (MUST be set in production)
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "dev-only-secret-key-change-in-production"
)

# Environment mode
FLASK_ENV = os.environ.get("FLASK_ENV", "development")
DEBUG = FLASK_ENV != "production"

# Port (for cloud deployment)
PORT = int(os.environ.get("PORT", 5000))
