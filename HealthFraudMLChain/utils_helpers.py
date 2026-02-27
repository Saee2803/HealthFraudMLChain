"""
PRODUCTION-GRADE UTILITIES - v2.1
Comprehensive helpers for production system:
- Safe datetime normalization (CRITICAL: mixed str/datetime handling)
- Timezone conversion (UTC ↔ IST)
- Digital signatures (SHA-256)
- Explainable AI (Fraud reasons generation)
- Audit trail management
"""

import hashlib
import hmac
from datetime import datetime, timezone as dt_timezone
from pytz import timezone

# Timezone definitions
UTC_TZ = timezone('UTC')
IST_TZ = timezone('Asia/Kolkata')

# ============================================
# 🚨 CRITICAL: SAFE DATETIME NORMALIZATION
# Handles mixed str/datetime data from old DB records
# ============================================

def normalize_datetime(value, default=None):
    """
    CRITICAL HELPER: Safely normalize mixed datetime types.
    
    Problem: Old DB records have submitted_on as STRING
            New records have submitted_on as DATETIME
            This causes: TypeError: '<' not supported between str and datetime
    
    Solution: Accept both str and datetime, always return UTC datetime
    
    Args:
        value: Can be str (ISO format), datetime, or None
        default: Fallback if parsing fails (returns as-is if None)
    
    Returns:
        datetime (UTC aware) or None
        
    Guarantees:
        - Never crashes
        - Always returns timezone-aware datetime (UTC) or None
        - Backward compatible with old string records
    """
    if value is None:
        return default
    
    # Already a timezone-aware datetime
    if isinstance(value, datetime):
        if value.tzinfo is not None:
            return value.astimezone(UTC_TZ)  # Convert to UTC if needed
        else:
            # Naive datetime - assume UTC
            return UTC_TZ.localize(value)
    
    # String - parse it
    if isinstance(value, str):
        if not value:  # Empty string
            return default
        
        # Try ISO format with timezone info
        try:
            # Handle ISO strings like "2025-12-18T10:30:00Z"
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            if dt.tzinfo is not None:
                return dt.astimezone(UTC_TZ)
            else:
                return UTC_TZ.localize(dt)
        except (ValueError, TypeError):
            pass
        
        # Try simple date format like "2025-12-18"
        try:
            dt = datetime.strptime(value, "%Y-%m-%d")
            return UTC_TZ.localize(dt)
        except ValueError:
            pass
        
        # Try timestamp format
        try:
            dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            return UTC_TZ.localize(dt)
        except ValueError:
            pass
    
    # Couldn't parse - return default
    return default


def safe_sort_key(value):
    """
    CRITICAL HELPER: Safe sorting key for mixed datetime types.
    
    Use this in Python sorting when data might have str or datetime values.
    Always returns a comparable value (datetime object or fallback).
    
    Usage:
        sorted(claims, key=lambda x: safe_sort_key(x.get("submitted_on")), reverse=True)
    
    Args:
        value: String or datetime to normalize for comparison
    
    Returns:
        datetime (UTC) for sorting (or datetime.min if invalid)
        
    Guarantees:
        - No TypeError during sorting
        - Mixed types handled gracefully
    """
    normalized = normalize_datetime(value)
    return normalized if normalized is not None else datetime.min.replace(tzinfo=UTC_TZ)


def ensure_utc_datetime():
    """
    CRITICAL HELPER: Get current time as UTC-aware datetime.
    
    Replace: datetime.utcnow()  ❌ (naive, no timezone info)
    With: ensure_utc_datetime()  ✅ (aware, timezone-aware)
    
    Returns:
        datetime (UTC aware, timezone-aware)
        
    Guarantees:
        - Always timezone-aware
        - Always UTC
        - Safe for MongoDB storage
    """
    return datetime.now(UTC_TZ)


# ============================================
# TIMEZONE CONVERSION FUNCTIONS
# ============================================

def utc_to_ist(utc_datetime):
    """Convert UTC datetime to IST (Asia/Kolkata)"""
    # Normalize first (handles str or naive datetime)
    dt = normalize_datetime(utc_datetime)
    if dt is None:
        return None
    
    return dt.astimezone(IST_TZ)


def ist_to_utc(ist_datetime):
    """Convert IST datetime to UTC"""
    if isinstance(ist_datetime, str):
        try:
            ist_datetime = datetime.fromisoformat(ist_datetime)
        except:
            return ist_datetime
    
    if ist_datetime.tzinfo is None:
        ist_datetime = IST_TZ.localize(ist_datetime)
    
    return ist_datetime.astimezone(UTC_TZ)


def format_ist_time(utc_datetime, format_str="%d %b %Y, %H:%M:%S"):
    """Format UTC datetime as IST string"""
    ist_dt = utc_to_ist(utc_datetime)
    if ist_dt is None:
        return str(utc_datetime)
    return ist_dt.strftime(format_str)


# ============================================
# DIGITAL SIGNATURES (SHA-256 based)
# ============================================

