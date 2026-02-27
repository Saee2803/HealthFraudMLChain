"""
Minimal notification service for HealthFraudMLChain

FIX: PyMongo Collection objects do not implement truth value testing.
All checks must use 'is None' or 'is not None' instead of bool() context.
"""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

class NotificationService:
    def __init__(self, db):
        self.db = db
        # FIX: PyMongo Database objects do not implement truth value testing.
        # Must use explicit 'is not None' comparison instead of 'if db'.
        self.notifications_collection = db["notifications"] if db is not None else None
    
    def create_notification(self, to_role: str, to_user_id: str, message: str,
                          notification_type: str = "general", 
                          related_claim_id: str = None,
                          priority: str = "normal") -> bool:
        """Create a new notification"""
        # FIX: PyMongo Collection objects do not implement truth value testing.
        if self.notifications_collection is None:
            return False
        
        try:
            notification = {
                "to_role": to_role,
                "to_user_id": to_user_id,
                "message": message,
                "notification_type": notification_type,
                "related_claim_id": related_claim_id,
                "priority": priority,
                "created_at": datetime.now(timezone.utc),
                "read": False
            }
            self.notifications_collection.insert_one(notification)
            return True
        except Exception as e:
            print(f"Error creating notification: {e}")
            return False
    
    def get_unread_count(self, user_id: str, role: str) -> int:
        """Get count of unread notifications"""
        # FIX: PyMongo Collection objects do not implement truth value testing.
        if self.notifications_collection is None:
            return 0
        
        try:
            return self.notifications_collection.count_documents({
                "to_user_id": user_id,
                "to_role": role,
                "read": False
            })
        except:
            return 0
    
    def get_recent_notifications(self, user_id: str, role: str, limit: int = 5) -> List[Dict]:
        """Get recent notifications"""
        # FIX: PyMongo Collection objects do not implement truth value testing.
        if self.notifications_collection is None:
            return []
        
        try:
            notifications = list(self.notifications_collection.find({
                "to_user_id": user_id,
                "to_role": role
            }).sort("created_at", -1).limit(limit))
            
            # Convert ObjectId to string
            for notif in notifications:
                notif["_id"] = str(notif["_id"])
            
            return notifications
        except:
            return []
    
    def get_notifications_for_user(self, user_id: str, role: str, limit: int = 20, skip: int = 0) -> List[Dict]:
        """Get paginated notifications for user"""
        # FIX: PyMongo Collection objects do not implement truth value testing.
        if self.notifications_collection is None:
            return []
        
        try:
            notifications = list(self.notifications_collection.find({
                "to_user_id": user_id,
                "to_role": role
            }).sort("created_at", -1).skip(skip).limit(limit))
            
            # Convert ObjectId to string
            for notif in notifications:
                notif["_id"] = str(notif["_id"])
            
            return notifications
        except:
            return []
    
    def mark_as_read(self, notification_id: str) -> Dict:
        """Mark notification as read"""
        # FIX: PyMongo Collection objects do not implement truth value testing.
        if self.notifications_collection is None:
            return {"success": False, "error": "Service unavailable"}
        
        try:
            from bson.objectid import ObjectId
            result = self.notifications_collection.update_one(
                {"_id": ObjectId(notification_id)},
                {"$set": {"read": True}}
            )
            return {"success": result.modified_count > 0}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def mark_all_as_read(self, user_id: str, role: str) -> Dict:
        """Mark all notifications as read for user"""
        # FIX: PyMongo Collection objects do not implement truth value testing.
        if self.notifications_collection is None:
            return {"success": False, "error": "Service unavailable"}
        
        try:
            result = self.notifications_collection.update_many(
                {"to_user_id": user_id, "to_role": role, "read": False},
                {"$set": {"read": True}}
            )
            return {"success": True, "modified_count": result.modified_count}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete_notification(self, notification_id: str) -> Dict:
        """Delete a notification"""
        # FIX: PyMongo Collection objects do not implement truth value testing.
        if self.notifications_collection is None:
            return {"success": False, "error": "Service unavailable"}
        
        try:
            from bson.objectid import ObjectId
            result = self.notifications_collection.delete_one(
                {"_id": ObjectId(notification_id)}
            )
            return {"success": result.deleted_count > 0}
        except Exception as e:
            return {"success": False, "error": str(e)}

def init_notification_service(db):
    """Initialize notification service"""
    return NotificationService(db)