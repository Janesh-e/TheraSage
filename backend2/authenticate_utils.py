import random
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from typing import Union
import jwt
import os
from dotenv import load_dotenv
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sqlalchemy.orm import Session
from db import get_db
from models import User
from schemas import UserCreate, UserResponse

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")  # fallback if missing
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Security scheme for JWT
security = HTTPBearer()

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

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(
    db: Session = Depends(get_db),
    user_id: str = Depends(verify_token)
) -> User:
    """Get current authenticated user"""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


def authenticate_therapist(identifier: str, password: str, db: Session):
    """Authenticate therapist with email or phone number"""
    from models import Therapist  # Import here to avoid circular imports
    
    # Try to find therapist by email first
    therapist = db.query(Therapist).filter(Therapist.email == identifier).first()
    
    # If not found by email, try by phone number
    if not therapist:
        therapist = db.query(Therapist).filter(Therapist.phone_number == identifier).first()
    
    if not therapist:
        return False
    
    if not check_password_hash(therapist.password_hash, password):
        return False
    
    return therapist

async def get_current_therapist(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated therapist"""
    token = credentials.credentials
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate therapist credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        user_type: str = payload.get("type")
        
        if user_id is None or user_type != "therapist":
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    # Import here to avoid circular imports
    from models import Therapist
    
    therapist = db.query(Therapist).filter(Therapist.id == user_id).first()
    if therapist is None:
        raise credentials_exception
    
    if not therapist.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Therapist account is deactivated"
        )
    
    return therapist