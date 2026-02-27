# Doctor-Hospital Collusion Detection Engine
## Quick Reference Guide

---

## 🎯 What Was Implemented

A **lightweight backend service** that flags suspicious doctors and hospitals by analyzing claim approval patterns. 

**Real-world use:** Detect when a doctor consistently approves claims with high fraud indicators, suggesting collusion with a specific hospital.

---

## 📁 Files Changed

### NEW
- **`services/collusion_detection_service.py`** (~350 lines)
  - Core collusion detection logic
  - Doctor and hospital risk scoring
  - MongoDB integration

### MODIFIED
- **`main.py`** (+15 lines)
  - Import collusion service
  - Initialize service at startup
  - Call after claim submission (line ~394)
  - Call after claim approval (line ~931)

- **`utils_helpers_v2.py`** (+50 lines)
  - `format_risk_level()` - Format risk for display
  - `get_collusion_risk_summary()` - Human-readable risk explanation

---

## 🔧 How It Works

### Simple Formula
```
Doctor Risk = (High-Fraud Claims) / (Total Claims)
Hospital Risk = (High-Fraud Claims) / (Total Claims at Hospital)

Risk Levels:
- LOW:    < 20%
- MEDIUM: 20-50%
- HIGH:   > 50%
```

### Example
```
Dr. John handled 100 claims
- 60 had fraud_probability >= 0.6 (suspicious)
- Risk Score = 60/100 = 60%
- Classification = HIGH ⚠️
```

---

## 🗄️ MongoDB Integration

### New Collection: `collusion_risk`

Stores risk assessments for doctors and hospitals:

```json
{
  "type": "doctor",
  "doctor_id": "...",
  "doctor_name": "Dr. John",
  "total_claims": 100,
  "high_risk_claims": 60,
  "risk_score": 0.60,
  "risk_level": "HIGH",
  "last_updated": "2025-12-28T10:30:00Z"
}
```

**Automatically created** with indexes on:
- `doctor_id`
- `hospital_name`
- `type`

---

## 💻 API Reference

### Service Methods

```python
# Initialize service
collusion_service = init_collusion_detection_service(db)

# Compute doctor risk
risk = collusion_service.compute_doctor_risk_score(
    doctor_id="...",
    doctor_name="Dr. John"
)
# Returns: Dict with risk_score, risk_level, reasoning

# Compute hospital risk
risk = collusion_service.compute_hospital_risk_score(
    hospital_name="City Medical"
)
# Returns: Dict with aggregated risk data

# Detect all suspicious entities
patterns = collusion_service.detect_collusion_patterns()
# Returns: {"HIGH_RISK_DOCTORS": [...], "HIGH_RISK_HOSPITALS": [...]}

# Update/store risk in database
success = collusion_service.update_collusion_risk_database(
    doctor_id="...",
    doctor_name="Dr. John",
    hospital_name="City Medical"
)

# Retrieve cached risk
risk = collusion_service.get_doctor_risk(doctor_id)
risk = collusion_service.get_hospital_risk(hospital_name)
```

### Helper Functions

```python
from utils_helpers_v2 import format_risk_level, get_collusion_risk_summary

# Format for display
risk_info = format_risk_level("HIGH")
# Returns: {"text": "🔴 High Risk", "class": "badge-danger"}

# Generate readable summary
summary = get_collusion_risk_summary(risk_assessment)
# Returns: "Dr. John (HIGH): Handled 100 claims, 60 were high-fraud-probability. Risk Score: 60.0%"
```

---

## 🔄 Integration Points in Workflow

### 1. Claim Submission (Line ~394 in main.py)
```python
# After patient submits claim
collusion_service.update_collusion_risk_database(
    doctor_id=assigned_doctor_id,
    doctor_name=doctor_name_for_display,
    hospital_name=hospital_name
)
```
**Effect:** Adds new claim to doctor's profile, recalculates risk

### 2. Claim Approval/Rejection (Line ~931 in main.py)
```python
# After doctor or admin reviews claim
collusion_service.update_collusion_risk_database(
    doctor_id=assigned_doctor_id,
    doctor_name=doctor_name,
    hospital_name=hospital_name
)
```
**Effect:** Updates risk after approval action is taken

