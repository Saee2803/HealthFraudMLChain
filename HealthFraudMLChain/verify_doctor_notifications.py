#!/usr/bin/env python3
"""
Verification script for Doctor Notification Fix
Checks MongoDB notifications collection for doctor-related notifications
"""

from pymongo import MongoClient
from datetime import datetime
import json

# MongoDB connection
MONGO_URI = "mongodb+srv://Saee:Saee2830@cluster1.cju5mqx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1"
client = MongoClient(MONGO_URI)
db = client["healthfraudmlchain"]

print("\n" + "="*80)
print("🔍 DOCTOR NOTIFICATION VERIFICATION")
print("="*80)

# Get collections
notifications_col = db["notifications"]
users_col = db["users"]

# 1. Check total notifications by role
print("\n📊 Notification Count by Role:")
print("-" * 40)
for role in ["doctor", "admin", "patient"]:
    count = notifications_col.count_documents({"to_role": role})
    print(f"   {role.upper():8} : {count} notifications")

# 2. Show all doctor notifications
print("\n👨‍⚕️  ALL DOCTOR NOTIFICATIONS:")
print("-" * 40)
doctor_notifs = list(notifications_col.find({"to_role": "doctor"}).sort("created_at", -1))
if doctor_notifs:
    for i, notif in enumerate(doctor_notifs, 1):
        print(f"\n   [{i}] {notif.get('notification_type', 'unknown')}")
        print(f"       Message: {notif.get('message', 'N/A')}")
        print(f"       To: {notif.get('to_user_id', 'N/A')}")
        print(f"       Priority: {notif.get('priority', 'N/A')}")
        print(f"       Seen: {notif.get('seen', False)}")
        if notif.get('created_at'):
            print(f"       Created: {notif['created_at']}")
else:
    print("   ❌ NO DOCTOR NOTIFICATIONS FOUND")

# 3. Show all doctors and their user IDs
print("\n👥 ALL DOCTORS IN SYSTEM:")
print("-" * 40)
doctors = list(users_col.find({"role": "doctor"}))
if doctors:
    for doctor in doctors:
        print(f"   Name: {doctor.get('name', 'N/A')}")
        print(f"   ID: {doctor['_id']}")
        print(f"   Email: {doctor.get('email', 'N/A')}")
        
        # Count their notifications
        doc_notif_count = notifications_col.count_documents({"to_user_id": str(doctor['_id']), "to_role": "doctor"})
        print(f"   Notifications: {doc_notif_count}")
        print()
else:
    print("   ❌ NO DOCTORS IN SYSTEM")

# 4. Show doctor notifications grouped by doctor
print("\n📋 DOCTOR NOTIFICATIONS BY RECIPIENT:")
print("-" * 40)
doctor_ids = [str(d['_id']) for d in doctors]
for doctor in doctors:
    doc_id = str(doctor['_id'])
    notifs = list(notifications_col.find({
        "to_user_id": doc_id,
        "to_role": "doctor"
    }).sort("created_at", -1))
    
    print(f"\n   Doctor: {doctor.get('name')} ({doc_id})")
    if notifs:
        for notif in notifs:
            print(f"      ✓ {notif.get('message', 'N/A')}")
    else:
        print(f"      ❌ No notifications")

# 5. Comparison: Admin vs Doctor vs Patient notifications
print("\n📈 COMPARISON: Notification Creation Status")
print("-" * 40)
admin_count = notifications_col.count_documents({"to_role": "admin"})
doctor_count = notifications_col.count_documents({"to_role": "doctor"})
patient_count = notifications_col.count_documents({"to_role": "patient"})

print(f"   Admin Notifications:    {admin_count} {'✅' if admin_count > 0 else '❌'}")
print(f"   Doctor Notifications:   {doctor_count} {'✅' if doctor_count > 0 else '❌'}")
print(f"   Patient Notifications:  {patient_count} {'✅' if patient_count > 0 else '❌'}")

# 6. Check for query issues
print("\n🔧 QUERY VERIFICATION:")
print("-" * 40)
if doctors:
    test_doctor = doctors[0]
    test_doctor_id = str(test_doctor['_id'])
    
    # Try different query formats
    queries = {
        "Query 1 - String ID": {"to_user_id": test_doctor_id, "to_role": "doctor"},
        "Query 2 - Role only": {"to_role": "doctor"},
        "Query 3 - Seen=False": {"to_role": "doctor", "seen": False},
    }
    
    print(f"\n   Testing doctor: {test_doctor.get('name')} (ID: {test_doctor_id})")
    for query_name, query in queries.items():
        count = notifications_col.count_documents(query)
        print(f"   {query_name}: {count} results")
else:
    print("   ⚠️  No doctors to test")

# 7. Recent notifications (for context)
print("\n⏰ RECENT NOTIFICATIONS (All Roles):")
print("-" * 40)
recent = list(notifications_col.find().sort("created_at", -1).limit(10))
for notif in recent:
    role = notif.get('to_role', 'unknown').upper()
    type_ = notif.get('notification_type', 'unknown')
    msg_preview = (notif.get('message', 'N/A')[:50] + '...') if len(notif.get('message', 'N/A')) > 50 else notif.get('message', 'N/A')
    print(f"   [{role:8}] {type_:20} - {msg_preview}")

print("\n" + "="*80)
print("✅ VERIFICATION COMPLETE")
print("="*80)
print("\nNotes:")
print("• If doctor count is 0, check if claims are being submitted")
print("• If doctor notifications exist but not visible, check user_id format matching")
print("• Run this script after submitting a new claim to see changes")
print("="*80 + "\n")
