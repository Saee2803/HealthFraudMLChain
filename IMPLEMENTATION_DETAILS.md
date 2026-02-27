# Permissioned Blockchain - Implementation Details

## Overview

Added role-based write access control to blockchain block creation. Only **Doctor** and **Admin** roles can write blocks. **Patient** role is explicitly denied at the service layer.

---

## Files Modified

### 1. [blockchain.py](HealthFraudMLChain/blockchain.py#L109-L153)
**Method:** `add_block(self, claim_dict: dict, actor_role: str = None)`

**Permission Check Location:**
```python
ALLOWED_ROLES = {'doctor', 'admin'}

if actor_role and actor_role.lower() not in ALLOWED_ROLES:
    raise PermissionError(
        f"Role '{actor_role}' is not authorized to write blockchain blocks. "
        f"Only {ALLOWED_ROLES} roles can write to the blockchain."
    )
```

**When Triggered:** Called from `main.py` when admin approves and finalizes a claim for blockchain entry.

---

### 2. [services/blockchain_service.py](HealthFraudMLChain/services/blockchain_service.py#L31-L60)
**Function:** `commit_block(claim_id: str, actor: dict, ...)`

**Permission Check Location:**
```python
ALLOWED_ROLES = {'doctor', 'admin'}

actor_role = actor.get('role', '').lower() if actor else None
if actor_role not in ALLOWED_ROLES:
    raise PermissionError(
        f"Role '{actor_role}' is not authorized to commit blocks to blockchain. "
        f"Only {ALLOWED_ROLES} roles can write to the blockchain. "
        f"This is enforced at the service layer for security compliance."
    )
```

**When Triggered:** Called from `routes/admin_routes.py` endpoint `/claims/<claim_id>/commit` (POST).

---

### 3. [main.py](HealthFraudMLChain/main.py#L770-L772)
**Context:** Admin claim approval workflow

**Change:**
```python
# OLD
blockchain.add_block(block_data)

# NEW
blockchain.add_block(block_data, actor_role=role)
```

**Role Source:** `role` variable from session context (admin or doctor role)

---

## Request Flow Examples

### ✅ Authorized Write (Admin)

```
1. Admin logs in → session['user']['role'] = 'admin'
2. Admin approves claim → route handler executes
3. role = 'admin' from session
4. blockchain.add_block(block_data, actor_role='admin')
5. Permission check: 'admin' ∈ {'doctor', 'admin'} → TRUE
6. Block created & persisted to MongoDB ✅
```

### ❌ Unauthorized Write (Patient)

```
1. Patient logs in → session['user']['role'] = 'patient'
2. Patient somehow triggers blockchain write
3. role = 'patient' from session
4. blockchain.add_block(block_data, actor_role='patient')
5. Permission check: 'patient' ∈ {'doctor', 'admin'} → FALSE
6. PermissionError raised ❌
7. Routes/app catches error → returns 403 Forbidden
```

### API Route Flow (Alternative)

```
POST /claims/<claim_id>/commit
{
    "signer_key_id": "key_123"
}

# In admin_routes.py
actor = {'id': 'admin_1', 'role': 'admin', 'email': 'admin@health.com'}
block = commit_block(claim_id, actor, ...)

# In blockchain_service.py
actor_role = actor.get('role', '').lower()  # 'admin'
if actor_role not in ALLOWED_ROLES:          # Check fails? Raise error
    raise PermissionError(...)
# Continue with blockchain write...
```

---

## Security Properties

### Role-Based Access Control (RBAC)
- **Doctor**: Can create blocks (clinical authority)
- **Admin**: Can review and commit blocks (administrative authority)
- **Patient**: Cannot create blocks (read-only access)

### Defense in Depth
- Permission check at **service layer** (blockchain_service.py)
- Permission check at **domain object layer** (blockchain.py)
- No reliance on frontend/UI validation
- Reuses existing session-based authentication

