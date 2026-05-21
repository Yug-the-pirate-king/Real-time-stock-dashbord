from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import SessionLocal
from models.auth import User 

router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Minimalistic Payload: Only requires the username string
class UserAuthPayload(BaseModel):
    username: str

@router.post("/create-user")
def create_user(payload: UserAuthPayload, db: Session = Depends(get_db)):
    username_cleaned = payload.username.strip()
    if not username_cleaned:
        raise HTTPException(status_code=400, detail="Username cannot be empty.")

    # Check if username already exists
    existing_user = db.query(User).filter(User.username == username_cleaned).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken.")
    
    # Create user with default balance defined in your model
    new_user = User(username=username_cleaned)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"id": new_user.id, "username": new_user.username, "balance": new_user.balance}

@router.post("/login")
def login(payload: UserAuthPayload, db: Session = Depends(get_db)):
    username_cleaned = payload.username.strip()
    
    # Find the user by username only
    user = db.query(User).filter(User.username == username_cleaned).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please register.")
        
    return {"id": user.id, "username": user.username, "balance": user.balance}