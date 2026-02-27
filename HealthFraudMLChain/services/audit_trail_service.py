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