### Clear Error Messages
Patient attempting unauthorized write receives:
```
403 Forbidden
"Role 'patient' is not authorized to commit blocks to blockchain. 
Only {'doctor', 'admin'} roles can write to the blockchain. 
This is enforced at the service layer for security compliance."
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ User Action (Claim Approval)                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │ routes/admin_routes.py        │
        │ or main.py claim approval     │
        │ Extract role from session     │
        └──────────────┬────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────┐
        │ blockchain_service.commit_block()    │
        │ services/blockchain_service.py:31-60 │
        │                                      │
        │ 1. Check: role ∈ {doctor, admin}?   │
        │    ├─ YES → Continue                 │
        │    └─ NO → raise PermissionError     │
        │ 2. Validate claim state              │
        │ 3. Encrypt payload                   │
        │ 4. Compute hash & signature          │
        └──────────────┬───────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │ Blockchain.add_block()           │
        │ blockchain.py:109-153            │
        │                                  │
        │ 1. Check: role ∈ {doctor,admin}? │
        │    ├─ YES → Continue              │
        │    └─ NO → raise PermissionError  │
        │ 2. Create Block object            │
        │ 3. Append to chain                │
        └──────────────┬────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │ MongoDB Persistence              │
        │ blockchain_blocks collection     │
        │ Block inserted with hash,        │
        │ timestamp, encrypted data        │
        └──────────────────────────────────┘
```

---

## Error Scenarios

### Scenario 1: Patient Logs In and Requests Blockchain Write
```python
# Session data
session['user']['role'] = 'patient'

# Attempt to write
try:
    blockchain.add_block(block_data, actor_role='patient')
except PermissionError as e:
    # Caught by route handler
    return jsonify({'error': str(e)}), 403
```

### Scenario 2: Malformed Actor Dict in Service
```python
# If actor dict is None or missing 'role'
actor_role = actor.get('role', '').lower() if actor else None
# actor_role = None or ''

if actor_role not in ALLOWED_ROLES:  # None/'' not in {'doctor', 'admin'}
    raise PermissionError(...)
```

### Scenario 3: Role Comparison (Case-Insensitive)
```python
# These all work correctly:
actor_role = 'Doctor'.lower()  # 'doctor' ✅
actor_role = 'ADMIN'.lower()   # 'admin' ✅
actor_role = 'Patient'.lower() # 'patient' ❌
```

---

## MongoDB Integration

### Block Document Structure
```json
{
  "_id": ObjectId("..."),
  "claim_id": "claim_123",
  "encrypted_data": "AESencryptedstring",
  "timestamp": 1234567890.123,
  "previous_hash": "abc123def456...",
  "hash": "xyz789uvw012...",
  "metadata": {
    "written_by_role": "admin",  // Audit trail
    "written_by_id": "admin_1"
  }
}
```

**Persistence:** Block written to MongoDB `blockchain_blocks` collection only after permission check passes.

---

## Testing Checklist

- [ ] Doctor can write blocks ✅
- [ ] Admin can write blocks ✅
- [ ] Patient cannot write blocks (403 error) ❌
- [ ] Error message is clear and actionable
- [ ] Blockchain chain integrity maintained
- [ ] MongoDB contains correct audit metadata
- [ ] Session role extraction works correctly
- [ ] Case-insensitive role comparison works
- [ ] No syntax errors in modified files
- [ ] Existing claim approval workflow unchanged

---

## Real-World Enterprise Adoption

This pattern is used in production systems because:

1. **Security**: Write access controlled at service layer
2. **Auditability**: MongoDB stores who wrote each block
3. **Maintainability**: Role definitions in one place (`ALLOWED_ROLES`)
4. **Compliance**: Clear enforcement of business rules
5. **Scalability**: No external blockchain (Ethereum, etc.)
6. **Simplicity**: Integrates with existing role-based auth

---

## Compatibility

- ✅ Works with existing Flask routes
- ✅ Works with existing MongoDB persistence
- ✅ Works with existing encryption (ECIES)
- ✅ No breaking changes to public APIs
- ✅ Backward compatible if `actor_role` not provided
