# Chapter 10: Database, APIs, and External Libraries

---

## 10.1 Database

### 10.1.1 MongoDB Atlas

| Aspect | Details |
|--------|---------|
| Type | Cloud-hosted NoSQL Database |
| Provider | MongoDB Atlas (Cloud) |
| Driver | PyMongo 4.6.1 |
| Data Model | Document-based (JSON-like) |

**Why MongoDB?**
- Flexible schema for varying claim structures
- High performance for read/write operations
- Cloud-hosted for reliability and scalability
- Native support for complex queries
- Easy integration with Python

### 10.1.2 Database Collections

| Collection | Purpose | Key Fields |
|------------|---------|------------|
| **users** | User account management | username, email, role, password_hash |
| **claims** | Insurance claim records | claim_id, patient_id, diagnosis, amount, status |
| **blockchain_blocks** | Immutable blockchain ledger | index, hash, previous_hash, data, timestamp |
| **notifications** | User notification system | user_id, message, type, read_status |
| **audit_logs** | Action history tracking | user_id, action, timestamp, details |

### 10.1.3 Database Schema

**Users Collection:**
```json
{
  "_id": "ObjectId",
  "username": "string",
  "email": "string",
  "password_hash": "string",
  "role": "patient | doctor | admin",
  "created_at": "datetime",
  "public_key": "string",
  "private_key": "string (encrypted)"
}
```

**Claims Collection:**
```json
{
  "_id": "ObjectId",
  "claim_id": "string",
  "patient_id": "ObjectId",
  "assigned_doctor": "ObjectId",
  "diagnosis_code": "string",
  "treatment_description": "string",
  "claim_amount": "number",
  "fraud_probability": "number",
  "status": "submitted | under_review | approved | rejected",
  "doctor_approved": "boolean",
  "admin_approved": "boolean",
  "doctor_signature": "string",
  "admin_signature": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**Blockchain Blocks Collection:**
```json
{
  "_id": "ObjectId",
  "index": "number",
  "timestamp": "datetime",
  "data": "encrypted_claim_data",
  "previous_hash": "string",
  "hash": "string",
  "nonce": "number"
}
```

---

## 10.2 API Endpoints

### 10.2.1 Authentication APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/login` | POST | User login with credentials |
| `/signup` | POST | New user registration |
| `/logout` | GET | Session termination |

### 10.2.2 Dashboard APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/dashboard_patient` | GET | Patient dashboard view |
| `/dashboard_doctor` | GET | Doctor dashboard view |
| `/admin/dashboard` | GET | Administrator dashboard |

### 10.2.3 Claim Management APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/claim_form` | GET/POST | Claim submission form |
| `/claim_view/<id>` | GET | View claim details |
| `/my_claims` | GET | List user's claims |
| `/update_claim_status` | POST | Update claim status |
| `/approve_claim/<id>` | POST | Doctor/Admin approval |
| `/reject_claim/<id>` | POST | Claim rejection |

### 10.2.4 Notification APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/notifications` | GET | Fetch user notifications |
| `/api/notifications/read/<id>` | POST | Mark notification as read |
| `/api/notifications/count` | GET | Get unread notification count |

### 10.2.5 Blockchain APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/blockchain_view` | GET | View blockchain ledger |
| `/api/blockchain/integrity` | GET | Verify blockchain integrity |
| `/api/blockchain/block/<index>` | GET | Get specific block details |

### 10.2.6 Administrative APIs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/add_doctor` | POST | Add new doctor account |
| `/admin/collusion_report` | GET | View collusion detection results |
| `/admin/audit_logs` | GET | View audit trail |
| `/admin/insider_threats` | GET | View insider threat alerts |

---

## 10.3 External Libraries

### 10.3.1 Web Framework Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| Flask | 3.0.2 | Web application framework |
| Werkzeug | 3.0.1 | WSGI utilities, password hashing |
| Jinja2 | 3.1.3 | Template engine |
| MarkupSafe | 2.1.5 | Safe HTML string handling |
| blinker | 1.7.0 | Signal support for Flask |
| click | 8.1.7 | CLI interface |
| itsdangerous | 2.1.2 | Data signing for sessions |

### 10.3.2 Machine Learning Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| scikit-learn | 1.4.0 | ML algorithms (Random Forest, TF-IDF) |
| pandas | 2.2.1 | Data manipulation and analysis |
| numpy | 1.26.4 | Numerical computing |

### 10.3.3 Cryptography Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| eciespy | 0.4.1 | ECIES asymmetric encryption |
| pycryptodome | 3.20.0 | SHA-256 hashing, crypto functions |

### 10.3.4 Database Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| pymongo | 4.6.1 | MongoDB driver for Python |

### 10.3.5 Utility Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| python-dateutil | 2.9.0.post0 | Date/time parsing |
| pytz | 2024.1 | Timezone handling |
| python-dotenv | 1.0.1 | Environment variable management |

### 10.3.6 Deployment Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| gunicorn | 21.2.0 | Production WSGI server |

---

## 10.4 Internal Service Modules

### 10.4.1 Service Layer

| Service | Description |
|---------|-------------|
| notification_service | Real-time notification dispatch |
| role_based_notification_manager | Role-aware notification routing |
| rules_engine | Smart contract business rule validation |
| signature_service | ECDSA digital signature operations |
| claim_encryption_service | ECIES encryption for claims |
| blockchain_service | Blockchain CRUD operations |
| collusion_detection_service | Provider fraud pattern analysis |
| xai_explanation_service | Explainable AI prediction details |
| audit_trail_service | Comprehensive action logging |
| fraud_risk_decision_engine | Automated approval logic |
| email_alert_service | Email notification dispatch |
| admin_risk_monitor_service | Insider threat detection |

---

## 10.5 File Upload Handling

| Supported Formats | Storage Location |
|-------------------|-----------------|
| PNG, JPG, JPEG | static/uploads/ |
| PDF | static/uploads/ |
| DOCX | static/uploads/ |

---
