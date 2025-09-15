from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from db import get_db
from models import User, Therapist
from schemas import UserCreate, UserResponse, TherapistResponse
from authenticate_utils import (
    generate_anonymous_username, 
    create_access_token, 
    authenticate_user, 
    authenticate_therapist,
    get_current_therapist,
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
    
    current_time = datetime.utcnow()
    user.last_login = current_time
    user.last_activity = current_time

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
            "college_name": user.college_name,
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
    }

@router.post("/therapist/login")
async def therapist_login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """Therapist login endpoint - accepts email or phone number"""
    therapist = authenticate_therapist(form_data.username, form_data.password, db)
    
    if not therapist:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/phone number or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not therapist.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )
    
    current_time = datetime.utcnow()
    # Note: You might want to add last_login field to Therapist model too
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(therapist.id), 
            "email": therapist.email,
            "type": "therapist"  # Add type to distinguish from regular users
        },
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "therapist": {
            "id": str(therapist.id),
            "name": therapist.name,
            "email": therapist.email,
            "phone_number": therapist.phone_number,
            "role": therapist.role.value,
            "college_name": therapist.college_name,
            "status": therapist.status.value,
            "is_on_call": therapist.is_on_call
        }
    }

@router.get("/therapist/me", response_model=TherapistResponse)
async def get_current_therapist_profile(
    current_therapist: Therapist = Depends(get_current_therapist)
):
    """Get current therapist profile"""
    return TherapistResponse(
        id=str(current_therapist.id),
        name=current_therapist.name,
        email=current_therapist.email,
        phone_number=current_therapist.phone_number,
        role=current_therapist.role.value,
        college_name=current_therapist.college_name,
        is_active=current_therapist.is_active,
        status=current_therapist.status.value,
        is_on_call=current_therapist.is_on_call,
        created_at=current_therapist.created_at,
        last_login=current_therapist.last_login
    )