from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

# 1. Tell Python where to create the database file locally
SQLALCHEMY_DATABASE_URL = "sqlite:///./simulator.db"

# 2. Create the database engine
engine = create_engine(
    # "connect_args" is only needed for SQLite to allow multiple requests at once
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. Create a Session local class (this is how our API will talk to the DB)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Base class that our tables will inherit from
Base = declarative_base()

# This creates the physical file and tables on your computer
def init_db():
    Base.metadata.create_all(bind=engine)