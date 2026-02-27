from flask import Blueprint, render_template, request, session, redirect, url_for
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

# MongoDB connection
client = MongoClient("mongodb+srv://Saee:Saee2830@cluster1.cju5mqx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1")
db = client["healthfraudmlchain"]
claims_collection = db["claims"]

# Blueprint
claim_bp = Blueprint('claim_bp', __name__)

@claim_bp.route("/claim_form", methods=["GET", "POST"])
def claim_form():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        # Claim data from form
        claim_data = {
            "user_id": str(session["user"].get("_id", "")),  # User ID (if stored in session)
            "user_email": session["user"]["email"],  # Link claim with email
            "username": session["user"]["name"],
            "patient_name": request.form.get("patient_name"),
            "doctor_name": request.form.get("doctor_name"),
            "treatment": request.form.get("treatment"),
            "amount": float(request.form.get("amount", 0)),
            "status": "Pending",
            "created_at": datetime.utcnow()
        }

        # Save to MongoDB
        claims_collection.insert_one(claim_data)

        # Prediction placeholder
        prediction = "Pending"
        return render_template("result.html", prediction=prediction, data=claim_data)

    return render_template("claim_form.html")
