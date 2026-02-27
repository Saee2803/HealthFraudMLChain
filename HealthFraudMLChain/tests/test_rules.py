# ============================================================
# test_rules.py
# State machine + RBAC + audit log test (mongomock)
# ============================================================

# ---------- STEP 1: Patch MongoClient FIRST ----------
import mongomock
import pymongo

pymongo.MongoClient = mongomock.MongoClient  # 🔥 critical


# ---------- STEP 2: Standard imports ----------
import importlib


# ---------- STEP 3: Import db connector AFTER patch ----------
from HealthFraudMLChain.database import mongodb_connect



# ---------- STEP 4: Force in-memory DB ----------
mock_client = mongomock.MongoClient()
mock_db = mock_client["healthfraud"]

mongodb_connect.client = mock_client
mongodb_connect.db = mock_db


# ---------- STEP 5: Reload services that depend on db ----------
import services.rules_engine as rules_engine
importlib.reload(rules_engine)

import services.audit_service as audit_service
importlib.reload(audit_service)

import services.crypto_service as crypto_service
importlib.reload(crypto_service)


# ============================================================
# TEST CASE
# ============================================================

def test_rules_and_transitions():
    """
    RBAC + state transition validation:
    patient ❌
    doctor ✅
    admin ✅
    """

    # ---------- Insert users ----------
    users = mongodb_connect.db["users"]

    users.insert_one({"user_id": "d1", "role": "doctor"})
    users.insert_one({"user_id": "p1", "role": "patient"})
    users.insert_one({"user_id": "a1", "role": "admin"})

    # ---------- Insert claim ----------
    claims = mongodb_connect.db["claims"]
    claim_id = "c-1"

    claims.insert_one({
        "claim_id": claim_id,
        "doctor_id": "d1",
        "payload": {"x": 1},
        "state": "SUBMITTED",
        "doctor_approved": False,
        "admin_approved": False
    })

    # ---------- Patient cannot approve ----------
    patient = {"id": "p1", "role": "patient"}
    try:
        rules_engine.apply_transition(patient, "doctor_approve", claim_id)
        assert False, "patient should not be allowed to doctor_approve"
    except Exception:
        pass

    # ---------- Doctor approves ----------
    doctor = {"id": "d1", "role": "doctor"}
    new_state = rules_engine.apply_transition(doctor, "doctor_approve", claim_id)
    assert new_state == "DOCTOR_REVIEWED"

    # ---------- Admin approves ----------
    admin = {"id": "a1", "role": "admin"}
    new_state2 = rules_engine.apply_transition(admin, "admin_approve", claim_id)
    assert new_state2 == "ADMIN_REVIEWED"

    # ---------- Invalid transition ----------
    try:
        rules_engine.apply_transition(doctor, "commit", claim_id)
        assert False, "doctor should not be able to commit"
    except Exception:
        pass

    # ---------- Audit log verification ----------
    audits = mongodb_connect.db["audit_logs"]
    assert audits.count_documents({"target_id": claim_id}) >= 2
