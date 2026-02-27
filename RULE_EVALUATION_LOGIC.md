# Smart-Contract Rule Engine - Rule Evaluation Logic

## The 3 Rules (Detailed)

### Rule 1: AI Fraud Score Threshold

**Rule Statement:**
```
AI fraud probability must be ≤ 0.5 (50%)
```

**Code:**
```python
fraud_probability = claim.get('fraud_probability', 1.0)
if fraud_probability > BLOCKCHAIN_FRAUD_SCORE_THRESHOLD:  # 0.5
    violations.append(
        f"AI Fraud Score {fraud_probability:.2f} exceeds threshold "
        f"{BLOCKCHAIN_FRAUD_SCORE_THRESHOLD}. Blockchain write blocked."
    )
```

**Examples:**
| Fraud Score | Passes? | Reason |
|------------|---------|--------|
| 0.15 | ✅ YES | 0.15 ≤ 0.5 |
| 0.30 | ✅ YES | 0.30 ≤ 0.5 |
| 0.50 | ✅ YES | 0.50 ≤ 0.5 (equal allowed) |
| 0.51 | ❌ NO | 0.51 > 0.5 |
| 0.75 | ❌ NO | 0.75 > 0.5 |
| 0.99 | ❌ NO | 0.99 > 0.5 |

**Error Message:**
```
"AI Fraud Score 0.72 exceeds threshold 0.5. Blockchain write blocked."
```

**Business Purpose:**
- Prevents high-risk claims from permanent blockchain recording
- AI model identifies fraud patterns; we trust ML output
- Threshold of 0.5 means "more likely legitimate than fraudulent"

---

### Rule 2: Doctor Approval

**Rule Statement:**
```
Doctor must explicitly approve the claim
```

**Code:**
```python
if BLOCKCHAIN_REQUIRES_DOCTOR_APPROVAL and not claim.get('doctor_approved'):
    violations.append(
        "Doctor approval is required for blockchain commitment."
    )
```

**Doctor Approval States:**
| State | Passes? | Reason |
|-------|---------|--------|
| True | ✅ YES | Doctor approved |
| False | ❌ NO | Doctor rejected |
| None | ❌ NO | Awaiting doctor decision |

**Error Message:**
```
"Doctor approval is required for blockchain commitment."
```

**Business Purpose:**
- Clinical authorization by qualified medical professional
- Ensures human oversight before immutable recording
- Doctor reviews claim details and medical necessity

---

### Rule 3: Admin Approval

**Rule Statement:**
```
Admin must explicitly approve the claim
```

**Code:**
```python
if BLOCKCHAIN_REQUIRES_ADMIN_APPROVAL and not claim.get('admin_approved'):
    violations.append(
        "Admin approval is required for blockchain commitment."
    )
```

**Admin Approval States:**
| State | Passes? | Reason |
|-------|---------|--------|
| True | ✅ YES | Admin approved |
| False | ❌ NO | Admin rejected |
| None | ❌ NO | Awaiting admin decision |

**Error Message:**
```
"Admin approval is required for blockchain commitment."
```

**Business Purpose:**
- Administrative/compliance authorization
- Ensures business logic compliance
- Admin reviews doctor's decision and final authorization

---

## Rule Evaluation Algorithm

```python
def validate_blockchain_rules(claim: dict) -> dict:
    violations = []  # Collect ALL failures
    
    # Check Rule 1: Fraud Score
    if fraud_probability > THRESHOLD:
        violations.append("Fraud Score violation message")
    
    # Check Rule 2: Doctor Approval
    if not doctor_approved:
        violations.append("Doctor approval violation message")
    
    # Check Rule 3: Admin Approval
    if not admin_approved:
        violations.append("Admin approval violation message")
    
    # Return Result
    if violations:
        return {
            'allowed': False,
            'reason': combine_all_messages(violations)  # All failures
        }
    else:
        return {
            'allowed': True,
            'reason': None
        }
```

**Key Points:**
1. ALL rules are evaluated (not short-circuit)
2. ALL violations are collected
3. ALL violation messages are combined
4. Only if ALL rules pass → allowed=True

---

## Example Evaluations

### Example 1: All Pass ✅
```
Input:
  fraud_probability: 0.35
  doctor_approved: True
  admin_approved: True

Evaluation:
  Rule 1: 0.35 ≤ 0.5? YES ✓
  Rule 2: doctor_approved == True? YES ✓
  Rule 3: admin_approved == True? YES ✓
  
  violations = []

Output:
  {
    'allowed': True,
    'reason': None
  }

Action: WRITE to blockchain ✅
```

