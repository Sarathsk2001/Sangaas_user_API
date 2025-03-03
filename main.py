from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
from dotenv import load_dotenv
import logging

# Set up logging to help debug issues
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI()

# Get MongoDB URI from environment variables - DO NOT hardcode credentials
# Update this part
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://SarathKumar2001:SarathKumar@cluster0.vianz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DATABASE_NAME = os.getenv("DATABASE_NAME", "career")
# MongoDB connection handler
async def get_database():
    try:
        client = AsyncIOMotorClient(MONGO_URI)
        return client[DATABASE_NAME]
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")

class User(BaseModel):
    id: str = None
    name: str
    status: str

    class Config:
        json_encoders = {ObjectId: str}
        
def user_serializer(user) -> dict:
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "status": user["status"],
    }

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "API is running"}

@app.post("/user", response_model=dict)
async def create_user(user: User):
    try:
        # Get database connection
        db = await get_database()
        collection = db["user"]
        
        # Convert to dict
        user_dict = user.dict(exclude={"id"})
        
        # Insert into MongoDB
        new_user = await collection.insert_one(user_dict)
        logger.info(f"Created user with ID: {new_user.inserted_id}")
        
        # Retrieve the created user
        created_user = await collection.find_one({"_id": new_user.inserted_id})
        
        if created_user:
            return user_serializer(created_user)
        raise HTTPException(status_code=400, detail="User creation failed")
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/users", response_model=List[dict])
async def get_users():
    try:
        # Get database connection
        db = await get_database()
        collection = db["user"]
        
        logger.info("Fetching users from MongoDB")
        users = await collection.find().to_list(100)
        logger.info(f"Found {len(users)} users")
        # Replace this line:
        # return {"message": "API is running"}
        # With this:
        return [user_serializer(u) for u in users]
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    

@app.get("/debug")
async def debug_connection():
    """Debug endpoint to test database connection"""
    try:
        # Get database connection
        db = await get_database()
        collection = db["user"]
        
        # Test connection
        count = await collection.count_documents({})
        return {
            "connected": True,
            "database": DATABASE_NAME,
            "collection": "user",
            "document_count": count
        }
    except Exception as e:
        logger.error(f"Debug connection error: {str(e)}")
        return {
            "connected": False,
            "error": str(e),
            "mongo_uri_set": bool(MONGO_URI),
            "database_name_set": bool(DATABASE_NAME)
        }
# This is only used when running locally
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)