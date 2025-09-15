# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL - Use environment variables in production
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./emotional_support_db.db")

# Create engine with appropriate configuration based on database type
if "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        echo=False,  # Set to True for SQL query debugging
        connect_args={"check_same_thread": False}
    )
elif "postgresql" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        echo=False,  # Set to True for SQL query debugging
        connect_args={"options": "-c timezone=utc"}
    )
else:
    # Default fallback
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
