from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import bcrypt
from bson.objectid import ObjectId
import logging

logger = logging.getLogger(__name__)

# Use bcrypt directly instead of passlib for better compatibility
def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    try:
        logger.debug(f"Hashing password of length {len(password)}")
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        logger.debug("Password hashed successfully")
        return hashed
    except Exception as e:
        logger.error(f"Error hashing password: {str(e)}")
        raise

def verify_password_hash(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception as e:
        logger.error(f"Error verifying password: {str(e)}")
        return False

_client = None


def get_client():
    global _client
    if not _client:
        _client = AsyncIOMotorClient(settings.MONGO_URI)
    return _client


def users_collection():
    return get_client()[settings.MONGO_DB].users


async def get_user_by_email(email: str):
    try:
        logger.debug(f"Looking up user by email: {email}")
        col = users_collection()
        doc = await col.find_one({"email": email})
        if doc:
            logger.debug(f"User found with email: {email}")
        else:
            logger.debug(f"No user found with email: {email}")
        return doc
    except Exception as e:
        logger.error(f"Error getting user by email: {str(e)}")
        raise


async def get_user_by_id(user_id: str):
    try:
        logger.debug(f"Looking up user by ID: {user_id}")
        col = users_collection()
        doc = await col.find_one({"_id": ObjectId(user_id)})
        return doc
    except Exception as e:
        logger.error(f"Error getting user by ID: {str(e)}")
        raise


async def create_user(user_in):
    try:
        logger.info(f"Creating user with email: {user_in.email}")
        col = users_collection()
        
        # Hash password
        hashed = hash_password(user_in.password)
        
        # Create document
        doc = {
            "email": user_in.email, 
            "password": hashed, 
            "full_name": user_in.full_name
        }
        logger.debug(f"Inserting document into MongoDB: {doc['email']}")
        
        # Insert into database
        res = await col.insert_one(doc)
        doc["_id"] = res.inserted_id
        
        logger.info(f"User created successfully with ID: {res.inserted_id}")
        return {
            "id": str(doc["_id"]), 
            "email": doc["email"], 
            "full_name": doc.get("full_name")
        }
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise


async def verify_password(plain, hashed):
    return verify_password_hash(plain, hashed)
