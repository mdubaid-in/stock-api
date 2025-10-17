from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from config.env import env


class MongoDBClient:
    """Centralized MongoDB client for the entire project."""

    def __init__(self, uri: str, db_name: str):
        """Initialize the MongoDB client and database."""
        self.client = MongoClient(uri, maxPoolSize=50, connect=True)
        self.db: Database = self.client[db_name]

    def get_collection(self, name: str) -> Collection:
        """Return a MongoDB collection by name."""
        return self.db[name]

    def close(self):
        """Close the MongoDB client connection."""
        self.client.close()


stock_mongo_client = MongoDBClient(env.MONGO_JOB_SERVER_URI, "smFeeds")
mongo_client = MongoDBClient(env.MONGO_PRODUCTION_URI, "pnq")
