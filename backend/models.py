from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
import certifi

class Database:
    _instance = None
    _client = None
    _db = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = Database()
        return cls._instance

    def __init__(self):
        # Default to local mongo if not provided, but intended for Atlas
        self.mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.db_name = os.getenv("MONGO_DB_NAME", "verifai")
        
        # Use certifi to fix SSL/TLS handshake errors common in some network environments
        self._client = AsyncIOMotorClient(
            self.mongo_uri,
            tlsCAFile=certifi.where()
        )
        self._db = self._client[self.db_name]

    def get_db(self):
        return self._db

    async def close(self):
        if self._client:
            self._client.close()

# We no longer need SQLAlchemy models for MongoDB, 
# but we'll use these as references for our document structure
"""
Verification Document Structure:
{
    "session_id": str,
    "status": str,
    "role": str,
    "user_email": str,
    "created_at": datetime
}

Report Document Structure:
{
    "verification_id": ObjectId,
    "decision": str,
    "confidence_score": float,
    "checks": str (Encrypted),
    "reasons": str (Encrypted),
    "stage_outputs": str (Encrypted),
    "created_at": datetime
}
"""
