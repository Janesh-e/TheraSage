from fastapi import APIRouter, HTTPException, Depends, status, Query, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from db import get_db
from models import (
    CrisisAlert, User, ChatSession, ChatMessage, TherapistSession,
    RiskLevel, CrisisType, SessionStatus, MessageRole,
    Therapist, TherapistNotification, TherapistRole, NotificationStatus
)

from pydantic import BaseModel

router = APIRouter(
    prefix="/crisis",
    tags=["crisis-management"],
)

# Pydantic models for requests/responses
class CrisisAlertResponse(BaseModel):
    id: str
    user_id: str
    session_id: Optional[str]
    crisis_type: str
    risk_level: str
    confidence_score: float
    status: str
    detected_indicators: List[str]
    trigger_message: Optional[str]
    detected_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    user_info: Optional[Dict[str, Any]] = None
    session_info: Optional[Dict[str, Any]] = None

class CrisisAlertUpdate(BaseModel):
    status: Optional[str] = None
    resolution_notes: Optional[str] = None
    escalated_to_human: Optional[bool] = None
    response_actions: Optional[Dict[str, Any]] = None

class CrisisStatsResponse(BaseModel):
    total_alerts: int
    pending_alerts: int
    acknowledged_alerts: int
    resolved_alerts: int
    high_priority_alerts: int
    alerts_last_24h: int
    avg_response_time_hours: float

# ===== CRISIS ALERT VIEWING ROUTES =====

