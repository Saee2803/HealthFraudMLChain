#!/usr/bin/env python3
"""
Verification script for doctor-claim mapping fix
Tests that assigned_doctor_id is correctly populated
"""

from pymongo import MongoClient
import json

# MongoDB connection
MONGO_URI = "mongodb+srv://Saee:Saee2830@cluster1.cju5mqx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1"
client = MongoClient(MONGO_URI)
db = client["healthfraudmlchain"]

print("\n" + "="*80)
print("🔍 DOCTOR-CLAIM MAPPING VERIFICATION")
print("="*80)

# Collections
claims_col = db["claims"]
users_col = db["users"]

# 1. Check doctor names in users collection
print("\n📋 DOCTORS IN SYSTEM:")
print("-" * 80)
doctors = list(users_col.find({"role": "doctor"}))
if doctors:
    for doctor in doctors:
        print(f"   Name: {doctor['name']}")
        print(f"   ID: {doctor['_id']}")
        print()
else:
    print("   ❌ No doctors found in system")

# 2. Check recent claims
print("\n📝 RECENT CLAIMS (Last 5):")
print("-" * 80)
recent_claims = list(claims_col.find().sort("submitted_on", -1).limit(5))
if recent_claims:
    for i, claim in enumerate(recent_claims, 1):
        print(f"\n   [{i}] Claim ID: {claim['_id']}")
        print(f"       Patient: {claim.get('patient_name', 'N/A')}")
        print(f"       Doctor Name (stored): {claim.get('doctor_name', 'N/A')}")
        print(f"       assigned_doctor_id: {claim.get('assigned_doctor_id', 'NULL ❌')}")
        
        if claim.get('assigned_doctor_id'):
            # Find matching doctor
            doctor = users_col.find_one({"_id": claim.get('assigned_doctor_id')})
            if doctor:
                print(f"       ✅ Resolved to Doctor: {doctor['name']}")
            else:
                print(f"       ⚠️  Doctor ID not found in users collection")
        else:
            print(f"       ❌ ISSUE: assigned_doctor_id is NULL")
else:
    print("   ❌ No claims found in system")

# 3. Check for claims with NULL assigned_doctor_id
print("\n\n🔴 CLAIMS WITH NULL assigned_doctor_id:")
print("-" * 80)
null_claims = list(claims_col.find({"assigned_doctor_id": None}))
print(f"   Count: {len(null_claims)}")
if null_claims:
    print("   ❌ Found claims with NULL assigned_doctor_id")
    for claim in null_claims[:3]:  # Show first 3
        print(f"\n      Claim: {claim['_id']}")
        print(f"      Patient: {claim.get('patient_name', 'N/A')}")
        print(f"      Doctor (name): {claim.get('doctor_name', 'N/A')}")
        
        # Try to match doctor
        doc_name = claim.get('doctor_name', '')
        matching_doctor = users_col.find_one({
            "name": {"$regex": f"^{doc_name}$", "$options": "i"},
            "role": "doctor"
        })
        if matching_doctor:
            print(f"      ⚠️  Doctor EXISTS but wasn't found: {matching_doctor['name']} ({matching_doctor['_id']})")
else:
    print("   ✅ No NULL claims found - all claims properly assigned!")

# 4. Verify doctor dashboard would work
print("\n\n✅ DOCTOR DASHBOARD VERIFICATION:")
print("-" * 80)
for doctor in doctors[:3]:  # Test first 3 doctors
    doctor_id = str(doctor['_id'])
    pending_count = claims_col.count_documents({
        "assigned_doctor_id": doctor_id,
        "status": "Pending",
        "doctor_approved": None
    })
    print(f"   Doctor: {doctor['name']}")
    print(f"      Pending claims assigned: {pending_count}")

# 5. Case sensitivity test
print("\n\n🔧 CASE-SENSITIVITY TEST:")
print("-" * 80)
if doctors:
    # Get a doctor name
    test_doctor_name = doctors[0]['name']
    test_doctor_id = doctors[0]['_id']
    
    # Test exact match
    exact = users_col.find_one({"name": test_doctor_name, "role": "doctor"})
    print(f"   Test doctor: {test_doctor_name}")
    print(f"   Exact match find_one(): {'✅ Found' if exact else '❌ Not found'}")
    
    # Test case-insensitive match
    ci_match = users_col.find_one({
        "name": {"$regex": f"^{test_doctor_name}$", "$options": "i"},
        "role": "doctor"
    })
    print(f"   Case-insensitive match: {'✅ Found' if ci_match else '❌ Not found'}")
    
    # Test with mixed case
    mixed_case = test_doctor_name.lower()
    ci_match_mixed = users_col.find_one({
        "name": {"$regex": f"^{mixed_case}$", "$options": "i"},
        "role": "doctor"
    })
    print(f"   Mixed case ({mixed_case}): {'✅ Found' if ci_match_mixed else '❌ Not found'}")

# 6. Summary
print("\n\n" + "="*80)
print("📊 SUMMARY")
print("="*80)
total_claims = claims_col.count_documents({})
assigned_claims = claims_col.count_documents({"assigned_doctor_id": {"$ne": None}})
unassigned_claims = claims_col.count_documents({"assigned_doctor_id": None})

print(f"   Total Claims: {total_claims}")
print(f"   ✅ With assigned_doctor_id: {assigned_claims}")
print(f"   ❌ Without assigned_doctor_id (NULL): {unassigned_claims}")

if unassigned_claims == 0:
    print(f"\n   🎉 SUCCESS: All claims are properly assigned!")
else:
    print(f"\n   ⚠️  ISSUE: {unassigned_claims} claims still have NULL assigned_doctor_id")
    print(f"      These were likely submitted before the fix.")
    print(f"      New claims after fix should be properly assigned.")

print("="*80 + "\n")
