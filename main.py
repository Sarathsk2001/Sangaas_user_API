from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from typing import Optional, List 

app = FastAPI()
MONGO_URI = "mongodb+srv://SarathKumar2001:SarathKumar@cluster0.vianz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DATABASE_NAME = "career"

client = AsyncIOMotorClient(MONGO_URI)
db = client[DATABASE_NAME] 
#collection = db["user"]

class User(BaseModel): #data validation
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



@app.post("/user", response_model=User)
async def create_user(product: User): 
    product_dict = product.dict
    new_user = await db["user"].insert_one(product_dict) 
    created_user = await db["user"].find_one({"_id": new_user.inserted_id}) 

    if created_user:
        return user_serializer(created_user)
    raise HTTPException(status_code=400, detail="user creation failed")


@app.get("/users/", response_model=List[dict])
async def get_users():
    users = await db.user.find().to_list(100)
    return [user_serializer(u) for u in users]

@app.get("/user/{user_id}")
async def get_user_by_id(user_id: str):
    user = await db.user.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    return user_serializer(user)


@app.put("/user/{user_id}")
async def update_user(user_id: str, user: User):
    result = await db.user.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": user.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="user not found")
    return {"message": "user updated successfully"}


@app.delete("/user/{user_id}")
async def delete_user(user_id: str):
    result = await db.user.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="user not found")
    return {"message": "Puser deleted successfully"}
