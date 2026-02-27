"""
Utility helper functions for HealthFraudMLChain
PRODUCTION-SAFE VERSION
"""

import hashlib
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

# --------------------------------------------------
# DATETIME HELPERS (🔥 CRITICAL FIX INCLUDED)
# --------------------------------------------------

def normalize_datetime(dt: Any) -> datetime:
    """
    Normalize any datetime/string to timezone-aware UTC datetime.
    Prevents offset-naive vs offset-aware comparison errors.
    """
    if dt is None:
        return datetime.min.replace(tzinfo=timezone.utc)

    # If string timestamp
    if isinstance(dt, str):
        try:
            parsed = datetime.fromisoformat(dt.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except Exception:
            return datetime.min.replace(tzinfo=timezone.utc)

    # If datetime object
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    return datetime.min.replace(tzinfo=timezone.utc)


def safe_sort_key(dt: Any) -> datetime:
    """
    Safe sorting key for datetime fields.
    Always returns timezone-aware UTC datetime.
    """
    return normalize_datetime(dt)


def ensure_utc_datetime() -> datetime:
    """Get current UTC datetime (timezone-aware)"""
    return datetime.now(timezone.utc)


def utc_to_ist(dt: datetime) -> datetime:
    """
    Convert UTC datetime to IST (UTC + 5:30)
    """
    if dt is None:
        return dt

    if isinstance(dt, str):
        dt = normalize_datetime(dt)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt + timedelta(hours=5, minutes=30)


def format_ist_time(dt: Any, fmt: str = "%d %b %Y, %H:%M:%S") -> str:
    """
    Format datetime as IST string for UI display.
    """
    try:
        dt = normalize_datetime(dt)
        ist_dt = utc_to_ist(dt)
        return ist_dt.strftime(fmt)
    except Exception:
        return str(dt)

# --------------------------------------------------
# SECURITY & AUDIT HELPERS
# --------------------------------------------------

def generate_digital_signature(claim_id: str, name: str, timestamp: str) -> str:
    """
    Generate a deterministic short digital signature.
    """
    data = f"{claim_id}:{name}:{timestamp}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def create_audit_entry(
    action: str,
    by_name: str,
    by_role: str,
    remarks: str = "",
    digital_signature: str = None
) -> Dict:
    """
    Create audit log entry (blockchain + audit trail safe).
    """
    ts = ensure_utc_datetime()
    return {
        "action": action,
        "by_name": by_name,
        "by_role": by_role,
        "timestamp": ts,
        "remarks": remarks,
        "digital_signature": digital_signature
        or generate_digital_signature(action, by_name, ts.isoformat())
    }

# --------------------------------------------------
# FRAUD EXPLANATION HELPERS (XAI) - Updated for v2.0 Model
# --------------------------------------------------

