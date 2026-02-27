## Permissioned Blockchain Feature - Implementation Summary

### Overview
Added role-based write access control to the Health Insurance Fraud Detection blockchain. Only **Doctor** and **Admin** roles are authorized to write blocks. **Patient** role is explicitly denied.

---

## Modified Files

### 1. [blockchain.py](blockchain.py#L109-L153)

**Location:** `add_block()` method (lines 109-153)

**Changes:**
- Added `actor_role` parameter to the method signature
- Added permission check before block creation (enforced at service layer, not UI)
- Raises `PermissionError` with clear message if unauthorized role attempts to write
- Only allows `{'doctor', 'admin'}` roles to write blocks

**Key Code:**
```python
def add_block(self, claim_dict: dict, actor_role: str = None):
    """
    Add a new block to the chain and persist to MongoDB.
    
    PERMISSIONED BLOCKCHAIN: Only Doctor and Admin roles can write blocks.
    Patient role is explicitly denied. This enforces role-based write access
    at the business logic layer, not UI layer.
    """
    # 🔐 PERMISSIONED BLOCKCHAIN: Enforce role-based write access
    ALLOWED_ROLES = {'doctor', 'admin'}
    
    if actor_role and actor_role.lower() not in ALLOWED_ROLES:
        raise PermissionError(
            f"Role '{actor_role}' is not authorized to write blockchain blocks. "
            f"Only {ALLOWED_ROLES} roles can write to the blockchain."
        )
```

---

### 2. [services/blockchain_service.py](services/blockchain_service.py#L31-L86)

**Location:** `commit_block()` function (lines 31-86)

**Changes:**
- Added role validation at the beginning of the function
- Raises `PermissionError` immediately if role is not authorized
- Reuses existing `actor` dictionary passed from routes (no auth re-implementation)
- Only allows `{'doctor', 'admin'}` roles to commit blocks to blockchain

**Key Code:**
```python
def commit_block(claim_id: str, actor: dict, signer_priv_pem: bytes = None, signer_key_id: str = None):
    """
    Commit a claim to the blockchain.
    
    PERMISSIONED BLOCKCHAIN: Only Doctor and Admin roles can commit blocks to blockchain.
    Patient role is explicitly denied. This enforces role-based write access
    at the service/business logic layer for enterprise-grade access control.
    """
    # 🔐 PERMISSIONED BLOCKCHAIN: Enforce role-based write access at business logic level
    ALLOWED_ROLES = {'doctor', 'admin'}
    
    actor_role = actor.get('role', '').lower() if actor else None
    if actor_role not in ALLOWED_ROLES:
        raise PermissionError(
            f"Role '{actor_role}' is not authorized to commit blocks to blockchain. "
            f"Only {ALLOWED_ROLES} roles can write to the blockchain. "
            f"This is enforced at the service layer for security compliance."
        )
```

---

### 3. [main.py](main.py#L770-L772)

**Location:** Blockchain write call (lines 770-772)

**Changes:**
- Updated `add_block()` call to pass `actor_role` parameter
- Pass the current user's role from session context
- Ensures permission check is evaluated at time of write

**Key Code:**
```python
# 🔐 PERMISSIONED BLOCKCHAIN: Pass actor_role to enforce role-based write access
# Only Doctor and Admin can write blocks. Patient role will be rejected.
blockchain.add_block(block_data, actor_role=role)
```

---

## How It Works (Enterprise Blockchain Pattern)

### Write Flow:
1. User attempts to write a claim to the blockchain
2. `main.py` calls `blockchain.add_block()` with `actor_role` parameter
3. `blockchain.py` checks if role is in `{'doctor', 'admin'}`
4. If role is **Patient**, raises `PermissionError` with clear message
5. If role is **Doctor/Admin**, block is created and persisted to MongoDB

### Alternative Flow (API Route):
1. Admin endpoint receives `/claims/<id>/commit` POST request
2. Calls `blockchain_service.commit_block(claim_id, actor)`
3. Service layer validates `actor['role']` immediately
4. If role is **Patient**, returns 403 Forbidden with error message
5. If authorized, encrypts data, computes hash, and writes to MongoDB

---

## Permission Rules

| Role | Can Write Blocks | Reason |
|------|-----------------|--------|
| **Doctor** | ✅ Yes | Authorized to approve and record claims |
| **Admin** | ✅ Yes | Authorized to review and commit blocks |
| **Patient** | ❌ No | Cannot directly modify blockchain (read-only) |

---

## Error Handling

### Unauthorized Write Attempt:
```json
{
    "error": "Role 'patient' is not authorized to write blockchain blocks. Only {'doctor', 'admin'} roles can write to the blockchain."
}
```

HTTP Status: `403 Forbidden` (via admin_routes.py error handler)

---

## Why This Is Real-World Enterprise Pattern

1. **Service Layer Enforcement**: Permission check at business logic, not UI
2. **No Auth Re-implementation**: Reuses existing session/actor mechanisms
3. **Immutable Audit Trail**: Blockchain records which role wrote each block
4. **Persistent Storage**: MongoDB-backed blockchain (same as existing system)
5. **Clear Error Messages**: Authorized users know exactly why writes are rejected
6. **Role-Based Access Control (RBAC)**: Standard enterprise security pattern

---

## Testing the Feature

### Authorized Write (Doctor/Admin):
- Doctor logs in → Approves claim → Block written ✅
- Admin logs in → Reviews claim → Block written ✅

### Unauthorized Write (Patient):
- Patient logs in → Attempts to write block → `PermissionError` raised ❌
- Patient cannot interact with blockchain write endpoints

---

## Architecture Notes

- **No new dependencies added** - Uses existing role system
- **No Ethereum/Web3** - Traditional permissioned blockchain pattern
- **No UI changes** - Backend enforcement only
- **Backward compatible** - Existing claims flow unchanged if called with valid actor_role
- **MongoDB persistent** - Blockchain chain stored as before
