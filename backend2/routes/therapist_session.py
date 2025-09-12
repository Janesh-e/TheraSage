from fastapi import APIRouter, HTTPException, Depends, status, Query, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from db import get_db
from models import (
    TherapistSession, User, CrisisAlert, ChatSession,
    RiskLevel, SessionStatus, CrisisType
)

from pydantic import BaseModel

router = APIRouter(
    prefix="/therapist-sessions",
    tags=["therapist-sessions"],
)

# Pydantic models
class TherapistSessionCreate(BaseModel):
    user_id: str
    crisis_alert_id: Optional[str] = None
    session_type: str = "crisis"  # crisis, regular, follow_up, group
    urgency_level: str = "high"  # low, medium, high, critical
    scheduled_for: Optional[datetime] = None
    duration_minutes: int = 50
    meeting_type: str = "online"  # online, offline, phone
    notes: Optional[str] = None

class TherapistSessionResponse(BaseModel):
    id: str
    user_id: str
    crisis_alert_id: Optional[str]
    session_type: str
    urgency_level: str
    status: str
    requested_at: datetime
    scheduled_for: Optional[datetime]
    duration_minutes: int
    meeting_link: Optional[str]
    session_notes: Optional[str]
    attended: Optional[bool]
    follow_up_needed: bool
    user_info: Optional[Dict[str, Any]] = None
    crisis_info: Optional[Dict[str, Any]] = None

class SessionScheduleRequest(BaseModel):
    scheduled_for: datetime
    duration_minutes: int = 50
    meeting_type: str = "online"  # online, offline, phone
    meeting_location: Optional[str] = None
    notes: Optional[str] = None

class SessionUpdateRequest(BaseModel):
    status: Optional[str] = None
    attended: Optional[bool] = None
    session_notes: Optional[str] = None
    follow_up_needed: Optional[bool] = None
    next_session_recommended: Optional[datetime] = None

# ===== THERAPIST SESSION CREATION =====

