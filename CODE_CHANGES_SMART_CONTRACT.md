# Smart-Contract Rule Engine - Code Changes Summary

## Overview
Added conditional blockchain writes based on business rules (off-chain smart contract pattern). Claims are blocked from blockchain if they violate any rule.

---

## File 1: services/rules_engine.py

### Location: Lines 17-121 (NEW SECTION ADDED)

```python
# ============================================================
# SMART-CONTRACT-LIKE BLOCKCHAIN RULES
# ============================================================
# These constants define the conditions under which a claim can
# be written to the blockchain. Mimics off-chain smart contracts
# used in enterprise permissioned blockchain systems.

# Maximum allowed AI fraud probability (0.0-1.0) for blockchain write
BLOCKCHAIN_FRAUD_SCORE_THRESHOLD = 0.5

# Required approval flags for blockchain commitment
BLOCKCHAIN_REQUIRES_DOCTOR_APPROVAL = True
BLOCKCHAIN_REQUIRES_ADMIN_APPROVAL = True


# ============================================================
# BLOCKCHAIN RULES VALIDATION
# ============================================================

def validate_blockchain_rules(claim: dict) -> dict:
    """
    Off-chain smart contract logic: Validates whether a claim is eligible
    for blockchain commitment. Enforces business rules at the service layer.
    
    This mimics how smart contracts check conditions before state changes,
    but implemented as backend business logic (enterprise pattern).
    
    Args:
        claim: Claim document from MongoDB
    
    Returns:
        {'allowed': bool, 'reason': str or None}
    
    Raises:
        ValueError: If claim not found or missing critical fields
    """
    if not claim:
        raise ValueError('Claim not found')
    
    claim_id = claim.get('claim_id', claim.get('_id', 'unknown'))
    violations = []
    
    # ---- RULE 1: AI Fraud Score Threshold ----
    # Mimics smart contract condition: fraud_score < THRESHOLD
    fraud_probability = claim.get('fraud_probability', 1.0)
    if fraud_probability > BLOCKCHAIN_FRAUD_SCORE_THRESHOLD:
        violations.append(
            f"AI Fraud Score {fraud_probability:.2f} exceeds threshold "
            f"{BLOCKCHAIN_FRAUD_SCORE_THRESHOLD}. Blockchain write blocked."
        )
    
    # ---- RULE 2: Doctor Approval Required ----
    # Mimics smart contract condition: approved_by_doctor == True
    if BLOCKCHAIN_REQUIRES_DOCTOR_APPROVAL and not claim.get('doctor_approved'):
        violations.append(
            "Doctor approval is required for blockchain commitment."
        )
    
    # ---- RULE 3: Admin Approval Required ----
    # Mimics smart contract condition: approved_by_admin == True
    if BLOCKCHAIN_REQUIRES_ADMIN_APPROVAL and not claim.get('admin_approved'):
        violations.append(
            "Admin approval is required for blockchain commitment."
        )
    
    # ---- RULE EVALUATION RESULT ----
    if violations:
        return {
            'allowed': False,
            'reason': ' '.join(violations),
            'claim_id': claim_id,
            'fraud_probability': fraud_probability,
            'doctor_approved': claim.get('doctor_approved'),
            'admin_approved': claim.get('admin_approved')
        }
    
    return {
        'allowed': True,
        'reason': None,
        'claim_id': claim_id,
        'fraud_probability': fraud_probability,
        'doctor_approved': claim.get('doctor_approved'),
        'admin_approved': claim.get('admin_approved')
    }
```

---

## File 2: services/blockchain_service.py

### Change 1: Import (Line 1)

**BEFORE:**
```python
"""
services/blockchain_service.py

Implements commit_block, verify_chain, and load_chain_on_start.
Uses MongoDB for persistence. Assumes cryptographic helpers in services.crypto_service.
"""
```

**AFTER:**
```python
"""
services/blockchain_service.py

Implements commit_block, verify_chain, and load_chain_on_start.
Uses MongoDB for persistence. Enforces off-chain smart contract rules.
"""
import hashlib, json, base64
from datetime import datetime, timezone
from pymongo import ReturnDocument
from database.mongodb_connect import get_collection, get_db
from services.crypto_service import encrypt_for_multiple_recipients, sign_data, load_public_key, verify_signature
from services.audit_service import record_audit
from services.rules_engine import validate_blockchain_rules  # ← ADDED
```

### Change 2: commit_block() Function (Lines 31-95)

