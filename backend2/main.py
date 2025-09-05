from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from uuid import uuid4
import os
import json
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from pydub import AudioSegment

from schemas import UserCreate, UserResponse

from authenticate_utils import generate_anonymous_username, create_access_token, authenticate_user, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# Import database and models
from db import get_db, engine, Base
from models import (
    User, ChatSession, ChatMessage, CrisisAlert, TherapistSession,
    CommunityPost, Comment, UserMatch, UserAnalytics,
    RiskLevel, CrisisType, SessionStatus, PostStatus, MessageRole
)

# Import utility functions
from stt_utils import transcribe_audio
from vad_utils import is_speech

router = APIRouter()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
UPLOAD_FOLDER = "temp_audio"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database initialization
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
    yield
    logger.info("Application shutdown")

# Initialize FastAPI
app = FastAPI(
    title="TheraSage",
    description="AI-powered emotional support platform for college students",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== SIGN-UP AND LOGIN =====

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
    
    return new_user

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

# ===== SPEECH-TO-TEXT =====
@app.post("/stt/")
async def speech_to_text(file: UploadFile = File(...)):
    try:
        # Generate unique file path
        original_filename = file.filename
        base_filename = f"{uuid4().hex}_{original_filename}"
        filepath = os.path.join(UPLOAD_FOLDER, base_filename)

        # Save uploaded file
        with open(filepath, "wb") as f:
            content = await file.read()
            f.write(content)

        # Convert to WAV mono 16-bit 16kHz for VAD and Whisper
        wav_path = os.path.splitext(filepath)[0] + "_converted.wav"
        sound = AudioSegment.from_file(filepath)
        sound = sound.set_channels(1).set_frame_rate(16000).set_sample_width(2)
        sound.export(wav_path, format="wav")

        # Voice Activity Detection
        if not is_speech(wav_path):
            return JSONResponse({
                "text": "",
                "message": "No speech detected",
                "filename": base_filename
            })

        # Transcribe
        transcription = transcribe_audio(wav_path)

        return JSONResponse({
            "text": transcription,
            "message": "Speech transcribed successfully",
            "filename": base_filename
        })

    except Exception as e:
        return JSONResponse(
            {"error": "Failed to process audio", "details": str(e)},
            status_code=500
        )
    finally:
        # Clean up files
        for path in [filepath, wav_path]:
            if os.path.exists(path):
                os.remove(path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
