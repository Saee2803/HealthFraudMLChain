# Signature service
def create_approval_signature(**kwargs):
    return {"signature": "dummy_signature"}

def store_approval_signature(**kwargs):
    pass

def validate_blockchain_signatures(claim):
    return {"valid": True}

# Claim encryption service  
def prepare_claim_for_blockchain(claim):
    return {"encrypted": "dummy_data"}

# Blockchain service
def verify_blockchain_integrity():
    return {"status": "VALID", "errors": []}

# Collusion detection service
def init_collusion_detection_service(db):
    class CollusionService:
        def update_collusion_risk_database(self, doctor_id, doctor_name, hospital_name):
            pass
    return CollusionService()

# XAI explanation service
def init_xai_explanation_service(db):
    class XAIService:
        def generate_comprehensive_explanation(self, claim_data, fraud_probability, fraud_reasons):
            return {"generated_at": "dummy", "explanation": "AI explanation"}
        def store_explanation(self, explanation):
            pass
    return XAIService()

# Audit trail service
def init_audit_trail_service(db, blockchain):
    class AuditService:
        def record_approval_action(self, **kwargs):
            return {"id": "dummy"}
        def get_doctor_approval_record(self, claim_id):
            return {"record": "dummy"}
        def get_admin_approval_record(self, claim_id):
            return {"record": "dummy"}
        def commit_approval_to_blockchain(self, **kwargs):
            return True
    return AuditService()

# Fraud risk decision engine
def init_fraud_risk_decision_engine(db):
    class DecisionEngine:
        def evaluate_claim_decision(self, fraud_prob):
            if fraud_prob < 0.3:
                return {
                    "final_status": "Approved",
                    "decision_type": "AUTO_APPROVE", 
                    "is_automated": True,
                    "reason": "Low fraud risk"
                }
            elif fraud_prob > 0.8:
                return {
                    "final_status": "Rejected",
                    "decision_type": "AUTO_REJECT",
                    "is_automated": True, 
                    "reason": "High fraud risk"
                }
            else:
                return {
                    "final_status": "Pending",
                    "decision_type": "MANUAL_REVIEW",
                    "is_automated": False,
                    "reason": "Requires manual review"
                }
        def log_decision(self, claim_id, decision_result):
            pass
    return DecisionEngine()

# Email alert service
def init_email_alert_service(db):
    class EmailService:
        def send_alert(self, **kwargs):
            pass
    return EmailService()

# Admin risk monitor service
def init_admin_risk_monitor_service(db, email_service):
    class RiskMonitor:
        def evaluate_and_alert_if_needed(self, admin_id, admin_name):
            return {"risk_level": "LOW"}
    return RiskMonitor()