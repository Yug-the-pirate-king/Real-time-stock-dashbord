from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models.auth import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Database connection helper
def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally: 
        db.close()

# 1. THE LOGIN ROUTE
@router.post("/login")  
def login_user(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user

# 2. THE MISSING REGISTRATION ROUTE (Add this!)
@router.post("/create-user/{username}")
def create_user(username: str, db: Session = Depends(get_db)):
    # Check if the username is already taken by someone else
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken.")
    
    # Create the new user with a starting virtual balance of $100,000
    new_user = User(username=username, balance=100000.0)
    
    # Save the new user into your simulator.db file
    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # Gives the new_user its unique ID from the database
    
    return {"message": "Account created successfully!", "user": new_user}