@router.get("/alerts", response_model=List[CrisisAlertResponse])
async def get_crisis_alerts(
    db: Session = Depends(get_db),
    college_id: Optional[str] = Query(None, description="Filter by college"),
    status: Optional[str] = Query(None, description="Filter by status"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    limit: int = Query(50, le=100),
    skip: int = Query(0),
    include_resolved: bool = Query(False),
    therapist_id: Optional[str] = Query(None, description="Filter by assigned therapist")
):
    """Get crisis alerts for therapist dashboard"""
    
    query = db.query(CrisisAlert).options(
        joinedload(CrisisAlert.user),
        joinedload(CrisisAlert.session)
    )
    
    # Apply filters
    if college_id:
        query = query.join(User).filter(User.college_id == college_id)
    
    if status:
        query = query.filter(CrisisAlert.status == status)
    
    if risk_level:
        query = query.filter(CrisisAlert.risk_level == RiskLevel(risk_level))
    
    if not include_resolved:
        query = query.filter(CrisisAlert.status != "resolved")
    
    if therapist_id:
        query = query.filter(CrisisAlert.assigned_therapist_id == therapist_id)
    
    # Order by priority: critical first, then by detection time
    query = query.order_by(
        CrisisAlert.risk_level.desc(),
        CrisisAlert.detected_at.desc()
    )
    
    alerts = query.offset(skip).limit(limit).all()
    
    # Format response with user and session info
    response_alerts = []
    for alert in alerts:
        user_info = None
        session_info = None
        
        if alert.user:
            user_info = {
                "anonymous_username": alert.user.anonymous_username,
                "college_name": alert.user.college_name,
                "last_activity": alert.user.last_activity
            }
        
        if alert.session:
            session_info = {
                "title": alert.session.title,
                "session_number": alert.session.session_number,
                "total_messages": alert.session.total_messages,
                "risk_score": alert.session.risk_score
            }
        
        response_alerts.append(CrisisAlertResponse(
            id=str(alert.id),
            user_id=str(alert.user_id),
            session_id=str(alert.session_id) if alert.session_id else None,
            crisis_type=alert.crisis_type.value,
            risk_level=alert.risk_level.value,
            confidence_score=alert.confidence_score,
            status=alert.status,
            detected_indicators=alert.detected_indicators or [],
            trigger_message=alert.trigger_message,
            detected_at=alert.detected_at,
            acknowledged_at=alert.acknowledged_at,
            resolved_at=alert.resolved_at,
            user_info=user_info,
            session_info=session_info
        ))
    
    return response_alerts

@router.get("/alerts/{alert_id}", response_model=CrisisAlertResponse)
async def get_crisis_alert(
    alert_id: UUID,
    db: Session = Depends(get_db)
):
    """Get detailed crisis alert information"""
    
    alert = db.query(CrisisAlert).options(
        joinedload(CrisisAlert.user),
        joinedload(CrisisAlert.session)
    ).filter(CrisisAlert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Crisis alert not found")
    
    # Get additional context - recent messages from the session
    context_messages = []
    if alert.session_id:
        recent_messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == alert.session_id
        ).order_by(ChatMessage.message_order.desc()).limit(10).all()
        
        context_messages = [
            {
                "content": msg.content,
                "role": msg.role.value,
                "created_at": msg.created_at,
                "risk_indicators": msg.risk_indicators
            }
            for msg in reversed(recent_messages)
        ]
    
    user_info = None
    session_info = None
    
    if alert.user:
        user_info = {
            "anonymous_username": alert.user.anonymous_username,
            "college_name": alert.user.college_name,
            "created_at": alert.user.created_at,
            "last_activity": alert.user.last_activity
        }
    
    if alert.session:
        session_info = {
            "title": alert.session.title,
            "session_number": alert.session.session_number,
            "total_messages": alert.session.total_messages,
            "risk_score": alert.session.risk_score,
            "context_messages": context_messages
        }
    
    return CrisisAlertResponse(
        id=str(alert.id),
        user_id=str(alert.user_id),
        session_id=str(alert.session_id) if alert.session_id else None,
        crisis_type=alert.crisis_type.value,
        risk_level=alert.risk_level.value,
        confidence_score=alert.confidence_score,
        status=alert.status,
        detected_indicators=alert.detected_indicators or [],
        trigger_message=alert.trigger_message,
        detected_at=alert.detected_at,
        acknowledged_at=alert.acknowledged_at,
        resolved_at=alert.resolved_at,
        user_info=user_info,
        session_info=session_info
    )

# ===== CRISIS ALERT MANAGEMENT ROUTES =====

@router.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_crisis_alert(
    alert_id: UUID,
    therapist_id: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Acknowledge a crisis alert"""
    
    alert = db.query(CrisisAlert).filter(CrisisAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Crisis alert not found")
    
    if alert.status != "pending":
        raise HTTPException(status_code=400, detail="Alert already acknowledged")
    
    current_time = datetime.utcnow()
    alert.status = "acknowledged"
    alert.acknowledged_at = current_time
    alert.assigned_therapist_id = therapist_id
    alert.human_reviewer_id = therapist_id
    
    db.commit()
    
    return {
        "message": "Crisis alert acknowledged successfully",
        "alert_id": str(alert_id),
        "acknowledged_at": current_time,
        "status": "acknowledged"
    }

@router.put("/alerts/{alert_id}/escalate")
async def escalate_crisis_alert(
    alert_id: UUID,
    escalation_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Escalate crisis alert to human intervention"""
    
    alert = db.query(CrisisAlert).filter(CrisisAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Crisis alert not found")
    
    if alert.status not in ["pending", "acknowledged"]:
        raise HTTPException(status_code=400, detail="Cannot escalate resolved alert")
    
    current_time = datetime.utcnow()
    
    # Update alert status
    alert.status = "escalated"
    alert.escalated_to_human = True
    alert.response_actions = {
        "escalated_at": current_time.isoformat(),
        "escalation_reason": escalation_data.get("reason", ""),
        "urgency_level": escalation_data.get("urgency", "high"),
        "recommended_actions": escalation_data.get("actions", [])
    }
    
    # Create therapist session if requested
    create_session = escalation_data.get("create_session", False)
    session_id = None
    
    if create_session:
        therapist_session = TherapistSession(
            user_id=alert.user_id,
            crisis_alert_id=alert.id,
            session_type="crisis",
            urgency_level=RiskLevel.HIGH if escalation_data.get("urgency") == "high" else RiskLevel.MEDIUM,
            requested_at=current_time,
            status=SessionStatus.SCHEDULED
        )
        
        db.add(therapist_session)
        db.flush()  # Get the ID
        session_id = str(therapist_session.id)
    
    db.commit()
    
    return {
        "message": "Crisis alert escalated successfully", 
        "alert_id": str(alert_id),
        "escalated_at": current_time,
        "status": "escalated",
        "therapist_session_id": session_id
    }

@router.put("/alerts/{alert_id}/resolve")
async def resolve_crisis_alert(
    alert_id: UUID,
    resolution_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Mark crisis alert as resolved"""
    
    alert = db.query(CrisisAlert).filter(CrisisAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Crisis alert not found")
    
    current_time = datetime.utcnow()
    
    alert.status = "resolved"
    alert.resolved_at = current_time
    alert.resolution_notes = resolution_data.get("notes", "")
    
    # Update response actions
    if alert.response_actions:
        alert.response_actions.update({
            "resolved_at": current_time.isoformat(),
            "resolution_method": resolution_data.get("method", ""),
            "follow_up_needed": resolution_data.get("follow_up", False)
        })
    else:
        alert.response_actions = {
            "resolved_at": current_time.isoformat(),
            "resolution_method": resolution_data.get("method", ""),
            "follow_up_needed": resolution_data.get("follow_up", False)
        }
    
    db.commit()
    
    return {
        "message": "Crisis alert resolved successfully",
        "alert_id": str(alert_id), 
        "resolved_at": current_time,
        "status": "resolved"
    }

# ===== CRISIS STATISTICS AND DASHBOARD =====

@router.get("/stats", response_model=CrisisStatsResponse)
async def get_crisis_statistics(
    college_id: Optional[str] = Query(None),
    days_back: int = Query(30, le=365),
    db: Session = Depends(get_db)
):
    """Get crisis management statistics"""
    
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
    
    base_query = db.query(CrisisAlert).filter(CrisisAlert.detected_at >= cutoff_date)
    
    if college_id:
        base_query = base_query.join(User).filter(User.college_id == college_id)
    
    # Total alerts
    total_alerts = base_query.count()
    
    # By status
    pending_alerts = base_query.filter(CrisisAlert.status == "pending").count()
    acknowledged_alerts = base_query.filter(CrisisAlert.status == "acknowledged").count()
    resolved_alerts = base_query.filter(CrisisAlert.status == "resolved").count()
    
    # High priority (critical and high risk)
    high_priority_alerts = base_query.filter(
        CrisisAlert.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL])
    ).count()
    
    # Last 24 hours
    last_24h = datetime.utcnow() - timedelta(hours=24)
    alerts_last_24h = base_query.filter(CrisisAlert.detected_at >= last_24h).count()
    
    # Average response time (for acknowledged alerts)
    avg_response_time = db.query(
        func.avg(
            func.extract('epoch', CrisisAlert.acknowledged_at - CrisisAlert.detected_at) / 3600
        )
    ).filter(
        and_(
            CrisisAlert.detected_at >= cutoff_date,
            CrisisAlert.acknowledged_at.isnot(None)
        )
    ).scalar()
    
    return CrisisStatsResponse(
        total_alerts=total_alerts,
        pending_alerts=pending_alerts,
        acknowledged_alerts=acknowledged_alerts,
        resolved_alerts=resolved_alerts,
        high_priority_alerts=high_priority_alerts,
        alerts_last_24h=alerts_last_24h,
        avg_response_time_hours=round(avg_response_time or 0.0, 2)
    )

# ===== BULK OPERATIONS =====

@router.put("/alerts/bulk-acknowledge")
async def bulk_acknowledge_alerts(
    alert_ids: List[UUID] = Body(...),
    therapist_id: str = Body(...),
    db: Session = Depends(get_db)
):
    """Acknowledge multiple alerts at once"""
    
    alerts = db.query(CrisisAlert).filter(
        and_(
            CrisisAlert.id.in_(alert_ids),
            CrisisAlert.status == "pending"
        )
    ).all()
    
    if not alerts:
        raise HTTPException(status_code=404, detail="No pending alerts found")
    
    current_time = datetime.utcnow()
    updated_count = 0
    
    for alert in alerts:
        alert.status = "acknowledged"
        alert.acknowledged_at = current_time
        alert.human_reviewer_id = therapist_id
        updated_count += 1
    
    db.commit()
    
    return {
        "message": f"Successfully acknowledged {updated_count} alerts",
        "updated_count": updated_count,
        "acknowledged_at": current_time
    }

@router.get("/alerts/urgent")
async def get_urgent_alerts(
    college_id: Optional[str] = Query(None),
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db)
):
    """Get urgent crisis alerts needing immediate attention"""
    
    # Urgent criteria: high/critical risk, pending/acknowledged status, recent detection
    query = db.query(CrisisAlert).options(
        joinedload(CrisisAlert.user)
    ).filter(
        and_(
            CrisisAlert.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL]),
            CrisisAlert.status.in_(["pending", "acknowledged"]),
            CrisisAlert.detected_at >= datetime.utcnow() - timedelta(hours=48)
        )
    )
    
    if college_id:
        query = query.join(User).filter(User.college_id == college_id)
    
    urgent_alerts = query.order_by(
        CrisisAlert.risk_level.desc(),
        CrisisAlert.detected_at.desc()
    ).limit(limit).all()
    
    return [
        {
            "id": str(alert.id),
            "user_anonymous": alert.user.anonymous_username if alert.user else "Unknown",
            "crisis_type": alert.crisis_type.value,
            "risk_level": alert.risk_level.value,
            "confidence_score": alert.confidence_score,
            "status": alert.status,
            "detected_at": alert.detected_at,
            "hours_since_detection": (datetime.utcnow() - alert.detected_at).total_seconds() / 3600
        }
        for alert in urgent_alerts
    ]