### Example 2: High Fraud Only ❌
```
Input:
  fraud_probability: 0.72
  doctor_approved: True
  admin_approved: True

Evaluation:
  Rule 1: 0.72 ≤ 0.5? NO ✗
  Rule 2: doctor_approved == True? YES ✓
  Rule 3: admin_approved == True? YES ✓
  
  violations = [
    "AI Fraud Score 0.72 exceeds threshold 0.5. Blockchain write blocked."
  ]

Output:
  {
    'allowed': False,
    'reason': "AI Fraud Score 0.72 exceeds threshold 0.5. Blockchain write blocked."
  }

Action: BLOCK from blockchain ❌
```

### Example 3: Missing Both Approvals ❌
```
Input:
  fraud_probability: 0.25
  doctor_approved: None (not approved)
  admin_approved: None (not approved)

Evaluation:
  Rule 1: 0.25 ≤ 0.5? YES ✓
  Rule 2: doctor_approved == True? NO ✗
  Rule 3: admin_approved == True? NO ✗
  
  violations = [
    "Doctor approval is required for blockchain commitment.",
    "Admin approval is required for blockchain commitment."
  ]

Output:
  {
    'allowed': False,
    'reason': "Doctor approval is required for blockchain commitment. 
              Admin approval is required for blockchain commitment."
  }

Action: BLOCK from blockchain ❌
Message: Shows all missing approvals
```

### Example 4: All Rules Violated ❌
```
Input:
  fraud_probability: 0.95
  doctor_approved: False
  admin_approved: False

Evaluation:
  Rule 1: 0.95 ≤ 0.5? NO ✗
  Rule 2: doctor_approved == True? NO ✗
  Rule 3: admin_approved == True? NO ✗
  
  violations = [
    "AI Fraud Score 0.95 exceeds threshold 0.5. Blockchain write blocked.",
    "Doctor approval is required for blockchain commitment.",
    "Admin approval is required for blockchain commitment."
  ]

Output:
  {
    'allowed': False,
    'reason': "AI Fraud Score 0.95 exceeds threshold 0.5. Blockchain write blocked. 
              Doctor approval is required for blockchain commitment. 
              Admin approval is required for blockchain commitment."
  }

Action: BLOCK from blockchain ❌
Message: Shows ALL violations combined
```

---

## Decision Tree

```
Is fraud_probability ≤ 0.5?
  └─ NO  → BLOCKED ❌ "Fraud Score violation"
  └─ YES → Continue to next rule

Is doctor_approved == True?
  └─ NO  → BLOCKED ❌ "Doctor approval required"
  └─ YES → Continue to next rule

Is admin_approved == True?
  └─ NO  → BLOCKED ❌ "Admin approval required"
  └─ YES → ALLOWED ✅

RESULT: Write to blockchain
```

---

## Configuration Options

### Option 1: Increase Fraud Threshold
```python
BLOCKCHAIN_FRAUD_SCORE_THRESHOLD = 0.7  # Allow up to 70% fraud score
```
- More lenient: Higher-risk claims can be recorded
- Use if: Want to record more claims despite higher risk

### Option 2: Make Doctor Approval Optional
```python
BLOCKCHAIN_REQUIRES_DOCTOR_APPROVAL = False
```
- Less strict: Claims don't need doctor sign-off
- Use if: Admin approval is sufficient

### Option 3: Make Admin Approval Optional
```python
BLOCKCHAIN_REQUIRES_ADMIN_APPROVAL = False
```
- Less strict: Claims don't need admin sign-off
- Use if: Doctor approval is sufficient

### Option 4: Disable All Rules
```python
BLOCKCHAIN_REQUIRES_DOCTOR_APPROVAL = False
BLOCKCHAIN_REQUIRES_ADMIN_APPROVAL = False
```
- Effect: Only fraud score matters
- Use if: Simplifying approval workflow

---

## Real-World Thresholds

| Industry | Fraud Threshold | Doctor | Admin |
|----------|-----------------|--------|-------|
| **Conservative** | 0.3 (30%) | Required | Required |
| **Balanced** | 0.5 (50%) | Required | Required |
| **Lenient** | 0.7 (70%) | Required | Required |
| **Trust-Based** | 0.9 (90%) | Optional | Required |

**Our Implementation:** Balanced approach (0.5 threshold)

---

## Audit Trail

When a rule is violated:
1. Claim status: Remains "Approved" (passed manual review)
2. Blockchain: No block written
3. Log: Rule violation logged in error message
4. User: Flash message shows reason
5. Claim: Still retrievable, but not on immutable ledger

This maintains compliance while preventing bad data from permanent recording.
