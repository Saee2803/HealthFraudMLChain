# Collusion Detection Engine - Code Changes Summary

## 📋 Overview
Added a Doctor-Hospital Collusion Detection service to identify suspicious fraud patterns. The system analyzes historical claim data to flag doctors and hospitals with unusually high fraud rates, indicating potential coordinated fraud schemes.

---

## 📁 New Files

### `services/collusion_detection_service.py` (350 lines)

**Purpose:** Core collusion detection logic and database integration

**Key Classes:**
- `CollusionDetectionService` - Main service class

**Key Methods:**
```python
def compute_doctor_risk_score(doctor_id, doctor_name) → Dict
    # Calculates risk score for a doctor
    # Risk = (high-fraud claims) / (total claims)
    # Returns: score, level (LOW/MEDIUM/HIGH), statistics

def compute_hospital_risk_score(hospital_name) → Dict
    # Calculates aggregated risk for a hospital
    # Returns: score, level, doctor count, statistics

def detect_collusion_patterns() → Dict
    # Identifies all high-risk doctors and hospitals
    # Returns: {"HIGH_RISK_DOCTORS": [...], "HIGH_RISK_HOSPITALS": [...]}

def update_collusion_risk_database(doctor_id, doctor_name, hospital_name) → bool
    # Updates MongoDB with latest risk assessments
    # Called after each claim submission/approval

def get_doctor_risk(doctor_id) → Optional[Dict]
    # Retrieves cached risk assessment for doctor

def get_hospital_risk(hospital_name) → Optional[Dict]
    # Retrieves cached risk assessment for hospital

def init_collusion_detection_service(db) → CollusionDetectionService
    # Factory function to initialize service with MongoDB connection
    # Creates indexes automatically
```

**Algorithm:**
```
For each doctor:
    claims_with_doctor = find all claims where assigned_doctor_id = doctor
    high_fraud_count = count claims where fraud_probability >= 0.6
    risk_score = high_fraud_count / len(claims_with_doctor)
    risk_level = classify(risk_score) # LOW | MEDIUM | HIGH

For each hospital:
    claims_with_hospital = find all claims from hospital_name
    high_fraud_count = count claims where fraud_probability >= 0.6
    risk_score = high_fraud_count / len(claims_with_hospital)
    risk_level = classify(risk_score)
```

**Threshold Logic:**
```
Risk Score    | Classification | Meaning
0.0 - 0.2     | LOW            | Normal, <20% high-fraud claims
0.2 - 0.5     | MEDIUM         | Moderate concern, 20-50%
0.5 - 1.0     | HIGH           | High suspicion, >50%
```

**MongoDB Collections Used:**
- `claims` (existing) - read claims data
- `users` (existing) - read doctor information  
- `collusion_risk` (NEW) - write risk assessments

---

## 📝 Modified Files

### `main.py`

**Change 1: Import (Line 17)**
```python
# OLD
from services.claim_encryption_service import prepare_claim_for_blockchain
from services.blockchain_service import verify_blockchain_integrity

# NEW
from services.claim_encryption_service import prepare_claim_for_blockchain
from services.blockchain_service import verify_blockchain_integrity
from services.collusion_detection_service import init_collusion_detection_service
```

**Change 2: Service Initialization (Line 56-58)**
```python
# OLD
# ---------- Notification Service ----------
notification_service = init_notification_service(db)

# NEW
# ---------- Notification Service ----------
notification_service = init_notification_service(db)

# ---------- Collusion Detection Service ----------
# Detects suspicious patterns of doctor-hospital fraud collusion
collusion_service = init_collusion_detection_service(db)
```

**Change 3: Claim Submission Workflow (After line 383)**
```python
# Location: In submit_claim() route, after notifications block

# Added code:
# ============ COLLUSION DETECTION ============
# Update doctor-hospital collusion risk scores after each claim submission
# This detects suspicious patterns of coordinated fraud
if assigned_doctor_id:
    collusion_service.update_collusion_risk_database(
        doctor_id=assigned_doctor_id,
        doctor_name=doctor_name_for_display,
        hospital_name=request.form.get("hospitalName")
    )
```

**When it runs:** After each new claim submission, before redirect
**Impact:** Updates doctor and hospital risk profiles

