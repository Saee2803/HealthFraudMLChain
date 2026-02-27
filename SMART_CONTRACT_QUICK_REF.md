# Smart-Contract Rule Engine - Quick Reference

## What Was Added

A backend-enforced business rule engine that conditionally controls blockchain writes. **No blockchain is written unless ALL rules pass.**

---

## The 3 Rules

```
BLOCKCHAIN WRITE IS ALLOWED ONLY IF:

1️⃣  AI Fraud Score < 0.5  (50% fraud probability)
     └─ High-risk claims blocked from immutable ledger

2️⃣  Doctor Approval = True  (doctor_approved flag)
     └─ Clinical authorization required

3️⃣  Admin Approval = True  (admin_approved flag)
     └─ Administrative authorization required
```

---

## Files Modified

### 1. `services/rules_engine.py`
**Added:** `validate_blockchain_rules(claim)` function + constants

```python
# Configurable thresholds:
BLOCKCHAIN_FRAUD_SCORE_THRESHOLD = 0.5
BLOCKCHAIN_REQUIRES_DOCTOR_APPROVAL = True
BLOCKCHAIN_REQUIRES_ADMIN_APPROVAL = True
```

### 2. `services/blockchain_service.py`
**Modified:** `commit_block()` function

```python
# Before writing block:
rules_result = validate_blockchain_rules(claim)
if not rules_result['allowed']:
    raise ValueError(f"Blocked: {rules_result['reason']}")
```

### 3. `main.py`
**Modified:** Blockchain write section (claim approval flow)

```python
# Before writing block:
rules_result = validate_blockchain_rules(claim)
if not rules_result['allowed']:
    flash(f"⚠ {rules_result['reason']}", "warning")
else:
    blockchain.add_block(block_data, actor_role=role)
```

---

## How It Works

### ✅ Claim Passes All Rules
```
Fraud Score: 0.35 (< 0.5) ✓
Doctor Approved: True ✓
Admin Approved: True ✓

RESULT: Block written to blockchain ✅
```

### ❌ Claim Violates Fraud Score Rule
```
Fraud Score: 0.72 (> 0.5) ✗
Doctor Approved: True ✓
Admin Approved: True ✓

RESULT: Block NOT written ❌
Message: "AI Fraud Score 0.72 exceeds threshold 0.5"
```

### ❌ Claim Missing Doctor Approval
```
Fraud Score: 0.25 (< 0.5) ✓
Doctor Approved: False ✗
Admin Approved: True ✓

RESULT: Block NOT written ❌
Message: "Doctor approval is required for blockchain commitment"
```

---

## Real-World Behavior

This mimics how smart contracts work:

**Smart Contract**: 
```solidity
require(fraud_score < 0.5);
require(doctor_approved == true);
require(admin_approved == true);
// Only then: write to blockchain
```

**Our Implementation**: 
```python
rules_result = validate_blockchain_rules(claim)
if rules_result['allowed']:
    # Write to blockchain
```

**Key Difference**: Off-chain business logic (backend) instead of on-chain code. This is the **enterprise pattern** used in production systems.

---

## When Rules Are Checked

1. **API Route**: `/claims/<claim_id>/commit` (POST)
   - Calls: `services/blockchain_service.py:commit_block()`
   - Used by: Admin dashboard API

2. **Web Route**: `/update_claim_status/<claim_id>` (POST)
   - Calls: `main.py` blockchain write section
   - Used by: Admin web UI when approving claims

---

## Customization

### Change Fraud Threshold
```python
# In services/rules_engine.py:
BLOCKCHAIN_FRAUD_SCORE_THRESHOLD = 0.6  # Was 0.5, now 0.6 (60%)
```

### Disable a Rule
```python
# In services/rules_engine.py:
BLOCKCHAIN_REQUIRES_DOCTOR_APPROVAL = False  # Doctor approval optional
```

### Add New Rule
```python
# In validate_blockchain_rules() function:
if claim.get('claim_amount', 0) > 500000:
    violations.append("Claim exceeds max amount for blockchain")
```

---

## Error Response Examples

### Web UI (Flash Message):
```
⚠ Blockchain write blocked: AI Fraud Score 0.80 exceeds threshold 0.5. 
Blockchain write blocked.
```

### API Response (JSON):
```json
{
    "error": "Blockchain write blocked by smart contract rules: 
    AI Fraud Score 0.80 exceeds threshold 0.5. Blockchain write blocked."
}

HTTP 400 (Bad Request)
```

---

## Data Flow

```
Admin Approves Claim
        │
        ▼
Conditions Met?
(doctor_approved ✓ + admin_approved ✓ + status='Approved' ✓)
        │
        ├─ NO → Skip blockchain
        │
        └─ YES → Check Rules
                  │
                  ├─ fraud_score < 0.5? ──┐
                  ├─ doctor_approved? ────┤─ ALL PASS?
                  ├─ admin_approved? ─────┤
                  │                       │
                  │                   ┌───┴───┐
                  │              ✅ YES    ❌ NO
                  │                 │         │
                  ▼                 ▼         ▼
            Write to Blockchain  Flash Error  No Change
            ✅ Success           ❌ Failed
```

---

## Key Advantages

| Aspect | Benefit |
|--------|---------|
| **Service Layer** | Rules enforced at business logic, not UI |
| **Immutable Ledger** | Bad data never reaches blockchain |
| **Transparent** | Rules visible in code, not hidden in contracts |
| **Maintainable** | Change thresholds as constants, not contracts |
| **Enterprise Pattern** | Off-chain smart contract logic (industry standard) |
| **No Ethereum** | Self-contained, no external dependencies |

---

## Testing

Test these scenarios:
1. ✅ Low fraud (0.3) + both approvals → **Blockchain write**
2. ❌ High fraud (0.8) + both approvals → **Blocked**
3. ❌ Low fraud + no doctor approval → **Blocked**
4. ❌ Low fraud + no admin approval → **Blocked**
5. ✅ Low fraud + both approvals → **Blockchain write** (repeated to verify consistency)

All error messages should be clear and actionable.

---

## Summary

✅ **Blockchain writes conditionally controlled by business rules**  
✅ **Rules mimic smart contract behavior (off-chain)**  
✅ **No high-fraud or unapproved claims reach blockchain**  
✅ **Enterprise-grade, production-ready implementation**
