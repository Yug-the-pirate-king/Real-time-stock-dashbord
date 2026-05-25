import os
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

# Load variables from a .env file if running locally
load_dotenv()

# 1. Grab the URL from the environment (Render) or fall back to your local SQLite
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # CockroachDB fix: SQLAlchemy requires the string to start with 'cockroachdb://'
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "cockroachdb://", 1)
        
    # Create cloud engine
    engine = create_engine(DATABASE_URL, echo=False)
else:
    # 2. Local fallback to SQLite so your app still works on your computer
    SQLALCHEMY_DATABASE_URL = "sqlite:///./simulator.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )

# 3. Create a Session local class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Base class that your tables will inherit from
Base = declarative_base()

# This creates the physical tables in CockroachDB or SQLite
def init_db():
    Base.metadata.create_all(bind=engine)