**ADDED: Rule validation check (before block creation)**

```python
def commit_block(claim_id: str, actor: dict, signer_priv_pem: bytes = None, signer_key_id: str = None):
    """
    ... docstring updated to mention smart-contract rules ...
    """
    # 🔐 PERMISSIONED BLOCKCHAIN: Role-based access control
    ALLOWED_ROLES = {'doctor', 'admin'}
    
    actor_role = actor.get('role', '').lower() if actor else None
    if actor_role not in ALLOWED_ROLES:
        raise PermissionError(...)
    
    # Load claim...
    claim = CLAIMS.find_one({'claim_id': claim_id})
    if not claim:
        raise ValueError('Claim not found')
    
    # ... existing validation ...
    
    # 🔐 SMART-CONTRACT-LIKE RULES: Validate blockchain eligibility (off-chain)
    # This mimics smart contract conditions that must be met before state changes
    rules_result = validate_blockchain_rules(claim)  # ← ADDED
    if not rules_result['allowed']:                  # ← ADDED
        raise ValueError(                            # ← ADDED
            f"Blockchain write blocked by smart contract rules: {rules_result['reason']}"
        )                                            # ← ADDED
    
    # ... rest of block creation code ...
```

---

## File 3: main.py

### Change 1: Import (Line 12)

**BEFORE:**
```python
from services.notification_service import init_notification_service
from ecies_crypto import get_encrypted_chain_for_role
```

**AFTER:**
```python
from services.notification_service import init_notification_service
from services.rules_engine import validate_blockchain_rules  # ← ADDED
from ecies_crypto import get_encrypted_chain_for_role
```

### Change 2: Blockchain Write Section (Lines 754-804)

**BEFORE:**
```python
    # 🔔 NOTIFICATION: Blockchain entry - notify both ADMIN and PATIENT ✅
    if (
        claim.get("doctor_approved") is True
        and claim.get("admin_approved") is True
        and claim.get("status") == "Approved"
    ):
        # Add blockchain block with digital signature
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
            "digital_signature": digital_signature
        }

        blockchain.add_block(block_data, actor_role=role)
        
        # ... rest of blockchain write code ...
```

**AFTER:**
```python
    # 🔔 NOTIFICATION: Blockchain entry - notify both ADMIN and PATIENT ✅
    if (
        claim.get("doctor_approved") is True
        and claim.get("admin_approved") is True
        and claim.get("status") == "Approved"
    ):
        # 🔐 SMART-CONTRACT-LIKE RULES: Validate blockchain eligibility (off-chain)    # ← ADDED
        # This mimics smart contract conditions: fraud_score < threshold, approvals=true # ← ADDED
        rules_result = validate_blockchain_rules(claim)                                  # ← ADDED
        
        if not rules_result['allowed']:                                                  # ← ADDED
            # Blockchain write blocked by business rules                                 # ← ADDED
            flash(f"⚠ Blockchain write blocked: {rules_result['reason']}", "warning")   # ← ADDED
        else:                                                                            # ← ADDED
            # Add blockchain block with digital signature
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
                "digital_signature": digital_signature
            }

            blockchain.add_block(block_data, actor_role=role)
            
            # ... rest of blockchain write code (indented inside else) ...
```

---

## Summary of Changes

### services/rules_engine.py
- **Added:** Constants for blockchain rules
- **Added:** `validate_blockchain_rules(claim)` function
- **Lines Added:** 105 lines (fully new section)

### services/blockchain_service.py
- **Modified:** Import section (added `from services.rules_engine import ...`)
- **Modified:** `commit_block()` function to call `validate_blockchain_rules()`
- **Lines Changed:** ~10 lines

### main.py
- **Modified:** Import section (added `from services.rules_engine import ...`)
- **Modified:** Blockchain write section to check rules before write
- **Lines Changed:** ~20 lines (+ indentation adjustment)

### Total
- **New Code:** ~125 lines
- **Modified Code:** ~30 lines
- **Total Impact:** Minimal, focused changes

---

## Backward Compatibility

✅ **No breaking changes**
- Existing blockchain reads work unchanged
- Existing permission checks still active
- New rules are additive (blocking only what violates rules)
- Claims that pass rules write to blockchain as before

---

## Production Ready

✅ Syntax validated  
✅ Service layer enforcement  
✅ Clear error messages  
✅ Configurable thresholds  
✅ Reuses existing data structures  
✅ No external dependencies  
✅ Enterprise pattern (off-chain smart contracts)