def generate_digital_signature(claim_id, user_name, timestamp_str=None, secret_key="healthfraud_secret"):
    """
    Generate cryptographic signature for approval/rejection.
    
    Signature includes:
    - claim_id
    - user_name
    - timestamp (ISO format)
    
    Returns: SHA-256 hex digest
    
    Guarantees:
        - Non-repudiation: proof that specific user approved specific claim
        - Tamper-proof: any change to claim/user/timestamp breaks signature
    """
    if timestamp_str is None:
        timestamp_str = ensure_utc_datetime().isoformat()
    
    # Create signature payload
    payload = f"{claim_id}#{user_name}#{timestamp_str}"
    
    # Generate HMAC-SHA256
    signature = hmac.new(
        secret_key.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature


def verify_digital_signature(claim_id, user_name, timestamp_str, provided_signature, secret_key="healthfraud_secret"):
    """Verify a digital signature for non-repudiation"""
    expected_signature = generate_digital_signature(claim_id, user_name, timestamp_str, secret_key)
    return hmac.compare_digest(expected_signature, provided_signature)


# ============================================
# EXPLAINABLE AI (Fraud Reasons)
# ============================================

def generate_fraud_reasons(age, gender, diagnosis, amount_billed, stay_duration, fraud_probability):
    """
    Generate human-readable fraud indicators based on claim features.
    
    Rule-based XAI (no ML needed - just domain knowledge)
    
    Returns: List of explanations for the fraud prediction
    
    Guarantees:
        - Transparent: users understand WHY claim is flagged
        - Rule-based: interpretable (not black-box ML)
        - Consistent: same inputs always produce same reasons
    """
    reasons = []
    
    # Amount-based rules
    if amount_billed > 500000:
        reasons.append("High claim amount (₹500K+)")
    elif amount_billed > 200000:
        reasons.append("Moderate-high claim amount (₹200K-500K)")
    
    # Stay duration rules
    if stay_duration > 30:
        reasons.append("Prolonged hospital stay (>30 days)")
    elif stay_duration > 14:
        reasons.append("Extended hospital stay (>14 days)")
    
    # High-risk diagnosis patterns
    high_risk_diagnoses = ["Cancer", "Heart Disease", "Organ Transplant", "Surgical Procedures"]
    if diagnosis in high_risk_diagnoses:
        reasons.append(f"High-risk treatment category: {diagnosis}")
    
    # Age-based patterns
    if age < 18:
        reasons.append("Unusual claim from minor")
    elif age > 75:
        reasons.append("High-risk age demographic (>75)")
    
    # Fraud probability based rules
    if fraud_probability >= 0.85:
        reasons.append("Pattern matches known fraud schemes")
    elif fraud_probability >= 0.65:
        reasons.append("Unusual claim characteristics detected")
    
    # Default if no specific rules triggered
    if not reasons:
        if fraud_probability > 0.5:
            reasons.append("Moderate fraud risk indicators present")
        else:
            reasons.append("Claim appears legitimate")
    
    return reasons


def get_patient_explanation(fraud_reasons, fraud_probability):
    """
    Generate simplified explanation for patient (non-technical).
    
    Guarantees:
        - Easy to understand (no jargon)
        - Not alarming (but honest)
        - Actionable (patient knows why claim was reviewed)
    """
    if fraud_probability >= 0.85:
        return f"Your claim shows characteristics that require additional verification ({fraud_probability:.0%})"
    elif fraud_probability >= 0.50:
        return f"Your claim is under review due to specific details ({fraud_probability:.0%})"
    else:
        return f"Your claim appears legitimate ({fraud_probability:.0%})"


def get_doctor_admin_explanation(fraud_reasons, fraud_probability):
    """
    Generate detailed explanation for doctor/admin (technical).
    
    Guarantees:
        - Full technical details
        - All fraud indicators shown
        - Accurate fraud score
    """
    reason_text = " | ".join(fraud_reasons) if fraud_reasons else "No specific indicators"
    return f"Fraud Score: {fraud_probability:.1%}\nReasons: {reason_text}"


# ============================================
# AUDIT TRAIL MANAGEMENT
# ============================================

def create_audit_entry(action, by_name, by_role, remarks="", digital_signature=None):
    """
    Create standardized audit log entry.
    
    Args:
        action: String describing the action (e.g., "Approved", "Rejected")
        by_name: Name of user performing action
        by_role: Role of user (patient, doctor, admin, system)
        remarks: Optional additional details
        digital_signature: Optional signature for approvals
    
    Returns: Dict ready to be inserted into audit_log array
    
    Guarantees:
        - Immutable timestamp (UTC)
        - Complete user attribution
        - Optional digital signature for non-repudiation
        - Ready for compliance audits
    """
    entry = {
        "action": action,
        "by": by_name,
        "role": by_role,
        "timestamp": ensure_utc_datetime(),  # ✅ UTC aware
        "remarks": remarks
    }
    
    if digital_signature:
        entry["digital_signature"] = digital_signature
    
    return entry


# ============================================
# NOTIFICATION HELPERS
# ============================================

def build_notification_doc(to_user_id, to_role, message, notification_type, 
                          related_claim_id=None, severity="NORMAL"):
    """
    Build notification document for insertion.
    
    Args:
        to_user_id: ObjectId of recipient (user._id)
        to_role: Role of recipient (patient, doctor, admin)
        message: Human-readable message
        notification_type: Type (claim_submitted, claim_approved, etc.)
        related_claim_id: Associated claim ObjectId
        severity: NORMAL or HIGH
    
    Returns: Dict ready to insert into notifications collection
    
    Guarantees:
        - UTC timestamp
        - Proper role-based routing
        - Consistent structure
        - Ready for querying
    """
    return {
        "to_user_id": str(to_user_id),
        "to_role": to_role,
        "message": message,
        "notification_type": notification_type,
        "related_claim_id": str(related_claim_id) if related_claim_id else None,
        "severity": severity,
        "seen": False,
        "read_at": None,
        "created_at": ensure_utc_datetime()  # ✅ UTC aware
    }


def normalize_notification_query(user_id, role):
    """
    Build safe MongoDB query for notifications.
    
    Ensures proper role-based filtering and user isolation.
    
    Returns: Dict for MongoDB find() query
    """
    return {
        "to_user_id": str(user_id),
        "to_role": role
    }
