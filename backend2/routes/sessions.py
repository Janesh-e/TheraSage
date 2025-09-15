from fastapi import APIRouter, HTTPException, Depends, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from db import get_db
from models import ChatSession, User, RiskLevel
from schemas import ChatSessionCreate, ChatSessionResponse, SessionRenameRequest
from authenticate_utils import get_current_user  # Missing import

router = APIRouter(
    prefix="/sessions",
    tags=["sessions"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new chat session for the authenticated user"""
    # Get the next session number for this user
    last_session = db.query(ChatSession).filter(
        ChatSession.user_id == str(current_user.id)
    ).order_by(ChatSession.session_number.desc()).first()

    next_session_number = (last_session.session_number + 1) if last_session else 1

    # Create new session
    new_session = ChatSession(
        user_id=str(current_user.id),
        title=session_data.title or f"Chat Session {next_session_number}",
        session_number=next_session_number,
        current_risk_level=RiskLevel.LOW,
        total_messages=0
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    current_user.last_activity = datetime.utcnow()
    db.commit()

    return new_session

@router.put("/{session_id}/rename", response_model=ChatSessionResponse)
async def rename_chat_session(
    session_id: str,
    rename_data: SessionRenameRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rename a chat session"""
    # Find the session - Fixed variable reference
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == str(current_user.id)  # Fixed: was user_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or access denied"
        )

    # Update the title using the schema
    current_time = datetime.utcnow()
    session.title = rename_data.new_title
    session.updated_at = current_time

    # Update user activity
    current_user.last_activity = current_time
    
    db.commit()
    db.refresh(session)
    
    return session

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a chat session and all its messages"""
    try:
        # Find the session - Fixed variable reference
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == str(current_user.id)  # Fixed: was user_id
        ).first()

        if not session:
            # Log for debugging - Fixed variable reference
            print(f"Session not found: session_id={session_id}, user_id={str(current_user.id)}")
            
            # Check if session exists at all - Fixed variable name
            session_exists = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not session_exists:
                print(f"Session {session_id} does not exist in database")
            else:
                print(f"Session {session_id} exists but belongs to different user")
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )

        # Update user activity
        current_user.last_activity = datetime.utcnow()

        # Delete the session (messages will be deleted due to cascade)
        db.delete(session)
        
        # Commit the transaction
        db.commit()
        
        print(f"Session {session_id} successfully deleted")
        return None
        
    except HTTPException:
        # Re-raise HTTP exceptions
        db.rollback()
        raise
    except Exception as e:
        # Rollback on any other error
        db.rollback()
        print(f"Error deleting session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )

@router.get("/user/sessions", response_model=List[ChatSessionResponse])
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    include_archived: bool = Query(False)
):
    """Get all chat sessions for the authenticated user"""
    # Update user activity
    current_user.last_activity = datetime.utcnow()
    db.commit()

    # Build query
    query = db.query(ChatSession).filter(ChatSession.user_id == str(current_user.id))

    if not include_archived:
        query = query.filter(ChatSession.is_archived == False)

    query = query.filter(ChatSession.is_active == True)

    # Order by last message time (most recent first), fallback to created_at
    sessions = query.order_by(
        ChatSession.last_message_at.desc().nullslast(),
        ChatSession.created_at.desc()
    ).offset(skip).limit(limit).all()

    return sessions

@router.get("/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific chat session"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == str(current_user.id)
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or access denied"
        )

    # Update user activity
    current_user.last_activity = datetime.utcnow()
    db.commit()

    return session

@router.put("/{session_id}/risk")
async def update_session_risk(
    session_id: str,
    risk_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update session risk assessment"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == str(current_user.id)
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found or access denied")

    # Update risk assessment
    current_time = datetime.utcnow()

    if "risk_score" in risk_data:
        session.risk_score = float(risk_data["risk_score"])

    if "risk_level" in risk_data:
        try:
            session.current_risk_level = RiskLevel(risk_data["risk_level"])
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid risk level")

    session.last_risk_assessment = current_time
    session.updated_at = current_time

    db.commit()

    return {
        "message": "Risk assessment updated",
        "session_id": str(session.id),
        "risk_score": session.risk_score,
        "risk_level": session.current_risk_level.value,
        "last_assessment": session.last_risk_assessment
    }

@router.put("/{session_id}/archive")
async def archive_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Archive a session"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == str(current_user.id)
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found or access denied")

    current_time = datetime.utcnow()
    session.is_archived = True
    session.updated_at = current_time

    # Update user activity
    current_user.last_activity = current_time

    db.commit()

    return {
        "message": "Session archived successfully",
        "session_id": str(session.id),
        "archived_at": current_time
    }