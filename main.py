"""
FastAPI User API with MongoDB Atlas.

This API provides CRUD operations for managing users in a MongoDB Atlas database.
"""

from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Initialize FastAPI app
app = FastAPI()

# MongoDB connection details
MONGO_URI = ("mongodb+srv://SarathKumar2001:SarathKumar@cluster0.vianz.mongodb.net/"
             "?retryWrites=true&w=majority&appName=Cluster0"
)
DATABASE_NAME = "career"

# Connect to MongoDB
client = AsyncIOMotorClient(MONGO_URI)
db = client[DATABASE_NAME]

class User(BaseModel):
    """ Represents a user object. """
    id: str
    name: str
    status: str

    class Config:
        """ Pydantic configuration for JSON serialization. """
        json_encoders = {ObjectId: str}

def user_serializer(user) -> dict:
    """ Serializes MongoDB user document into a dictionary. """
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "status": user["status"],
    }

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/user", response_model=User)
async def create_user(user: User):
    """ Creates a new user in MongoDB. """
    user_dict = user.dict()  # Fix: Added ()
    new_user = await db["user"].insert_one(user_dict)
    created_user = await db["user"].find_one({"_id": new_user.inserted_id})

    if created_user:
        return user_serializer(created_user)
    raise HTTPException(status_code=400, detail="User creation failed")

@app.get("/users/", response_model=List[dict])
async def get_users():
    """ Retrieves all users from MongoDB. """
    users = await db.user.find().to_list(100)
    return [user_serializer(user) for user in users]

@app.get("/user/{user_id}")
async def get_user_by_id(user_id: str):
    """ Retrieves a user by their ID. """
    user = await db.user.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_serializer(user)

@app.put("/user/{user_id}")
async def update_user(user_id: str, user: User):
    """ Updates an existing user's details. """
    result = await db.user.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": user.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User updated successfully"}

@app.delete("/user/{user_id}")
async def delete_user(user_id: str):
    """ Deletes a user by their ID. """
    result = await db.user.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}  # Fix: Changed "Puser" to "User"
