"""
MongoDB connection handler.
"""
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db_name: str = settings.MONGO_DB_NAME

    def connect(self):
        """Connect to MongoDB."""
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        print(f"✅ Connected to MongoDB at {settings.MONGO_URI}")
        
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            self.client = None
            print("❌ MongoDB connection closed")

    def get_db(self):
        """Get database instance."""
        if self.client is None:
            self.connect()
        return self.client[self.db_name]

mongodb = MongoDB()
