# Smart-Contract-Like Rule Engine - Complete Implementation

## Overview

Added an off-chain smart-contract-like rule engine that conditionally controls blockchain writes. Mimics how smart contracts check conditions before state changes, but implemented as enterprise backend business logic (no Ethereum/Solidity).

**Key Features:**
- Rules are enforced at the **service layer**, not UI
- Claims violating any rule are blocked from blockchain
- Reuses existing claim, approval, and AI scoring data
- Configurable fraud score threshold

---

## Modified & New Files

### 1. **services/rules_engine.py** (Extended)
**New Section:** Smart-Contract-Like Blockchain Rules (lines 17-121)

#### Configurable Constants:
```python
# Maximum allowed AI fraud probability (0.0-1.0) for blockchain write
BLOCKCHAIN_FRAUD_SCORE_THRESHOLD = 0.5

# Required approval flags for blockchain commitment
BLOCKCHAIN_REQUIRES_DOCTOR_APPROVAL = True
BLOCKCHAIN_REQUIRES_ADMIN_APPROVAL = True
```

#### New Function: `validate_blockchain_rules(claim)`
```python
def validate_blockchain_rules(claim: dict) -> dict:
    """
    Off-chain smart contract logic: Validates whether a claim is eligible
    for blockchain commitment. Enforces business rules at the service layer.
    
    Returns:
        {
            'allowed': bool,
            'reason': str or None,
            'claim_id': str,
            'fraud_probability': float,
            'doctor_approved': bool,
            'admin_approved': bool
        }
    """
```

**Rules Enforced:**
1. **Fraud Score Rule**: `fraud_probability <= BLOCKCHAIN_FRAUD_SCORE_THRESHOLD (0.5)`
2. **Doctor Approval Rule**: `doctor_approved == True`
3. **Admin Approval Rule**: `admin_approved == True`

**Behavior:**
- If ALL rules pass → `allowed=True`
- If ANY rule fails → `allowed=False` + clear reason message

---

### 2. **services/blockchain_service.py** (Modified)
**Location:** `commit_block()` function (lines 31-95)

**Import Added:**
```python
from services.rules_engine import validate_blockchain_rules
```

**Rule Validation Added:**
```python
# 🔐 SMART-CONTRACT-LIKE RULES: Validate blockchain eligibility (off-chain)
# This mimics smart contract conditions that must be met before state changes
rules_result = validate_blockchain_rules(claim)
if not rules_result['allowed']:
    raise ValueError(
        f"Blockchain write blocked by smart contract rules: {rules_result['reason']}"
    )
```

**When Triggered:** 
- API endpoint `/claims/<claim_id>/commit` (POST) in admin_routes.py

---

### 3. **main.py** (Modified)
**Location:** Blockchain write section (lines 754-804)

**Import Added:**
```python
from services.rules_engine import validate_blockchain_rules
```

**Rule Validation Added:**
```python
# 🔐 SMART-CONTRACT-LIKE RULES: Validate blockchain eligibility (off-chain)
# This mimics smart contract conditions: fraud_score < threshold, approvals = true
rules_result = validate_blockchain_rules(claim)

if not rules_result['allowed']:
    # Blockchain write blocked by business rules
    flash(f"⚠ Blockchain write blocked: {rules_result['reason']}", "warning")
else:
    # Proceed with blockchain write
    blockchain.add_block(block_data, actor_role=role)
```

**When Triggered:**
- Admin approves a claim in web UI (route: `/update_claim_status/<claim_id>`, POST)

---

## How It Works

### Example 1: Compliant Claim (All Rules Pass) ✅

```
Claim: claim_id="123"
- fraud_probability: 0.35 (< 0.5 threshold)
- doctor_approved: True
- admin_approved: True

Validation Result:
{
    'allowed': True,
    'reason': None
}

Action: Block WRITTEN to blockchain ✅
```

### Example 2: High Fraud Score (Rule Fails) ❌

```
Claim: claim_id="456"
- fraud_probability: 0.72 (> 0.5 threshold) 🚫
- doctor_approved: True
- admin_approved: True

Validation Result:
{
    'allowed': False,
    'reason': "AI Fraud Score 0.72 exceeds threshold 0.5. Blockchain write blocked."
}

Action: Block NOT written, error message returned ❌
```

### Example 3: Missing Doctor Approval (Rule Fails) ❌

```
Claim: claim_id="789"
- fraud_probability: 0.25 (< 0.5 threshold)
- doctor_approved: False 🚫
- admin_approved: True

Validation Result:
{
    'allowed': False,
    'reason': "Doctor approval is required for blockchain commitment."
}

Action: Block NOT written, error message returned ❌
```

---

## Request Flow Diagram

```
┌──────────────────────────────────────────────────┐
│ Admin Approves Claim (Web UI)                    │
│ POST /update_claim_status/<claim_id>             │
└─────────────────────┬────────────────────────────┘
                      │
                      ▼
        ┌─────────────────────────────┐
        │ Check if all conditions met:│
        │ - doctor_approved = True?   │
        │ - admin_approved = True?    │
        │ - status = "Approved"?      │
        │                             │
        │ If NO → skip blockchain ❌  │
        │ If YES → continue           │
        └─────────────────┬───────────┘
                          │
                          ▼
        ┌──────────────────────────────────────────┐
        │ Call validate_blockchain_rules(claim)    │
        │ services/rules_engine.py                 │
        │                                          │
        │ Check:                                   │
        │ 1. fraud_probability < 0.5? ────────┐   │
        │ 2. doctor_approved == True? ────────┤   │
        │ 3. admin_approved == True?  ────────┤   │
        │                                 ▼   │   │
        │                    Any rule fails?──┘   │
        │                         │               │
        └─────────────────────────┼───────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
              ❌ BLOCKED               ✅ ALLOWED
                    │                           │
                    ▼                           ▼
        ┌──────────────────────┐  ┌──────────────────────┐
        │ Block NOT written    │  │ Block written to     │
        │ to blockchain        │  │ MongoDB blockchain   │
        │                      │  │ collection           │
        │ Return error message │  │                      │
        │ to client (flash)    │  │ Notification sent    │
        └──────────────────────┘  └──────────────────────┘
```

