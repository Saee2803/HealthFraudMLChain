"""
Email Alert Service - Production Implementation
Sends email alerts for insider threat detection (admin misuse)
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required if env vars are set externally


def init_email_alert_service(db):
    """
    Initialize email alert service with MongoDB connection.
    Returns EmailAlertService instance.
    """
    
    class EmailAlertService:
        def __init__(self, database):
            self.db = database
            self.users_collection = database["users"]
            self.email_alert_log = database["email_alert_log"]
            
            # SMTP Configuration from environment
            self.smtp_host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
            self.smtp_port = int(os.getenv("EMAIL_PORT", "587"))
            self.smtp_user = os.getenv("EMAIL_USER", "")
            self.smtp_password = os.getenv("EMAIL_PASSWORD", "")
            self.email_from = os.getenv("EMAIL_FROM", self.smtp_user)
            
            # Log initialization status
            if self.smtp_user and self.smtp_password:
                print(f"✅ Email Alert Service initialized (SMTP: {self.smtp_host}:{self.smtp_port})")
            else:
                print("⚠️ Email Alert Service: SMTP credentials not configured")
            
        def get_super_admin_emails(self):
            """
            Fetch all super admin emails dynamically from users collection.
            Returns list of email addresses.
            """
            try:
                super_admins = list(self.users_collection.find({
                    "is_super_admin": True
                }))
                emails = [admin.get("email") for admin in super_admins if admin.get("email")]
                
                # Fallback: If no super_admin found, try regular admins
                if not emails:
                    admins = list(self.users_collection.find({"role": "admin"}))
                    emails = [admin.get("email") for admin in admins if admin.get("email")]
                
                return emails
            except Exception as e:
                print(f"⚠️ Error fetching super admin emails: {e}")
                return []
        
        def send_insider_threat_alert(
            self,
            claim_id: str,
            fraud_probability: float,
            admin_name: str,
            admin_id: str,
            claim_amount: float = 0,
            patient_name: str = "",
            additional_context: dict = None
        ):
            """
            Send email alert when admin approves high-risk fraud claim.
            
            WHEN:
            - Admin approves a claim with fraud_probability >= 0.7
            
            THEN:
            - Send email to all super admins
            - Log to email_alert_log collection
            - Never crash the claim flow
            """
            try:
                # Get super admin emails
                to_emails = self.get_super_admin_emails()
                
                if not to_emails:
                    print("⚠️ No super admin emails found, skipping email alert")
                    self._log_alert(
                        to_emails=[],
                        claim_id=claim_id,
                        fraud_probability=fraud_probability,
                        status="SKIPPED",
                        error="No super admin emails configured"
                    )
                    return False
                
                if not self.smtp_user or not self.smtp_password:
                    print("⚠️ SMTP credentials not configured, skipping email alert")
                    self._log_alert(
                        to_emails=to_emails,
                        claim_id=claim_id,
                        fraud_probability=fraud_probability,
                        status="SKIPPED",
                        error="SMTP credentials not configured"
                    )
                    return False
                
                # Build email
                timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                
                subject = "🚨 Insider Risk Alert – High Fraud Claim Approved"
                
                body = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 INSIDER THREAT ALERT - URGENT REVIEW REQUIRED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

An admin has approved a claim with HIGH FRAUD PROBABILITY.
This action has been flagged for compliance review.

📋 CLAIM DETAILS
────────────────────────────────────────────────────
• Claim ID:          {claim_id}
• Fraud Probability: {fraud_probability:.1%}
• Patient Name:      {patient_name}
• Claim Amount:      ₹{claim_amount:,.2f}

👤 ADMIN WHO APPROVED
────────────────────────────────────────────────────
• Admin Name:        {admin_name}
• Admin ID:          {admin_id}
• Approval Time:     {timestamp}

⚠️ RECOMMENDED ACTION
────────────────────────────────────────────────────
1. Review the claim in the admin dashboard
2. Verify the admin's recent approval patterns
3. Check for potential collusion indicators
4. Document findings in compliance log

This alert was auto-generated by HealthFraudMLChain
Insider Threat Detection System.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
                
                # Create email message
                msg = MIMEMultipart()
                msg['From'] = self.email_from
                msg['To'] = ", ".join(to_emails)
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'plain'))
                
                # Send email via SMTP
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.email_from, to_emails, msg.as_string())
                
                print(f"📧 Email alert sent to super admin(s): {to_emails}")
                
                # Log success
                self._log_alert(
                    to_emails=to_emails,
                    claim_id=claim_id,
                    fraud_probability=fraud_probability,
                    status="SENT",
                    admin_name=admin_name,
                    admin_id=admin_id
                )
                
                return True
                
            except Exception as e:
                error_msg = str(e)
                print(f"⚠️ Email failed, logged to DB: {error_msg}")
                
                # Log failure
                self._log_alert(
                    to_emails=to_emails if 'to_emails' in dir() else [],
                    claim_id=claim_id,
                    fraud_probability=fraud_probability,
                    status="FAILED",
                    error=error_msg
                )
                
                return False
        
        def _log_alert(
            self,
            to_emails: list,
            claim_id: str,
            fraud_probability: float,
            status: str,
            error: str = None,
            admin_name: str = None,
            admin_id: str = None
        ):
            """
            Insert log entry into email_alert_log collection.
            """
            try:
                log_entry = {
                    "to_emails": to_emails,
                    "claim_id": claim_id,
                    "fraud_probability": fraud_probability,
                    "triggered_by": "admin_approval",
                    "status": status,
                    "created_at": datetime.now(timezone.utc)
                }
                
                if error:
                    log_entry["error"] = error
                if admin_name:
                    log_entry["admin_name"] = admin_name
                if admin_id:
                    log_entry["admin_id"] = admin_id
                    
                self.email_alert_log.insert_one(log_entry)
                print(f"📝 Email alert logged to DB: status={status}")
                
            except Exception as e:
                print(f"⚠️ Failed to log email alert: {e}")
        
        def send_alert(self, **kwargs):
            """
            Backward-compatible method.
            Calls send_insider_threat_alert with provided kwargs.
            """
            return self.send_insider_threat_alert(**kwargs)
    
    return EmailAlertService(db)