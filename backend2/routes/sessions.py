from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from db import get_db
from models import ChatSession, User, RiskLevel
from schemas import ChatSessionCreate, ChatSessionResponse

router = APIRouter(
    prefix="/sessions",
    tags=["sessions"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    session_data: ChatSessionCreate,
    user_id: str,
    db: Session = Depends(get_db)
):
    """Create a new chat session for a user"""
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get the next session number for this user
    last_session = db.query(ChatSession).filter(
        ChatSession.user_id == user_id
    ).order_by(ChatSession.session_number.desc()).first()
    
    next_session_number = (last_session.session_number + 1) if last_session else 1
    
    # Create new session
    new_session = ChatSession(
        user_id=user_id,
        title=session_data.title or f"Chat Session {next_session_number}",
        session_number=next_session_number,
        current_risk_level=RiskLevel.LOW,
        total_messages=0
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return new_session

@router.put("/{session_id}/rename", response_model=ChatSessionResponse)
async def rename_chat_session(
    session_id: str,
    new_title: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """Rename a chat session"""
    # Find the session
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or access denied"
        )
    
    # Update the title
    session.title = new_title
    session.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(session)
    
    return session

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """Delete a chat session and all its messages"""
    # Find the session
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or access denied"
        )
    
    # Delete the session (messages will be deleted due to cascade)
    db.delete(session)
    db.commit()
    
    return None

@router.get("/user/{user_id}", response_model=List[ChatSessionResponse])
async def get_user_sessions(
    user_id: str,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """Get all chat sessions for a user"""
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == user_id,
        ChatSession.is_active == True
    ).order_by(ChatSession.updated_at.desc()).offset(skip).limit(limit).all()
    
    return sessions

@router.get("/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific chat session"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or access denied"
        )
    
    return session
