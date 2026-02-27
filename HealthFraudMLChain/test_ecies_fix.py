#!/usr/bin/env python3
"""
Test suite for ECIES encryption fix.
Verifies: Key loading, encryption, decryption, and blockchain integration.
"""

import os
import sys
import json
import tempfile
import shutil

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_key_generation_and_storage():
    """Test 1: Key generation and storage with hex prefix handling"""
    print("\n" + "="*60)
    print("TEST 1: Key Generation & Storage")
    print("="*60)
    
    try:
        from ecies_crypto import load_or_create_keys, _hex_to_bytes, _bytes_to_hex
        
        # Load existing keys
        private_key_bytes, public_key_bytes = load_or_create_keys()
        
        print(f"✅ Keys loaded successfully")
        print(f"   Private key length: {len(private_key_bytes)} bytes")
        print(f"   Public key length: {len(public_key_bytes)} bytes")
        
        # Verify byte types
        assert isinstance(private_key_bytes, bytes), "Private key should be bytes"
        assert isinstance(public_key_bytes, bytes), "Public key should be bytes"
        
        # Check hex conversion
        hex_private = _bytes_to_hex(private_key_bytes)
        hex_public = _bytes_to_hex(public_key_bytes)
        
        print(f"✅ Hex conversion working")
        print(f"   Private key (hex): {hex_private[:20]}... (length: {len(hex_private)})")
        print(f"   Public key (hex): {hex_public[:20]}... (length: {len(hex_public)})")
        
        # Verify 0x prefix
        assert hex_private.startswith('0x'), "Hex private key should have 0x prefix"
        assert hex_public.startswith('0x'), "Hex public key should have 0x prefix"
        
        # Test reverse conversion (critical for the fix)
        recovered_private = _hex_to_bytes(hex_private)
        recovered_public = _hex_to_bytes(hex_public)
        
        assert recovered_private == private_key_bytes, "Private key round-trip failed"
        assert recovered_public == public_key_bytes, "Public key round-trip failed"
        
        print(f"✅ Round-trip conversion (with 0x prefix) working perfectly")
        print(f"   This fix prevents: ValueError: non-hexadecimal number found in fromhex()")
        
        return True
    
    except Exception as e:
        print(f"❌ TEST 1 FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_encryption_decryption():
    """Test 2: ECIES encryption and decryption"""
    print("\n" + "="*60)
    print("TEST 2: ECIES Encryption & Decryption")
    print("="*60)
    
    try:
        from ecies_crypto import ecies_encrypt, ecies_decrypt
        
        # Test data
        test_data = {
            "claim_id": "CLM_12345",
            "amount": 5000.00,
            "status": "approved",
            "doctor_name": "Dr. Smith",
            "encrypted": False
        }
        
        print(f"Encrypting test data: {json.dumps(test_data, indent=2)}")
        
        # Encrypt
        encrypted_payload = ecies_encrypt(test_data)
        print(f"✅ Encryption successful")
        print(f"   Encrypted payload length: {len(encrypted_payload)} chars")
        print(f"   Payload (base64): {encrypted_payload[:50]}...")
        
        # Verify it's valid base64
        import base64
        try:
            base64.b64decode(encrypted_payload)
            print(f"✅ Payload is valid base64")
        except Exception as e:
            print(f"❌ Payload is NOT valid base64: {e}")
            return False
        
        # Decrypt
        decrypted_data = ecies_decrypt(encrypted_payload)
        print(f"✅ Decryption successful")
        print(f"   Decrypted data: {json.dumps(decrypted_data, indent=2)}")
        
        # Verify data integrity
        assert decrypted_data == test_data, "Decrypted data doesn't match original"
        print(f"✅ Data integrity verified - encryption/decryption cycle complete")
        
        return True
    
    except Exception as e:
        print(f"❌ TEST 2 FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_blockchain_integration():
    """Test 3: Blockchain genesis block creation and encryption"""
    print("\n" + "="*60)
    print("TEST 3: Blockchain Integration")
    print("="*60)
    
    try:
        from blockchain import Blockchain, Block
        from ecies_crypto import ecies_decrypt
        
        # Create blockchain instance (without MongoDB for testing)
        blockchain = Blockchain(db=None)
        
        # Create genesis block
        genesis_block = blockchain.create_genesis_block()
        blockchain.chain = [genesis_block]
        
        print(f"✅ Genesis block created successfully")
        print(f"   Index: {genesis_block.index}")
        print(f"   Hash: {genesis_block.hash[:20]}...")
        print(f"   Encrypted data length: {len(genesis_block.encrypted_data)} chars")
        
        # Verify we can decrypt genesis block
        genesis_payload = {
            "genesis": True,
            "message": "HealthFraudMLChain Ledger Started",
            "doctor_approved": False,
            "admin_approved": False,
            "status": "Genesis"
        }
        
        decrypted = ecies_decrypt(genesis_block.encrypted_data)
        print(f"✅ Genesis block decrypted successfully")
        print(f"   Decrypted content: {json.dumps(decrypted, indent=2)}")
        
        assert decrypted == genesis_payload, "Genesis block payload mismatch"
        print(f"✅ Genesis block payload verified")
        
        # Test get_decrypted_chain
        decrypted_chain = blockchain.get_decrypted_chain()
        print(f"✅ Decrypted chain retrieved: {len(decrypted_chain)} blocks")
        print(f"   Block 0: {json.dumps(decrypted_chain[0]['data'], indent=2)}")
        
        return True
    
    except Exception as e:
        print(f"❌ TEST 3 FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_role_based_access():
    """Test 4: Role-based access control"""
    print("\n" + "="*60)
    print("TEST 4: Role-Based Access Control")
    print("="*60)
    
    try:
        from ecies_crypto import can_decrypt_blockchain_data, get_encrypted_chain_for_role
        from blockchain import Blockchain
        
        # Test role access
        roles = {
            'admin': True,
            'doctor': True,
            'patient': False
        }
        
        for role, should_access in roles.items():
            can_access = can_decrypt_blockchain_data(role)
            assert can_access == should_access, f"Role {role} access check failed"
            status = "✅ CAN decrypt" if can_access else "❌ CANNOT decrypt"
            print(f"   {role.capitalize()}: {status}")
        
        # Create blockchain and test role-based chain retrieval
        blockchain = Blockchain(db=None)
        genesis_block = blockchain.create_genesis_block()
        blockchain.chain = [genesis_block]
        
        # Test admin access
        admin_chain = get_encrypted_chain_for_role(blockchain, 'admin')
        assert admin_chain[0]['encrypted'] == False, "Admin should see decrypted data"
        print(f"✅ Admin can see decrypted data: {admin_chain[0]['data']}")
        
        # Test patient access
        patient_chain = get_encrypted_chain_for_role(blockchain, 'patient')
        assert patient_chain[0]['encrypted'] == True, "Patient should not see decrypted data"
        print(f"✅ Patient sees encrypted marker only: {patient_chain[0]['data']}")
        
        return True
    
    except Exception as e:
        print(f"❌ TEST 4 FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "╔" + "="*58 + "╗")
    print("║" + " ECIES ENCRYPTION FIX - COMPREHENSIVE TEST SUITE ".center(58) + "║")
    print("╚" + "="*58 + "╝")
    
    results = []
    
    # Run tests
    results.append(("Key Generation & Storage", test_key_generation_and_storage()))
    results.append(("Encryption/Decryption", test_encryption_decryption()))
    results.append(("Blockchain Integration", test_blockchain_integration()))
    results.append(("Role-Based Access", test_role_based_access()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! ECIES encryption fix is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. See details above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