---

## 📊 Risk Assessment Example

```
Hospital X (256 claims processed)
├─ Doctor A: 50/100 = 50% → MEDIUM risk
├─ Doctor B: 70/90  = 78% → HIGH risk ⚠️
├─ Doctor C: 5/50   = 10% → LOW risk
└─ Hospital Aggregate: 125/256 = 49% → MEDIUM risk

Action Items:
✓ Flag Doctor B for investigation
✓ Review Hospital X's approval procedures
✓ Check if Doctors B and X coordinate (same hospital pattern)
```

---

## 🎯 When It Triggers

| Event | What Happens |
|-------|--------------|
| Patient submits claim | Risk score updated for assigned doctor + hospital |
| Doctor approves claim | Risk score recalculated based on approval pattern |
| Doctor rejects claim | Risk score recalculated |
| Admin approves claim | Risk score recalculated |
| Admin rejects claim | Risk score recalculated |

---

## 🔍 Query Examples for Investigations

```python
from pymongo import MongoClient

db = MongoClient(...)["healthfraudmlchain"]
collusion_risk = db["collusion_risk"]

# Find all high-risk doctors
high_risk_doctors = collusion_risk.find({
    "type": "doctor",
    "risk_level": "HIGH"
}).sort("risk_score", -1)

# Find doctors at high-risk hospitals
doctors_at_risk_hospital = collusion_risk.find({
    "hospital_name": "City Medical",
    "type": "doctor",
    "risk_level": {"$in": ["MEDIUM", "HIGH"]}
})

# Find doctors with >60% fraud rate
very_high_risk = collusion_risk.find({
    "type": "doctor",
    "risk_score": {"$gt": 0.6}
})
```

---

## ✅ Validation Checklist

- [x] Service creates `collusion_risk` collection automatically
- [x] Risk scores calculated from existing `claims` collection
- [x] Indexes created on `doctor_id`, `hospital_name`, `type`
- [x] Integration with claim submission workflow
- [x] Integration with claim approval workflow
- [x] Helper functions for display formatting
- [x] No modifications to existing fraud model
- [x] No breaking changes to existing code
- [x] Uses only existing dependencies (pymongo)

---

## 🚀 Performance Notes

- **First Run:** Scans all claims in database (one-time cost)
- **Subsequent Updates:** O(n) where n = claims by that doctor
- **Query Time:** Indexed lookup on doctor_id/hospital_name is O(1)
- **Memory:** Risk scores stored in MongoDB, not in-memory caching

---

## 🔐 Security & Privacy

- ✅ No additional PII collected
- ✅ Calculations use only existing claim data
- ✅ Risk assessments timestamped for audit
- ✅ No direct exposure of personal information
- ✅ Suitable for regulatory review (transparent math)

---

## 📈 Future Enhancements

1. **Risk Trends:** Track score changes week-over-week
2. **Peer Comparison:** Compare against specialty average
3. **Network Analysis:** Identify if same doctors work at multiple high-risk hospitals
4. **Time-based Patterns:** Detect if fraud escalates during certain periods
5. **Investigation Integration:** Flag high-risk claims for manual review queue

---

## 🐛 Troubleshooting

### Risk scores not updating
- Verify `collusion_service.update_collusion_risk_database()` is called
- Check doctor_id and hospital_name are correctly passed
- Verify MongoDB connection is active

### Scores seem incorrect
- Ensure claims have `fraud_probability` field populated by ML model
- Check that threshold (0.6) for "high-risk" claims is appropriate for your data
- Verify claims have correct `assigned_doctor_id` and `hospital_name`

### Collection not created
- Service auto-creates on first initialization
- Check MongoDB connection permissions
- Verify `init_collusion_detection_service(db)` is called in main.py startup

---

## 📞 Support

For questions on:
- **Logic:** See `services/collusion_detection_service.py` comments
- **Integration:** Check integration points in `main.py` (lines ~394, ~931)
- **Display:** See `utils_helpers_v2.py` helper functions

