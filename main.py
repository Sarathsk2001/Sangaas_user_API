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
MONGO_URI = os.getenv("mongodb+srv://SarathKumar2001:SarathKumar@cluster0.vianz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
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

'''@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "API is running"}'''


@app.get("/users", response_model=List[dict])
async def get_users():
    try:
        # Get database connection
        db = await get_database()
        collection = db["user"]
        
        logger.info("Fetching users from MongoDB")
        users = await collection.find().to_list(100)
        logger.info(f"Found {len(users)} users")
        return [user_serializer(u) for u in users]
    except Exception as e:
        logger.error(f"Error fetching users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# This is only used when running locally
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)