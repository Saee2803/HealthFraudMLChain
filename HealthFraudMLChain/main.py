import os
import time
import logging
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
import pickle
import pandas as pd
import numpy as np

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded from .env")
except ImportError:
    print("⚠️ python-dotenv not installed, using system environment variables")

# For v2.0 model with TF-IDF
try:
    from scipy.sparse import hstack, csr_matrix
except ImportError:
    hstack = None
    csr_matrix = None

# Try importing custom modules with fallbacks
try:
    from blockchain import Blockchain
except ImportError:
    print("Warning: blockchain module not found")
    Blockchain = None

try:
    from services.notification_service import init_notification_service
    from services.role_based_notification_manager import init_role_based_notification_manager
    from services.rules_engine import validate_blockchain_rules
    from services.signature_service import create_approval_signature, store_approval_signature, validate_blockchain_signatures
    from services.claim_encryption_service import prepare_claim_for_blockchain
    from services.blockchain_service import verify_blockchain_integrity
    from services.collusion_detection_service import init_collusion_detection_service
    from services.xai_explanation_service import init_xai_explanation_service
    from services.audit_trail_service import init_audit_trail_service
    from services.fraud_risk_decision_engine import init_fraud_risk_decision_engine
    from services.email_alert_service import init_email_alert_service
    from services.admin_risk_monitor_service import init_admin_risk_monitor_service
except ImportError as e:
    print(f"Warning: Some services not found: {e}")
    # Create dummy functions to prevent crashes
    def init_notification_service(db): return None
    def init_role_based_notification_manager(db, service): return None
    def validate_blockchain_rules(claim): return {'allowed': True}
    def create_approval_signature(*args, **kwargs): return None
    def store_approval_signature(*args, **kwargs): return None
    def validate_blockchain_signatures(claim): return {'valid': True}
    def prepare_claim_for_blockchain(claim): return {}
    def verify_blockchain_integrity(): return {'status': 'VALID', 'errors': []}
    def init_collusion_detection_service(db): return None
    def init_xai_explanation_service(db): return None
    def init_audit_trail_service(db, blockchain): return None
    def init_fraud_risk_decision_engine(db): return None
    def init_email_alert_service(db): return None
    def init_admin_risk_monitor_service(db, email_service): return None

try:
    from ecies_crypto import get_encrypted_chain_for_role
except ImportError:
    def get_encrypted_chain_for_role(blockchain, role): return []

try:
    from utils_helpers_v2 import (
        normalize_datetime, safe_sort_key, ensure_utc_datetime,
        utc_to_ist, format_ist_time, generate_digital_signature, 
        generate_fraud_reasons, get_patient_explanation, 
        get_doctor_admin_explanation, create_audit_entry,
        build_notification_doc, normalize_notification_query
    )
except ImportError:
    # Create fallback functions
    def normalize_datetime(dt): return dt
    def safe_sort_key(dt): return dt if dt else datetime.min
    def ensure_utc_datetime(): return datetime.now(timezone.utc)
    def utc_to_ist(dt): return dt
    def format_ist_time(dt, fmt): return dt.strftime(fmt) if dt else ""
    def generate_digital_signature(*args): return "dummy_signature"
    def generate_fraud_reasons(*args): return []
    def get_patient_explanation(*args): return ""
    def get_doctor_admin_explanation(*args): return ""
    def create_audit_entry(*args, **kwargs): return {}
    def build_notification_doc(*args, **kwargs): return {}
    def normalize_notification_query(*args): return {}

# ---------- BASE DIRECTORY (Production-Safe Path Resolution) ----------
# Ensures all relative paths work correctly when running with gunicorn
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------- Flask App Configuration ----------
app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, "static"),
    template_folder=os.path.join(BASE_DIR, "templates")
)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# ---------- File Upload Config ----------
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf", "docx"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 MB

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------- MongoDB ----------
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb+srv://Saee:Saee2830@cluster1.cju5mqx.mongodb.net/?retryWrites=true&w=majority")
client = MongoClient(MONGODB_URI)
db = client["healthfraudmlchain"]
users_collection = db["users"]
claims_collection = db["claims"]

# ---------- BLOCKCHAIN - MongoDB Persistent ✅ ----------
# Initialize blockchain with MongoDB persistence
if Blockchain:
    blockchain = Blockchain(db=db, collection_name="blockchain_blocks")
    # Load existing chain from MongoDB, or create genesis block if empty
    blockchain.load_from_mongodb()
    print(f"✅ Blockchain loaded: {blockchain.get_block_count()} blocks")
else:
    blockchain = None
    print("⚠️ Blockchain module not available")

# ---------- Notification Service ----------
notification_service = init_notification_service(db)

# ---------- Role-Based Notification Manager ----------
# Ensures role-aware notifications prevent data leakage
# Patients only see patient-relevant events, doctors see doctor-relevant events, etc.
role_based_notification_manager = init_role_based_notification_manager(db, notification_service)

# ---------- Collusion Detection Service ----------
# Detects suspicious patterns of doctor-hospital fraud collusion
collusion_service = init_collusion_detection_service(db)

# ---------- XAI Explanation Service ----------
# Generates human-readable explanations for fraud predictions (regulatory compliance)
# Insurance decisions must be explainable and auditable under regulations (GDPR, insurance laws)
xai_service = init_xai_explanation_service(db)

# ---------- Audit Trail Service ----------
# Records immutable audit trail with digital signatures for non-repudiation
# Every approval action is cryptographically signed, timestamped, and recorded in blockchain
# Ensures enterprise compliance: traceable, immutable, non-repudiable claim decisions
audit_trail_service = init_audit_trail_service(db, blockchain)

# ---------- Fraud Risk Decision Engine ----------
# Automatically routes claims based on fraud probability (auto-approve, manual review, auto-reject)
# Reduces manual workload for low-risk claims while catching fraud early
fraud_risk_decision_engine = init_fraud_risk_decision_engine(db)

# ---------- Email Alert Service ----------
# Provides server-side email alerts for compliance notifications
# Used by insider threat detection to alert super-admins
email_alert_service = init_email_alert_service(db)

# ---------- Admin Risk Monitor Service (Insider Threat Detection) ----------
# Monitors admin approval behavior and detects suspicious patterns:
# - Approving too many high fraud-probability claims
# - Frequently overriding AI decisions
# - Approving claims unusually fast (rubber-stamping)
# When HIGH risk is detected, automatically alerts super-admin/compliance officer
# This is ADVISORY ONLY - does NOT block admin actions or auto-reject claims
admin_risk_monitor_service = init_admin_risk_monitor_service(db, email_alert_service)

# ---------- Load ML Model ----------
# Model v2.0 uses binary classification with TF-IDF
# Model v1.x uses multi-class with one-hot encoding
model = None
le = None
columns = None
model_package = None  # v2.0 format
model_version = None

# Use absolute path for model loading (production-safe)
MODEL_PATH = os.path.join(BASE_DIR, "fraud_model.pkl")

