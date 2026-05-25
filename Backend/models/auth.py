from sqlalchemy import Column, Integer, String, Float
from database import Base
import bcrypt

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    balance = Column(Float, default=5000.0)

# --- Password Hashing Helpers ---

def hash_password(password: str) -> str:
    """Converts a plain text password into a secure hash."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Checks if the provided password matches the stored hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))