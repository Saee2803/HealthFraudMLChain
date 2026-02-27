"""
services/audit_service.py

Records audit logs with signatures into MongoDB.
"""
from datetime import datetime, timezone
import base64
from .crypto_service import sign_data
from database.mongodb_connect import get_collection


def record_audit(actor_id: str, actor_role: str, action: str, target_id: str, details: dict, signer_priv_pem: bytes = None):
    timestamp = datetime.now(timezone.utc).isoformat()
    payload = {
        "actor_id": actor_id,
        "actor_role": actor_role,
        "action": action,
        "target_id": target_id,
        "details": details or {},
        "timestamp": timestamp
    }
    serialized = (str(payload)).encode()
    signature_b64 = None
    if signer_priv_pem:
        signature_b64 = sign_data(serialized, signer_priv_pem)
    entry = {
        "actor_id": actor_id,
        "actor_role": actor_role,
        "action": action,
        "target_id": target_id,
        "details": details or {},
        "timestamp": timestamp,
        "signature": signature_b64
    }
    # Insert into audit_logs collection (lazy-get)
    get_collection('audit_logs').insert_one(entry)
    return entry
