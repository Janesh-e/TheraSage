# db_utils.py
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from models import User, ChatSession, ChatMessage, MessageRole, RiskLevel
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import random
import string

def generate_anonymous_username() -> str:
    """
    Generate a Reddit-style anonymous username
    """
    adjectives = ["thoughtful", "calm", "brave", "kind", "peaceful", "gentle", "strong", "wise", "hopeful", "bright"]
    animals = ["owl", "deer", "fox", "bear", "rabbit", "wolf", "eagle", "dolphin", "panda", "lion"]
    
    adjective = random.choice(adjectives)
    animal = random.choice(animals)
    number = random.randint(100, 9999)
    
    return f"{adjective}_{animal}_{number}"

def create_new_user(db: Session, name: str, email: str, password: str, college_id: str, college_name: str) -> User:
    """
    Create a new user with proper defaults
    """
    # Generate unique anonymous username
    while True:
        username = generate_anonymous_username()
        if not db.query(User).filter(User.anonymous_username == username).first():
            break
    current_time = datetime.utcnow()
    user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
        anonymous_username=username,
        college_id=college_id,
        college_name=college_name,
        created_at=current_time,
        last_activity=current_time,
        last_login=None,
        privacy_settings={
            "show_activity_status": False,
            "allow_matching": True,
            "data_retention_days": 365
        },
        notification_preferences={
            "crisis_alerts": True,
            "session_reminders": True,
            "community_updates": False
        },
        is_active=True,
        is_verified=False,
        mental_health_profile=None 
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_new_chat_session(
    db: Session, 
    user_id: str, 
    title: str = None
) -> ChatSession:
    """Enhanced chat session creation with proper initialization"""
    
    # Get the next session number for this user
    last_session = db.query(ChatSession).filter(
        ChatSession.user_id == user_id
    ).order_by(ChatSession.session_number.desc()).first()

    next_session_number = (last_session.session_number + 1) if last_session else 1
    current_time = datetime.utcnow()

    session = ChatSession(
        user_id=user_id,
        title=title or f"Session {next_session_number}",
        session_number=next_session_number,
        
        # ✅ ENHANCED: Proper risk assessment initialization
        current_risk_level=RiskLevel.LOW,
        risk_score=0.0,
        last_risk_assessment=None,
        
        # ✅ ENHANCED: Proper status and timestamps
        is_active=True,
        is_archived=False,
        created_at=current_time,
        updated_at=current_time,
        last_message_at=current_time,
        
        # ✅ ENHANCED: Initialize counters
        total_messages=0,
        conversation_summary=None
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    # ✅ UPDATE user activity
    update_user_last_activity(db, user_id)
    
    return session

def get_user_active_sessions(
    db: Session, 
    user_id: str, 
    limit: int = 10,
    include_archived: bool = False
) -> List[ChatSession]:
    """Enhanced get active sessions with filtering options"""
    
    query = db.query(ChatSession).filter(
        ChatSession.user_id == user_id,
        ChatSession.is_active == True
    )
    
    if not include_archived:
        query = query.filter(ChatSession.is_archived == False)
    
    sessions = query.order_by(
        ChatSession.last_message_at.desc()
    ).limit(limit).all()
    
    # ✅ UPDATE user activity
    update_user_last_activity(db, user_id)
    
    return sessions

def update_user_last_activity(db: Session, user_id: str):
    """Enhanced user activity update"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.last_activity = datetime.utcnow()
            db.commit()
    except Exception as e:
        print(f"Error updating user activity: {e}")
        db.rollback()

def update_session_risk_assessment(
    db: Session, 
    session_id: str, 
    risk_score: float, 
    risk_level: RiskLevel = None,
    risk_factors: List[str] = None
):
    """Update session risk assessment with comprehensive data"""
    
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        return False
    
    current_time = datetime.utcnow()
    
    # Update risk metrics
    session.risk_score = float(risk_score)
    session.last_risk_assessment = current_time
    session.updated_at = current_time
    
    # Auto-determine risk level if not provided
    if risk_level is None:
        if risk_score >= 8 or (risk_factors and len(risk_factors) > 0):
            if risk_score >= 9:
                risk_level = RiskLevel.CRITICAL
            elif risk_score >= 7:
                risk_level = RiskLevel.HIGH
            else:
                risk_level = RiskLevel.MEDIUM
        elif risk_score >= 4:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
    
    session.current_risk_level = risk_level
    
    db.commit()
    return True

def get_session_analytics(db: Session, session_id: str) -> Dict[str, Any]:
    """Get comprehensive session analytics"""
    
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        return {}
    
    # Message statistics
    message_stats = db.query(
        func.count(ChatMessage.id).label('total_messages'),
        func.count(func.nullif(ChatMessage.role != MessageRole.USER, True)).label('user_messages'),
        func.count(func.nullif(ChatMessage.role != MessageRole.ASSISTANT, True)).label('ai_messages'),
        func.avg(ChatMessage.sentiment_score).label('avg_sentiment'),
        func.avg(ChatMessage.response_time_ms).label('avg_response_time')
    ).filter(ChatMessage.session_id == session_id).first()
    
    # Risk analysis
    risk_messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id,
        ChatMessage.risk_indicators.isnot(None)
    ).all()
    
    all_risk_factors = []
    all_cognitive_distortions = []
    
    for msg in risk_messages:
        if msg.risk_indicators:
            risk_data = msg.risk_indicators
            all_risk_factors.extend(risk_data.get('risk_factors', []))
            all_cognitive_distortions.extend(risk_data.get('cognitive_distortions', []))
    
    # Session duration
    duration_seconds = None
    if session.last_message_at and session.created_at:
        duration_seconds = (session.last_message_at - session.created_at).total_seconds()
    
    return {
        'session_id': str(session.id),
        'title': session.title,
        'created_at': session.created_at,
        'last_message_at': session.last_message_at,
        'duration_seconds': duration_seconds,
        'total_messages': message_stats.total_messages or 0,
        'user_messages': message_stats.user_messages or 0,
        'ai_messages': message_stats.ai_messages or 0,
        'current_risk_level': session.current_risk_level.value,
        'risk_score': session.risk_score,
        'last_risk_assessment': session.last_risk_assessment,
        'average_sentiment': round(message_stats.avg_sentiment or 0.0, 3),
        'average_response_time_ms': round(message_stats.avg_response_time or 0.0, 1),
        'unique_risk_factors': list(set(all_risk_factors)),
        'unique_cognitive_distortions': list(set(all_cognitive_distortions)),
        'messages_with_risk_analysis': len(risk_messages),
        'has_conversation_summary': session.conversation_summary is not None
    }

def get_user_analytics(db: Session, user_id: str, days_back: int = 30) -> Dict[str, Any]:
    """Get comprehensive user analytics"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {}
    
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
    
    # Session statistics
    session_stats = db.query(
        func.count(ChatSession.id).label('total_sessions'),
        func.count(func.nullif(ChatSession.is_active != True, True)).label('active_sessions'),
        func.avg(ChatSession.total_messages).label('avg_messages_per_session'),
        func.avg(ChatSession.risk_score).label('avg_risk_score')
    ).filter(
        and_(
            ChatSession.user_id == user_id,
            ChatSession.created_at >= cutoff_date
        )
    ).first()
    
    # Message activity
    message_activity = db.query(
        func.count(ChatMessage.id).label('total_messages'),
        func.avg(ChatMessage.sentiment_score).label('avg_sentiment')
    ).join(ChatSession).filter(
        and_(
            ChatSession.user_id == user_id,
            ChatMessage.created_at >= cutoff_date,
            ChatMessage.role == MessageRole.USER
        )
    ).first()
    
    # Risk trends
    high_risk_sessions = db.query(func.count(ChatSession.id)).filter(
        and_(
            ChatSession.user_id == user_id,
            ChatSession.current_risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL]),
            ChatSession.created_at >= cutoff_date
        )
    ).scalar()
    
    return {
        'user_id': str(user.id),
        'analysis_period_days': days_back,
        'total_sessions': session_stats.total_sessions or 0,
        'active_sessions': session_stats.active_sessions or 0,
        'total_messages': message_activity.total_messages or 0,
        'avg_messages_per_session': round(session_stats.avg_messages_per_session or 0.0, 1),
        'avg_risk_score': round(session_stats.avg_risk_score or 0.0, 2),
        'avg_sentiment': round(message_activity.avg_sentiment or 0.0, 3),
        'high_risk_sessions': high_risk_sessions or 0,
        'last_activity': user.last_activity,
        'account_created': user.created_at
    }

def cleanup_old_sessions(db: Session, days_to_keep: int = 90):
    """Archive old inactive sessions"""
    
    cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
    
    old_sessions = db.query(ChatSession).filter(
        and_(
            ChatSession.last_message_at < cutoff_date,
            ChatSession.is_archived == False
        )
    ).all()
    
    for session in old_sessions:
        session.is_archived = True
        session.updated_at = datetime.utcnow()
    
    db.commit()
    
    return len(old_sessions)