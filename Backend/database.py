import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Convert standard postgres string to cockroachdb dialect for SQLAlchemy
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "cockroachdb://", 1)
        
    # Create the cloud engine with explicit SSL connection arguments
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "sslmode": "verify-full",
            "sslrootcert": "system"
        },
        echo=False
    )
else:
    # Local fallback to SQLite for offline work
    SQLALCHEMY_DATABASE_URL = "sqlite:///./simulator.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)