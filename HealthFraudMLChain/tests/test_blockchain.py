# ============================================================
# test_blockchain.py
# Full commit → verify → tamper test (mongomock)
# ============================================================

# ---------- STEP 1: Patch MongoClient FIRST ----------
import mongomock
import pymongo

pymongo.MongoClient = mongomock.MongoClient  # 🔥 critical


# ---------- STEP 2: Standard imports ----------
import importlib
from datetime import datetime


# ---------- STEP 3: Import db connector AFTER patch ----------
from HealthFraudMLChain.database import mongodb_connect



# ---------- STEP 4: Force in-memory DB ----------
mock_client = mongomock.MongoClient()
mock_db = mock_client["healthfraud"]

mongodb_connect.client = mock_client
mongodb_connect.db = mock_db


# ---------- STEP 5: Reload services that depend on db ----------
import services.crypto_service as crypto_service
importlib.reload(crypto_service)

import services.blockchain_service as blockchain_service
importlib.reload(blockchain_service)

import services.audit_service as audit_service
importlib.reload(audit_service)


# ============================================================
# TEST CASE
# ============================================================

def test_commit_and_verify_cycle():
    """
    Full lifecycle test:
    commit → verify → tamper → detect
    """

    # ---------- Create crypto keys ----------
    priv_doc, pub_doc = crypto_service.generate_ec_key_pair()
    priv_admin, pub_admin = crypto_service.generate_ec_key_pair()

    # ---------- Insert users ----------
    users = mongodb_connect.db["users"]

    users.insert_one({
        "user_id": "d1",
        "role": "doctor",
        "public_key": pub_doc.decode("utf-8")
    })

    users.insert_one({
        "user_id": "a1",
        "role": "admin",
        "public_key": pub_admin.decode("utf-8"),
        "key_id": "admin-key-1"
    })

    # ---------- Insert approved claim ----------
    claims = mongodb_connect.db["claims"]
    claim_id = "claim-123"

    claims.insert_one({
        "claim_id": claim_id,
        "doctor_id": "d1",
        "payload": {"foo": "bar"},
        "doctor_approved": True,
        "admin_approved": True,
        "state": "ADMIN_REVIEWED"
    })

    # ---------- Commit block ----------
    actor = {"id": "a1", "role": "admin"}

    block = blockchain_service.commit_block(
        claim_id=claim_id,
        actor=actor,
        signer_priv_pem=priv_admin,
        signer_key_id="admin-key-1"
    )

    assert "block_hash" in block

    # ---------- Verify chain (valid) ----------
    report = blockchain_service.verify_chain()
    assert report["valid"] is True

    # ---------- Tamper block ----------
    blocks = mongodb_connect.db["blocks"]
    blk = blocks.find_one({"claim_id": claim_id})

    blocks.update_one(
        {"_id": blk["_id"]},
        {"$set": {"encrypted_payload": "tampered"}}
    )

    # ---------- Verify chain (invalid) ----------
    report2 = blockchain_service.verify_chain()

    assert report2["valid"] is False
    assert any(
        e["reason"] == "block_hash_mismatch"
        for e in report2["errors"]
    )