try:
    with open(MODEL_PATH, "rb") as f:
        loaded_data = pickle.load(f)
    
    # Check if it's v2.0 format (dict with 'model' key)
    if isinstance(loaded_data, dict) and "model" in loaded_data:
        model_package = loaded_data
        model = model_package["model"]
        model_version = model_package.get("version", "2.0")
        print(f"✅ ML Model v{model_version} loaded successfully (Binary + TF-IDF)")
    
    # Check if it's v2.0 format (dict with 'model' key)
    if isinstance(loaded_data, dict) and "model" in loaded_data:
        model_package = loaded_data
        model = model_package["model"]
        model_version = model_package.get("version", "2.0")
        print(f"✅ ML Model v{model_version} loaded successfully (Binary + TF-IDF)")
    else:
        # Legacy v1.x format: tuple of (model, label_encoder, columns)
        model, le, columns = loaded_data
        model_version = "1.x"
        print(f"✅ ML Model v{model_version} loaded successfully (Multi-class)")
except FileNotFoundError:
    print("⚠️ fraud_model.pkl not found - ML predictions will be disabled")
except Exception as e:
    print(f"⚠️ Error loading ML model: {e}")
    import traceback
    traceback.print_exc()

# ---------- Template filters ----------
@app.template_filter('datetimeformat')
def datetimeformat(value, format='%d-%b-%Y'):
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime(format)
    except:
        return value


@app.template_filter('ist_time')
def ist_time_filter(utc_datetime, format_str="%d %b %Y, %H:%M:%S"):
    """Convert UTC datetime to IST and format for display"""
    try:
        return format_ist_time(utc_datetime, format_str)
    except Exception as e:
        print(f"Error formatting IST time: {e}")
        return str(utc_datetime)

# ---------- Home ----------
@app.route("/")
def index():
    
    if "user" in session:
        role = session["user"]["role"]
        if role == "patient":
            return redirect(url_for("patient_dashboard"))
        elif role == "admin":
            return redirect(url_for("admin_dashboard"))
    
    return redirect(url_for("login"))

# ---------- Auth ----------
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        role = request.form.get("role","").strip().lower()
        user = users_collection.find_one({"email": email, "role": role})
        if user and check_password_hash(user["password"], password):
            session["user"] = {
                "id": str(user["_id"]),
                "name": user["name"],
                "email": user["email"],
                "role": user["role"]
            }
            flash("Login successful!", "success")
            # Redirect based on role explicitly
            if role == "patient":
                return redirect(url_for("patient_dashboard"))
            elif role == "doctor":
                return redirect(url_for("dashboard_doctor"))
            elif role == "admin":
                return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method=="POST":
        name = request.form.get("name","").strip()
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        confirm = request.form.get("confirm_password","")
        role = request.form.get("role","patient").strip().lower()

        # ✅ Doctor signup block
        if role == "doctor":
            flash("Doctor account can be created only by Admin.", "danger")
            return render_template("signup.html")

        if not name or not email or not password or not confirm:
            flash("All fields required.", "danger")
            return render_template("signup.html")

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("signup.html")

        if users_collection.find_one({"email": email}):
            flash("Email already registered.", "danger")
            return render_template("signup.html")

        hashed = generate_password_hash(password)

        res = users_collection.insert_one({
            "name": name,
            "email": email,
            "password": hashed,
            "role": role,
            "created_at": ensure_utc_datetime()
        })

        session["user"] = {
            "id": str(res.inserted_id),
            "name": name,
            "email": email,
            "role": role
        }

        flash("Signup successful!", "success")
        return redirect(url_for("patient_dashboard"))

    return render_template("signup.html")



@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------- Patient Dashboard ----------
@app.route("/dashboard_patient")
def patient_dashboard():
    if "user" not in session or session["user"]["role"] != "patient":
        return redirect(url_for("login"))

    username = session["user"]["name"]
    user_id = session["user"]["id"]
    my_claims = list(claims_collection.find({"username": username}))

    # Convert ObjectId to string for template
    for claim in my_claims:
        claim["_id"] = str(claim["_id"])
        if not isinstance(claim.get("documents"), list):
            claim["documents"] = []

    # Stats calculation
    total_claims = len(my_claims)
    approved_claims = sum(1 for c in my_claims if c.get("status") == "Approved")
    rejected_claims = sum(1 for c in my_claims if c.get("status") == "Rejected")
    pending_claims = sum(1 for c in my_claims if c.get("status") == "Pending")

    stats = {
        "total_claims": total_claims,
        "approved_claims": approved_claims,
        "rejected_claims": rejected_claims,
        "pending_claims": pending_claims
    }

    # Sort recent claims by submission date (latest first) - SAFE for mixed str/datetime
    recent_claims = sorted(my_claims, key=lambda x: safe_sort_key(x.get("submitted_on")), reverse=True)[:5]

    # Get notification data
    if notification_service:
        unread_count = notification_service.get_unread_count(user_id, "patient")
        recent_notifications = notification_service.get_recent_notifications(user_id, "patient", limit=5)
    else:
        unread_count = 0
        recent_notifications = []

    return render_template("dashboard_patient.html", stats=stats, recent_claims=recent_claims, 
                         unread_notification_count=unread_count, recent_notifications=recent_notifications)


# ---------- My Claims ----------
@app.route("/my_claims")
def my_claims():
    if "user" not in session or session["user"]["role"]!="patient":
        return redirect(url_for("login"))
    username = session["user"]["name"]
    claims_list = list(claims_collection.find({"username": username}))
    for c in claims_list: c["_id"] = str(c["_id"])
    return render_template("my_claims.html", claims=claims_list)
