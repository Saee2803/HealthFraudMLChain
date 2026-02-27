# Minimal service implementations

def validate_blockchain_rules(claim):
    """Validate blockchain rules"""
    return {"allowed": True, "reason": "All rules passed"}

def init_collusion_detection_service(db):
    """Initialize collusion detection service"""
    class CollusionService:
        def update_collusion_risk_database(self, doctor_id, doctor_name, hospital_name):
            pass
    return CollusionService()

def init_xai_explanation_service(db):
    """Initialize XAI explanation service"""
    class XAIService:
        def generate_comprehensive_explanation(self, claim_data, fraud_probability, fraud_reasons):
            return {"generated_at": "dummy", "explanation": "AI explanation"}
        def store_explanation(self, explanation):
            pass
    return XAIService()

def init_audit_trail_service(db, blockchain):
    """Initialize audit trail service"""
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

def init_fraud_risk_decision_engine(db):
    """Initialize fraud risk decision engine"""
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

def init_email_alert_service(db):
    """Initialize email alert service"""
    class EmailService:
        def send_alert(self, **kwargs):
            pass
    return EmailService()

def init_admin_risk_monitor_service(db, email_service):
    """Initialize admin risk monitor service"""
    class RiskMonitor:
        def evaluate_and_alert_if_needed(self, admin_id, admin_name):
            return {"risk_level": "LOW"}
    return RiskMonitor()