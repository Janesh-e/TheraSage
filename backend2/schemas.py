from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

# Pydantic models
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    college_id: str
    college_name: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    anonymous_username: str
    college_name: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        orm_mode = True

class ChatSessionCreate(BaseModel):
    title: Optional[str] = None
    user_id: str

class ChatSessionResponse(BaseModel):
    id: str
    title: Optional[str]
    session_number: int
    current_risk_level: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime
    total_messages: int
    conversation_summary: Optional[str] = None
    risk_score: Optional[float] = None
    
    class Config:
        from_attributes = True
        orm_mode = True

class SessionRenameRequest(BaseModel):
    new_title: str
    user_id: str

    class Config:
        schema_extra = {
            "example": {
                "new_title": "My Updated Session Title",
                "user_id": "52e5122b-fbff-4d60-b338-c4f417ce2872"
            }
        }

class ChatMessageCreate(BaseModel):
    content: str
    role: str = "user"

class ChatMessageResponse(BaseModel):
    id: str
    content: str
    role: str
    message_order: int
    created_at: datetime
    sentiment_score: Optional[float] = None
    risk_indicators: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True
        orm_mode = True

class SessionRenameRequest(BaseModel):
    new_title: str
    
    class Config:
        schema_extra = {
            "example": {
                "new_title": "My Updated Session Title"
            }
        }

class CommunityPostCreate(BaseModel):
    title: str
    content: str
    anonymous_level: int = 2
    show_college: bool = True

class CommunityPostResponse(BaseModel):
    id: str
    title: str
    content: str
    college_id: str
    moderation_status: str
    upvote_count: int
    comment_count: int
    created_at: datetime
    anonymous_level: int
    
    class Config:
        from_attributes = True
        orm_mode = True

class CommentCreate(BaseModel):
    content: str
    parent_comment_id: Optional[str] = None

class CommentResponse(BaseModel):
    id: str
    content: str
    upvote_count: int
    created_at: datetime
    author_anonymous_username: str
    
    class Config:
        from_attributes = True
        orm_mode = True