def generate_fraud_reasons(
    age: int,
    gender: str,
    diagnosis: str,
    claim_amount: float,
    stay_duration: int,
    fraud_prob: float
) -> List[str]:
    """
    Generate explainable fraud risk reasons aligned with ML v2.0 model features.
    These reasons match the engineered features used in the model for consistency.
    """
    reasons = []

    # CRITICAL: Gender-Diagnosis Mismatch (strongest fraud signal)
    pregnancy_related = ["Pregnancy", "Cesarean Section"]
    if gender == "Male" and diagnosis in pregnancy_related:
        reasons.append(f"🚨 CRITICAL: Gender mismatch - Male patient with {diagnosis}")

    # Age-Diagnosis Anomalies
    if age < 15 and diagnosis == "Cataract Surgery":
        reasons.append(f"⚠️ Age anomaly: {age}-year-old with Cataract Surgery")
    if age < 10 and diagnosis == "Hypertension":
        reasons.append(f"⚠️ Age anomaly: {age}-year-old with Hypertension")
    if age > 55 and diagnosis == "Pregnancy":
        reasons.append(f"⚠️ Unusual: {age}-year-old with Pregnancy")

    # Amount-based indicators
    if claim_amount > 500000:
        reasons.append(f"🔴 Extreme claim amount: ₹{claim_amount:,.0f}")
    elif claim_amount > 300000:
        reasons.append(f"🟠 Very high claim amount: ₹{claim_amount:,.0f}")
    elif claim_amount > 100000:
        reasons.append(f"🟡 High claim amount: ₹{claim_amount:,.0f}")

    # Stay duration indicators
    if stay_duration == 0:
        reasons.append("🔴 Zero-day hospital stay with billing")
    elif stay_duration <= 1 and claim_amount > 100000:
        reasons.append(f"⚠️ Short stay ({stay_duration} day) with high amount")

    # Amount per day ratio
    if stay_duration is not None and stay_duration >= 0:
        amount_per_day = claim_amount / (stay_duration + 1)
        if amount_per_day > 200000:
            reasons.append(f"🔴 Extreme daily cost: ₹{amount_per_day:,.0f}/day")
        elif amount_per_day > 100000:
            reasons.append(f"🟠 High daily cost: ₹{amount_per_day:,.0f}/day")

    # Age risk indicators
    if age < 5 or age > 85:
        reasons.append(f"⚠️ High-risk age group: {age} years")
    elif age > 75:
        reasons.append(f"Elderly patient: {age} years")

    # Extended hospital stays
    if stay_duration and stay_duration > 30:
        reasons.append(f"Extended hospital stay: {stay_duration} days")

    # ML model confidence
    if fraud_prob >= 0.85:
        reasons.append("🔴 ML model: Very high fraud probability")
    elif fraud_prob >= 0.7:
        reasons.append("🟠 ML model: High fraud probability")
    elif fraud_prob >= 0.5:
        reasons.append("🟡 ML model: Moderate fraud probability")

    # Default if no specific reasons
    if not reasons:
        if fraud_prob < 0.3:
            reasons.append("✅ Claim appears legitimate")
        else:
            reasons.append("Standard risk indicators present")

    return reasons


def get_patient_explanation(claim_data: Dict, fraud_prob: float) -> str:
    """
    Patient-friendly fraud explanation.
    Provides clear, non-alarming feedback to patients.
    """
    if fraud_prob < 0.25:
        return "✅ Your claim appears legitimate and is being processed normally."
    elif fraud_prob < 0.5:
        return "📋 Your claim is under standard review. Processing may take 1-2 business days."
    elif fraud_prob < 0.75:
        return "📋 Your claim requires additional verification. Our team will contact you if needed."
    else:
        return "⚠️ Your claim is under detailed review due to unusual patterns. Please ensure all documents are accurate."


def get_doctor_admin_explanation(claim_data: Dict, fraud_prob: float) -> str:
    """
    Detailed explanation for doctors/admins with full risk breakdown.
    """
    # Extract claim details
    age = claim_data.get("age", 0)
    gender = claim_data.get("gender", "")
    diagnosis = claim_data.get("diagnosis", claim_data.get("treatment", ""))
    claim_amount = claim_data.get("claim_amount", claim_data.get("amount", 0))
    stay_duration = claim_data.get("stay_duration", 0)
    
    # Generate detailed reasons
    reasons = generate_fraud_reasons(
        age, gender, diagnosis, claim_amount, stay_duration, fraud_prob
    )

    # Risk level indicator
    if fraud_prob >= 0.8:
        risk_level = "🔴 CRITICAL"
    elif fraud_prob >= 0.6:
        risk_level = "🟠 HIGH"
    elif fraud_prob >= 0.4:
        risk_level = "🟡 MODERATE"
    else:
        risk_level = "🟢 LOW"

    return (
        f"Risk Level: {risk_level} ({fraud_prob:.1%})\n"
        f"Risk Factors:\n• " + "\n• ".join(reasons)
    )

# --------------------------------------------------
# NOTIFICATION HELPERS
# --------------------------------------------------

def build_notification_doc(
    to_role: str,
    to_user_id: str,
    message: str,
    notification_type: str = "general",
    related_claim_id: str = None,
    priority: str = "normal"
) -> Dict:
    """
    Build notification document (MongoDB safe).
    """
    return {
        "to_role": to_role,
        "to_user_id": to_user_id,
        "message": message,
        "notification_type": notification_type,
        "related_claim_id": related_claim_id,
        "priority": priority,
        "created_at": ensure_utc_datetime(),
        "read": False
    }


def normalize_notification_query(user_id: str, role: str) -> Dict:
    """
    Normalize notification query filters.
    """
    return {
        "to_user_id": user_id,
        "to_role": role
    }
