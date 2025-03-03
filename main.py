from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

app = FastAPI()
MONGO_URI = "mongodb+srv://SarathKumar2001:SarathKumar@cluster0.vianz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

DATABASE_NAME = "career"
client = AsyncIOMotorClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db["user"]

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

@app.post("/user", response_model=dict)
async def create_user(user: User):
    # Convert to dict - note: using .dict() method, not .dict property
    user_dict = user.dict(exclude={"id"})
    
    # Insert into MongoDB
    new_user = await collection.insert_one(user_dict)
    
    # Retrieve the created user
    created_user = await collection.find_one({"_id": new_user.inserted_id})
    
    if created_user:
        return user_serializer(created_user)
    raise HTTPException(status_code=400, detail="User creation failed")

@app.get("/users/", response_model=List[dict])
async def get_users():
    users = await collection.find().to_list(100)
    return [user_serializer(u) for u in users]

# Add this if you want to run the app locally
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)