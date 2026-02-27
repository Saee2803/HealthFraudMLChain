def init_xai_explanation_service(db):
    class XAIService:
        def generate_comprehensive_explanation(self, claim_data, fraud_probability, fraud_reasons):
            return {"generated_at": "dummy", "explanation": "AI explanation"}
        def store_explanation(self, explanation):
            pass
    return XAIService()