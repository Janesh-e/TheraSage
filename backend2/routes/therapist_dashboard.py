from fastapi import APIRouter, HTTPException, Depends, status, Query, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from uuid import UUID

from db import get_db
from models import (
    CrisisAlert, User, ChatSession, Therapist, TherapistSession,
    RiskLevel, CrisisType, SessionStatus, TherapistStatus, TherapistRole
)
from crisis_alert_manager import CrisisAlertManager
from pydantic import BaseModel

router = APIRouter(
    prefix="/therapist-dashboard",
    tags=["therapist-dashboard"],
)

# Pydantic models
class TherapistDashboardStats(BaseModel):
    """Dashboard statistics for therapist overview"""
    active_crisis_alerts: int
    pending_sessions: int
    completed_sessions_today: int
    high_priority_cases: int
    workload_score: int
    availability_status: str
    next_session: Optional[Dict[str, Any]] = None

class CrisisWorklistItem(BaseModel):
    """Crisis alert item for therapist worklist"""
    id: str
    user_anonymous: str
    crisis_type: str
    risk_level: str
    status: str
    detected_at: datetime
    hours_since_detection: float
    confidence_score: float
    has_session_scheduled: bool
    user_college: str
    trigger_message: Optional[str] = None
    detected_indicators: Optional[Dict[str, Any]] = None
    risk_factors: Optional[List[str]] = None
    main_concerns: Optional[List[str]] = None
    cognitive_distortions: Optional[List[str]] = None
    urgency_level: Optional[int] = None

# ===== THERAPIST DASHBOARD OVERVIEW =====

@router.get("/overview/{therapist_id}", response_model=TherapistDashboardStats)
async def get_therapist_dashboard_overview(
    therapist_id: UUID,
    db: Session = Depends(get_db)
):
    """Get comprehensive dashboard overview for a therapist"""
    
    # Verify therapist exists
    therapist = db.query(Therapist).filter(Therapist.id == therapist_id).first()
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    current_time = datetime.utcnow()
    today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Active crisis alerts assigned to this therapist
    active_crisis_count = db.query(CrisisAlert).filter(
        and_(
            CrisisAlert.assigned_therapist_id == therapist_id,
            CrisisAlert.status.in_(["pending", "acknowledged", "escalated"])
        )
    ).count()
    
    # Pending therapist sessions
    pending_sessions_count = db.query(TherapistSession).filter(
        and_(
            TherapistSession.external_therapist_id == str(therapist_id),
            TherapistSession.status == SessionStatus.SCHEDULED,
            TherapistSession.scheduled_for >= current_time
        )
    ).count()
    
    # Completed sessions today
    completed_today_count = db.query(TherapistSession).filter(
        and_(
            TherapistSession.external_therapist_id == str(therapist_id),
            TherapistSession.status == SessionStatus.COMPLETED,
            TherapistSession.completed_at >= today_start
        )
    ).count()
    
    # High priority cases (critical and high risk)
    high_priority_count = db.query(CrisisAlert).filter(
        and_(
            CrisisAlert.assigned_therapist_id == therapist_id,
            CrisisAlert.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL]),
            CrisisAlert.status.in_(["pending", "acknowledged", "escalated"])
        )
    ).count()
    
    # Calculate workload score
    in_progress_sessions = db.query(TherapistSession).filter(
        and_(
            TherapistSession.external_therapist_id == str(therapist_id),
            TherapistSession.status == SessionStatus.IN_PROGRESS
        )
    ).count()
    
    workload_score = (active_crisis_count * 2) + pending_sessions_count + (in_progress_sessions * 3)
    
    # Get next scheduled session
    next_session = db.query(TherapistSession).filter(
        and_(
            TherapistSession.external_therapist_id == str(therapist_id),
            TherapistSession.status == SessionStatus.SCHEDULED,
            TherapistSession.scheduled_for >= current_time
        )
    ).order_by(TherapistSession.scheduled_for.asc()).first()
    
    next_session_info = None
    if next_session:
        next_session_info = {
            "id": str(next_session.id),
            "scheduled_for": next_session.scheduled_for,
            "session_type": next_session.session_type,
            "urgency_level": next_session.urgency_level.value,
            "duration_minutes": next_session.duration_minutes,
            "meeting_link": next_session.meeting_link
        }
    
    return TherapistDashboardStats(
        active_crisis_alerts=active_crisis_count,
        pending_sessions=pending_sessions_count,
        completed_sessions_today=completed_today_count,
        high_priority_cases=high_priority_count,
        workload_score=workload_score,
        availability_status=therapist.status.value,
        next_session=next_session_info
    )

