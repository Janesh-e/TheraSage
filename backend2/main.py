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
    
    # Run migration for enhanced features
    try:
        from database_migration import add_summary_features
        add_summary_features()
        logger.info("Enhanced features migration completed")
    except Exception as e:
        logger.warning(f"Migration warning: {e}")
    
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

# ========== ENHANCED CHAT ===========
@app.post("/chat/{user_id}/{session_id}")
async def chat_api(
    user_id: str,
    session_id: str,
    payload: dict = Body(...),
    db: Session = Depends(get_db)
):
    """
    Enhanced REST endpoint for user–AI chat with natural conversation flow.
    Expects JSON: {"message": ""}
    """
    message = payload.get("message", "")
    if not message:
        raise HTTPException(400, "Missing 'message' field")
    
    # Add request logging for better debugging
    logger.info(f"Chat request from user {user_id[:8]}... in session {session_id[:8]}...")
    
    try:
        # Process through enhanced AI agent
        result = await process_ai_conversation(db, user_id, session_id, message)
        
        # Log response quality for monitoring
        logger.info(f"Response generated: {result['intervention_type']}, "
                   f"Crisis: {result['crisis_detected']}")
        
        return {
            "response": result["response"],
            "intervention": result["intervention_type"],
            "analysis": result.get("analysis", {}),
            "crisis_detected": result["crisis_detected"],
            "conversation_quality": "enhanced"  # Indicator of new system
        }
    
    except Exception as e:
        logger.error(f"Chat processing error: {e}")
        # Fallback response
        return {
            "response": "I'm here to help. Could you tell me a bit more about what's on your mind?",
            "intervention": "fallback",
            "analysis": {},
            "crisis_detected": False,
            "error": "fallback_response"
        }

# ===== SESSION SUMMARY ENDPOINT =====
@app.get("/api/v1/sessions/{session_id}/summary")
async def get_session_summary(
    session_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get session summary for user review"""
    # Verify session belongs to user
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id
    ).first()
    
    if not session:
        raise HTTPException(404, "Session not found or access denied")
    
    return {
        "session_id": session_id,
        "summary": session.conversation_summary,
        "message_count": session.total_messages,
        "last_updated": session.updated_at,
        "risk_level": session.current_risk_level.value if session.current_risk_level else "low"
    }

# ===== CONVERSATION INSIGHTS ENDPOINT =====
@app.get("/api/v1/users/{user_id}/insights")
async def get_user_insights(
    user_id: str,
    db: Session = Depends(get_db),
    limit: int = 5
):
    """Get user's conversation insights across sessions"""
    # Get recent sessions with summaries
    recent_sessions = db.query(ChatSession).filter(
        ChatSession.user_id == user_id,
        ChatSession.conversation_summary.isnot(None)
    ).order_by(ChatSession.last_message_at.desc()).limit(limit).all()
    
    if not recent_sessions:
        return {
            "insights": [],
            "total_sessions": 0,
            "message": "No conversation history available yet"
        }
    
    insights = []
    for session in recent_sessions:
        insights.append({
            "session_id": str(session.id),
            "title": session.title,
            "summary": session.conversation_summary,
            "date": session.last_message_at,
            "message_count": session.total_messages,
            "risk_level": session.current_risk_level.value if session.current_risk_level else "low"
        })
    
    return {
        "insights": insights,
        "total_sessions": len(recent_sessions),
        "message": "Conversation insights generated successfully"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# to run "uvicorn main:app --reload --host 0.0.0.0 --port 8000"