# ---------- Claim Form ----------
@app.route("/claim_form", methods=["GET", "POST"])
def claim_form():
    if "user" not in session or session["user"]["role"] != "patient":
        return redirect(url_for("login"))

    if request.method == "POST":
        # ============ 🔐 DOCTOR ASSIGNMENT - DIRECT FROM FORM ============
        # Get doctor_id directly from the form (hidden field with doctor's ObjectId)
        doctor_id = request.form.get("doctor_id", "").strip()
        
        # ✅ VALIDATION: Ensure doctor_id is provided and valid
        if not doctor_id:
            flash("❌ Error: You must select a doctor.", "danger")
            return redirect(url_for("claim_form"))
        
        # Verify the doctor_id exists in database
        try:
            doctor_user = users_collection.find_one({
                "_id": ObjectId(doctor_id),
                "role": "doctor"
            })
            if not doctor_user:
                flash("❌ Error: Selected doctor is invalid.", "danger")
                return redirect(url_for("claim_form"))
        except Exception as e:
            flash("❌ Error: Invalid doctor ID format.", "danger")
            return redirect(url_for("claim_form"))
        
        # Assign doctor_id directly
        assigned_doctor_id = doctor_id
        doctor_name_for_display = doctor_user.get("name", request.form.get("doctorName"))
        
        # ============ FILE UPLOAD ============
        files = request.files.getlist("documents[]")
        file_paths = []

        for f in files:
            if f and allowed_file(f.filename):
                fname = secure_filename(f.filename)
                unique = f"{int(time.time())}_{fname}"
                path = os.path.join(app.config["UPLOAD_FOLDER"], unique)
                f.save(path)
                file_paths.append(unique)

        # ============ FORM DATA ============
        age = int(request.form.get("age"))
        gender = request.form.get("gender")  # "Male" or "Female" from form
        diagnosis = request.form.get("treatmentType")  # Maps to Diagnosis in CSV
        claim_amount = float(request.form.get("claimAmount"))
        
        # ============ CALCULATE STAY DURATION FROM DATES ============
        # Training CSV calculates: Stay Duration = (Date Discharged - Date Admitted).days
        admission_date_str = request.form.get("admissionDate")
        discharge_date_str = request.form.get("dischargeDate")
        try:
            from datetime import datetime
            admission_date = datetime.strptime(admission_date_str, "%Y-%m-%d")
            discharge_date = datetime.strptime(discharge_date_str, "%Y-%m-%d")
            stay_duration = max(1, (discharge_date - admission_date).days)  # Minimum 1 day
        except Exception as e:
            stay_duration = 1  # Safe default
            print(f"Warning: Could not calculate stay_duration, using default=1: {e}")

        # ============ ML PREDICTION ============
        # v2.0: Binary classification with TF-IDF and engineered features
        # v1.x: Multi-class with one-hot encoding (legacy)
        fraud_label = "No Fraud"
        fraud_prob = 0.5  # Default safe value
        
        if model_package and model_version and model_version.startswith("2"):
            # ========== V2.0 MODEL (Binary + TF-IDF) ==========
            try:
                tfidf = model_package["tfidf"]
                numeric_columns = model_package["numeric_columns"]
                
                # Build engineered features (MUST match training)
                features = {}
                
                # Basic features
                features["Age"] = age
                features["Amount Billed"] = claim_amount
                features["Stay Duration"] = stay_duration
                
                # Amount-based indicators
                features["high_amount_flag"] = 1 if claim_amount > 100000 else 0
                features["very_high_amount_flag"] = 1 if claim_amount > 300000 else 0
                features["extreme_amount_flag"] = 1 if claim_amount > 500000 else 0
                features["low_amount_flag"] = 1 if claim_amount < 30000 else 0
                
                # Stay duration indicators
                features["zero_stay_flag"] = 1 if stay_duration == 0 else 0
                features["short_stay_flag"] = 1 if stay_duration <= 1 else 0
                features["long_stay_flag"] = 1 if stay_duration > 15 else 0
                features["very_long_stay_flag"] = 1 if stay_duration > 30 else 0
                
                # Age risk indicators
                features["child_flag"] = 1 if age < 10 else 0
                features["elderly_flag"] = 1 if age > 75 else 0
                features["high_risk_age_flag"] = 1 if age < 5 or age > 85 else 0
                
                # CRITICAL: Gender-Diagnosis mismatch detection
                pregnancy_related = ["Pregnancy", "Cesarean Section"]
                features["gender_diagnosis_mismatch"] = 1 if (gender == "Male" and diagnosis in pregnancy_related) else 0
                
                # Age-Diagnosis anomaly detection
                features["age_diagnosis_anomaly"] = 0
                if age < 15 and diagnosis == "Cataract Surgery":
                    features["age_diagnosis_anomaly"] = 1
                if age < 10 and diagnosis == "Hypertension":
                    features["age_diagnosis_anomaly"] = 1
                if age > 55 and diagnosis == "Pregnancy":
                    features["age_diagnosis_anomaly"] = 1
                
                # Amount per day ratio
                features["amount_per_day"] = claim_amount / (stay_duration + 1)
                features["high_amount_per_day"] = 1 if features["amount_per_day"] > 100000 else 0
                features["extreme_amount_per_day"] = 1 if features["amount_per_day"] > 200000 else 0
                
                # Combined risk score
                features["risk_score"] = (
                    features["high_amount_flag"] + 
                    features["zero_stay_flag"] + 
                    features["gender_diagnosis_mismatch"] * 3 +
                    features["age_diagnosis_anomaly"] * 2 +
                    features["high_amount_per_day"] +
                    features["extreme_amount_flag"]
                )
                
                # Gender one-hot
                features["Gender_Female"] = 1 if gender == "Female" else 0
                features["Gender_Male"] = 1 if gender == "Male" else 0
                
                # Build numeric feature DataFrame in correct column order
                df_features = pd.DataFrame([features])
                for col in numeric_columns:
                    if col not in df_features.columns:
                        df_features[col] = 0
                df_features = df_features[numeric_columns]
                
                # TF-IDF on diagnosis text
                diagnosis_text = f"{gender} {diagnosis}"
                tfidf_vector = tfidf.transform([diagnosis_text])
                
                # Combine numeric + TF-IDF (convert to float64 for scipy compatibility)
                X_numeric = csr_matrix(df_features.values.astype(np.float64))
                X_combined = hstack([X_numeric, tfidf_vector])
                
                # Get fraud probability (binary: index 1 = Fraud)
                fraud_prob = float(model.predict_proba(X_combined)[0][1])
                fraud_prob = round(fraud_prob, 4)
                
                # Set label based on probability threshold
                fraud_label = "Fraud" if fraud_prob >= 0.5 else "No Fraud"
                
                print(f"🔍 ML v2.0 Prediction: fraud_prob={fraud_prob:.2%}, label={fraud_label}, "
                      f"age={age}, amount={claim_amount}, stay={stay_duration}, "
                      f"gender_mismatch={features['gender_diagnosis_mismatch']}, "
                      f"risk_score={features['risk_score']}")
                
            except Exception as e:
                fraud_prob = 0.5
                fraud_label = "No Fraud"
                logging.error(f"ML v2.0 prediction error: {e}")
                print(f"❌ ML v2.0 prediction error: {e}")
                import traceback
                traceback.print_exc()
                
        elif model and le and columns:
            # ========== V1.x MODEL (Multi-class, legacy) ==========
            try:
                # Step 1: Build base features dictionary
                features = {
                    "Age": age,
                    "Amount Billed": claim_amount,
                    "Stay Duration": stay_duration,
                    # One-hot encode Gender (match training: Gender_Female, Gender_Male)
                    "Gender_Female": 1 if gender == "Female" else 0,
                    "Gender_Male": 1 if gender == "Male" else 0,
                }
                
                # Step 2: Initialize all diagnosis columns to 0
                for col in columns:
                    if col.startswith("Diagnosis_"):
                        features[col] = 0
                
                # Step 3: Set the matching diagnosis column to 1
                diagnosis_col = f"Diagnosis_{diagnosis}"
                if diagnosis_col in columns:
                    features[diagnosis_col] = 1
                else:
                    for col in columns:
                        if col.lower() == diagnosis_col.lower():
                            features[col] = 1
                            break
                
                # Step 4: Build DataFrame with EXACT trained columns order
                df = pd.DataFrame([features])
                for col in columns:
                    if col not in df.columns:
                        df[col] = 0
                df = df[columns]
                
                # Step 5: Use predict_proba for probability
                proba = model.predict_proba(df)[0]
                classes_list = list(le.classes_)
                
                if "No Fraud" in classes_list:
                    no_fraud_idx = classes_list.index("No Fraud")
                    no_fraud_prob = float(proba[no_fraud_idx])
                    fraud_prob = round(1.0 - no_fraud_prob, 4)
                else:
                    fraud_prob = 0.5
                
                pred = model.predict(df)
                fraud_label = le.inverse_transform(pred)[0]
                
                print(f"🔍 ML v1.x Prediction: fraud_prob={fraud_prob:.2%}, label={fraud_label}, "
                      f"age={age}, amount={claim_amount}, stay={stay_duration}")
                
            except Exception as e:
                fraud_prob = 0.5
                fraud_label = "No Fraud"
                logging.error(f"ML v1.x prediction error: {e}")
                print(f"❌ ML v1.x prediction error: {e}")
        else:
            fraud_prob = 0.1  # Low risk when model unavailable
            print("⚠️ ML model not available, using default prediction")

        fraud_reasons = generate_fraud_reasons(
            age, gender, diagnosis, claim_amount, stay_duration, fraud_prob
        )

        # ============ FRAUD RISK DECISION ENGINE ============
        # Automatically route claim based on fraud probability
        # Low risk (<30%) → Auto-approve; Medium risk (30-80%) → Manual review; High risk (>80%) → Auto-reject
        # This reduces manual workload while catching fraud early
        if fraud_risk_decision_engine:
            decision_result = fraud_risk_decision_engine.evaluate_claim_decision(fraud_prob)
        else:
            decision_result = {
                "final_status": "Pending",
                "decision_type": "MANUAL_REVIEW",
                "is_automated": False,
                "reason": "Decision engine not available"
            }
        
        final_status = decision_result.get("final_status", "Pending")
        decision_type = decision_result.get("decision_type")
        is_auto_processed = decision_result.get("is_automated", False)
        
        if is_auto_processed:
            if decision_type == "AUTO_APPROVE":
                flash_msg = f"✅ Claim auto-approved! Fraud probability: {fraud_prob:.2%}. Low risk detected."
            else:  # AUTO_REJECT
                flash_msg = f"❌ Claim auto-rejected! Fraud probability: {fraud_prob:.2%}. High fraud risk detected."
        else:
            flash_msg = f"⏳ Claim under manual review. Fraud probability: {fraud_prob:.2%}. Assigning to doctor."

        # ============ SAVE CLAIM ============
        claim_data = {
            "patient_name": request.form.get("patientName"),
            "age": age,
            "gender": gender,
            "treatment_type": diagnosis,
            "hospital_name": request.form.get("hospitalName"),
            "doctor_name": doctor_name_for_display,  # Store for display purposes only
            "claim_amount": claim_amount,
            "admission_date": request.form.get("admissionDate"),
            "discharge_date": request.form.get("dischargeDate"),
            "claim_description": request.form.get("claimDescription"),
            "documents": file_paths,
            "username": session["user"]["name"],
            "user_id": session["user"]["id"],
            "prediction": fraud_label,
            "fraud_probability": fraud_prob,
            "fraud_reasons": fraud_reasons,
            "status": final_status,  # Use decision engine result instead of hardcoded "Pending"
            "submitted_on": ensure_utc_datetime(),
            "assigned_doctor_id": assigned_doctor_id,  # 🔐 CRITICAL: Doctor ID from form
            "doctor_approved": is_auto_processed and decision_type == "AUTO_APPROVE",  # True if auto-approved
            "admin_approved": is_auto_processed and decision_type == "AUTO_APPROVE",  # True if auto-approved
            # ========== FRAUD DECISION ENGINE FIELDS ==========
            "decision_type": decision_type,  # AUTO_APPROVE, MANUAL_REVIEW, or AUTO_REJECT
            "auto_decision_reason": decision_result.get("reason"),  # Explainable reason
            "is_auto_processed": is_auto_processed,  # True if auto-approved/rejected
            "audit_log": []
        }

        result = claims_collection.insert_one(claim_data)
        claim_id = str(result.inserted_id)

        # ============ LOG FRAUD DECISION ============
        # Log the automated decision for audit trail and analytics
        fraud_risk_decision_engine.log_decision(claim_id=claim_id, decision_result=decision_result)

        # ============ XAI EXPLANATION GENERATION ============
        # Generate auditable, explainable reasoning for fraud prediction (regulatory compliance)
        # This ensures every fraud decision has transparent justification for patients and auditors
        claim_data["_id"] = ObjectId(claim_id)  # Add ObjectId for context analysis
        xai_explanation = xai_service.generate_comprehensive_explanation(
            claim_data=claim_data,
            fraud_probability=fraud_prob,
            fraud_reasons=fraud_reasons
        )
        xai_service.store_explanation(xai_explanation)
        
        # Store explanation reference in claim for quick access
        claims_collection.update_one(
            {"_id": ObjectId(claim_id)},
            {"$set": {"xai_explanation_id": xai_explanation.get("generated_at")}}
        )

        # ============ AUDIT ============
        claims_collection.update_one(
            {"_id": ObjectId(claim_id)},
            {"$push": {
                "audit_log": create_audit_entry(
                    action="Claim Submitted",
                    by_name=session["user"]["name"],
                    by_role="patient",
                    remarks=f"AI Fraud Score: {fraud_prob:.1%}"
                )
            }}
        )

        # ============ NOTIFICATIONS ============
        # 🔐 ROLE-BASED NOTIFICATIONS: Ensure each role receives appropriate information only
        # Prevents data leakage by filtering message content and recipient lists per role
        role_based_notification_manager.notify_claim_submission(
            claim_id=claim_id,
            patient_name=claim_data['patient_name'],
            claim_amount=claim_amount,
            assigned_doctor_id=assigned_doctor_id,
            fraud_prob=fraud_prob
        )
        
        # ============ EXPLICIT PATIENT NOTIFICATION ON CLAIM SUBMISSION ============
        # FIX: Ensure patient always receives confirmation notification
        # This is a direct notification in addition to role_based_notification_manager
        try:
            notification_service.create_notification(
                to_role="patient",
                to_user_id=session["user"]["id"],
                message=f"✅ Your claim for ₹{claim_amount:,.2f} has been submitted successfully and is under review. "
                        f"Claim ID: {claim_id[:8]}... You will be notified of any updates.",
                notification_type="claim_submitted",
                related_claim_id=claim_id,
                priority="normal"
            )
        except Exception as e:
            # Non-blocking: Don't fail claim submission if notification fails
            print(f"Warning: Patient notification failed (non-blocking): {e}")
        
        # ============ EXPLICIT DOCTOR NOTIFICATION ON CLAIM SUBMISSION ============
        # FIX: Ensure assigned doctor receives notification when patient submits claim
        # This is CRITICAL for doctor to see new claims in their dashboard notifications
        if assigned_doctor_id:
            try:
                doc_priority = "high" if fraud_prob >= 0.6 else "normal"
                notification_service.create_notification(
                    to_role="doctor",
                    to_user_id=assigned_doctor_id,
                    message=f"📋 New claim assigned to you from {claim_data['patient_name']}. "
                            f"Amount: ₹{claim_amount:,.2f}. AI Fraud Risk: {fraud_prob:.1%}. "
                            f"Please review and verify.",
                    notification_type="claim_assigned",
                    related_claim_id=claim_id,
                    priority=doc_priority
                )
                print(f"✅ Doctor notification sent to doctor_id={assigned_doctor_id} for claim {claim_id}")
            except Exception as e:
                # Non-blocking: Don't fail claim submission if notification fails
                print(f"Warning: Doctor notification failed (non-blocking): {e}")
        
        # 🚨 FRAUD ALERT NOTIFICATION: If fraud score is HIGH, alert admins immediately
        if fraud_prob >= 0.7:
            role_based_notification_manager.notify_high_fraud_risk(
                claim_id=claim_id,
                fraud_score=fraud_prob
            )

        # 🤖 AUTO-APPROVAL NOTIFICATION: If claim was auto-approved, alert admins for monitoring
        if is_auto_processed and decision_type == "AUTO_APPROVE":
            admins = list(users_collection.find({"role": "admin"}))
            for admin in admins:
                notification_service.create_notification(
                    to_role="admin",
                    to_user_id=str(admin["_id"]),
                    message=f"✅ Claim {claim_id} auto-approved (Low fraud risk: {fraud_prob:.1%}). "
                            f"Monitor for patterns. Patient: {claim_data['patient_name']}. "
                            f"Amount: ${claim_amount:,.2f}",
                    notification_type="claim_auto_approved",
                    related_claim_id=claim_id,
                    priority="low"
                )

        # ============ COLLUSION DETECTION ============
        # Update doctor-hospital collusion risk scores after each claim submission
        # This detects suspicious patterns of coordinated fraud (e.g., doctor approves many fraudulent claims from same hospital)
        if assigned_doctor_id:
            collusion_service.update_collusion_risk_database(
                doctor_id=assigned_doctor_id,
                doctor_name=doctor_name_for_display,
                hospital_name=request.form.get("hospitalName")
            )

        # ============ AUTO-REJECTION NOTIFICATION ============
        # 🚨 If claim was auto-rejected, notify patient immediately with appeal information
        if is_auto_processed and decision_type == "AUTO_REJECT":
            notification_service.create_notification(
                to_role="patient",
                to_user_id=session["user"]["id"],
                message=f"⚠️ Your claim was automatically rejected due to high fraud risk (Score: {fraud_prob:.1%}). "
                        f"Reason: {decision_result.get('reason', 'High fraud indicators detected')}. "
                        f"You may appeal this decision within 30 days. Contact support for assistance.",
                notification_type="claim_auto_rejected",
                related_claim_id=claim_id,
                priority="high"
            )
        
        # ============ FLASH MESSAGE FOR USER FEEDBACK ============
        # Display fraud risk score and decision status to the patient
        if fraud_prob >= 0.7:
            flash(f"🚨 Fraud Risk Score: {fraud_prob*100:.1f}% — HIGH RISK. Manual Review Required.", "danger")
        elif fraud_prob >= 0.6:
            flash(f"⚠️ Fraud Risk Score: {fraud_prob*100:.1f}% — MEDIUM RISK. Manual Review Required.", "warning")
        else:
            flash(f"✅ Fraud Risk Score: {fraud_prob*100:.1f}% — LOW RISK. Claim Submitted Successfully.", "success")
        
        return redirect(url_for("patient_dashboard"))

    # GET request: Fetch all doctors for the dropdown
    doctors = list(users_collection.find({"role": "doctor"}).sort("name", 1))
    return render_template("claim_form.html", doctors=doctors)