**Change 4: Claim Approval Workflow (After line 930)**
```python
# Location: In update_claim_status() route, after blockchain operations

# Added code:
# ============ COLLUSION DETECTION ============
# Update doctor-hospital collusion risk after approval/rejection
# Tracks doctor behavior patterns to flag suspicious approval practices
assigned_doctor_id = claim.get("assigned_doctor_id")
if assigned_doctor_id:
    doctor = users_collection.find_one({"_id": ObjectId(assigned_doctor_id)})
    if doctor:
        collusion_service.update_collusion_risk_database(
            doctor_id=assigned_doctor_id,
            doctor_name=doctor.get("name", "Unknown"),
            hospital_name=claim.get("hospital_name")
        )
```

**When it runs:** After doctor or admin reviews a claim
**Impact:** Recalculates risk based on approval action

---

### `utils_helpers_v2.py`

**Change 1: Export List (Line 543-544)**
```python
# Added to __all__:
'get_collusion_risk_summary',
'format_risk_level',
```

**Change 2: New Function - `format_risk_level()` (Line 556)**
```python
def format_risk_level(risk_level: str) -> Dict[str, str]:
    """
    Format risk level for display with styling information.
    
    Args:
        risk_level: Risk level (LOW, MEDIUM, HIGH, UNKNOWN)
        
    Returns:
        Dict with display text and CSS class
    """
    risk_styles = {
        "LOW": {"text": "🟢 Low Risk", "class": "badge-success"},
        "MEDIUM": {"text": "🟡 Medium Risk", "class": "badge-warning"},
        "HIGH": {"text": "🔴 High Risk", "class": "badge-danger"},
        "UNKNOWN": {"text": "⚪ Unknown", "class": "badge-secondary"}
    }
    return risk_styles.get(risk_level, risk_styles["UNKNOWN"])
```

**Use:** Format risk levels for dashboard/report display

**Change 3: New Function - `get_collusion_risk_summary()` (Line 575)**
```python
def get_collusion_risk_summary(risk_assessment: Dict) -> str:
    """
    Generate human-readable summary of collusion risk assessment.
    
    Real-world use: Explain to compliance officers why a doctor/hospital is flagged.
    
    Args:
        risk_assessment: Dict from collusion_detection_service
        
    Returns:
        String explanation of the risk
    """
    # For doctor: "{name} ({level}): Handled {n} claims, {m} were high-fraud. Risk: {score}%"
    # For hospital: "{name} ({level}): {n} claims with {d} doctors, {m} high-fraud. Risk: {score}%"
```

**Use:** Generate compliance-ready explanations

---

## 🗄️ Database Changes

### New Collection: `collusion_risk`

**Auto-created by:** `init_collusion_detection_service(db)`

**Indexes Created:**
```javascript
db.collusion_risk.createIndex({ "doctor_id": 1 })
db.collusion_risk.createIndex({ "hospital_name": 1 })
db.collusion_risk.createIndex({ "type": 1 })
```

**Document Examples:**

Doctor Risk Document:
```json
{
  "_id": ObjectId("..."),
  "type": "doctor",
  "doctor_id": "ObjectId_string",
  "doctor_name": "Dr. John Smith",
  "total_claims": 100,
  "approved_claims": 70,
  "rejected_claims": 30,
  "high_risk_claims": 60,
  "risk_score": 0.60,
  "risk_level": "HIGH",
  "last_updated": ISODate("2025-12-28T10:30:00Z"),
  "reasoning": "Doctor handled 100 claims; 60 were high-fraud-probability."
}
```

Hospital Risk Document:
```json
{
  "_id": ObjectId("..."),
  "type": "hospital",
  "hospital_name": "City Medical Center",
  "total_claims": 250,
  "total_doctors": 15,
  "high_risk_claims": 140,
  "risk_score": 0.56,
  "risk_level": "HIGH",
  "last_updated": ISODate("2025-12-28T10:30:00Z"),
  "reasoning": "Hospital processed 250 claims with 15 doctors; 140 were high-fraud-probability."
}
```

---

## 🔄 Workflow Integration

### Claim Submission Flow
```
Patient submits claim
    ↓
AI fraud model predicts fraud_probability
    ↓
Claim saved to MongoDB
    ↓
[NEW] Collusion detection updates doctor/hospital risk
    ↓
Notifications sent
    ↓
Doctor dashboard updated
```

### Claim Approval Flow
```
Doctor/Admin reviews claim
    ↓
Approves or rejects
    ↓
Claim status updated
    ↓
[NEW] Collusion risk recalculated based on approval pattern
    ↓
Blockchain updated (if approved)
    ↓
Notifications sent
```

---

