from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from db import get_db
from models import User
from schemas import UserCreate, UserResponse
from authenticate_utils import (
    generate_anonymous_username, 
    create_access_token, 
    authenticate_user, 
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from werkzeug.security import generate_password_hash

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """User registration endpoint"""
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Generate unique anonymous username
    while True:
        username = generate_anonymous_username()
        if not db.query(User).filter(User.anonymous_username == username).first():
            break

    # Create new user
    hashed_password = generate_password_hash(user_data.password)
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hashed_password,
        anonymous_username=username,
        college_id=user_data.college_id,
        college_name=user_data.college_name,
        privacy_settings={
            "show_activity_status": False,
            "allow_matching": True,
            "data_retention_days": 365
        },
        notification_preferences={
            "crisis_alerts": True,
            "session_reminders": True,
            "community_updates": False
        }
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "id": str(new_user.id),
        "name": new_user.name,
        "email": new_user.email,
        "anonymous_username": new_user.anonymous_username,
        "college_name": new_user.college_name,
        "is_active": new_user.is_active,
        "created_at": new_user.created_at,
        "last_login": new_user.last_login,
    }

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """User login endpoint - accepts email or username"""
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )

    # Update last login timestamp
    user.last_login = datetime.utcnow()
    db.commit()

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "anonymous_username": user.anonymous_username,
            "college_name": user.college_name
        }
    }