@router.get("/crisis-worklist/{therapist_id}", response_model=List[CrisisWorklistItem])
async def get_therapist_crisis_worklist(
    therapist_id: UUID,
    db: Session = Depends(get_db),
    status_filter: Optional[str] = Query(None),
    risk_filter: Optional[str] = Query(None),
    limit: int = Query(25, le=100)
):
    """Get prioritized crisis worklist for a therapist"""
    
    query = db.query(CrisisAlert).options(
        joinedload(CrisisAlert.user)
    ).filter(CrisisAlert.assigned_therapist_id == therapist_id)
    
    # Apply filters
    if status_filter:
        query = query.filter(CrisisAlert.status == status_filter)
    else:
        # Default: show active cases only
        query = query.filter(CrisisAlert.status.in_(["pending", "acknowledged", "escalated"]))
    
    if risk_filter:
        query = query.filter(CrisisAlert.risk_level == RiskLevel(risk_filter))
    
    # Order by priority: critical first, then by detection time
    crisis_alerts = query.order_by(
        CrisisAlert.risk_level.desc(),
        CrisisAlert.detected_at.desc()
    ).limit(limit).all()
    
    # Format response
    worklist_items = []
    for alert in crisis_alerts:
        
        # Check if session is scheduled for this crisis
        has_session = db.query(TherapistSession).filter(
            TherapistSession.crisis_alert_id == alert.id
        ).first() is not None
        
        hours_since = (datetime.now(timezone.utc) - alert.detected_at).total_seconds() / 3600

        # Extract data from detected_indicators JSON
        detected_indicators = alert.detected_indicators or {}
        risk_factors = detected_indicators.get("risk_factors", [])
        main_concerns = detected_indicators.get("main_concerns", [])
        cognitive_distortions = detected_indicators.get("cognitive_distortions", [])
        urgency_level = detected_indicators.get("urgency_level")
        
        worklist_items.append(CrisisWorklistItem(
            id=str(alert.id),
            user_anonymous=alert.user.anonymous_username if alert.user else "Unknown",
            crisis_type=alert.crisis_type.value,
            risk_level=alert.risk_level.value,
            status=alert.status,
            detected_at=alert.detected_at,
            hours_since_detection=round(hours_since, 2),
            confidence_score=round(alert.confidence_score / 10.0, 2),
            has_session_scheduled=has_session,
            user_college=alert.user.college_name if alert.user else "Unknown",
            trigger_message=alert.trigger_message,
            detected_indicators=detected_indicators,
            risk_factors=risk_factors,
            main_concerns=main_concerns,
            cognitive_distortions=cognitive_distortions,
            urgency_level=urgency_level
        ))
    
    return worklist_items

@router.get("/session-schedule/{therapist_id}")
async def get_therapist_session_schedule(
    therapist_id: UUID,
    days_ahead: int = Query(7, le=30),
    db: Session = Depends(get_db)
):
    """Get therapist's upcoming session schedule"""
    
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(days=days_ahead)
    
    sessions = db.query(TherapistSession).options(
        joinedload(TherapistSession.user),
        joinedload(TherapistSession.crisis_alert)
    ).filter(
        and_(
            TherapistSession.external_therapist_id == str(therapist_id),
            TherapistSession.scheduled_for.between(start_time, end_time),
            TherapistSession.status.in_([SessionStatus.SCHEDULED, SessionStatus.IN_PROGRESS])
        )
    ).order_by(TherapistSession.scheduled_for.asc()).all()
    
    schedule = []
    for session in sessions:
        user_info = {
            "anonymous_username": session.user.anonymous_username if session.user else "Unknown",
            "college_name": session.user.college_name if session.user else "Unknown"
        }
        
        crisis_info = None
        if session.crisis_alert:
            crisis_info = {
                "crisis_type": session.crisis_alert.crisis_type.value,
                "risk_level": session.crisis_alert.risk_level.value
            }
        
        schedule.append({
            "id": str(session.id),
            "scheduled_for": session.scheduled_for,
            "duration_minutes": session.duration_minutes,
            "session_type": session.session_type,
            "urgency_level": session.urgency_level.value,
            "status": session.status.value,
            "meeting_link": session.meeting_link,
            "user_info": user_info,
            "crisis_info": crisis_info
        })
    
    return {
        "therapist_id": str(therapist_id),
        "schedule_period": f"{days_ahead} days",
        "total_sessions": len(schedule),
        "sessions": schedule
    }

# ===== CRISIS ALERT ACTIONS =====

