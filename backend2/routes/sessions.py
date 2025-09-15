from fastapi import APIRouter, HTTPException, Depends, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from db import get_db
from models import ChatSession, User, RiskLevel
from schemas import ChatSessionCreate, ChatSessionResponse, SessionRenameRequest
from uuid import UUID

router = APIRouter(
    prefix="/sessions",
    tags=["sessions"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_chat_session(
    session_data: ChatSessionCreate,
    db: Session = Depends(get_db)
):
    """Create a new chat session for a user"""
    try:
        # Debug logging
        print(f"DEBUG: Creating session for user_id: {session_data.user_id}")
        print(f"DEBUG: Session data: {session_data}")
        
        # Verify user exists
        user_id = session_data.user_id
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"DEBUG: User not found with ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found with ID: {user_id}"
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

        user.last_activity = datetime.utcnow()
        db.commit()

        print(f"DEBUG: Session created successfully with ID: {new_session.id}")
        
        # Convert UUID fields to strings for JSON serialization
        response_data = ChatSessionResponse(
            id=str(new_session.id),  # Convert UUID to string
            title=new_session.title,
            session_number=new_session.session_number,
            current_risk_level=new_session.current_risk_level.value,
            is_active=new_session.is_active,
            created_at=new_session.created_at,
            updated_at=new_session.updated_at,
            last_message_at=new_session.last_message_at,
            total_messages=new_session.total_messages,
            conversation_summary=new_session.conversation_summary,
            risk_score=new_session.risk_score
        )
        
        return response_data
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print(f"DEBUG: Error creating session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )

@router.put("/{session_id}/rename", response_model=ChatSessionResponse)
async def rename_chat_session(
    session_id: str,
    rename_data: SessionRenameRequest,
    user_id: str = Query(...),  # Extract user_id from request body
    db: Session = Depends(get_db)
):
    """Rename a chat session"""
    try:
        # Convert string UUIDs to proper UUID objects
        try:
            session_uuid = UUID(session_id)
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid UUID format"
            )
        
        print(f"DEBUG: Renaming session {session_id} for user {user_id}")
        print(f"DEBUG: New title: {rename_data.new_title}")
        
        # Find the session
        session = db.query(ChatSession).filter(
            ChatSession.id == session_uuid,
            ChatSession.user_id == user_uuid
        ).first()
        
        if not session:
            print(f"DEBUG: Session not found - session_id={session_id}, user_id={user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )
        
        # Update the title using the schema
        current_time = datetime.utcnow()
        session.title = rename_data.new_title
        session.updated_at = current_time
        
        # Update user activity
        user = db.query(User).filter(User.id == user_uuid).first()
        if user:
            user.last_activity = current_time
        
        db.commit()
        db.refresh(session)
        
        print(f"DEBUG: Session {session_id} renamed to '{rename_data.new_title}' successfully")
        
        # Convert to response format
        response_data = ChatSessionResponse(
            id=str(session.id),
            title=session.title,
            session_number=session.session_number,
            current_risk_level=session.current_risk_level.value,
            is_active=session.is_active,
            created_at=session.created_at,
            updated_at=session.updated_at,
            last_message_at=session.last_message_at,
            total_messages=session.total_messages,
            conversation_summary=session.conversation_summary,
            risk_score=session.risk_score
        )
        
        return response_data
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        print(f"Error renaming session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rename session: {str(e)}"
        )

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: str,
    user_id: str = Query(...), # Accept as query parameter
    db: Session = Depends(get_db)
):
    """Delete a chat session and all its messages"""
    try:
        try:
            session_uuid = UUID(session_id)
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid UUID format"
            )
        # Find the session
        session = db.query(ChatSession).filter(
            ChatSession.id == session_uuid,
            ChatSession.user_id == user_uuid
        ).first()

        if not session:
            # Log for debugging
            print(f"Session not found: session_id={session_id}, user_id={user_id}")
            
            # Check if session exists at all
            session_exists = db.query(ChatSession).filter(ChatSession.id == session_uuid).first()
            if not session_exists:
                print(f"Session {session_id} does not exist in database")
            else:
                print(f"Session {session_id} exists but belongs to different user")
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found or access denied"
            )

        print(f"Deleting session: {session_id} for user: {user_id}")
            
        # Update user activity
        user = db.query(User).filter(User.id == user_uuid).first()
        if user:
            user.last_activity = datetime.utcnow()

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

@router.get("/user/{user_id}", response_model=List[ChatSessionResponse])
async def get_user_sessions(
    user_id: str,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    include_archived: bool = Query(False)
):
    """Get all chat sessions for a user"""
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update user activity
    user.last_activity = datetime.utcnow()
    db.commit()

    # Build query
    query = db.query(ChatSession).filter(ChatSession.user_id == user_id)

    if not include_archived:
        query = query.filter(ChatSession.is_archived == False)

    query = query.filter(ChatSession.is_active == True)

    # Order by last message time (most recent first)
    sessions = query.order_by(
        ChatSession.last_message_at.desc()
    ).offset(skip).limit(limit).all()

    # Convert each session to response format with string IDs
    response_sessions = []
    for session in sessions:
        response_sessions.append(ChatSessionResponse(
            id=str(session.id),
            title=session.title,
            session_number=session.session_number,
            current_risk_level=session.current_risk_level.value,
            is_active=session.is_active,
            created_at=session.created_at,
            updated_at=session.updated_at,
            last_message_at=session.last_message_at,
            total_messages=session.total_messages,
            conversation_summary=session.conversation_summary,
            risk_score=session.risk_score
        ))

    return response_sessions

@router.get("/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: str,
    user_id: str = Query(...),
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

    # Update user activity
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.last_activity = datetime.utcnow()
        db.commit()

    # Convert to response format
    response_data = ChatSessionResponse(
        id=str(session.id),
        title=session.title,
        session_number=session.session_number,
        current_risk_level=session.current_risk_level.value,
        is_active=session.is_active,
        created_at=session.created_at,
        updated_at=session.updated_at,
        last_message_at=session.last_message_at,
        total_messages=session.total_messages,
        conversation_summary=session.conversation_summary,
        risk_score=session.risk_score
    )

    return response_data

@router.put("/{session_id}/risk")
async def update_session_risk(
    session_id: str,
    risk_data: dict,
    user_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Update session risk assessment"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id
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
    user_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Archive a session"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found or access denied")

    current_time = datetime.utcnow()
    session.is_archived = True
    session.updated_at = current_time

    # Update user activity
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.last_activity = current_time

    db.commit()

    return {
        "message": "Session archived successfully",
        "session_id": str(session.id),
        "archived_at": current_time
    }