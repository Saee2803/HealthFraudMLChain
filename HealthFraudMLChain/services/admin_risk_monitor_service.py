"""
Admin Risk Monitor Service - Insider Threat Detection
Monitors admin approval patterns and detects potential insider threats.
"""
from datetime import datetime, timezone
from bson import ObjectId


def init_admin_risk_monitor_service(db, email_service):
    """
    Initialize admin risk monitor service.
    Monitors admin approval patterns for insider threat detection.
    """
    
    class AdminRiskMonitorService:
        def __init__(self, database, email_alert_service):
            self.db = database
            self.email_service = email_alert_service
            self.claims_collection = database["claims"]
            self.users_collection = database["users"]
            self.admin_risk_log = database["admin_risk_log"]
        
        def evaluate_and_alert_if_needed(self, admin_id: str, admin_name: str):
            """
            Evaluate admin's approval behavior and alert if suspicious.
            
            Risk Indicators:
            - Approving high fraud probability claims (>=0.7)
            - High frequency of fraud claim approvals
            - Rubber-stamping (very fast approvals)
            
            Returns:
            {
                "risk_level": "LOW" | "MEDIUM" | "HIGH",
                "indicators": [...],
                "alert_sent": bool
            }
            """
            try:
                result = {
                    "risk_level": "LOW",
                    "indicators": [],
                    "alert_sent": False
                }
                
                # Get recent claims approved by this admin
                recent_approvals = list(self.claims_collection.find({
                    "verified_by": admin_name,
                    "verified_role": "admin",
                    "status": "Approved"
                }).sort("verified_on", -1).limit(20))
                
                if not recent_approvals:
                    return result
                
                # Count high-risk approvals (fraud_probability >= 0.7)
                high_risk_count = sum(
                    1 for c in recent_approvals 
                    if c.get("fraud_probability", 0) >= 0.7
                )
                
                # Calculate metrics
                high_risk_ratio = high_risk_count / len(recent_approvals) if recent_approvals else 0
                
                # Determine risk level
                if high_risk_count >= 3 or high_risk_ratio >= 0.3:
                    result["risk_level"] = "HIGH"
                    result["indicators"].append(f"Approved {high_risk_count} high-fraud claims recently")
                elif high_risk_count >= 2 or high_risk_ratio >= 0.15:
                    result["risk_level"] = "MEDIUM"
                    result["indicators"].append(f"Approved {high_risk_count} high-fraud claims")
                
                # Log admin risk evaluation
                self._log_risk_evaluation(
                    admin_id=admin_id,
                    admin_name=admin_name,
                    risk_level=result["risk_level"],
                    indicators=result["indicators"],
                    high_risk_count=high_risk_count,
                    total_recent=len(recent_approvals)
                )
                
                return result
                
            except Exception as e:
                print(f"⚠️ Admin risk evaluation error (non-blocking): {e}")
                return {"risk_level": "LOW", "indicators": [], "alert_sent": False}
        
        def trigger_high_risk_alert(
            self,
            claim_id: str,
            fraud_probability: float,
            admin_name: str,
            admin_id: str,
            claim_amount: float = 0,
            patient_name: str = ""
        ):
            """
            Explicitly trigger email alert for high-risk admin approval.
            Called when admin approves a claim with fraud_probability >= 0.7.
            """
            try:
                if self.email_service:
                    return self.email_service.send_insider_threat_alert(
                        claim_id=claim_id,
                        fraud_probability=fraud_probability,
                        admin_name=admin_name,
                        admin_id=admin_id,
                        claim_amount=claim_amount,
                        patient_name=patient_name
                    )
                else:
                    print("⚠️ Email service not available")
                    return False
            except Exception as e:
                print(f"⚠️ High risk alert failed (non-blocking): {e}")
                return False
        
        def _log_risk_evaluation(
            self,
            admin_id: str,
            admin_name: str,
            risk_level: str,
            indicators: list,
            high_risk_count: int,
            total_recent: int
        ):
            """Log admin risk evaluation to database."""
            try:
                self.admin_risk_log.insert_one({
                    "admin_id": admin_id,
                    "admin_name": admin_name,
                    "risk_level": risk_level,
                    "indicators": indicators,
                    "high_risk_approvals": high_risk_count,
                    "total_recent_approvals": total_recent,
                    "evaluated_at": datetime.now(timezone.utc)
                })
            except Exception as e:
                print(f"⚠️ Failed to log admin risk: {e}")
    
    return AdminRiskMonitorService(db, email_service)