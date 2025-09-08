from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, status, APIRouter, WebSocket, Body
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

from fastapi import WebSocket
from ai_agent import process_ai_conversation

from schemas import UserCreate, UserResponse

from authenticate_utils import generate_anonymous_username, create_access_token, authenticate_user, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# Import database and models
from db import get_db, engine, Base
from models import (
    User, ChatSession, ChatMessage, CrisisAlert, TherapistSession,
    CommunityPost, Comment, UserMatch, UserAnalytics,
    RiskLevel, CrisisType, SessionStatus, PostStatus, MessageRole
)

# Import routes
from routes import sessions, messages, auth

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

# Include routers
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(messages.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(router, prefix="/api/v1")


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

# ========== CHAT ===========

@app.post("/chat/{user_id}/{session_id}")
async def chat_api(
    user_id: str,
    session_id: str,
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    """
    Simple REST endpoint for user–AI chat.
    Expects JSON: {"message": "<user message>"}
    """
    message = payload.get("message", "")
    if not message:
        raise HTTPException(400, "Missing 'message' field")

    result = await process_ai_conversation(db, user_id, session_id, message)

    return {
        "response": result["response"],
        "intervention": result["intervention_type"],
        "analysis": result["analysis"],
        "crisis_detected": result["crisis_detected"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# to run "uvicorn main:app --reload --host 0.0.0.0 --port 8000"