@router.post("/", response_model=TherapistSessionResponse)
async def create_therapist_session(
    session_data: TherapistSessionCreate,
    therapist_id: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Create a new therapist session"""
    
    # Verify user exists
    user = db.query(User).filter(User.id == session_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify crisis alert if provided
    crisis_alert = None
    if session_data.crisis_alert_id:
        crisis_alert = db.query(CrisisAlert).filter(
            CrisisAlert.id == session_data.crisis_alert_id
        ).first()
        if not crisis_alert:
            raise HTTPException(status_code=404, detail="Crisis alert not found")
    
    current_time = datetime.utcnow()
    
    # Convert urgency level to enum
    try:
        urgency_enum = RiskLevel(session_data.urgency_level)
    except ValueError:
        urgency_enum = RiskLevel.HIGH
    
    # Create therapist session
    therapist_session = TherapistSession(
        user_id=session_data.user_id,
        crisis_alert_id=session_data.crisis_alert_id,
        session_type=session_data.session_type,
        urgency_level=urgency_enum,
        requested_at=current_time,
        scheduled_for=session_data.scheduled_for,
        duration_minutes=session_data.duration_minutes,
        status=SessionStatus.SCHEDULED,
        follow_up_needed=False
    )
    
    # Generate meeting link for online sessions
    if session_data.session_type == "online" or session_data.get("meeting_type") == "online":
        # Generate a secure meeting link (implement your video calling solution)
        meeting_id = str(therapist_session.id)[:8]
        therapist_session.meeting_link = f"https://meet.therasage.com/session/{meeting_id}"
    
    db.add(therapist_session)
    
    # Update crisis alert if linked
    if crisis_alert:
        crisis_alert.status = "escalated"
        crisis_alert.escalated_to_human = True
        crisis_alert.response_actions = {
            "therapist_session_created": current_time.isoformat(),
            "therapist_id": therapist_id,
            "session_type": session_data.session_type
        }
    
    db.commit()
    db.refresh(therapist_session)
    
    # Prepare response
    user_info = {
        "anonymous_username": user.anonymous_username,
        "college_name": user.college_name,
        "last_activity": user.last_activity
    }
    
    crisis_info = None
    if crisis_alert:
        crisis_info = {
            "crisis_type": crisis_alert.crisis_type.value,
            "risk_level": crisis_alert.risk_level.value,
            "confidence_score": crisis_alert.confidence_score,
            "detected_at": crisis_alert.detected_at
        }
    
    return TherapistSessionResponse(
        id=str(therapist_session.id),
        user_id=str(therapist_session.user_id),
        crisis_alert_id=str(therapist_session.crisis_alert_id) if therapist_session.crisis_alert_id else None,
        session_type=therapist_session.session_type,
        urgency_level=therapist_session.urgency_level.value,
        status=therapist_session.status.value,
        requested_at=therapist_session.requested_at,
        scheduled_for=therapist_session.scheduled_for,
        duration_minutes=therapist_session.duration_minutes,
        meeting_link=therapist_session.meeting_link,
        session_notes=therapist_session.session_notes,
        attended=therapist_session.attended,
        follow_up_needed=therapist_session.follow_up_needed,
        user_info=user_info,
        crisis_info=crisis_info
    )

@router.post("/from-crisis/{crisis_alert_id}")
async def create_session_from_crisis(
    crisis_alert_id: UUID,
    session_request: SessionScheduleRequest,
    therapist_id: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Create therapist session directly from a crisis alert"""
    
    crisis_alert = db.query(CrisisAlert).options(
        joinedload(CrisisAlert.user)
    ).filter(CrisisAlert.id == crisis_alert_id).first()
    
    if not crisis_alert:
        raise HTTPException(status_code=404, detail="Crisis alert not found")
    
    # Check if session already exists for this crisis
    existing_session = db.query(TherapistSession).filter(
        TherapistSession.crisis_alert_id == crisis_alert_id
    ).first()
    
    if existing_session:
        raise HTTPException(
            status_code=400, 
            detail="Therapist session already exists for this crisis alert"
        )
    
    current_time = datetime.utcnow()
    
    # Determine urgency based on crisis risk level
    urgency_mapping = {
        RiskLevel.CRITICAL: RiskLevel.CRITICAL,
        RiskLevel.HIGH: RiskLevel.HIGH,
        RiskLevel.MEDIUM: RiskLevel.MEDIUM,
        RiskLevel.LOW: RiskLevel.LOW
    }
    
    therapist_session = TherapistSession(
        user_id=crisis_alert.user_id,
        crisis_alert_id=crisis_alert.id,
        session_type="crisis",
        urgency_level=urgency_mapping.get(crisis_alert.risk_level, RiskLevel.HIGH),
        requested_at=current_time,
        scheduled_for=session_request.scheduled_for,
        duration_minutes=session_request.duration_minutes,
        status=SessionStatus.SCHEDULED,
        follow_up_needed=False
    )
    
    # Generate meeting link based on type
    if session_request.meeting_type == "online":
        meeting_id = str(crisis_alert.id)[:8]
        therapist_session.meeting_link = f"https://meet.therasage.com/crisis/{meeting_id}"
    elif session_request.meeting_type == "offline":
        therapist_session.meeting_link = f"Office Location: {session_request.meeting_location or 'TBD'}"
    
    db.add(therapist_session)
    
    # Update crisis alert
    crisis_alert.status = "escalated"
    crisis_alert.escalated_to_human = True
    crisis_alert.response_actions = {
        "session_scheduled_at": current_time.isoformat(),
        "scheduled_for": session_request.scheduled_for.isoformat(),
        "therapist_id": therapist_id,
        "meeting_type": session_request.meeting_type
    }
    
    db.commit()
    
    return {
        "message": "Therapist session scheduled successfully",
        "session_id": str(therapist_session.id),
        "scheduled_for": session_request.scheduled_for,
        "meeting_link": therapist_session.meeting_link,
        "crisis_alert_status": "escalated"
    }

# ===== THERAPIST SESSION MANAGEMENT =====

@router.get("/", response_model=List[TherapistSessionResponse])
async def get_therapist_sessions(
    db: Session = Depends(get_db),
    therapist_id: Optional[str] = Query(None),
    college_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    session_type: Optional[str] = Query(None),
    days_ahead: int = Query(7, description="Look ahead days for scheduled sessions"),
    limit: int = Query(50, le=100),
    skip: int = Query(0)
):
    """Get therapist sessions with filtering options"""
    
    query = db.query(TherapistSession).options(
        joinedload(TherapistSession.user),
        joinedload(TherapistSession.crisis_alert)
    )
    
    # Apply filters
    if therapist_id:
        # Filter by external therapist ID when available
        query = query.filter(TherapistSession.external_therapist_id == therapist_id)
    
    if college_id:
        query = query.join(User).filter(User.college_id == college_id)
    
    if status:
        query = query.filter(TherapistSession.status == SessionStatus(status))
    
    if session_type:
        query = query.filter(TherapistSession.session_type == session_type)
    
    # Filter by upcoming sessions
    end_date = datetime.utcnow() + timedelta(days=days_ahead)
    query = query.filter(
        or_(
            TherapistSession.scheduled_for.between(datetime.utcnow(), end_date),
            TherapistSession.scheduled_for.is_(None),
            TherapistSession.status.in_([SessionStatus.IN_PROGRESS, SessionStatus.SCHEDULED])
        )
    )
    
    sessions = query.order_by(
        TherapistSession.urgency_level.desc(),
        TherapistSession.scheduled_for.asc()
    ).offset(skip).limit(limit).all()
    
    # Format response
    response_sessions = []
    for session in sessions:
        user_info = None
        crisis_info = None
        
        if session.user:
            user_info = {
                "anonymous_username": session.user.anonymous_username,
                "college_name": session.user.college_name,
                "last_activity": session.user.last_activity
            }
        
        if session.crisis_alert:
            crisis_info = {
                "crisis_type": session.crisis_alert.crisis_type.value,
                "risk_level": session.crisis_alert.risk_level.value,
                "detected_indicators": session.crisis_alert.detected_indicators or [],
                "detected_at": session.crisis_alert.detected_at
            }
        
        response_sessions.append(TherapistSessionResponse(
            id=str(session.id),
            user_id=str(session.user_id),
            crisis_alert_id=str(session.crisis_alert_id) if session.crisis_alert_id else None,
            session_type=session.session_type,
            urgency_level=session.urgency_level.value,
            status=session.status.value,
            requested_at=session.requested_at,
            scheduled_for=session.scheduled_for,
            duration_minutes=session.duration_minutes,
            meeting_link=session.meeting_link,
            session_notes=session.session_notes,
            attended=session.attended,
            follow_up_needed=session.follow_up_needed,
            user_info=user_info,
            crisis_info=crisis_info
        ))
    
    return response_sessions

@router.get("/{session_id}", response_model=TherapistSessionResponse)
async def get_therapist_session(
    session_id: UUID,
    db: Session = Depends(get_db)
):
    """Get detailed therapist session information"""
    
    session = db.query(TherapistSession).options(
        joinedload(TherapistSession.user),
        joinedload(TherapistSession.crisis_alert)
    ).filter(TherapistSession.id == session_id).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Therapist session not found")
    
    # Get additional context from chat session
    chat_context = None
    if session.crisis_alert and session.crisis_alert.session_id:
        chat_session = db.query(ChatSession).filter(
            ChatSession.id == session.crisis_alert.session_id
        ).first()
        
        if chat_session:
            chat_context = {
                "session_title": chat_session.title,
                "total_messages": chat_session.total_messages,
                "risk_score": chat_session.risk_score,
                "conversation_summary": chat_session.conversation_summary
            }
    
    user_info = None
    crisis_info = None
    
    if session.user:
        user_info = {
            "anonymous_username": session.user.anonymous_username,
            "college_name": session.user.college_name,
            "created_at": session.user.created_at,
            "last_activity": session.user.last_activity,
            "chat_context": chat_context
        }
    
    if session.crisis_alert:
        crisis_info = {
            "crisis_type": session.crisis_alert.crisis_type.value,
            "risk_level": session.crisis_alert.risk_level.value,
            "confidence_score": session.crisis_alert.confidence_score,
            "detected_indicators": session.crisis_alert.detected_indicators or [],
            "trigger_message": session.crisis_alert.trigger_message,
            "detected_at": session.crisis_alert.detected_at
        }
    
    return TherapistSessionResponse(
        id=str(session.id),
        user_id=str(session.user_id),
        crisis_alert_id=str(session.crisis_alert_id) if session.crisis_alert_id else None,
        session_type=session.session_type,
        urgency_level=session.urgency_level.value,
        status=session.status.value,
        requested_at=session.requested_at,
        scheduled_for=session.scheduled_for,
        duration_minutes=session.duration_minutes,
        meeting_link=session.meeting_link,
        session_notes=session.session_notes,
        attended=session.attended,
        follow_up_needed=session.follow_up_needed,
        user_info=user_info,
        crisis_info=crisis_info
    )

# ===== SESSION STATUS UPDATES =====

@router.put("/{session_id}/start")
async def start_therapist_session(
    session_id: UUID,
    therapist_id: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Mark therapist session as in progress"""
    
    session = db.query(TherapistSession).filter(TherapistSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Therapist session not found")
    
    if session.status != SessionStatus.SCHEDULED:
        raise HTTPException(status_code=400, detail="Session is not in scheduled status")
    
    current_time = datetime.utcnow()
    session.status = SessionStatus.IN_PROGRESS
    session.external_therapist_id = therapist_id
    
    db.commit()
    
    return {
        "message": "Session started successfully",
        "session_id": str(session_id),
        "status": "in_progress",
        "started_at": current_time
    }

@router.put("/{session_id}/complete")
async def complete_therapist_session(
    session_id: UUID,
    completion_data: SessionUpdateRequest,
    db: Session = Depends(get_db)
):
    """Mark therapist session as completed with notes"""
    
    session = db.query(TherapistSession).filter(TherapistSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Therapist session not found")
    
    current_time = datetime.utcnow()
    
    # Update session
    session.status = SessionStatus.COMPLETED
    session.completed_at = current_time
    session.attended = completion_data.attended if completion_data.attended is not None else True
    session.session_notes = completion_data.session_notes
    session.follow_up_needed = completion_data.follow_up_needed or False
    session.next_session_recommended = completion_data.next_session_recommended
    
    # Update linked crisis alert
    if session.crisis_alert_id:
        crisis_alert = db.query(CrisisAlert).filter(
            CrisisAlert.id == session.crisis_alert_id
        ).first()
        
        if crisis_alert and crisis_alert.status != "resolved":
            crisis_alert.status = "resolved"
            crisis_alert.resolved_at = current_time
            crisis_alert.resolution_notes = f"Resolved through therapist session. Follow-up needed: {session.follow_up_needed}"
    
    db.commit()
    
    return {
        "message": "Session completed successfully",
        "session_id": str(session_id),
        "status": "completed",
        "completed_at": current_time,
        "follow_up_needed": session.follow_up_needed
    }

@router.put("/{session_id}/cancel")
async def cancel_therapist_session(
    session_id: UUID,
    cancellation_reason: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Cancel a therapist session"""
    
    session = db.query(TherapistSession).filter(TherapistSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Therapist session not found")
    
    if session.status in [SessionStatus.COMPLETED, SessionStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Session cannot be cancelled")
    
    current_time = datetime.utcnow()
    
    session.status = SessionStatus.CANCELLED
    session.cancelled_at = current_time
    session.session_notes = f"Cancelled: {cancellation_reason}"
    
    db.commit()
    
    return {
        "message": "Session cancelled successfully",
        "session_id": str(session_id),
        "status": "cancelled",
        "cancelled_at": current_time
    }

# ===== SESSION ANALYTICS =====

@router.get("/stats/therapist/{therapist_id}")
async def get_therapist_session_stats(
    therapist_id: str,
    days_back: int = Query(30, le=365),
    db: Session = Depends(get_db)
):
    """Get session statistics for a specific therapist"""
    
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
    
    base_query = db.query(TherapistSession).filter(
        and_(
            TherapistSession.external_therapist_id == therapist_id,
            TherapistSession.requested_at >= cutoff_date
        )
    )
    
    total_sessions = base_query.count()
    completed_sessions = base_query.filter(TherapistSession.status == SessionStatus.COMPLETED).count()
    cancelled_sessions = base_query.filter(TherapistSession.status == SessionStatus.CANCELLED).count()
    no_show_sessions = base_query.filter(TherapistSession.attended == False).count()
    
    # Crisis sessions
    crisis_sessions = base_query.filter(TherapistSession.session_type == "crisis").count()
    
    # Average session duration (for completed sessions)
    avg_duration = db.query(func.avg(TherapistSession.duration_minutes)).filter(
        and_(
            TherapistSession.external_therapist_id == therapist_id,
            TherapistSession.status == SessionStatus.COMPLETED,
            TherapistSession.requested_at >= cutoff_date
        )
    ).scalar()
    
    return {
        "therapist_id": therapist_id,
        "period_days": days_back,
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "cancelled_sessions": cancelled_sessions,
        "no_show_sessions": no_show_sessions,
        "crisis_sessions": crisis_sessions,
        "completion_rate": round((completed_sessions / total_sessions * 100) if total_sessions > 0 else 0, 2),
        "average_duration_minutes": round(avg_duration or 0, 1)
    }