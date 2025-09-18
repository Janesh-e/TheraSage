from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from enum import Enum

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

    class Config:
        schema_extra = {
            "example": {
                "new_title": "My Updated Session Title"
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


class TherapistResponse(BaseModel):
    id: str
    name: str
    email: str
    phone_number: str
    role: str
    college_name: str
    is_active: bool
    status: str
    is_on_call: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        orm_mode = True


class TherapistSessionType(str, Enum):
    ONLINE_MEET = "online_meet"
    PHONE_CALL = "phone_call"  
    IN_PERSON = "in_person"

class TherapistSessionCreate(BaseModel):
    session_type: TherapistSessionType
    scheduled_for: datetime
    duration_minutes: int = 50
    meeting_link: Optional[str] = None  # Required only if session_type is online_meet
    therapist_id: str
    
    @validator('meeting_link')
    def validate_meeting_link(cls, v, values):
        if values.get('session_type') == TherapistSessionType.ONLINE_MEET:
            if not v or not v.strip():
                raise ValueError('meeting_link is required for online meetings')
        return v

class TherapistSessionUpdate(BaseModel):
    attended: Optional[bool] = None
    session_notes: Optional[str] = None
    follow_up_needed: Optional[bool] = None
    next_session_recommended: Optional[datetime] = None
    status: Optional[str] = None  # completed, cancelled

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
    external_therapist_id: Optional[str]
    attended: Optional[bool]
    session_notes: Optional[str]
    follow_up_needed: bool
    next_session_recommended: Optional[datetime]
    completed_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    
    class Config:
        from_attributes = True