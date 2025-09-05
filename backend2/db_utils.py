# db_utils.py
from sqlalchemy.orm import Session
from models import User, ChatSession, ChatMessage
from werkzeug.security import generate_password_hash
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
    
    user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
        anonymous_username=username,
        college_id=college_id,
        college_name=college_name,
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
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_new_chat_session(db: Session, user_id: str, title: str = None) -> ChatSession:
    """
    Create a new chat session for a user
    """
    # Get the next session number for this user
    last_session = db.query(ChatSession).filter(
        ChatSession.user_id == user_id
    ).order_by(ChatSession.session_number.desc()).first()
    
    next_session_number = (last_session.session_number + 1) if last_session else 1
    
    session = ChatSession(
        user_id=user_id,
        title=title or f"Session {next_session_number}",
        session_number=next_session_number
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def get_user_active_sessions(db: Session, user_id: str, limit: int = 10):
    """
    Get user's recent active chat sessions
    """
    return db.query(ChatSession).filter(
        ChatSession.user_id == user_id,
        ChatSession.is_active == True
    ).order_by(ChatSession.last_message_at.desc()).limit(limit).all()

def update_user_last_activity(db: Session, user_id: str):
    """
    Update user's last activity timestamp
    """
    from sqlalchemy import text
    db.execute(
        text("UPDATE users SET last_activity = NOW() WHERE id = :user_id"),
        {"user_id": user_id}
    )
    db.commit()
