# III. METHODOLOGY

The methodology of HealthFraudMLChain follows a structured 9-step approach from user registration to blockchain-based immutable record creation through AI-driven fraud detection and multi-layer security verification.

## 1. User Registration and Role-Based Access Setup

Users create accounts via secure authentication, providing basic information and selecting their role (Patient, Doctor, or Administrator). The system creates secure profiles in MongoDB database with role-based permissions for personalized access control and activity tracking.

## 2. Claim Submission and Document Upload

Patients submit insurance claims which undergo automated parsing to extract essential details such as patient information, diagnosis codes, treatment descriptions, claim amounts, and supporting documentation. The system validates input data and stores claims securely for structured analysis.

## 3. ML-Based Fraud Detection and Scoring

Submitted claims undergo automated analysis using a comprehensive machine learning pipeline. The system identifies fraud patterns, categorizes risk levels, and maps claim features against historical fraud indicators, generating targeted fraud probability scores.

The fraud detection module applies:
- **Random Forest Classifier:** Ensemble learning with 100+ decision trees for robust classification
- **TF-IDF Feature Extraction:** Text-based analysis of diagnosis descriptions and treatment notes
- **Pattern Recognition:** Historical claim comparison and anomaly detection

Fraud Score = (Claim Amount Risk × 0.30) + (Provider Pattern × 0.25) + (Diagnosis Anomaly × 0.25) + (Historical Behavior × 0.20)

## 4. Doctor Review and Clinical Verification

Based on fraud analysis, claims are routed to assigned doctors for clinical review. Doctors access claim details through role-specific dashboards:

- **Claim Verification:** Review patient information, diagnosis, and treatment details
- **Medical Validation:** Verify clinical appropriateness of claimed procedures
- **Fraud Assessment:** Review AI-generated fraud probability and XAI explanations
- **Approval Decision:** Approve or reject claims with documented reasoning

## 5. Digital Signature Generation (Doctor)

Upon doctor approval, the system generates ECDSA digital signatures for non-repudiation. The signature service creates cryptographic proof of approval:

```
Doctor Signature = ECDSA_Sign(SHA256(claim_data), doctor_private_key)
Timestamp: UTC timestamp of approval action
```

## 6. Admin Review and Final Approval

Approved claims proceed to administrator review for final verification:

- **Compliance Check:** Verify regulatory and policy compliance
- **Fraud Score Validation:** Confirm AI assessment aligns with business rules
- **Doctor Signature Verification:** Validate doctor's digital signature authenticity
- **Final Decision:** Grant final approval or escalate for investigation

## 7. Smart-Contract-Like Rule Validation

Before blockchain commitment, claims undergo automated business rule validation:

```
Rule 1: fraud_probability < 0.5 (AI threshold)
Rule 2: doctor_approved == True (Clinical authorization)
Rule 3: admin_approved == True (Administrative authorization)
Rule 4: doctor_signature_valid == True (Non-repudiation check)
Rule 5: admin_signature_valid == True (Final verification)
```

Only claims passing all five rules proceed to blockchain recording.

## 8. Blockchain Record Creation and Encryption

Approved claims are encrypted and recorded on the immutable blockchain ledger:

- **ECIES Encryption:** Sensitive data (SSN, medical notes, diagnosis) encrypted using Elliptic Curve Integrated Encryption Scheme
- **Role-Based Decryption:** Only authorized doctors and admins can decrypt sensitive fields
- **Hash Chain:** SHA256 hash linking to previous block ensures immutability
- **Digital Signatures:** Both doctor and admin signatures stored permanently

**Figure 1. System Architecture**

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

## 9. Real-time Notification and Alert System

Post-approval processes include comprehensive notification delivery:

- **Patient Notifications:** Claim status updates (submitted, under review, approved, rejected)
- **Doctor Alerts:** New claims assigned, pending reviews, approval confirmations
- **Admin Alerts:** High-risk claims flagged, collusion detection warnings, insider threat alerts
- **Email Integration:** Critical notifications delivered via email for immediate attention

## 10. Collusion Detection and Insider Threat Monitoring

Unique feature enabling administrators to detect fraudulent patterns:

- **Provider Network Analysis:** Identify suspicious relationships between doctors and hospitals
- **Billing Pattern Detection:** Flag unusual claim frequencies and amounts
- **Insider Threat Monitoring:** Track administrative behavior for anomaly detection
- **Audit Trail:** Complete action history with timestamps for regulatory compliance

## 11. Continuous Monitoring and Blockchain Integrity Verification

The system encourages continuous security monitoring through integrity verification APIs, blockchain hash validation, signature authentication, and comprehensive audit logging. This methodology ensures complete fraud detection coverage through ML-based analysis, multi-layer security verification, blockchain immutability, and detailed audit trails for regulatory compliance and financial protection.

---