---

## Rule Validation Details

### Rule 1: Fraud Score Threshold
```python
fraud_probability = claim.get('fraud_probability', 1.0)
if fraud_probability > BLOCKCHAIN_FRAUD_SCORE_THRESHOLD:
    violations.append("AI Fraud Score ... exceeds threshold ...")
```
- **Threshold**: 0.5 (configurable)
- **Reason**: High-fraud claims shouldn't be on immutable ledger

### Rule 2: Doctor Approval
```python
if BLOCKCHAIN_REQUIRES_DOCTOR_APPROVAL and not claim.get('doctor_approved'):
    violations.append("Doctor approval is required ...")
```
- **Requirement**: `claim.doctor_approved == True`
- **Reason**: Clinical authorization needed for blockchain commitment

### Rule 3: Admin Approval
```python
if BLOCKCHAIN_REQUIRES_ADMIN_APPROVAL and not claim.get('admin_approved'):
    violations.append("Admin approval is required ...")
```
- **Requirement**: `claim.admin_approved == True`
- **Reason**: Administrative/compliance authorization needed

---

## Error Messages

When rules are violated, clear messages are returned:

### Fraud Score Violation:
```
⚠ Blockchain write blocked: AI Fraud Score 0.72 exceeds threshold 0.5. 
Blockchain write blocked.
```

### Missing Doctor Approval:
```
⚠ Blockchain write blocked: Doctor approval is required for blockchain commitment.
```

### Missing Admin Approval:
```
⚠ Blockchain write blocked: Admin approval is required for blockchain commitment.
```

### Multiple Violations:
```
⚠ Blockchain write blocked: AI Fraud Score 0.80 exceeds threshold 0.5. 
Blockchain write blocked. Doctor approval is required for blockchain commitment.
```

---

## Real-World Enterprise Pattern

This implementation mimics how smart contracts work:

| Smart Contract Concept | Implementation |
|---|---|
| **Condition Checking** | `validate_blockchain_rules()` checks ALL rules |
| **State Transition Rules** | Specific conditions must be met before blockchain write |
| **Atomic Execution** | All rules must pass OR write fails (no partial writes) |
| **Immutable Log** | Rules enforced before data goes to immutable blockchain |
| **Transparent Logic** | Rules defined in code (like smart contract ABI) |

**Key Difference**: Off-chain rules (backend service) vs. on-chain smart contracts. This is the **enterprise blockchain pattern** where business logic is enforced at the application layer, not on-chain.

---

## Configuration & Customization

### Changing Fraud Threshold:
```python
# In services/rules_engine.py, line 23:
BLOCKCHAIN_FRAUD_SCORE_THRESHOLD = 0.5  # Change to 0.6, 0.7, etc.
```

### Disabling a Rule:
```python
# In services/rules_engine.py, lines 28-29:
BLOCKCHAIN_REQUIRES_DOCTOR_APPROVAL = True   # Set to False to disable
BLOCKCHAIN_REQUIRES_ADMIN_APPROVAL = True    # Set to False to disable
```

### Adding New Rules:
Extend `validate_blockchain_rules()` function:
```python
# Example: Add claim amount limit
if claim.get('claim_amount', 0) > 100000:
    violations.append("Claim amount exceeds maximum for blockchain ...")
```

---

## Testing Checklist

- [ ] High fraud claim (0.72) → Blocked ❌
- [ ] Low fraud claim (0.25) → Allowed (if approvals present) ✅
- [ ] Missing doctor approval → Blocked ❌
- [ ] Missing admin approval → Blocked ❌
- [ ] All approvals + low fraud → Allowed ✅
- [ ] Error message is clear and actionable
- [ ] Blockchain persistence unaffected
- [ ] MongoDB blockchain_blocks collection only contains valid blocks
- [ ] No syntax errors in modified files
- [ ] Existing claim workflow unchanged

---

## Architecture Benefits

✅ **Business Logic Centralized**: All rules in `rules_engine.py`  
✅ **Reuses Existing Data**: No new fields or schemas needed  
✅ **Enterprise Pattern**: Off-chain smart contract logic (industry standard)  
✅ **Easy to Maintain**: Rules defined as constants and functions  
✅ **Audit Trail**: Failed rules logged in error messages  
✅ **No External Dependencies**: No Ethereum, Solidity, or third-party blockchains  

---

## Files Summary

| File | Changes | Lines |
|------|---------|-------|
| **services/rules_engine.py** | Added blockchain rules validation function & constants | 17-121 |
| **services/blockchain_service.py** | Added import + rule validation before block creation | 1-95 |
| **main.py** | Added import + rule check before blockchain write | 1-804 |

All changes are **minimal, production-ready, and backward compatible**.
