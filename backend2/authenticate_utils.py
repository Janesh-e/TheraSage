import random
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from typing import Union
import jwt
import os
from dotenv import load_dotenv

from sqlalchemy.orm import Session
from db import get_db
from models import User
from schemas import UserCreate, UserResponse

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")  # fallback if missing
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

def generate_anonymous_username() -> str:
    """Generate Reddit-style anonymous username"""
    adjectives = ["thoughtful", "calm", "brave", "kind", "peaceful", "gentle", "strong", "wise", "hopeful", "bright"]
    animals = ["owl", "deer", "fox", "bear", "rabbit", "wolf", "eagle", "dolphin", "panda", "lion"]
    adjective = random.choice(adjectives)
    animal = random.choice(animals)
    number = random.randint(100, 9999)
    return f"{adjective}_{animal}_{number}"

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(identifier: str, password: str, db: Session):
    """Authenticate user with email or username"""
    # Try to find user by email first
    user = db.query(User).filter(User.email == identifier).first()
    
    # If not found by email, try by anonymous username
    if not user:
        user = db.query(User).filter(User.anonymous_username == identifier).first()
    
    if not user:
        return False
    
    if not check_password_hash(user.password_hash, password):
        return False
    
    return user