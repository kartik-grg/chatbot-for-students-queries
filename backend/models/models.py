import datetime
from bson import ObjectId
from config.database import db_instance

class User:
    """User model for handling user-related database operations"""
    
    def __init__(self):
        self.collection = db_instance.get_collection("users")
    
    def create_user(self, username, email, hashed_password):
        """Create a new user"""
        user_data = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "created_at": datetime.datetime.utcnow()
        }
        result = self.collection.insert_one(user_data)
        return result.inserted_id
    
    def find_by_email(self, email):
        """Find user by email"""
        return self.collection.find_one({"email": email})
    
    def find_by_username(self, username):
        """Find user by username"""
        return self.collection.find_one({"username": username})
    
    def find_by_id(self, user_id):
        """Find user by ID"""
        return self.collection.find_one({"_id": ObjectId(user_id)})
    
    def get_total_users(self):
        """Get total number of users"""
        return self.collection.count_documents({})

class Query:
    """Query model for handling query-related database operations"""
    
    def __init__(self):
        self.collection = db_instance.get_collection("queries")
    
    def create_query(self, question, user_id=None, answered=False):
        """Create a new query"""
        query_data = {
            "question": question,
            "answered": answered,
            "user_id": ObjectId(user_id) if user_id else None,
            "timestamp": datetime.datetime.utcnow()
        }
        print(query_data)
        result = self.collection.insert_one(query_data)
        # print(result.inserted_id)
        return result.inserted_id
    
    def get_unanswered_queries(self):
        """Get all unanswered queries"""
        try:
            unanswered = list(self.collection.find({"answered": False}))
            
            # Also check for queries without the answered field
            no_answered_field = list(self.collection.find({"answered": {"$exists": False}}))
            
            # Check total queries
            total = self.collection.count_documents({})
            
            if total > 0:
                sample = self.collection.find_one({})
            
            return unanswered
        except Exception as e:
            print(f"=== QUERY MODEL ERROR: {str(e)} ===")
            return []
    
    def update_query(self, query_id, answer):
        """Update query with answer"""
        return self.collection.update_one(
            {"_id": ObjectId(query_id)},
            {"$set": {"answer": answer, "answered": True}}
        )
    
    def delete_query(self, query_id):
        """Delete a query"""
        return self.collection.delete_one({"_id": ObjectId(query_id)})
    
    def find_by_id(self, query_id):
        """Find query by ID"""
        return self.collection.find_one({"_id": ObjectId(query_id)})
    
    def get_unanswered_count(self):
        """Get count of unanswered queries"""
        return self.collection.count_documents({"answered": False})

class ChatHistory:
    """Chat history model for handling chat-related database operations"""
    
    def __init__(self):
        self.collection = db_instance.get_collection("chat_history")
    
    def create_chat(self, user_id, question, answer):
        """Create a new chat entry"""
        chat_data = {
            "user_id": ObjectId(user_id),
            "question": question,
            "answer": answer,
            "timestamp": datetime.datetime.utcnow()
        }
        result = self.collection.insert_one(chat_data)
        return result.inserted_id
    
    def get_user_history(self, user_id):
        """Get chat history for a specific user"""
        return list(self.collection.find(
            {"user_id": ObjectId(user_id)},
            {"_id": 1, "question": 1, "answer": 1, "timestamp": 1}
        ).sort("timestamp", -1))
    
    def get_all_history_with_users(self):
        """Get all chat history with user details for admin"""
        pipeline = [
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "user"
                }
            },
            {
                "$unwind": "$user"
            },
            {
                "$project": {
                    "question": 1,
                    "answer": 1,
                    "timestamp": 1,
                    "username": "$user.username"
                }
            },
            {
                "$sort": {"timestamp": -1}
            }
        ]
        return list(self.collection.aggregate(pipeline))
    
    def get_total_chats(self):
        """Get total number of chats"""
        return self.collection.count_documents({})
    
    def get_all_questions_with_timestamps(self):
        """Get all questions with timestamps for analytics"""
        return list(self.collection.find({}, {"question": 1, "timestamp": 1}))
