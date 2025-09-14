from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, status, APIRouter, WebSocket, Body
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text, and_, or_, desc, func
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
from crisis_alert_manager import CrisisAlertManager

# Import database and models
from db import get_db, engine, Base
from models import (
    User, ChatSession, ChatMessage, CrisisAlert, TherapistSession, Therapist, TherapistStatus,
    CommunityPost, Comment, UserMatch, UserAnalytics,
    RiskLevel, CrisisType, SessionStatus, PostStatus, MessageRole
)

# Import routes
from routes import sessions, messages, auth, crisis, therapist_dashboard, therapist_session, community, user_matching, peer_messaging

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
app.include_router(sessions.router)
app.include_router(messages.router)
app.include_router(auth.router)
app.include_router(crisis.router, prefix="/api/v1")
app.include_router(therapist_session.router, prefix="/api/v1")
app.include_router(therapist_dashboard.router, prefix="/api/v1")
app.include_router(community.router, prefix="/api/v1")
app.include_router(user_matching.router, prefix="/api/v1")
app.include_router(peer_messaging.router, prefix="/api/v1")
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
        
        # Enhanced response with crisis management info
        response_data = {
            "response": result["response"],
            "intervention": result["intervention_type"],
            "analysis": result.get("analysis", {}),
            "crisis_detected": result["crisis_detected"],
            "conversation_quality": "enhanced"
        }
        
        # Include crisis management results if present
        if result.get("crisis_alert_id"):
            response_data["crisis_management"] = {
                "crisis_alert_id": result["crisis_alert_id"],
                "assigned_therapist_id": result.get("assigned_therapist_id"),
                "therapist_session_id": result.get("therapist_session_id"),
                "auto_escalated": result.get("auto_escalated", False),
                "professional_help_contacted": True,
                "estimated_response_time": "30-60 minutes" if result.get("auto_escalated") else "2-4 hours"
            }

        logger.info(f"Response generated: {result['intervention_type']}, Crisis: {result['crisis_detected']}")
        
        # Log crisis management actions
        if result.get("crisis_alert_id"):
            logger.info(f"🚨 Crisis alert created: {result['crisis_alert_id']}")
            if result.get("assigned_therapist_id"):
                logger.info(f"👨‍⚕️ Therapist assigned: {result['assigned_therapist_id']}")
            if result.get("therapist_session_id"):
                logger.info(f"📅 Emergency session scheduled: {result['therapist_session_id']}")

        return response_data
    
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


# ===== CRISIS MANAGEMENT UTILITY ENDPOINTS =====

@app.get("/api/v1/crisis-system/status")
async def get_crisis_system_status(db: Session = Depends(get_db)):
    """Get overall crisis management system status"""
    
    crisis_manager = CrisisAlertManager(db)
    
    # Get system-wide statistics
    total_therapists = db.query(Therapist).filter(Therapist.is_active == True).count()
    active_therapists = db.query(Therapist).filter(
        and_(Therapist.is_active == True, Therapist.status == TherapistStatus.ACTIVE)
    ).count()
    
    # Get recent crisis activity
    last_24h = datetime.utcnow() - timedelta(hours=24)
    recent_crises = db.query(CrisisAlert).filter(
        CrisisAlert.detected_at >= last_24h
    ).count()
    
    pending_crises = db.query(CrisisAlert).filter(
        CrisisAlert.status == "pending"
    ).count()
    
    return {
        "system_status": "operational",
        "therapist_availability": {
            "total_therapists": total_therapists,
            "active_therapists": active_therapists,
            "availability_rate": round((active_therapists / total_therapists * 100) if total_therapists > 0 else 0, 2)
        },
        "crisis_activity": {
            "alerts_last_24h": recent_crises,
            "pending_alerts": pending_crises
        },
        "last_updated": datetime.utcnow()
    }

@app.get("/api/v1/crisis-system/colleges/{college_id}/overview")
async def get_college_crisis_overview(
    college_id: str, 
    db: Session = Depends(get_db)
):
    """Get crisis management overview for a specific college"""
    
    crisis_manager = CrisisAlertManager(db)
    availability_stats = crisis_manager.get_therapist_availability_stats(college_id)
    
    # Get college-specific crisis statistics
    college_crises = db.query(CrisisAlert).join(User).filter(
        User.college_id == college_id
    )
    
    total_crises = college_crises.count()
    pending_crises = college_crises.filter(CrisisAlert.status == "pending").count()
    critical_crises = college_crises.filter(
        and_(
            CrisisAlert.risk_level == RiskLevel.CRITICAL,
            CrisisAlert.status.in_(["pending", "acknowledged", "escalated"])
        )
    ).count()
    
    return {
        "college_id": college_id,
        "therapist_availability": availability_stats,
        "crisis_statistics": {
            "total_alerts": total_crises,
            "pending_alerts": pending_crises,
            "critical_alerts": critical_crises
        },
        "system_health": "good" if critical_crises == 0 and availability_stats["active_therapists"] > 0 else "attention_needed"
    }

@app.get("/api/v1/user-matching/overview/{user_id}")
async def get_user_matching_overview(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get comprehensive matching overview for a user
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get basic matching eligibility
    session_count = db.query(ChatSession).filter(
        and_(
            ChatSession.user_id == user_id,
            ChatSession.total_messages >= 3
        )
    ).count()
    
    eligible_for_matching = session_count > 0
    
    # Get existing matches count
    matches_count = db.query(UserMatch).filter(UserMatch.user_id == user_id).count()
    
    # Get connection statistics
    connected_count = db.query(UserMatch).filter(
        and_(
            UserMatch.user_id == user_id,
            UserMatch.connection_accepted == True
        )
    ).count()
    
    pending_count = db.query(UserMatch).filter(
        and_(
            UserMatch.user_id == user_id,
            UserMatch.connection_initiated == True,
            UserMatch.connection_accepted.is_(None)
        )
    ).count()
    
    return {
        "user_id": user_id,
        "matching_eligibility": {
            "eligible": eligible_for_matching,
            "conversation_sessions": session_count,
            "requirement": "At least one conversation with 3+ messages"
        },
        "matching_stats": {
            "total_matches": matches_count,
            "connected": connected_count,
            "pending_connections": pending_count
        },
        "next_steps": {
            "can_generate_matches": eligible_for_matching and matches_count < 10,
            "can_message_peers": connected_count > 0,
            "suggestions": [
                "Generate matches to find compatible peers" if eligible_for_matching else "Have more conversations to unlock matching",
                "Connect with your matches to start peer support",
                "Share your experiences in community posts"
            ]
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# to run "uvicorn main:app --reload --host 0.0.0.0 --port 8000"