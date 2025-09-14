from fastapi import APIRouter, HTTPException, Depends, status, Query, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from db import get_db
from models import User, UserMatch
from pydantic import BaseModel

router = APIRouter(
    prefix="/peer-messaging",
    tags=["peer-messaging"],
)

# Pydantic models
class PeerMessage(BaseModel):
    id: str
    sender_id: str
    sender_username: str
    recipient_id: str
    recipient_username: str
    content: str
    created_at: datetime
    read: bool

class SendMessageRequest(BaseModel):
    content: str
    message_type: str = "text"  # text, emoji, support

class ConversationInfo(BaseModel):
    match_id: str
    other_user_id: str
    other_user_username: str
    compatibility_score: float
    message_count: int
    last_message_at: Optional[datetime]
    unread_count: int

# In-memory message store for demonstration
# In production, use a proper database table or message queue
peer_messages_store = {}

def get_or_create_conversation_key(user1_id: str, user2_id: str) -> str:
    """Create a unique key for conversation between two users"""
    sorted_ids = sorted([user1_id, user2_id])
    return f"conv_{sorted_ids[0]}_{sorted_ids[1]}"

@router.post("/send")
async def send_peer_message(
    message_request: SendMessageRequest,
    sender_id: str = Body(..., embed=True),
    recipient_id: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """
    Send a message to a matched peer
    """
    # Verify both users exist
    sender = db.query(User).filter(User.id == sender_id).first()
    recipient = db.query(User).filter(User.id == recipient_id).first()
    
    if not sender or not recipient:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify connection exists and is accepted
    connection = db.query(UserMatch).filter(
        or_(
            and_(UserMatch.user_id == sender_id, UserMatch.matched_user_id == recipient_id),
            and_(UserMatch.user_id == recipient_id, UserMatch.matched_user_id == sender_id)
        ),
        UserMatch.connection_accepted == True
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=403,
            detail="No active connection found. You can only message users you're connected with."
        )
    
    # Create message
    message_id = str(uuid4())
    conversation_key = get_or_create_conversation_key(sender_id, recipient_id)
    
    if conversation_key not in peer_messages_store:
        peer_messages_store[conversation_key] = []
    
    message = {
        "id": message_id,
        "sender_id": sender_id,
        "sender_username": sender.anonymous_username,
        "recipient_id": recipient_id,
        "recipient_username": recipient.anonymous_username,
        "content": message_request.content,
        "message_type": message_request.message_type,
        "created_at": datetime.utcnow(),
        "read": False
    }
    
    peer_messages_store[conversation_key].append(message)
    
    # Update connection interaction count
    connection.interaction_count += 1
    connection.last_interaction = datetime.utcnow()
    db.commit()
    
    return {
        "message": "Message sent successfully",
        "message_id": message_id,
        "sent_at": message["created_at"],
        "conversation_key": conversation_key
    }

@router.get("/conversations/{user_id}")
async def get_user_conversations(
    user_id: str,
    limit: int = Query(20, le=50),
    db: Session = Depends(get_db)
):
    """
    Get all conversations for a user
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get all connections where user is connected
    connections = db.query(UserMatch).options(
        joinedload(UserMatch.user),
        joinedload(UserMatch.matched_user)
    ).filter(
        or_(
            UserMatch.user_id == user_id,
            UserMatch.matched_user_id == user_id
        ),
        UserMatch.connection_accepted == True
    ).limit(limit).all()
    
    conversations = []
    
    for connection in connections:
        # Determine the other user
        if str(connection.user_id) == user_id:
            other_user = connection.matched_user
        else:
            other_user = connection.user
        
        if not other_user or not other_user.is_active:
            continue
        
        # Get conversation messages
        conversation_key = get_or_create_conversation_key(user_id, str(other_user.id))
        messages = peer_messages_store.get(conversation_key, [])
        
        # Calculate unread count
        unread_count = sum(
            1 for msg in messages 
            if msg["recipient_id"] == user_id and not msg["read"]
        )
        
        # Get last message info
        last_message_at = None
        if messages:
            last_message_at = max(msg["created_at"] for msg in messages)
        
        conversations.append(ConversationInfo(
            match_id=str(connection.id),
            other_user_id=str(other_user.id),
            other_user_username=other_user.anonymous_username,
            compatibility_score=connection.compatibility_score,
            message_count=len(messages),
            last_message_at=last_message_at,
            unread_count=unread_count
        ))
    
    # Sort by last activity
    conversations.sort(
        key=lambda x: x.last_message_at or datetime.min, 
        reverse=True
    )
    
    return {
        "conversations": conversations,
        "total_count": len(conversations)
    }

@router.get("/messages/{user_id}/{other_user_id}")
async def get_conversation_messages(
    user_id: str,
    other_user_id: str,
    limit: int = Query(50, le=100),
    before: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get messages in a conversation between two users
    """
    # Verify users and connection
    user = db.query(User).filter(User.id == user_id).first()
    other_user = db.query(User).filter(User.id == other_user_id).first()
    
    if not user or not other_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify connection
    connection = db.query(UserMatch).filter(
        or_(
            and_(UserMatch.user_id == user_id, UserMatch.matched_user_id == other_user_id),
            and_(UserMatch.user_id == other_user_id, UserMatch.matched_user_id == user_id)
        ),
        UserMatch.connection_accepted == True
    ).first()
    
    if not connection:
        raise HTTPException(status_code=403, detail="No connection found")
    
    # Get messages
    conversation_key = get_or_create_conversation_key(user_id, other_user_id)
    messages = peer_messages_store.get(conversation_key, [])
    
    # Filter by timestamp if provided
    if before:
        messages = [msg for msg in messages if msg["created_at"] < before]
    
    # Sort by timestamp (newest first) and limit
    messages.sort(key=lambda x: x["created_at"], reverse=True)
    messages = messages[:limit]
    
    # Reverse to show oldest first in response
    messages.reverse()
    
    # Mark messages as read for the requesting user
    for msg in messages:
        if msg["recipient_id"] == user_id:
            msg["read"] = True
    
    return {
        "conversation_id": conversation_key,
        "messages": [PeerMessage(**msg) for msg in messages],
        "message_count": len(messages),
        "other_user": {
            "id": other_user_id,
            "username": other_user.anonymous_username
        }
    }

@router.post("/mark-read")
async def mark_messages_read(
    user_id: str = Body(..., embed=True),
    other_user_id: str = Body(..., embed=True),
    message_ids: Optional[List[str]] = Body(None),
    db: Session = Depends(get_db)
):
    """
    Mark messages as read
    """
    # Verify connection
    connection = db.query(UserMatch).filter(
        or_(
            and_(UserMatch.user_id == user_id, UserMatch.matched_user_id == other_user_id),
            and_(UserMatch.user_id == other_user_id, UserMatch.matched_user_id == user_id)
        ),
        UserMatch.connection_accepted == True
    ).first()
    
    if not connection:
        raise HTTPException(status_code=403, detail="No connection found")
    
    # Mark messages as read
    conversation_key = get_or_create_conversation_key(user_id, other_user_id)
    messages = peer_messages_store.get(conversation_key, [])
    
    marked_count = 0
    for msg in messages:
        if msg["recipient_id"] == user_id:
            if message_ids is None or msg["id"] in message_ids:
                msg["read"] = True
                marked_count += 1
    
    return {
        "message": f"Marked {marked_count} messages as read",
        "marked_count": marked_count
    }

@router.get("/unread-count/{user_id}")
async def get_unread_message_count(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get total unread message count for a user
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    total_unread = 0
    
    # Check all conversations
    connections = db.query(UserMatch).filter(
        or_(
            UserMatch.user_id == user_id,
            UserMatch.matched_user_id == user_id
        ),
        UserMatch.connection_accepted == True
    ).all()
    
    for connection in connections:
        other_user_id = (
            str(connection.matched_user_id) 
            if str(connection.user_id) == user_id 
            else str(connection.user_id)
        )
        
        conversation_key = get_or_create_conversation_key(user_id, other_user_id)
        messages = peer_messages_store.get(conversation_key, [])
        
        unread_in_conversation = sum(
            1 for msg in messages 
            if msg["recipient_id"] == user_id and not msg["read"]
        )
        
        total_unread += unread_in_conversation
    
    return {
        "user_id": user_id,
        "total_unread": total_unread,
        "active_conversations": len(connections)
    }

@router.delete("/conversation/{user_id}/{other_user_id}")
async def delete_conversation(
    user_id: str,
    other_user_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete conversation history (for privacy)
    """
    # Verify connection
    connection = db.query(UserMatch).filter(
        or_(
            and_(UserMatch.user_id == user_id, UserMatch.matched_user_id == other_user_id),
            and_(UserMatch.user_id == other_user_id, UserMatch.matched_user_id == user_id)
        )
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    # Delete messages
    conversation_key = get_or_create_conversation_key(user_id, other_user_id)
    if conversation_key in peer_messages_store:
        message_count = len(peer_messages_store[conversation_key])
        del peer_messages_store[conversation_key]
    else:
        message_count = 0
    
    return {
        "message": "Conversation deleted successfully",
        "deleted_messages": message_count,
        "conversation_key": conversation_key
    }

@router.post("/report")
async def report_inappropriate_message(
    message_id: str = Body(..., embed=True),
    reporter_id: str = Body(..., embed=True),
    reason: str = Body(...),
    details: Optional[str] = Body(None),
    db: Session = Depends(get_db)
):
    """
    Report inappropriate message content
    """
    user = db.query(User).filter(User.id == reporter_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Find the message across all conversations
    message_found = None
    conversation_key_found = None
    
    for conv_key, messages in peer_messages_store.items():
        for msg in messages:
            if msg["id"] == message_id:
                # Verify reporter is part of this conversation
                if reporter_id in [msg["sender_id"], msg["recipient_id"]]:
                    message_found = msg
                    conversation_key_found = conv_key
                    break
        if message_found:
            break
    
    if not message_found:
        raise HTTPException(status_code=404, detail="Message not found or access denied")
    
    # In a real implementation, this would create a moderation record
    # For now, we'll just flag the message
    message_found["reported"] = True
    message_found["report_reason"] = reason
    message_found["report_details"] = details
    message_found["reported_by"] = reporter_id
    message_found["reported_at"] = datetime.utcnow()
    
    return {
        "message": "Message reported successfully",
        "report_id": f"report_{uuid4()}",
        "message_id": message_id,
        "action_taken": "Content flagged for moderation review"
    }