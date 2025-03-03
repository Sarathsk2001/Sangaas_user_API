from typing import List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
from dotenv import load_dotenv
import logging
import json

# Set up logging to help debug issues
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI()

# Get MongoDB URI from environment variables
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "career")

# Create a global variable for the MongoDB client to reuse connections
mongodb_client = None

# Database connection dependency
async def get_database():
    global mongodb_client
    try:
        # Reuse existing client if available
        if mongodb_client is None:
            logger.info("Creating new MongoDB client connection")
            mongodb_client = AsyncIOMotorClient(
                MONGO_URI,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=10000,         # 10 second timeout
                socketTimeoutMS=45000,          # 45 second timeout
            )
            # Test the connection
            await mongodb_client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
        return mongodb_client[DATABASE_NAME]
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

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
    # Add environment variable check to debug in production
    mongo_uri_exists = "MONGO_URI exists" if MONGO_URI else "MONGO_URI is missing"
    return {
        "message": "API is running",
        "env_check": mongo_uri_exists,
        "database": DATABASE_NAME
    }

@app.get("/test-db-connection")
async def test_db_connection():
    """Test database connection"""
    try:
        db = await get_database()
        # Just check if we can list collections
        collections = await db.list_collection_names()
        return {
            "status": "success",
            "message": "Database connection successful",
            "collections": collections
        }
    except Exception as e:
        logger.error(f"Error testing database connection: {str(e)}")
        return {
            "status": "error",
            "message": f"Database connection error: {str(e)}"
        }

@app.post("/user", response_model=dict)
async def create_user(user: User, db=Depends(get_database)):
    try:
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
async def get_users(db=Depends(get_database)):
    try:
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