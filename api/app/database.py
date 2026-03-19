from motor.motor_asyncio import AsyncIOMotorClient
from app.config import MONGO_URI, MONGO_DB

client: AsyncIOMotorClient = None
db = None


async def connect_to_mongo():
    """Connect to MongoDB at app startup."""
    global client, db
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[MONGO_DB]
    print(f"Connected to MongoDB: {MONGO_DB}")


async def close_mongo_connection():
    """Close connection to MongoDB."""
    global client
    if client:
        client.close()
        print("MongoDB connection closed")


def get_database():
    """Get reference to the database."""
    return db
