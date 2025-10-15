from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from passlib.context import CryptContext
from bson.objectid import ObjectId

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_client = None


def get_client():
    global _client
    if not _client:
        _client = AsyncIOMotorClient(settings.MONGO_URI)
    return _client


def users_collection():
    return get_client()[settings.MONGO_DB].users


async def get_user_by_email(email: str):
    col = users_collection()
    doc = await col.find_one({"email": email})
    return doc


async def get_user_by_id(user_id: str):
    col = users_collection()
    doc = await col.find_one({"_id": ObjectId(user_id)})
    return doc


async def create_user(user_in):
    col = users_collection()
    hashed = pwd_context.hash(user_in.password)
    doc = {"email": user_in.email, "password": hashed, "full_name": user_in.full_name}
    res = await col.insert_one(doc)
    doc["_id"] = res.inserted_id
    return {"id": str(doc["_id"]), "email": doc["email"], "full_name": doc.get("full_name")}


async def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)
