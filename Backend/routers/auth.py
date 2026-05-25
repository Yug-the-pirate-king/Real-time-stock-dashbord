from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import SessionLocal
from models.auth import User, hash_password, verify_password 

router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class UserAuthPayload(BaseModel):
    username: str
    password: str

@router.post("/create-user")
def create_user(payload: UserAuthPayload, db: Session = Depends(get_db)):
    username_cleaned = payload.username.strip()
    password_cleaned = payload.password.strip()
    
    if not username_cleaned or not password_cleaned:
        raise HTTPException(status_code=400, detail="Username and password cannot be empty.")

    # Check if username already exists
    existing_user = db.query(User).filter(User.username == username_cleaned).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken.")
    
    # Hash the password before saving
    hashed_pw = hash_password(password_cleaned)
    
    new_user = User(username=username_cleaned, password_hash=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # CONVERT ID TO STRING: Prevents JavaScript precision rounding errors
    return {"id": str(new_user.id), "username": new_user.username, "balance": new_user.balance}

@router.post("/login")
def login(payload: UserAuthPayload, db: Session = Depends(get_db)):
    username_cleaned = payload.username.strip()
    password_cleaned = payload.password.strip()
    
    # Find the user by username
    user = db.query(User).filter(User.username == username_cleaned).first()
    
    # Check if user exists AND if the password matches the hash
    if not user or not verify_password(password_cleaned, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
        
    # CONVERT ID TO STRING: Prevents JavaScript precision rounding errors
    return {"id": str(user.id), "username": user.username, "balance": user.balance}