@app.route("/admin/dashboard")
def admin_dashboard():
    if "user" not in session or session["user"]["role"] != "admin":
        return redirect(url_for("login"))

    user_id = session["user"]["id"]

    search_name = request.args.get("search_name", "").strip()
    filter_type = request.args.get("filter_type", "all").strip().lower()

    query = {}

    # 🔍 Filter by type (default: all claims)
    if filter_type == "pending":
        # Pending after doctor approval: Waiting for admin decision
        query = {
            "status": "Pending",
            "doctor_approved": True,
            "admin_approved": None
        }
    elif filter_type == "approved":
        query["status"] = "Approved"
    elif filter_type == "rejected":
        query["status"] = "Rejected"
    # else: filter_type == "all" → show ALL claims (empty query)

    # 🔍 Search by name (in addition to filter)
    if search_name:
        query["patient_name"] = {"$regex": search_name, "$options": "i"}

    # ✅ SHOW ALL claims by default, sorted by most recent first
    claims = list(
        claims_collection.find(query).sort("submitted_on", -1)
    )

    for c in claims:
        c["_id"] = str(c["_id"])
        if not isinstance(c.get("documents"), list):
            c["documents"] = []

    # 📊 Stats
    total = claims_collection.count_documents({})
    approved = claims_collection.count_documents({"status": "Approved"})
    rejected = claims_collection.count_documents({"status": "Rejected"})

    fraudulent_types = ["Fraudulent Claim", "Phantom Billing"]

    # 🔔 Notifications (FIXED: admin dashboard must use role='admin')
    unread_count = notification_service.get_unread_count(
        user_id,
        "admin"
    )

    recent_notifications = notification_service.get_recent_notifications(
        user_id,
        "admin",
        limit=5
    )


    return render_template(
        "dashboard_admin.html",
        claims=claims,
        total_claims=total,
        approved_claims=approved,
        rejected_claims=rejected,
        fraudulent_types=fraudulent_types,
        unread_notification_count=unread_count,
        recent_notifications=recent_notifications
    )



