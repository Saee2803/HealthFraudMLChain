# 🏥 HealthFraudMLChain

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.2-green.svg)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-brightgreen.svg)
![Blockchain](https://img.shields.io/badge/Blockchain-Custom-orange.svg)
![ML](https://img.shields.io/badge/ML-RandomForest-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**Healthcare Insurance Fraud Detection System using Machine Learning & Blockchain Technology**

[Features](#-features) • [Architecture](#-system-architecture) • [Installation](#-installation) • [Usage](#-usage-guide) • [API](#-api-endpoints)

</div>

---

## 📋 Table of Contents

1. [Overview](#-overview)
2. [Features](#-features)
3. [System Architecture](#-system-architecture)
4. [Technology Stack](#-technology-stack)
5. [Project Structure](#-project-structure)
6. [Installation](#-installation)
7. [Configuration](#-configuration)
8. [Usage Guide](#-usage-guide)
9. [User Roles](#-user-roles)
10. [Machine Learning Model](#-machine-learning-model)
11. [Blockchain Implementation](#-blockchain-implementation)
12. [Security Features](#-security-features)
13. [API Endpoints](#-api-endpoints)
14. [Services](#-services)
15. [Database Schema](#-database-schema)
16. [Testing](#-testing)
17. [Troubleshooting](#-troubleshooting)
18. [Future Enhancements](#-future-enhancements)
19. [Contributing](#-contributing)
20. [License](#-license)

---

## 🎯 Overview

**HealthFraudMLChain** is an enterprise-grade web application designed to combat healthcare insurance fraud through the integration of **Machine Learning** and **Blockchain** technologies. The system provides:

- **Real-time fraud detection** using trained ML models
- **Immutable audit trails** via blockchain technology
- **Role-based access control** for patients, doctors, and administrators
- **Automated claim processing** with intelligent routing
- **Comprehensive notification system** for all stakeholders

### Problem Statement
Healthcare insurance fraud costs the industry billions annually. Traditional rule-based systems fail to detect sophisticated fraud patterns. Manual claim verification is slow, error-prone, and expensive.

### Our Solution
HealthFraudMLChain combines:
- **AI-powered fraud detection** (Random Forest with TF-IDF)
- **Blockchain-based immutability** for audit compliance
- **Smart contract-like rules** for automated decision making
- **Insider threat detection** to monitor suspicious admin behavior

---

## ✨ Features

### Core Features

| Feature | Description |
|---------|-------------|
| 🔍 **Fraud Detection** | ML-powered fraud probability scoring (0-100%) |
| ⛓️ **Blockchain Ledger** | Immutable record of all approved claims |
| 👥 **Multi-Role System** | Patient, Doctor, Admin with role-specific access |
| 🔔 **Notifications** | Real-time alerts for claim status updates |
| 📊 **Dashboard Analytics** | Visual statistics and claim monitoring |
| 📁 **Document Upload** | Support for PNG, JPG, PDF, DOCX attachments |

### Advanced Features

| Feature | Description |
|---------|-------------|
| 🤖 **Auto-Decision Engine** | Automatic approve/reject for clear-cut cases |
| 🔐 **Digital Signatures** | ECDSA-based non-repudiation for approvals |
| 🔒 **ECIES Encryption** | Role-based encrypted blockchain data |
| 🕵️ **Collusion Detection** | Doctor-hospital fraud pattern detection |
| 📝 **XAI Explanations** | Explainable AI for fraud predictions |
| 🚨 **Insider Threat Monitor** | Admin behavior anomaly detection |
| 📧 **Email Alerts** | Critical notifications via email |
| ⏰ **Audit Trail** | Complete action history with timestamps |

---

## 🏗 System Architecture

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
└───────────────────────────────┬─────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│   SERVICES    │      │  ML ENGINE    │      │  BLOCKCHAIN   │
│               │      │               │      │               │
│ • Notification│      │ • RandomForest│      │ • SHA-256     │
│ • Audit Trail │      │ • TF-IDF      │      │ • MongoDB     │
│ • Collusion   │      │ • Fraud Score │      │ • Immutable   │
│ • XAI         │      │ • Binary/     │      │ • Role-based  │
│ • Encryption  │      │   Multi-class │      │   Access      │
│ • Risk Monitor│      │               │      │               │
└───────┬───────┘      └───────┬───────┘      └───────┬───────┘
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   MongoDB Atlas     │
                    │                     │
                    │ Collections:        │
                    │ • users             │
                    │ • claims            │
                    │ • blockchain_blocks │
                    │ • notifications     │
                    │ • audit_logs        │
                    └─────────────────────┘
```

### Claim Processing Flow

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           CLAIM LIFECYCLE                                     │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────┐    ┌────────────┐    ┌────────────┐    ┌──────────────────┐   │
│  │ Patient │───▶│ Submit     │───▶│ ML Model   │───▶│ Fraud Risk       │   │
│  │         │    │ Claim      │    │ Prediction │    │ Decision Engine  │   │
│  └─────────┘    └────────────┘    └────────────┘    └────────┬─────────┘   │
│                                                               │              │
│                      ┌────────────────────────────────────────┘              │
│                      │                                                       │
│         ┌────────────┼────────────┬────────────────────┐                    │
│         │            │            │                    │                    │
│         ▼            ▼            ▼                    ▼                    │
│  ┌────────────┐ ┌─────────┐ ┌─────────────┐   ┌─────────────┐              │
│  │AUTO-APPROVE│ │ MANUAL  │ │ AUTO-REJECT │   │    XAI      │              │
│  │  (<30%)    │ │ REVIEW  │ │   (>80%)    │   │ Explanation │              │
│  └──────┬─────┘ │(30-80%) │ └──────┬──────┘   └─────────────┘              │
│         │       └────┬────┘        │                                        │
│         │            │             │                                        │
│         │            ▼             │                                        │
│         │   ┌────────────────┐     │                                        │
│         │   │Doctor Approval │     │                                        │
│         │   │  (Assigned)    │     │                                        │
│         │   └───────┬────────┘     │                                        │
│         │           │              │                                        │
│         │           ▼              │                                        │
│         │   ┌────────────────┐     │                                        │
│         │   │Admin Approval  │     │                                        │
│         │   │ (Final)        │     │                                        │
│         │   └───────┬────────┘     │                                        │
│         │           │              │                                        │
│         ▼           ▼              ▼                                        │
│  ┌──────────────────────────────────────────┐                              │
│  │            BLOCKCHAIN LEDGER             │                              │
│  │  • Digital Signatures (Non-repudiation)  │                              │
│  │  • Encrypted Sensitive Data (ECIES)      │                              │
│  │  • Immutable Audit Trail                 │                              │
│  └──────────────────────────────────────────┘                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠 Technology Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.10+ | Core language |
| Flask | 3.0.2 | Web framework |
| PyMongo | 4.6.1 | MongoDB driver |
| Werkzeug | 3.0.1 | Password hashing, security |

### Machine Learning
| Technology | Version | Purpose |
|------------|---------|---------|
| scikit-learn | 1.4.0 | Random Forest classifier |
| pandas | 2.2.1 | Data processing |
| numpy | 1.26.4 | Numerical operations |
| TF-IDF | - | Text feature extraction |

### Blockchain & Security
| Technology | Version | Purpose |
|------------|---------|---------|
| eciespy | 0.4.1 | Elliptic Curve encryption |
| pycryptodome | 3.20.0 | Cryptographic functions |
| SHA-256 | - | Block hashing |
| ECDSA | - | Digital signatures |

### Database
| Technology | Purpose |
|------------|---------|
| MongoDB Atlas | Cloud-hosted NoSQL database |
| Collections | users, claims, blockchain_blocks, notifications |

### Frontend
| Technology | Purpose |
|------------|---------|
| Jinja2 | Template engine |
| Bootstrap | UI framework |
| HTML5/CSS3 | Markup and styling |
| JavaScript | Client-side interactivity |

---

## 📁 Project Structure

```
HealthFraudMLChain/
├── main.py                      # 🎯 Main Flask application (1500+ lines)
├── blockchain.py                # ⛓️ Blockchain implementation
├── ecies_crypto.py              # 🔐 ECIES encryption utilities
├── encryption_utils.py          # 🔒 Additional encryption helpers
├── utils_helpers.py             # 🛠️ Utility functions (v1)
├── utils_helpers_v2.py          # 🛠️ Utility functions (v2 - current)
├── config.py                    # ⚙️ Configuration settings
├── train_model.py               # 🤖 ML model training (v1)
├── train_model_v2.py            # 🤖 ML model training (v2 - binary)
│
├── services/                    # 📦 Service Layer
│   ├── notification_service.py         # 🔔 Notification management
│   ├── role_based_notification_manager.py  # 👥 Role-aware notifications
│   ├── rules_engine.py                 # 📜 Smart contract rules
│   ├── signature_service.py            # ✍️ Digital signature service
│   ├── claim_encryption_service.py     # 🔐 Claim encryption
│   ├── blockchain_service.py           # ⛓️ Blockchain operations
│   ├── collusion_detection_service.py  # 🕵️ Fraud collusion detection
│   ├── xai_explanation_service.py      # 📊 Explainable AI
│   ├── audit_trail_service.py          # 📝 Audit logging
│   ├── fraud_risk_decision_engine.py   # 🤖 Auto-decision engine
│   ├── email_alert_service.py          # 📧 Email notifications
│   └── admin_risk_monitor_service.py   # 🚨 Insider threat detection
│
├── routes/                      # 🛣️ Route Blueprints
│   ├── admin_routes.py          # Admin-specific routes
│   ├── auth_routes.py           # Authentication routes
│   └── claim_routes.py          # Claim management routes
│
├── models/                      # 📦 Data Models
│   └── user_model.py            # User model definition
│
├── templates/                   # 🎨 HTML Templates
│   ├── login.html               # Login page
│   ├── signup.html              # Registration page
│   ├── dashboard_patient.html   # Patient dashboard
│   ├── dashboard_admin.html     # Admin dashboard
│   ├── doctor_dashboard.html    # Doctor dashboard
│   ├── claim_form.html          # Claim submission form
│   ├── claim_view.html          # Claim details view
│   ├── my_claims.html           # Patient's claims list
│   ├── blockchain_view.html     # Blockchain explorer
│   ├── notifications.html       # Notification list
│   ├── add_doctor.html          # Admin: Add doctor
│   └── ...                      # Other templates
│
├── static/                      # 📁 Static Files
│   └── uploads/                 # Uploaded documents
│
├── tests/                       # 🧪 Test Files
│   └── ...                      # Unit and integration tests
│
├── artifacts/                   # 📦 ML Artifacts
├── blockchain/                  # ⛓️ Blockchain data files
├── data/                        # 📊 Data files
├── Dataset/                     # 📊 Training datasets
│
├── fraud_model.pkl              # 🤖 Trained ML model
├── fraud_model_v2.pkl           # 🤖 V2 binary model
├── label_encoders.pkl           # 🏷️ Label encoders
├── insurance.csv                # 📊 Training dataset
│
├── .env                         # 🔑 Environment variables
├── .ecies_private_key           # 🔐 ECIES private key
├── .ecies_public_key            # 🔐 ECIES public key
├── secret.key                   # 🔑 Secret key
├── aes_key.bin                  # 🔐 AES encryption key
│
├── requirements_txt       # 📦 Python dependencies
├── start.bat                    # 🚀 Windows startup script
└── README.md                    # 📖 This file
```

---

## 🚀 Installation

### Prerequisites

- **Python 3.10+** installed
- **MongoDB Atlas** account (or local MongoDB)
- **Git** for cloning repository
- **pip** package manager

### Step-by-Step Installation

#### 1. Clone the Repository

```powershell
git clone https://github.com/Saee2803/HealthFraudMLChain.git
cd HealthFraudMLChain/HealthFraudMLChain
```

#### 2. Create Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate virtual environment (Windows CMD)
.\venv\Scripts\activate.bat

# Activate virtual environment (Linux/Mac)
source venv/bin/activate
```

#### 3. Install Dependencies

```powershell
pip install -r requirements_.txt
```

#### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=healthfraudmlchain

# Flask Configuration
FLASK_APP=main.py
FLASK_ENV=development
SECRET_KEY=your-super-secret-key-here

# Email Configuration (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Security Keys
ECIES_PRIVATE_KEY_PATH=.ecies_private_key
ECIES_PUBLIC_KEY_PATH=.ecies_public_key
```

#### 5. Train the ML Model (Optional)

```powershell
# If you need to retrain the model
python train_model_v2.py
```

#### 6. Run the Application

```powershell
# Method 1: Using Flask CLI
$env:FLASK_APP = "main.py"
$env:FLASK_ENV = "development"
flask run

# Method 2: Direct Python
python main.py

# Method 3: Using start.bat (Windows)
.\start.bat
```

#### 7. Access the Application

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## ⚙️ Configuration

### MongoDB Configuration

Update the MongoDB connection string in `main.py`:

```python
client = MongoClient("your-mongodb-connection-string")
db = client["healthfraudmlchain"]
```

### ML Model Configuration

The fraud detection thresholds can be configured in `fraud_risk_decision_engine.py`:

```python
# Auto-approve threshold (fraud probability < 30%)
AUTO_APPROVE_THRESHOLD = 0.30

# Auto-reject threshold (fraud probability > 80%)
AUTO_REJECT_THRESHOLD = 0.80

# Claims between 30-80% go to manual review
```

### File Upload Configuration

```python
UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf", "docx"}
MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20 MB
```

---

## 📖 Usage Guide

### For Patients

1. **Sign Up**: Create a patient account
2. **Login**: Access your dashboard
3. **Submit Claim**: Fill out the claim form with:
   - Patient information (name, age, gender)
   - Medical details (diagnosis, hospital, doctor)
   - Financial details (claim amount)
   - Supporting documents
4. **Track Claims**: View status updates in "My Claims"
5. **Notifications**: Receive real-time updates on claim progress

### For Doctors

1. **Login**: Use credentials created by admin
2. **View Pending Claims**: See claims assigned to you
3. **Review Claims**: Examine claim details and documents
4. **Approve/Reject**: Make decision with remarks
5. **View History**: See verified claims history

### For Admins

1. **Login**: Access admin dashboard
2. **Manage Claims**: View all claims with filters
3. **Final Approval**: Approve doctor-verified claims
4. **Add Doctors**: Create new doctor accounts
5. **View Blockchain**: Inspect the immutable ledger
6. **Monitor Alerts**: Review high-risk notifications

---

## 👥 User Roles

### Patient Role
| Permission | Description |
|------------|-------------|
| Submit Claims | Create new insurance claims |
| View Own Claims | See personal claim history |
| Upload Documents | Attach supporting files |
| Receive Notifications | Get status updates |

### Doctor Role
| Permission | Description |
|------------|-------------|
| View Assigned Claims | See claims assigned by patients |
| Approve/Reject Claims | First-level verification |
| Add Remarks | Provide medical opinions |
| View Blockchain | Limited blockchain access |

### Admin Role
| Permission | Description |
|------------|-------------|
| View All Claims | Full claim visibility |
| Final Approval | Ultimate decision authority |
| Add Doctors | Create doctor accounts |
| View Full Blockchain | Complete ledger access |
| Verify Integrity | Run blockchain validation |
| Monitor Fraud Alerts | High-risk claim notifications |

---

## 🤖 Machine Learning Model

### Model Architecture

**Version 2.0 (Current)**: Binary Classification with TF-IDF

```python
# Model: Random Forest Classifier
RandomForestClassifier(
    n_estimators=300,        # Number of trees
    class_weight="balanced", # Handle class imbalance
    max_depth=15,            # Prevent overfitting
    min_samples_split=5      # Minimum samples to split
)
```

### Features Engineering

| Feature Category | Features |
|------------------|----------|
| **Basic** | Age, Amount Billed, Stay Duration |
| **Amount Indicators** | high_amount_flag, very_high_amount_flag, extreme_amount_flag, low_amount_flag |
| **Stay Indicators** | zero_stay_flag, short_stay_flag, long_stay_flag, very_long_stay_flag |
| **Age Risk** | child_flag, elderly_flag, high_risk_age_flag |
| **Anomaly Detection** | gender_diagnosis_mismatch, age_diagnosis_anomaly |
| **Computed** | amount_per_day, risk_score |
| **Text Features** | TF-IDF on diagnosis descriptions |

### Fraud Detection Logic

```python
# Gender-Diagnosis Mismatch (Critical Fraud Indicator)
if gender == "Male" and diagnosis in ["Pregnancy", "Cesarean Section"]:
    flag = 1  # High fraud probability

# Age-Diagnosis Anomaly
if age < 15 and diagnosis == "Cataract Surgery":
    anomaly = 1
if age > 55 and diagnosis == "Pregnancy":
    anomaly = 1
```

### Training Data

- **Dataset**: `insurance.csv`
- **Features**: Patient demographics, diagnosis, billing info
- **Target**: Binary (Fraud / No Fraud)
- **Split**: 80% training, 20% testing

---

## ⛓️ Blockchain Implementation

### Block Structure

```python
class Block:
    index: int              # Block position
    timestamp: str          # ISO format UTC
    data: dict              # Claim data (encrypted)
    previous_hash: str      # Link to previous block
    hash: str               # SHA-256 hash of block
```

### Hash Calculation

```python
def calculate_hash(self) -> str:
    block_string = json.dumps({
        "index": self.index,
        "timestamp": self.timestamp,
        "data": self.data,
        "previous_hash": self.previous_hash
    }, sort_keys=True)
    return hashlib.sha256(block_string.encode()).hexdigest()
```

### Chain Validation

```python
def is_chain_valid(self) -> bool:
    for i in range(1, len(self.chain)):
        current = self.chain[i]
        previous = self.chain[i-1]
        
        # Verify hash integrity
        if current.hash != current.calculate_hash():
            return False
        
        # Verify chain linkage
        if current.previous_hash != previous.hash:
            return False
    
    return True
```

### Blockchain Features

| Feature | Description |
|---------|-------------|
| **Immutability** | Once written, blocks cannot be modified |
| **Tamper Detection** | Any modification breaks hash chain |
| **MongoDB Persistence** | Chain stored in database |
| **Role-Based Access** | Different data visibility per role |
| **ECIES Encryption** | Sensitive data encrypted |

---

## 🔐 Security Features

### 1. Authentication & Authorization

- **Password Hashing**: Werkzeug PBKDF2-SHA256
- **Session Management**: Flask secure sessions
- **Role-Based Access Control**: Patient, Doctor, Admin

### 2. Data Encryption

- **ECIES**: Elliptic Curve Integrated Encryption
- **AES-256**: Symmetric encryption for data at rest
- **Role-Based Decryption**: Only authorized roles can decrypt

### 3. Digital Signatures

```python
# ECDSA signature for non-repudiation
signature = create_approval_signature(
    claim_id=claim_id,
    approver_id=user_id,
    approver_role=role,
    approval_action='approved'
)
```

### 4. Audit Trail

- Every action is logged with timestamp
- Digital signatures on approvals
- Immutable blockchain record

### 5. Insider Threat Detection

- Monitors admin approval patterns
- Alerts on suspicious behavior:
  - Approving many high-risk claims
  - Overriding AI decisions frequently
  - Rubber-stamping (too-fast approvals)

---

## 🔌 API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/login` | User login |
| GET/POST | `/signup` | User registration |
| GET | `/logout` | User logout |

### Dashboards

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard_patient` | Patient dashboard |
| GET | `/dashboard_doctor` | Doctor dashboard |
| GET | `/admin/dashboard` | Admin dashboard |

### Claims

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/claim_form` | Submit new claim |
| GET | `/my_claims` | Patient's claims |
| GET | `/claim_view/<id>` | View claim details |
| POST | `/update_claim_status/<id>` | Approve/reject claim |

### Blockchain

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin/blockchain` | View blockchain |
| GET | `/doctor/blockchain` | Doctor blockchain view |
| GET | `/admin/validate_blockchain` | Validate chain |
| GET | `/api/blockchain/integrity` | API integrity check |

### Notifications

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notifications` | Get notifications |
| GET | `/api/notifications/unread-count` | Unread count |
| POST | `/api/notifications/mark-read/<id>` | Mark as read |
| POST | `/api/notifications/mark-all-read` | Mark all read |
| DELETE | `/api/notifications/delete/<id>` | Delete notification |

### API Response Example

```json
// GET /api/blockchain/integrity
{
    "status": "VALID",
    "total_blocks_checked": 15,
    "total_blocks_in_chain": 15,
    "tamper_proof": true,
    "errors": [],
    "timestamp": "2026-01-27T10:30:00Z"
}
```

---

## 📦 Services

### Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     SERVICE LAYER                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐          │
│  │ Notification Service│  │ Audit Trail Service │          │
│  │ • Create alerts     │  │ • Record actions    │          │
│  │ • Send by role      │  │ • Digital signatures│          │
│  │ • Mark read/unread  │  │ • Commit to chain   │          │
│  └─────────────────────┘  └─────────────────────┘          │
│                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐          │
│  │ Collusion Detection │  │  XAI Explanation    │          │
│  │ • Track patterns    │  │ • Generate reasons  │          │
│  │ • Flag suspicious   │  │ • Store explanations│          │
│  │ • Doctor-hospital   │  │ • Regulatory comply │          │
│  └─────────────────────┘  └─────────────────────┘          │
│                                                             │
│  ┌─────────────────────┐  ┌─────────────────────┐          │
│  │ Decision Engine     │  │ Risk Monitor        │          │
│  │ • Auto-approve      │  │ • Admin behavior    │          │
│  │ • Auto-reject       │  │ • Insider threats   │          │
│  │ • Manual routing    │  │ • Email alerts      │          │
│  └─────────────────────┘  └─────────────────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Service Descriptions

| Service | Purpose |
|---------|---------|
| `notification_service.py` | Creates and manages user notifications |
| `role_based_notification_manager.py` | Ensures role-appropriate notifications |
| `rules_engine.py` | Smart contract-like validation rules |
| `signature_service.py` | Digital signature creation/verification |
| `claim_encryption_service.py` | Encrypts claims for blockchain |
| `blockchain_service.py` | Blockchain integrity verification |
| `collusion_detection_service.py` | Detects doctor-hospital fraud patterns |
| `xai_explanation_service.py` | Generates explainable AI outputs |
| `audit_trail_service.py` | Records immutable audit logs |
| `fraud_risk_decision_engine.py` | Automated claim routing |
| `email_alert_service.py` | Sends email notifications |
| `admin_risk_monitor_service.py` | Monitors admin behavior |

---

## 🗄️ Database Schema

### Users Collection

```javascript
{
    "_id": ObjectId,
    "name": "John Doe",
    "email": "john@example.com",
    "password": "hashed_password",
    "role": "patient" | "doctor" | "admin",
    "created_at": ISODate
}
```

### Claims Collection

```javascript
{
    "_id": ObjectId,
    "patient_name": "Jane Doe",
    "age": 35,
    "gender": "Female",
    "treatment_type": "Surgery",
    "hospital_name": "City Hospital",
    "doctor_name": "Dr. Smith",
    "claim_amount": 50000,
    "admission_date": "2026-01-20",
    "discharge_date": "2026-01-25",
    "claim_description": "Appendix surgery",
    "documents": ["doc1.pdf", "doc2.jpg"],
    "username": "janedoe",
    "user_id": "user_object_id",
    "prediction": "No Fraud",
    "fraud_probability": 0.15,
    "fraud_reasons": [],
    "status": "Pending" | "Approved" | "Rejected",
    "submitted_on": ISODate,
    "assigned_doctor_id": "doctor_object_id",
    "doctor_approved": null | true | false,
    "admin_approved": null | true | false,
    "decision_type": "AUTO_APPROVE" | "MANUAL_REVIEW" | "AUTO_REJECT",
    "digital_signature": "signature_hash",
    "audit_log": [
        {
            "action": "Claim Submitted",
            "by_name": "Jane Doe",
            "by_role": "patient",
            "timestamp": ISODate,
            "remarks": "AI Fraud Score: 15%"
        }
    ]
}
```

### Blockchain Blocks Collection

```javascript
{
    "_id": ObjectId,
    "index": 1,
    "timestamp": "2026-01-27T10:00:00Z",
    "data": {
        "claim_id": "claim_object_id",
        "patient_name": "Jane Doe",
        "amount": 50000,
        "doctor_approved": true,
        "admin_approved": true,
        "status": "Approved",
        "digital_signature": "ecdsa_signature",
        "encrypted_sensitive_data": "ecies_encrypted_blob"
    },
    "previous_hash": "abc123...",
    "hash": "def456..."
}
```

### Notifications Collection

```javascript
{
    "_id": ObjectId,
    "to_role": "patient",
    "to_user_id": "user_object_id",
    "message": "Your claim has been approved",
    "notification_type": "claim_approved",
    "related_claim_id": "claim_object_id",
    "priority": "normal" | "high",
    "created_at": ISODate,
    "read": false
}
```

---

## 🧪 Testing

### Run Tests

```powershell
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_blockchain.py -v
```

### Test Categories

| Test Type | Description |
|-----------|-------------|
| Unit Tests | Individual function testing |
| Integration Tests | Service interaction testing |
| API Tests | Endpoint response testing |
| Security Tests | Authentication/authorization |

---

## 🔧 Troubleshooting

### Common Issues

#### 1. MongoDB Connection Error

```
Error: pymongo.errors.ServerSelectionTimeoutError
```

**Solution**: Verify MongoDB URI and network connectivity

```python
# Check connection
from pymongo import MongoClient
client = MongoClient("your-uri", serverSelectionTimeoutMS=5000)
client.admin.command('ping')
```

#### 2. ML Model Not Found

```
Error: fraud_model.pkl not found
```

**Solution**: Train the model first

```powershell
python train_model_v2.py
```

#### 3. Import Errors

```
Error: ModuleNotFoundError: No module named 'xxx'
```

**Solution**: Install missing dependencies

```powershell
pip install -r requirements_.txt
```

#### 4. Session Issues

**Solution**: Clear browser cookies or restart Flask

#### 5. File Upload Errors

**Solution**: Ensure `static/uploads/` directory exists and has write permissions

---

## 🚀 Future Enhancements

- [ ] **REST API**: Full RESTful API with JWT authentication
- [ ] **Mobile App**: React Native or Flutter mobile application
- [ ] **Advanced ML**: Deep learning models (LSTM, Transformer)
- [ ] **Real Blockchain**: Integration with Ethereum/Hyperledger
- [ ] **OAuth 2.0**: Social login integration
- [ ] **Two-Factor Auth**: Enhanced security with 2FA
- [ ] **Analytics Dashboard**: Advanced visualizations with D3.js
- [ ] **Multi-language**: Internationalization support
- [ ] **PDF Reports**: Automated claim reports generation
- [ ] **Real-time Chat**: WebSocket-based communication

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

### Code Style

- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings to functions
- Write unit tests for new features

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

---

## 🙏 Acknowledgments

- **scikit-learn** for ML implementation
- **Flask** for web framework
- **MongoDB** for database
- **Bootstrap** for UI components
- All contributors and testers

---

## 📞 Contact

For questions or support:

- **GitHub Issues**: [Create an issue](https://github.com/your-username/HealthFraudMLChain/issues)
- **Email**: your-email@example.com

---

<div align="center">

**Built with ❤️ for Healthcare Fraud Prevention**

⭐ Star this repository if you find it helpful!

</div>

