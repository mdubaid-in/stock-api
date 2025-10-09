from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from typing import Optional
from config.env import env


class MongoDBClient:
    """Centralized MongoDB client for the entire project."""

    _instance = None

    def __new__(cls, uri: str, db_name: str):
        """Ensure a single client instance (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_client(uri, db_name)
        return cls._instance

    def _init_client(self, uri: str, db_name: str):
        """Initialize the MongoDB client and database."""
        self.client = MongoClient(uri, maxPoolSize=50, connect=True)
        self.db: Database = self.client[db_name]

    def get_collection(self, name: str) -> Collection:
        """Return a MongoDB collection by name."""
        return self.db[name]

    def close(self):
        """Close the MongoDB client connection."""
        self.client.close()
        MongoDBClient._instance = None


mongoClient = MongoDBClient(env.MONGO_JOB_SERVER_URI, env.MONGO_DB_NAME)