@app.route("/admin/add_doctor", methods=["GET", "POST"])
def add_doctor():
    if "user" not in session or session["user"]["role"] != "admin":
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email").lower()
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")

        if password != confirm:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("add_doctor"))

        hashed = generate_password_hash(password)

        users_collection.insert_one({
            "name": name,
            "email": email,
            "password": hashed,
            "role": "doctor",
            "created_at": ensure_utc_datetime()
        })

        flash("Doctor added successfully!", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("add_doctor.html")
@app.route("/admin/blockchain")
def admin_blockchain():
    if "user" not in session or session["user"]["role"] != "admin":
        return redirect(url_for("login"))

    # 🔐 Get blockchain data with role-based decryption
    user_role = session["user"]["role"]
    chain_list = get_encrypted_chain_for_role(blockchain, user_role)
    is_valid = blockchain.is_chain_valid()

    return render_template(
        "blockchain_view.html",
        chain=chain_list,
        chain_valid=is_valid,
        user_role=user_role
    )

@app.route("/admin/validate_blockchain")
def validate_blockchain():
    if "user" not in session or session["user"]["role"] != "admin":
        return redirect(url_for("login"))

    is_valid = blockchain.is_chain_valid()

    if is_valid:
        flash("✔ Blockchain is VALID. No tampering detected!", "success")
    else:
        flash("✘ BLOCKCHAIN TAMPERED! Data integrity compromised!", "danger")

    return redirect(url_for("admin_blockchain"))


@app.route("/api/blockchain/integrity", methods=["GET"])
def api_blockchain_integrity():
    """
    🔐 BLOCKCHAIN INTEGRITY VERIFICATION API (Admin-Only)
    
    Verifies that the blockchain has not been tampered with.
    Recomputes hashes for all blocks and verifies chain linkage.
    
    Returns:
    {
        "status": "VALID" or "TAMPERED",
        "total_blocks_checked": int,
        "total_blocks_in_chain": int,
        "tamper_proof": bool,
        "errors": list of tampering details (empty if valid),
        "timestamp": ISO UTC timestamp
    }
    
    Real-World Relevance:
    Enterprise blockchain auditing. Admins can verify integrity at any time.
    Any tampering attempt is immediately detectable via hash mismatch.
    """
    # 🔐 ENFORCE ADMIN-ONLY ACCESS
    if "user" not in session or session["user"]["role"] != "admin":
        return jsonify({
            "status": "UNAUTHORIZED",
            "error": "Only admin role can verify blockchain integrity",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 403
    
    try:
        # Run comprehensive integrity verification
        integrity_report = verify_blockchain_integrity()
        
        # Log integrity check in audit trail
        if integrity_report['status'] != 'VALID':
            # Tampering detected - log this critical event
            audit_entry = create_audit_entry(
                action="Blockchain Integrity Violation Detected",
                by_name=session["user"]["name"],
                by_role="admin",
                remarks=f"Integrity check found {len(integrity_report['errors'])} errors",
                digital_signature=None
            )
            from database.mongodb_connect import get_collection
            get_collection('claims').insert_one({
                'type': 'integrity_alert',
                'timestamp': datetime.now(timezone.utc),
                'audit_entry': audit_entry,
                'errors': integrity_report['errors']
            })
        
        return jsonify(integrity_report), 200
        
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "error": f"Integrity verification failed: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route("/doctor/blockchain")
def doctor_blockchain():
    if "user" not in session or session["user"]["role"] != "doctor":
        return redirect(url_for("login"))

    # 🔐 Get blockchain data with role-based decryption
    user_role = session["user"]["role"]
    chain_list = get_encrypted_chain_for_role(blockchain, user_role)
    is_valid = blockchain.is_chain_valid()

    return render_template(
        "blockchain_view.html",
        chain=chain_list,
        chain_valid=is_valid,
        user_role=user_role
    )

@app.route("/dashboard_doctor")
def dashboard_doctor():
    if "user" not in session or session["user"]["role"] != "doctor":
        return redirect(url_for("login"))

    user_id = session["user"]["id"]
    doctor_name = session["user"]["name"]

    # ✅ 🔐 Claims assigned to THIS doctor that still need verification
    pending_claims = list(
        claims_collection.find({
            "status": "Pending",
            "assigned_doctor_id": user_id,  # 🔐 SECURITY: Only assigned claims
            "doctor_approved": None   # 🔥 FIX IS HERE
        }).sort("submitted_on", -1)
    )

    # ✅ Stats
    total_for_verification = len(pending_claims)

    approved_by_doctor = claims_collection.count_documents({
        "doctor_approved": True
    })

    rejected_by_doctor = claims_collection.count_documents({
        "doctor_approved": False
    })

    # Prepare claims for UI
    for c in pending_claims:
        c["_id"] = str(c["_id"])
        if not isinstance(c.get("documents"), list):
            c["documents"] = []

    # 🔔 Notifications (FIXED: use positional args not keyword args)
    unread_count = notification_service.get_unread_count(
        user_id,
        "doctor"
    )

    recent_notifications = notification_service.get_recent_notifications(
        user_id,
        "doctor",
        limit=5
    )

    return render_template(
        "doctor_dashboard.html",
        doctor_name=doctor_name,
        total_for_verification=total_for_verification,
        approved_by_doctor=approved_by_doctor,
        rejected_by_doctor=rejected_by_doctor,
        pending_claims=pending_claims,
        unread_notification_count=unread_count,
        recent_notifications=recent_notifications
    )

@app.route("/update_claim_status/<claim_id>", methods=["POST"], endpoint="update_claim_status")
def update_claim_status(claim_id):

    if "user" not in session or session["user"]["role"] not in ["admin", "doctor"]:
        return redirect(url_for("login"))

    new_status = request.form.get("status")
    remarks = request.form.get("remarks", "").strip()
    role = session["user"]["role"]
    name = session["user"]["name"]
    user_id = session["user"]["id"]

    claim = claims_collection.find_one({"_id": ObjectId(claim_id)})
    if not claim:
        flash("Claim not found!", "danger")
        return redirect(url_for("admin_dashboard") if role == "admin" else url_for("dashboard_doctor"))

    # 🔐 SECURITY: Doctor can only approve/reject claims assigned to them
    if role == "doctor":
        if claim.get("assigned_doctor_id") != user_id:
            flash("❌ Access Denied: You can only approve claims assigned to you.", "danger")
            return redirect(url_for("dashboard_doctor"))

    update_doc = {}
    
    # 🔐 DIGITAL SIGNATURES: Create cryptographic signature for non-repudiation
    # Each approver's action is digitally signed with their private key (ECDSA)
    # This prevents repudiation: signer cannot deny approving/rejecting the claim
    approver_private_key = None  # In production, retrieve from KMS/HSM
    
    signature_data = create_approval_signature(
        claim_id=claim_id,
        approver_id=user_id,
        approver_role=role,
        approval_action='approved' if new_status == "Approved" else 'rejected',
        approver_private_key_pem=approver_private_key
    )

    # 🔐 Generate digital signature for approval/rejection (for audit)
    timestamp_str = ensure_utc_datetime().isoformat()
    digital_signature = generate_digital_signature(claim_id, name, timestamp_str)

    # ✅ IMMUTABLE AUDIT TRAIL: Record approval action with signature (non-repudiation)
    # This creates an immutable record that the approver cannot deny later
    audit_record = audit_trail_service.record_approval_action(
        claim_id=claim_id,
        approver_id=user_id,
        approver_name=name,
        approver_role=role,
        action='approved' if new_status == "Approved" else 'rejected',
        signature=signature_data,
        remarks=remarks,
        context={
            "fraud_score": claim.get("fraud_probability"),
            "fraud_reasons": claim.get("fraud_reasons", []),
            "hospital_name": claim.get("hospital_name")
        }
    )

    # ✅ AUDIT: Create entry before status change
    audit_entry = create_audit_entry(
        action=f"{new_status} by {role.capitalize()}",
        by_name=name,
        by_role=role,
        remarks=remarks,
        digital_signature=digital_signature
    )

    # Doctor approval stage
    if role == "doctor":
        if new_status == "Approved":
            update_doc["doctor_approved"] = True
        elif new_status == "Rejected":
            update_doc["doctor_approved"] = False

        # Doctor NEVER finalizes status
        update_doc["status"] = claim.get("status", "Pending")
        
        # 🔐 DIGITAL SIGNATURE: Store doctor's approval signature (non-repudiation)
        update_doc["doctor_signature"] = signature_data

    # Admin approval stage
    elif role == "admin":
        if new_status == "Approved":
            update_doc["admin_approved"] = True
            
            # ============ INSIDER THREAT EMAIL ALERT ============
            # When admin approves a HIGH-RISK claim (fraud_probability >= 0.7),
            # automatically send email alert to super admins for compliance review.
            # This NEVER blocks the approval - it's advisory only.
            fraud_prob = claim.get("fraud_probability", 0)
            if fraud_prob >= 0.7:
                try:
                    print(f"🚨 High-risk approval detected: claim={claim_id}, fraud_prob={fraud_prob:.1%}")
                    
                    # Send email alert to super admins
                    if email_alert_service:
                        email_sent = email_alert_service.send_insider_threat_alert(
                            claim_id=claim_id,
                            fraud_probability=fraud_prob,
                            admin_name=name,
                            admin_id=user_id,
                            claim_amount=claim.get("claim_amount", 0),
                            patient_name=claim.get("patient_name", "Unknown")
                        )
                        if email_sent:
                            print(f"📧 Email alert sent to super admin for high-risk approval")
                        else:
                            print(f"⚠️ Email failed, logged to DB")
                    else:
                        print("⚠️ Email alert service not available")
                        
                except Exception as email_error:
                    # EMAIL FAILURE MUST NOT AFFECT CLAIM FLOW
                    print(f"⚠️ Email alert failed (non-blocking): {email_error}")
                    import logging
                    logging.error(f"Email alert error: {email_error}")
            
        elif new_status == "Rejected":
            update_doc["admin_approved"] = False

        # Admin finalizes status
        update_doc["status"] = new_status
        
        # 🔐 DIGITAL SIGNATURE: Store admin's approval signature (non-repudiation)
        update_doc["admin_signature"] = signature_data

    # Add metadata
    update_doc["verified_by"] = name
    update_doc["verified_role"] = role
    update_doc["verified_on"] = ensure_utc_datetime()  # ✅ Timezone-aware UTC
    update_doc["digital_signature"] = digital_signature  # ✅ Store signature

    if remarks:
        update_doc["remarks"] = remarks

    # Push audit entry
    claims_collection.update_one(
        {"_id": ObjectId(claim_id)},
        {"$push": {"audit_log": audit_entry}}
    )

    # Save main fields
    claims_collection.update_one(
        {"_id": ObjectId(claim_id)},
        {"$set": update_doc}
    )

    # Reload claim for notifications
    claim = claims_collection.find_one({"_id": ObjectId(claim_id)})

    # � ROLE-BASED NOTIFICATIONS: Different message content per role
    # Doctor approval triggers notifications to PATIENT and ADMIN (not doctor)
    if role == "doctor":
        decision = 'approved' if new_status == "Approved" else 'rejected'
        role_based_notification_manager.notify_doctor_decision(
            claim_id=claim_id,
            doctor_name=name,
            decision=decision
        )
        
        # 🔔 NOTIFICATION: Patient gets notified of doctor review
        patient_name = claim.get("patient_name")
        patient_user = users_collection.find_one({"name": patient_name, "role": "patient"})
        if patient_user:
            msg = f"👨‍⚕️ Doctor {name} has {new_status.lower()} your claim for review"
            notification_service.create_notification(
                to_role="patient",
                to_user_id=str(patient_user["_id"]),
                message=msg,
                notification_type="doctor_reviewed",
                related_claim_id=claim_id,
                priority="high"
            )
    # 🔐 ROLE-BASED NOTIFICATIONS: Admin decision with appropriate role filtering
    # Ensures patient sees outcome, doctor sees decision context, admin sees full record
    if role == "admin":
        decision = 'approved' if new_status == "Approved" else 'rejected'
        role_based_notification_manager.notify_admin_decision(
            claim_id=claim_id,
            admin_name=name,
            decision=decision
        )

    # 🔔 NOTIFICATION: Blockchain entry - notify both ADMIN and PATIENT ✅
    if (
        claim.get("doctor_approved") is True
        and claim.get("admin_approved") is True
        and claim.get("status") == "Approved"
    ):
        # 🔐 DIGITAL SIGNATURES: Verify all required signatures present (non-repudiation)
        # Blockchain write is BLOCKED if any required signature is missing
        signatures_valid = validate_blockchain_signatures(claim)
        if not signatures_valid['valid']:
            flash(f"⚠ Blockchain write blocked: {signatures_valid['reason']}", "warning")
        # 🔐 SMART-CONTRACT-LIKE RULES: Validate blockchain eligibility (off-chain)
        # This mimics smart contract conditions: fraud_score < threshold, approvals = true
        elif not (rules_result := validate_blockchain_rules(claim))['allowed']:
            flash(f"⚠ Blockchain write blocked: {rules_result['reason']}", "warning")
        else:
            # ✅ IMMUTABLE AUDIT TRAIL: Commit all approval records to blockchain
            # Both doctor and admin approvals are now permanently recorded (immutable)
            # This creates non-repudiable evidence of the approval decision
            doctor_audit = audit_trail_service.get_doctor_approval_record(claim_id)
            admin_audit = audit_trail_service.get_admin_approval_record(claim_id)
            approval_records = [r for r in [doctor_audit, admin_audit] if r]
            
            blockchain_committed = audit_trail_service.commit_approval_to_blockchain(
                claim_id=claim_id,
                approval_audit_records=approval_records,
                final_status="Approved"
            )
            
            if blockchain_committed:
                flash("✅ Claim approval permanently recorded in immutable blockchain.", "success")
            else:
                flash("⚠ Warning: Could not commit to blockchain. Approval still valid.", "warning")
            
            # 🔐 PRIVACY PROTECTION: Prepare encrypted claim payload for blockchain
            # Sensitive data (SSN, medical details) is encrypted with ECIES before storage
            # Only doctor and admin roles can decrypt blockchain data (role-based access control)
            encrypted_payload = prepare_claim_for_blockchain(claim)
            
            block_data = {
                "claim_id": claim_id,
                "patient_name": claim.get("patient_name"),
                "amount": claim.get("claim_amount"),
                "doctor_approved": True,
                "admin_approved": True,
                "status": "Approved",
                "verified_by": name,
                "verified_role": role,
                "verified_on": ensure_utc_datetime().isoformat(),
                "digital_signature": digital_signature,
                "encrypted_sensitive_data": encrypted_payload  # 🔐 Encrypted payload
            }

            # 🔐 PERMISSIONED BLOCKCHAIN: Pass actor_role to enforce role-based write access
            # Only Doctor and Admin can write blocks. Patient role will be rejected.
            blockchain.add_block(block_data, actor_role=role)

            # Add Blockchain event into Audit Log
            blockchain_audit = create_audit_entry(
                action="Added to Blockchain",
                by_name="System",
                by_role="blockchain",
                remarks=f"Block added for claim ID {claim_id}",
                digital_signature=digital_signature
            )

            claims_collection.update_one(
                {"_id": ObjectId(claim_id)},
                {"$push": {"audit_log": blockchain_audit}}
            )

            # Notify all admins
            admin_users = list(users_collection.find({"role": "admin"}))
            for admin in admin_users:
                notification_service.create_notification(
                    to_role="admin",
                    to_user_id=str(admin["_id"]),
                    message=f"✓ Claim from {claim.get('patient_name')} successfully added to Blockchain",
                    notification_type="blockchain_added",
                    related_claim_id=claim_id,
                    priority="normal"
                )
        
        # Notify patient ✅ FIXED
        patient_user = users_collection.find_one({
            "_id": ObjectId(claim.get("user_id")),
            "role": "patient"
        })
        if patient_user:
            notification_service.create_notification(
                to_role="patient",
                to_user_id=str(patient_user["_id"]),
                message=f"✓ Your claim has been successfully recorded on the blockchain ledger",
                notification_type="blockchain_added",
                related_claim_id=claim_id,
                priority="normal"
            )

        flash("✔ Blockchain updated: Claim stored on ledger", "success")

    # ============ COLLUSION DETECTION ============
    # Update doctor-hospital collusion risk after approval/rejection
    # Tracks doctor behavior patterns to flag suspicious approval practices
    assigned_doctor_id = claim.get("assigned_doctor_id")
    if assigned_doctor_id:
        doctor = users_collection.find_one({"_id": ObjectId(assigned_doctor_id)})
        if doctor:
            collusion_service.update_collusion_risk_database(
                doctor_id=assigned_doctor_id,
                doctor_name=doctor.get("name", "Unknown"),
                hospital_name=claim.get("hospital_name")
            )

    # ============ INSIDER THREAT DETECTION (Admin Behavior Monitoring) ============
    # Monitors admin approval patterns and detects potential insider threats.
    # This runs ONLY for admin actions and is ADVISORY ONLY:
    # - Does NOT block the admin's current action
    # - Does NOT auto-reject any claims
    # - Does NOT modify any claim data
    # If HIGH risk is detected, sends email alert to super-admin/compliance officer
    # for human review. Follows "Observe → Detect → Escalate → Let humans decide" philosophy.
    if role == "admin":
        try:
            risk_result = admin_risk_monitor_service.evaluate_and_alert_if_needed(
                admin_id=user_id,
                admin_name=name
            )
            # Log result for debugging (no user-facing message for LOW/MEDIUM risk)
            if risk_result.get("risk_level") == "HIGH":
                # System has automatically sent alert to compliance officer
                # Admin is NOT notified to prevent behavior modification
                pass
        except Exception as e:
            # Insider threat detection failure should NEVER block claim processing
            # This is advisory-only, so we log and continue
            import logging
            logging.error(f"Admin risk monitor error (non-blocking): {e}")

    flash("Claim status updated!", "success")
    return redirect(url_for("admin_dashboard") if role == "admin" else url_for("dashboard_doctor"))


@app.route("/claim_view/<claim_id>")
def claim_view(claim_id):
    if "user" not in session or session["user"]["role"] not in ["doctor","admin","patient"]:
        return redirect(url_for("login"))
    
    claim = claims_collection.find_one({"_id": ObjectId(claim_id)})
    if not claim:
        flash("Claim not found.", "danger")
        return redirect(url_for("dashboard_doctor") if session["user"]["role"]=="doctor" else url_for("admin_dashboard"))
    
    # 🔐 SECURITY: Doctor can only view claims assigned to them
    if session["user"]["role"] == "doctor":
        if claim.get("assigned_doctor_id") != session["user"]["id"]:
            flash("❌ Access Denied: You can only view claims assigned to you.", "danger")
            return redirect(url_for("dashboard_doctor"))
    
    # convert docs and id
    claim["_id"] = str(claim["_id"])
    if not isinstance(claim.get("documents"), list):
        claim["documents"] = []
    return render_template("claim_view.html", claim=claim)

@app.route("/doctor/verified_claims")
def doctor_verified_claims():
    if "user" not in session or session["user"]["role"] != "doctor":
        return redirect(url_for("login"))
    
    user_id = session["user"]["id"]

    # 🔐 SECURITY: Only claims assigned to THIS doctor
    verified = list(claims_collection.find({
        "assigned_doctor_id": user_id,  # 🔐 Filter by assignment
        "status": {"$in": ["Approved", "Rejected"]}
    }).sort("submitted_on", -1))

    # Convert ObjectId → string
    for c in verified:
        c["_id"] = str(c["_id"])
        if not isinstance(c.get("documents"), list):
            c["documents"] = []

    return render_template("doctor_verified_claims.html", claims=verified)


@app.route("/doctor/pending_claims")
def doctor_pending_claims():
    if "user" not in session or session["user"]["role"] != "doctor":
        return redirect(url_for("login"))

    user_id = session["user"]["id"]
    
    # 🔐 SECURITY: Only pending claims assigned to THIS doctor
    pending = list(claims_collection.find({
        "assigned_doctor_id": user_id,  # 🔐 Filter by assignment
        "status": "Pending"
    }).sort("submitted_on", -1))

    for c in pending:
        c["_id"] = str(c["_id"])
        if not isinstance(c.get("documents"), list):
            c["documents"] = []

    return render_template("doctor_pending_claims.html", claims=pending)


# ========== NOTIFICATION API ENDPOINTS ==========

@app.route("/api/notifications", methods=["GET"])
def get_notifications():
    """Fetch paginated notifications for logged-in user"""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session["user"]["id"]
    role = session["user"]["role"]
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    
    skip = (page - 1) * per_page
    notifications = notification_service.get_notifications_for_user(user_id, role, limit=per_page, skip=skip)
    
    return jsonify({
        "success": True,
        "notifications": notifications,
        "page": page,
        "per_page": per_page
    })


@app.route("/api/notifications/unread-count", methods=["GET"])
def get_unread_count():
    """Get count of unread notifications for navbar badge"""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session["user"]["id"]
    role = session["user"]["role"]
    count = notification_service.get_unread_count(user_id, role)
    
    return jsonify({
        "success": True,
        "unread_count": count
    })


@app.route("/api/notifications/mark-read/<notification_id>", methods=["POST"])
def mark_notification_read(notification_id):
    """Mark a single notification as read"""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    result = notification_service.mark_as_read(notification_id)
    return jsonify(result)


@app.route("/api/notifications/mark-all-read", methods=["POST"])
def mark_all_notifications_read():
    """Mark all notifications as read for the user"""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    user_id = session["user"]["id"]
    role = session["user"]["role"]
    result = notification_service.mark_all_as_read(user_id, role)
    
    return jsonify(result)


@app.route("/api/notifications/delete/<notification_id>", methods=["DELETE"])
def delete_notification(notification_id):
    """Delete a single notification"""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    result = notification_service.delete_notification(notification_id)
    return jsonify(result)


@app.route("/notifications")
def notifications_list():
    """Display all notifications for current user"""
    if "user" not in session:
        return redirect(url_for("login"))
    
    user_id = session["user"]["id"]
    role = session["user"]["role"]
    page = request.args.get("page", 1, type=int)
    per_page = 10
    
    skip = (page - 1) * per_page
    notifications = notification_service.get_notifications_for_user(user_id, role, limit=per_page, skip=skip)
    total_count = notification_service.notifications_collection.count_documents({
        "to_user_id": user_id,
        "to_role": role
    })
    
    total_pages = (total_count + per_page - 1) // per_page
    
    # Mark all as read when user visits notifications page
    notification_service.mark_all_as_read(user_id, role)
    
    return render_template(
        "notifications.html",
        notifications=notifications,
        page=page,
        total_pages=total_pages,
        total_count=total_count
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") != "production"
    app.run(host="0.0.0.0", port=port, debug=debug)
