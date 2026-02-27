"""
Minimal role-based notification manager for HealthFraudMLChain
"""

class RoleBasedNotificationManager:
    def __init__(self, db, notification_service):
        self.db = db
        self.notification_service = notification_service
    
    def notify_claim_submission(self, claim_id: str, patient_name: str, claim_amount: float, 
                                   assigned_doctor_id: str = None, fraud_prob: float = 0.0):
        """Notify relevant parties of claim submission"""
        if not self.notification_service:
            return
        
        # Notify admins of new claim
        try:
            admins = list(self.db["users"].find({"role": "admin"}))
            for admin in admins:
                self.notification_service.create_notification(
                    to_role="admin",
                    to_user_id=str(admin["_id"]),
                    message=f"New claim submitted by {patient_name} for ₹{claim_amount:,.2f}",
                    notification_type="claim_submitted",
                    related_claim_id=claim_id,
                    priority="normal"
                )
        except Exception as e:
            print(f"Error notifying admins of claim submission: {e}")
        
        # Notify assigned doctor of new claim (CRITICAL FIX)
        if assigned_doctor_id:
            try:
                doc_priority = "high" if fraud_prob >= 0.6 else "normal"
                self.notification_service.create_notification(
                    to_role="doctor",
                    to_user_id=assigned_doctor_id,
                    message=f"📋 New claim assigned: {patient_name} - ₹{claim_amount:,.2f}. "
                            f"AI Fraud Risk: {fraud_prob:.1%}. Please review.",
                    notification_type="claim_assigned",
                    related_claim_id=claim_id,
                    priority=doc_priority
                )
            except Exception as e:
                print(f"Error notifying doctor of claim submission: {e}")
    
    def notify_high_fraud_risk(self, claim_id: str, fraud_score: float):
        """Notify of high fraud risk claims"""
        if not self.notification_service:
            return
        
        try:
            admins = list(self.db["users"].find({"role": "admin"}))
            for admin in admins:
                self.notification_service.create_notification(
                    to_role="admin",
                    to_user_id=str(admin["_id"]),
                    message=f"🚨 HIGH FRAUD RISK: Claim {claim_id} has {fraud_score:.1%} fraud probability",
                    notification_type="high_fraud_alert",
                    related_claim_id=claim_id,
                    priority="high"
                )
        except Exception as e:
            print(f"Error notifying high fraud risk: {e}")
    
    def notify_doctor_decision(self, claim_id: str, doctor_name: str, decision: str):
        """Notify of doctor decision"""
        if not self.notification_service:
            return
        
        try:
            # Notify admins
            admins = list(self.db["users"].find({"role": "admin"}))
            for admin in admins:
                self.notification_service.create_notification(
                    to_role="admin",
                    to_user_id=str(admin["_id"]),
                    message=f"Dr. {doctor_name} has {decision} claim {claim_id}",
                    notification_type="doctor_decision",
                    related_claim_id=claim_id,
                    priority="normal"
                )
        except Exception as e:
            print(f"Error notifying doctor decision: {e}")
    
    def notify_admin_decision(self, claim_id: str, admin_name: str, decision: str):
        """Notify of admin decision"""
        if not self.notification_service:
            return
        
        try:
            # Find the patient for this claim
            claim = self.db["claims"].find_one({"_id": claim_id})
            if claim and claim.get("user_id"):
                self.notification_service.create_notification(
                    to_role="patient",
                    to_user_id=claim["user_id"],
                    message=f"Your claim has been {decision.lower()} by admin {admin_name}",
                    notification_type="admin_decision",
                    related_claim_id=claim_id,
                    priority="high"
                )
        except Exception as e:
            print(f"Error notifying admin decision: {e}")

def init_role_based_notification_manager(db, notification_service):
    """Initialize role-based notification manager"""
    return RoleBasedNotificationManager(db, notification_service)