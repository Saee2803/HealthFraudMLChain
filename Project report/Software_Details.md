# Chapter 8: Software Details

---

## 8.1 System Architecture

### 8.1.1 Overall Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Flask/Jinja2)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐ │
│  │ Patient  │  │  Doctor  │  │  Admin   │  │   Notification UI    │ │
│  │Dashboard │  │Dashboard │  │Dashboard │  │   (Real-time)        │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────────┬───────────┘ │
└───────┼─────────────┼─────────────┼────────────────────┼────────────┘
        │             │             │                    │
        ▼             ▼             ▼                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         BACKEND (Flask API)                          │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                        main.py (Routes)                         │ │
│  │  • /login, /signup, /logout                                     │ │
│  │  • /dashboard_patient, /dashboard_doctor, /admin/dashboard      │ │
│  │  • /claim_form, /claim_view, /update_claim_status               │ │
│  │  • /api/notifications, /api/blockchain/integrity                │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### 8.1.2 Service Layer Architecture

```
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│   SERVICES    │      │  ML ENGINE    │      │  BLOCKCHAIN   │
│               │      │               │      │               │
│ • Notification│      │ • RandomForest│      │ • SHA-256     │
│ • Audit Trail │      │ • TF-IDF      │      │ • MongoDB     │
│ • Collusion   │      │ • Fraud Score │      │ • Immutable   │
│ • XAI         │      │ • Binary/     │      │ • Role-based  │
│ • Encryption  │      │   Multi-class │      │   Access      │
│ • Risk Monitor│      │               │      │               │
└───────────────┘      └───────────────┘      └───────────────┘
```

---

## 8.2 Five-Layer Security Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FIVE-LAYER SECURITY ARCHITECTURE                  │
├─────────────────────────────────────────────────────────────────────┤
│ Layer 5: Blockchain Integrity Verification (Tamper Detection)       │
│ Layer 4: ECIES Asymmetric Encryption (Data Confidentiality)        │
│ Layer 3: ECDSA Digital Signatures (Non-Repudiation)                │
│ Layer 2: Smart-Contract-Like Rules (Business Validation)           │
│ Layer 1: Role-Based Access Control (Permission Management)         │
├─────────────────────────────────────────────────────────────────────┤
│                    BLOCKCHAIN FOUNDATION (MongoDB + Hash Chain)      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 8.3 Module Description

### 8.3.1 Core Modules

| Module | File | Description |
|--------|------|-------------|
| Main Application | main.py | Flask application with all routes (1500+ lines) |
| Blockchain | blockchain.py | Blockchain implementation with hash chain |
| ECIES Crypto | ecies_crypto.py | ECIES encryption utilities |
| Encryption Utils | encryption_utils.py | Additional encryption helpers |
| Utility Helpers | utils_helpers.py | Common utility functions |
| Configuration | config.py | Application settings |

### 8.3.2 Service Modules

| Service | File | Purpose |
|---------|------|---------|
| Notification Service | notification_service.py | Real-time notification management |
| Role-Based Notifications | role_based_notification_manager.py | Role-aware notification routing |
| Rules Engine | rules_engine.py | Smart contract-like business rules |
| Signature Service | signature_service.py | ECDSA digital signature generation |
| Claim Encryption | claim_encryption_service.py | Sensitive data encryption |
| Blockchain Service | blockchain_service.py | Blockchain operations |
| Collusion Detection | collusion_detection_service.py | Provider fraud pattern detection |
| XAI Explanation | xai_explanation_service.py | Explainable AI predictions |
| Audit Trail | audit_trail_service.py | Comprehensive action logging |
| Fraud Risk Engine | fraud_risk_decision_engine.py | Automated approval/rejection |
| Email Alerts | email_alert_service.py | Critical email notifications |
| Risk Monitor | admin_risk_monitor_service.py | Insider threat detection |

### 8.3.3 ML Modules

| Module | File | Purpose |
|--------|------|---------|
| Model Training V1 | train_model.py | Initial model training |
| Model Training V2 | train_model_v2.py | Binary classification model |
| Trained Model | fraud_model.pkl | Serialized ML model |
| Label Encoders | label_encoders.pkl | Feature encoding data |

---

## 8.4 Claim Processing Flow

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           CLAIM LIFECYCLE                                     │
├──────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────┐    ┌────────────┐    ┌────────────┐    ┌──────────────────┐    │
│  │ Patient │───▶│ Submit     │───▶│ ML Model   │───▶│ Fraud Risk       │    │
│  │         │    │ Claim      │    │ Prediction │    │ Decision Engine  │    │
│  └─────────┘    └────────────┘    └────────────┘    └────────┬─────────┘    │
│                                                               │               │
│         ┌────────────────────────────────────────────────────┘               │
│         │                                                                     │
│         ├────────────┬────────────┬────────────────────┐                     │
│         │            │            │                    │                     │
│         ▼            ▼            ▼                    ▼                     │
│  ┌────────────┐ ┌─────────┐ ┌─────────────┐   ┌─────────────┐               │
│  │AUTO-APPROVE│ │ MANUAL  │ │ AUTO-REJECT │   │    XAI      │               │
│  │  (<30%)    │ │ REVIEW  │ │   (>80%)    │   │ Explanation │               │
│  └──────┬─────┘ │(30-80%) │ └──────┬──────┘   └─────────────┘               │
│         │       └────┬────┘        │                                         │
│         │            │             │                                         │
│         │            ▼             │                                         │
│         │   ┌────────────────┐     │                                         │
│         │   │Doctor Approval │     │                                         │
│         │   └───────┬────────┘     │                                         │
│         │           │              │                                         │
│         │           ▼              │                                         │
│         │   ┌────────────────┐     │                                         │
│         │   │Admin Approval  │     │                                         │
│         │   └───────┬────────┘     │                                         │
│         │           │              │                                         │
│         ▼           ▼              ▼                                         │
│  ┌──────────────────────────────────────────┐                               │
│  │            BLOCKCHAIN LEDGER             │                               │
│  │  • Digital Signatures (Non-repudiation)  │                               │
│  │  • Encrypted Sensitive Data (ECIES)      │                               │
│  │  • Immutable Audit Trail                 │                               │
│  └──────────────────────────────────────────┘                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8.5 Smart Contract Rules

Before blockchain commitment, claims undergo automated validation:

```python
Rule 1: fraud_probability < 0.5    # AI threshold
Rule 2: doctor_approved == True    # Clinical authorization
Rule 3: admin_approved == True     # Administrative authorization
Rule 4: doctor_signature_valid     # Non-repudiation check
Rule 5: admin_signature_valid      # Final verification
```

Only claims passing all five rules proceed to blockchain recording.

---
