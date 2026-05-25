import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # 1. Strip any native parameters to pass a pristine path to the adapter
    if "?" in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.split("?")[0]

    # 2. Convert postgres standard schema to cockroachdb dialect
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "cockroachdb://", 1)
        
    # 3. Create the database engine passing the secure sslmode flag explicitly
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "sslmode": "require"
        },
        echo=False
    )
else:
    # Local fallback file architecture
    SQLALCHEMY_DATABASE_URL = "sqlite:///./simulator.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)