@router.post("/crisis/{alert_id}/quick-response")
async def send_quick_crisis_response(
    alert_id: UUID,
    request_data: Dict[str, Any] = Body(...), 
    db: Session = Depends(get_db)
):
    """Send quick response to crisis alert"""
    # Extract therapist_id from the request data
    therapist_id = request_data.get("therapist_id")
    if not therapist_id:
        raise HTTPException(status_code=400, detail="therapist_id is required")
    
    # Convert to UUID
    try:
        therapist_id = UUID(therapist_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid therapist_id format")
    
    crisis_alert = db.query(CrisisAlert).filter(CrisisAlert.id == alert_id).first()
    if not crisis_alert:
        raise HTTPException(status_code=404, detail="Crisis alert not found")

    if crisis_alert.assigned_therapist_id != therapist_id:
        raise HTTPException(status_code=403, detail="Not authorized for this crisis alert")

    response_type = request_data.get("response_type")  # Get from request_data
    current_time = datetime.utcnow()

    if response_type == "acknowledge":
        if crisis_alert.status == "acknowledged":
            raise HTTPException(status_code=400, detail="Alert already acknowledged")

        crisis_alert.status = "acknowledged"
        crisis_alert.acknowledged_at = current_time

        # Update response actions
        crisis_alert.response_actions = crisis_alert.response_actions or {}
        crisis_alert.response_actions.update({
            "quick_acknowledged_at": current_time.isoformat(),
            "therapist_notes": request_data.get("notes", "")  # Get from request_data
        })

    elif response_type == "schedule_session":
        # Create therapist session
        scheduled_for_str = request_data.get("scheduled_for")  # Get from request_data
        if not scheduled_for_str:
            raise HTTPException(status_code=400, detail="scheduled_for is required")

        # Parse the datetime string
        try:
            scheduled_for = datetime.fromisoformat(scheduled_for_str.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid datetime format")

        therapist_session = TherapistSession(
            user_id=crisis_alert.user_id,
            crisis_alert_id=crisis_alert.id,
            session_type=request_data.get("session_type", "crisis"),  # Get from request_data
            urgency_level=crisis_alert.risk_level,
            requested_at=current_time,
            scheduled_for=scheduled_for,
            duration_minutes=request_data.get("duration_minutes", 50),  # Get from request_data
            status=SessionStatus.SCHEDULED,
            external_therapist_id=str(therapist_id),
            meeting_link=f"https://meet.therasage.com/crisis/{str(alert_id)[:8]}"
        )

        db.add(therapist_session)

        # Update crisis alert
        crisis_alert.status = "escalated"
        crisis_alert.escalated_to_human = True
        crisis_alert.response_actions = crisis_alert.response_actions or {}
        crisis_alert.response_actions.update({
            "session_scheduled_at": current_time.isoformat(),
            "session_scheduled_for": scheduled_for.isoformat(),
            "session_id": str(therapist_session.id)
        })

    db.commit()

    return {
        "message": f"Crisis alert {response_type} successful",
        "alert_id": str(alert_id),
        "status": crisis_alert.status,
        "updated_at": current_time
    }

# ===== THERAPIST AVAILABILITY MANAGEMENT =====

@router.put("/availability/{therapist_id}")
async def update_therapist_availability(
    therapist_id: UUID,
    availability_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Update therapist availability status"""
    
    therapist = db.query(Therapist).filter(Therapist.id == therapist_id).first()
    if not therapist:
        raise HTTPException(status_code=404, detail="Therapist not found")
    
    new_status = availability_data.get("status")
    if new_status:
        try:
            therapist.status = TherapistStatus(new_status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")
    
    # Update on-call availability
    if "is_on_call" in availability_data:
        therapist.is_on_call = availability_data["is_on_call"]
    
    db.commit()
    
    # Get updated workload after status change
    crisis_manager = CrisisAlertManager(db)
    availability_stats = crisis_manager.get_therapist_availability_stats(therapist.college_id)
    
    return {
        "message": "Availability updated successfully",
        "therapist_id": str(therapist_id),
        "new_status": therapist.status.value,
        "is_on_call": therapist.is_on_call,
        "college_availability": availability_stats
    }

@router.get("/workload-balance/{college_id}")
async def get_therapist_workload_balance(
    college_id: str,
    db: Session = Depends(get_db)
):
    """Get workload balance across all therapists in a college"""
    
    crisis_manager = CrisisAlertManager(db)
    availability_stats = crisis_manager.get_therapist_availability_stats(college_id)
    
    # Get crisis distribution by risk level
    crisis_distribution = db.query(
        CrisisAlert.risk_level,
        func.count(CrisisAlert.id).label('count')
    ).join(User).filter(
        and_(
            User.college_id == college_id,
            CrisisAlert.status.in_(["pending", "acknowledged", "escalated"])
        )
    ).group_by(CrisisAlert.risk_level).all()
    
    risk_distribution = {}
    for risk_level, count in crisis_distribution:
        risk_distribution[risk_level.value] = count
    
    return {
        "college_id": college_id,
        "availability_stats": availability_stats,
        "crisis_distribution": risk_distribution,
        "load_balancing_recommended": availability_stats["average_workload"] > 3,
        "immediate_attention_needed": risk_distribution.get("critical", 0) > 0
    }