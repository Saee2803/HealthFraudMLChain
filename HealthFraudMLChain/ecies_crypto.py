"""
Minimal ECIES crypto implementation for HealthFraudMLChain
"""
from typing import List, Dict, Any

def get_encrypted_chain_for_role(blockchain, role: str) -> List[Dict[str, Any]]:
    """
    Get blockchain data with role-based access control
    """
    if not blockchain:
        return []
    
    try:
        chain_data = blockchain.get_chain_as_dict()
        
        # Role-based filtering (simplified)
        filtered_chain = []
        for block in chain_data:
            block_copy = block.copy()
            
            # Filter sensitive data based on role
            if role == "patient":
                # Patients see limited data
                if "data" in block_copy and isinstance(block_copy["data"], dict):
                    sensitive_fields = ["admin_signature", "doctor_signature", "encrypted_sensitive_data"]
                    for field in sensitive_fields:
                        block_copy["data"].pop(field, None)
            elif role == "doctor":
                # Doctors see more data but not admin-specific info
                if "data" in block_copy and isinstance(block_copy["data"], dict):
                    admin_fields = ["admin_signature"]
                    for field in admin_fields:
                        block_copy["data"].pop(field, None)
            # Admins see all data (no filtering)
            
            filtered_chain.append(block_copy)
        
        return filtered_chain
    except Exception as e:
        print(f"Error filtering blockchain data: {e}")
        return []