## 📊 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Existing System                        │
├─────────────────────────────────────────────────────────────┤
│ Claims Collection (fraud_probability, assigned_doctor_id)   │
│ Users Collection (role: doctor)                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
                          ↓ (reads from)
┌─────────────────────────────────────────────────────────────┐
│           [NEW] CollusionDetectionService                   │
├─────────────────────────────────────────────────────────────┤
│ - compute_doctor_risk_score()                               │
│ - compute_hospital_risk_score()                             │
│ - update_collusion_risk_database()                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
                          ↓ (writes to)
┌─────────────────────────────────────────────────────────────┐
│              [NEW] collusion_risk Collection                │
├─────────────────────────────────────────────────────────────┤
│ {type: "doctor", doctor_id, risk_score, risk_level, ...}   │
│ {type: "hospital", hospital_name, risk_score, ...}         │
└─────────────────────────────────────────────────────────────┘
                          ↓
                          ↓ (retrieved by)
┌─────────────────────────────────────────────────────────────┐
│         [NEW] Helper Functions (utils_helpers_v2.py)        │
├─────────────────────────────────────────────────────────────┤
│ - format_risk_level()                                       │
│ - get_collusion_risk_summary()                              │
└─────────────────────────────────────────────────────────────┘
                          ↓
                          ↓ (formatted for)
┌─────────────────────────────────────────────────────────────┐
│              Admin Dashboard / Reports                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 Example: Risk Calculation Walkthrough

```
SCENARIO: Dr. Sarah handles multiple claims

Claim 1: Patient X, Hospital A, fraud_probability = 0.72 → HIGH-RISK
Claim 2: Patient Y, Hospital A, fraud_probability = 0.15 → LOW-RISK
Claim 3: Patient Z, Hospital B, fraud_probability = 0.85 → HIGH-RISK
Claim 4: Patient W, Hospital A, fraud_probability = 0.63 → HIGH-RISK
Claim 5: Patient V, Hospital B, fraud_probability = 0.25 → LOW-RISK

CALCULATION:
- Total claims: 5
- High-risk (>= 0.6): 3 (Claims 1, 3, 4)
- Doctor Risk Score = 3 / 5 = 0.60 (60%)
- Risk Level = HIGH (because > 0.5)

STORED:
{
  "type": "doctor",
  "doctor_id": "...",
  "doctor_name": "Dr. Sarah",
  "total_claims": 5,
  "high_risk_claims": 3,
  "risk_score": 0.60,
  "risk_level": "HIGH",
  "reasoning": "Doctor handled 5 claims; 3 were high-fraud-probability."
}

HOSPITAL IMPACT:
- Hospital A: 3 claims (Claims 1, 2, 4), 2 high-risk = 67% risk
- Hospital B: 2 claims (Claims 3, 5), 1 high-risk = 50% risk
```

---

## ✅ Changes Checklist

- [x] New file: `services/collusion_detection_service.py` (350 lines)
- [x] Import statement added to `main.py`
- [x] Service initialization added to `main.py`
- [x] Integration point 1: Claim submission (line ~394)
- [x] Integration point 2: Claim approval (line ~931)
- [x] Helper functions in `utils_helpers_v2.py`
- [x] MongoDB indexes created automatically
- [x] No modifications to fraud model
- [x] No breaking changes to existing code
- [x] Backward compatible with existing data

---

## 📈 Performance Impact

| Operation | Time Complexity | Notes |
|-----------|-----------------|-------|
| Doctor risk computation | O(n) | n = claims by that doctor |
| Hospital risk computation | O(m) | m = claims from hospital |
| Update to database | O(1) | Single MongoDB upsert |
| Query risk by ID | O(1) | Indexed lookup |
| Detect all patterns | O(n+m) | Full scan (used infrequently) |

**First Run:** Full scan of all claims and users
**Normal Operation:** Incremental updates on claim events

---

## 🔐 Security Considerations

- ✅ No new authentication required
- ✅ No new authorization needed (uses existing roles)
- ✅ No sensitive data exposed (uses only claim metadata)
- ✅ Timestamps for audit trail
- ✅ Calculation logic is transparent and explainable

---

## 📚 Related Documentation

- [COLLUSION_DETECTION_IMPLEMENTATION.md](./COLLUSION_DETECTION_IMPLEMENTATION.md) - Full implementation guide
- [COLLUSION_DETECTION_QUICK_REF.md](./COLLUSION_DETECTION_QUICK_REF.md) - Quick reference
- [services/collusion_detection_service.py](./HealthFraudMLChain/services/collusion_detection_service.py) - Source code

