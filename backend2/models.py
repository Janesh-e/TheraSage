# models.py
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, 
    ForeignKey, Float, Enum as SQLEnum, Index,
    UniqueConstraint, CheckConstraint, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
import uuid
import enum
from typing import Optional
import os

from db import Base

# Check if we're using SQLite to handle UUID differently
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./emotional_support_db.db")
USE_SQLITE = "sqlite" in DATABASE_URL

# UUID column type that works with both SQLite and PostgreSQL
def get_uuid_column():
    if USE_SQLITE:
        return String(36)  # Store UUID as string in SQLite
    else:
        from sqlalchemy import UUID
        return UUID(as_uuid=True)

def generate_uuid():
    return str(uuid.uuid4()) if USE_SQLITE else uuid.uuid4()

# Enums for better data integrity
class RiskLevel(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class CrisisType(enum.Enum):
    SUICIDE_IDEATION = "suicide_ideation"
    SELF_HARM = "self_harm"
    SEVERE_DEPRESSION = "severe_depression"
    ANXIETY_PANIC = "anxiety_panic"
    SUBSTANCE_ABUSE = "substance_abuse"
    EATING_DISORDER = "eating_disorder"

class SessionStatus(enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class PostStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    FLAGGED = "flagged"
    REMOVED = "removed"

class MessageRole(enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class TherapistRole(enum.Enum):
    COUNSELOR = "counselor"
    PSYCHOLOGIST = "psychologist" 
    PSYCHIATRIST = "psychiatrist"
    CRISIS_SPECIALIST = "crisis_specialist"
    SUPERVISOR = "supervisor"

class TherapistStatus(enum.Enum):
    ACTIVE = "active"
    OFFLINE = "offline"
    BUSY = "busy"
    UNAVAILABLE = "unavailable"

class NotificationStatus(enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    READ = "read"
    FAILED = "failed"

# ===== USER MANAGEMENT =====

class User(Base):
    """
    Core user model with anonymous capabilities
    """
    __tablename__ = "users"
    
    # Primary identification
    id = Column(get_uuid_column(), primary_key=True, default=generate_uuid, index=True)
    
    # User credentials and basic info
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Anonymous identity (Reddit-style username)
    anonymous_username = Column(String(50), unique=True, nullable=False, index=True)
    username_changed = Column(Boolean, default=False)  # Track if user changed default username
    
    # College affiliation (for college-specific isolation)
    college_id = Column(String(100), nullable=False, index=True)
    college_name = Column(String(200), nullable=False)
    
    # Account status and tracking
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps with timezone awareness
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Privacy and preferences
    privacy_settings = Column(JSON, default={})  # Store user preferences as JSON
    notification_preferences = Column(JSON, default={})
    
    # Mental health profile (encrypted sensitive data)
    mental_health_profile = Column(Text, nullable=True)  # Encrypted JSON with user's mental health context
    
    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    crisis_alerts = relationship("CrisisAlert", back_populates="user")
    therapist_sessions = relationship("TherapistSession", back_populates="user")
    created_communities = relationship("Community", back_populates="creator")
    community_memberships = relationship("CommunityMembership", back_populates="user", cascade="all, delete-orphan", overlaps="user")
    community_posts = relationship("CommunityPost", back_populates="author")
    comments = relationship("Comment", back_populates="author")
    user_matches = relationship("UserMatch", foreign_keys="UserMatch.user_id", back_populates="user")
    
    # Constraints and indexes
    __table_args__ = (
        Index('idx_user_college_active', 'college_id', 'is_active'),
        Index('idx_user_email_active', 'email', 'is_active'),
        CheckConstraint('LENGTH(name) >= 2', name='check_name_length'),
        CheckConstraint('LENGTH(anonymous_username) >= 3', name='check_username_length'),
    )

# ===== CHAT SYSTEM =====

class ChatSession(Base):
    """
    Chat sessions - like conversations in ChatGPT
    """
    __tablename__ = "chat_sessions"
    
    id = Column(get_uuid_column(), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(get_uuid_column(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Session metadata
    title = Column(String(200), nullable=True)  # User can name their sessions
    session_number = Column(Integer, nullable=False)  # Sequential numbering per user
    
    # Risk assessment data
    current_risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.LOW, nullable=False)
    risk_score = Column(Float, default=0.0)  # 0.0 to 10.0 scale
    last_risk_assessment = Column(DateTime(timezone=True), nullable=True)
    
    # Session status
    is_active = Column(Boolean, default=True, index=True)
    is_archived = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_message_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Encrypted conversation summary for AI context
    conversation_summary = Column(Text, nullable=True)  # Encrypted summary for AI context
    total_messages = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_session_user_active', 'user_id', 'is_active'),
        Index('idx_session_risk', 'current_risk_level', 'last_risk_assessment'),
        UniqueConstraint('user_id', 'session_number', name='uq_user_session_number'),
    )

class ChatMessage(Base):
    """
    Individual messages within chat sessions
    """
    __tablename__ = "chat_messages"
    
    id = Column(get_uuid_column(), primary_key=True, default=generate_uuid, index=True)
    session_id = Column(get_uuid_column(), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Message content (encrypted for privacy)
    content = Column(Text, nullable=False)  # Encrypted message content
    role = Column(SQLEnum(MessageRole), nullable=False, index=True)
    
    # Message metadata
    message_order = Column(Integer, nullable=False)  # Sequential order within session
    token_count = Column(Integer, nullable=True)  # For AI model tracking
    
    # Risk detection data
    risk_indicators = Column(JSON, nullable=True)  # Detected risk keywords/patterns
    sentiment_score = Column(Float, nullable=True)  # -1.0 to 1.0 sentiment
    emotion_analysis = Column(JSON, nullable=True)  # Detected emotions and confidence scores
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # AI response metadata (for assistant messages)
    ai_model_used = Column(String(100), nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    
    __table_args__ = (
        Index('idx_message_session_order', 'session_id', 'message_order'),
        Index('idx_message_role_created', 'role', 'created_at'),
        UniqueConstraint('session_id', 'message_order', name='uq_session_message_order'),
    )

# ===== CRISIS MANAGEMENT =====

class CrisisAlert(Base):
    """
    Crisis detection and alert management
    """
    __tablename__ = "crisis_alerts"
    
    id = Column(get_uuid_column(), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(get_uuid_column(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(get_uuid_column(), ForeignKey("chat_sessions.id", ondelete="SET NULL"), nullable=True)
    
    # Crisis details
    crisis_type = Column(SQLEnum(CrisisType), nullable=False, index=True)
    risk_level = Column(SQLEnum(RiskLevel), nullable=False, index=True)
    confidence_score = Column(Float, nullable=False)  # AI confidence in detection
    
    # Detection context (encrypted)
    trigger_message = Column(Text, nullable=True)  # Encrypted message that triggered alert
    context_messages = Column(Text, nullable=True)  # Encrypted surrounding context
    detected_indicators = Column(JSON, nullable=False)  # Keywords, patterns detected
    
    # Alert management
    status = Column(String(50), default='pending', index=True)  # pending, acknowledged, escalated, resolved
    escalated_to_human = Column(Boolean, default=False, index=True)
    auto_resources_sent = Column(Boolean, default=False)

    assigned_therapist_id = Column(get_uuid_column(), nullable=True, index=True)  # Therapist handling this crisis
    
    # Response tracking
    response_actions = Column(JSON, nullable=True)  # Actions taken (resources sent, session scheduled, etc.)
    human_reviewer_id = Column(String(100), nullable=True)  # Staff member who reviewed
    resolution_notes = Column(Text, nullable=True)  # How the crisis was handled
    
    # Timestamps
    detected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="crisis_alerts")
    
    __table_args__ = (
        Index('idx_crisis_user_status', 'user_id', 'status'),
        Index('idx_crisis_risk_detected', 'risk_level', 'detected_at'),
        Index('idx_crisis_type_confidence', 'crisis_type', 'confidence_score'),
        Index('idx_crisis_assigned_therapist', 'assigned_therapist_id'),
    )

# ===== THERAPIST INTEGRATION =====

class Therapist(Base):
    """
    Therapist/counselor accounts for crisis management
    """
    __tablename__ = "therapists"

    # Primary identification
    id = Column(get_uuid_column(), primary_key=True, default=generate_uuid, index=True)
    
    # Basic info
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Professional info
    role = Column(SQLEnum(TherapistRole), nullable=False, index=True)
    license_number = Column(String(100), nullable=True)
    specializations = Column(String(500), nullable=True)  # JSON array as string
    
    # College affiliation
    college_id = Column(String(100), nullable=False, index=True)
    college_name = Column(String(200), nullable=False)
    
    # Status and availability
    status = Column(SQLEnum(TherapistStatus), default=TherapistStatus.ACTIVE, index=True)
    is_active = Column(Boolean, default=True, index=True)
    is_on_call = Column(Boolean, default=False)  # Available for crisis calls
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class TherapistSession(Base):
    """
    Scheduled therapy sessions with licensed professionals
    """
    __tablename__ = "therapist_sessions"
    
    id = Column(get_uuid_column(), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(get_uuid_column(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    crisis_alert_id = Column(get_uuid_column(), ForeignKey("crisis_alerts.id", ondelete="SET NULL"), nullable=True)
    
    # Session details
    session_type = Column(String(50), nullable=False, index=True)  # crisis, regular, follow_up, group
    urgency_level = Column(SQLEnum(RiskLevel), nullable=False, index=True)
    
    # Scheduling
    requested_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    scheduled_for = Column(DateTime(timezone=True), nullable=True, index=True)
    duration_minutes = Column(Integer, default=50)  # Standard therapy session length
    
    # External system integration
    external_therapist_id = Column(String(100), nullable=True)  # Reference to therapist platform
    external_session_id = Column(String(100), nullable=True)  # Reference to external booking system
    meeting_link = Column(String(500), nullable=True)  # Video call link
    
    # Session status and outcome
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.SCHEDULED, nullable=False, index=True)
    attended = Column(Boolean, nullable=True)
    session_notes = Column(Text, nullable=True)  # Encrypted therapist notes
    follow_up_needed = Column(Boolean, default=False)
    next_session_recommended = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="therapist_sessions")
    
    __table_args__ = (
        Index('idx_session_user_status', 'user_id', 'status'),
        Index('idx_session_scheduled', 'scheduled_for', 'status'),
        Index('idx_session_urgency', 'urgency_level', 'requested_at'),
    )

# ===== COMMUNITY PLATFORM =====

class Community(Base):
    """
    Student-created communities with their own rules and moderation
    """
    __tablename__ = "communities"
    
    # Primary identification
    id = Column(get_uuid_column(), primary_key=True, default=generate_uuid, index=True)
    
    # Community basic info
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=False)
    rules = Column(Text, nullable=True)  # Community-specific rules
    
    # Creator and moderation
    creator_id = Column(get_uuid_column(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    moderator_ids = Column(JSON, default=list)  # List of user IDs who can moderate
    
    # College affiliation (communities are college-specific)
    college_id = Column(String(100), nullable=False, index=True)
    
    # Community settings
    is_public = Column(Boolean, default=True)  # Public vs private communities
    allow_posts = Column(Boolean, default=True)
    require_approval = Column(Boolean, default=False)  # Posts need approval before showing
    
    # Community status
    is_active = Column(Boolean, default=True, index=True)
    is_featured = Column(Boolean, default=False)  # Featured communities
    
    # Engagement metrics
    member_count = Column(Integer, default=1)  # Creator is first member
    post_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    creator = relationship("User", back_populates="created_communities")
    posts = relationship("CommunityPost", back_populates="community", cascade="all, delete-orphan")
    memberships = relationship("CommunityMembership", back_populates="community", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_community_college_active', 'college_id', 'is_active'),
        Index('idx_community_featured', 'is_featured', 'created_at'),
    )

class CommunityMembership(Base):
    """
    Track which users are members of which communities
    """
    __tablename__ = "community_memberships"
    
    id = Column(get_uuid_column(), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(get_uuid_column(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    community_id = Column(get_uuid_column(), ForeignKey("communities.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Membership status
    is_moderator = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    
    # Membership tracking
    joined_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="community_memberships", overlaps="community_memberships")
    community = relationship("Community", back_populates="memberships")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'community_id', name='uq_user_community_membership'),
        Index('idx_membership_user_active', 'user_id', 'is_banned'),
    )

class ModerationAction(Base):
    """
    Track all moderation actions taken on posts/comments
    """
    __tablename__ = "moderation_actions"
    
    id = Column(get_uuid_column(), primary_key=True, default=generate_uuid, index=True)
    
    # What was moderated
    content_type = Column(String(20), nullable=False, index=True)  # 'post' or 'comment'
    content_id = Column(get_uuid_column(), nullable=False, index=True)  # ID of post or comment
    
    # Moderation details
    action_type = Column(String(50), nullable=False, index=True)  # 'auto_removed', 'flagged', 'approved', 'rejected'
    reason = Column(String(200), nullable=False)  # Why it was moderated
    ai_confidence = Column(Float, nullable=True)  # AI confidence score (0.0-1.0)
    
    # AI analysis results
    detected_categories = Column(JSON, nullable=True)  # Categories of harmful content detected
    toxicity_scores = Column(JSON, nullable=True)  # Detailed toxicity analysis
    
    # Content copy (for review purposes)
    original_content = Column(Text, nullable=False)  # Copy of the moderated content
    
    # Moderation context
    moderator_id = Column(get_uuid_column(), nullable=True, index=True)  # Null if automated
    community_id = Column(get_uuid_column(), ForeignKey("communities.id", ondelete="SET NULL"), nullable=True)
    author_id = Column(get_uuid_column(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Appeal system
    can_appeal = Column(Boolean, default=True)
    appeal_submitted = Column(Boolean, default=False)
    appeal_resolved = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    author = relationship("User")
    community = relationship("Community")
    
    __table_args__ = (
        Index('idx_moderation_content', 'content_type', 'content_id'),
        Index('idx_moderation_action_created', 'action_type', 'created_at'),
        Index('idx_moderation_author_community', 'author_id', 'community_id'),
    )

class CommunityPost(Base):
    """
    Anonymous community posts (Reddit-style)
    """
    __tablename__ = "community_posts"
    
    id = Column(get_uuid_column(), primary_key=True, default=generate_uuid, index=True)
    community_id = Column(get_uuid_column(), ForeignKey("communities.id", ondelete="CASCADE"), nullable=True, index=True)
    author_id = Column(get_uuid_column(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Post content
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=False)
    
    # College-specific isolation
    college_id = Column(String(100), nullable=False, index=True)
    
    # Moderation and safety
    moderation_status = Column(SQLEnum(PostStatus), default=PostStatus.PENDING, nullable=False, index=True)
    moderation_flags = Column(JSON, nullable=True)  # AI-detected issues
    human_review_required = Column(Boolean, default=False, index=True)
    auto_resources_attached = Column(Boolean, default=False)  # If AI attached mental health resources

    # AI analysis results
    toxicity_score = Column(Float, nullable=True)  # Overall toxicity (0.0-1.0)
    harmful_categories = Column(JSON, nullable=True)  # Categories of harmful content
    
    # Content categorization
    detected_topics = Column(JSON, nullable=True)  # AI-detected topics/themes
    sentiment_score = Column(Float, nullable=True)
    support_level_needed = Column(SQLEnum(RiskLevel), default=RiskLevel.LOW, nullable=False, index=True)
    
    # Engagement metrics
    view_count = Column(Integer, default=0)
    upvote_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    
    # Anonymous display settings
    anonymous_level = Column(Integer, default=2)  # 1=partial, 2=full anonymity
    show_college = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    author = relationship("User", back_populates="community_posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    community = relationship("Community", back_populates="posts")
    
    __table_args__ = (
        Index('idx_post_college_status', 'college_id', 'moderation_status'),
        Index('idx_post_created_status', 'created_at', 'moderation_status'),
        Index('idx_post_support_level', 'support_level_needed', 'created_at'),
    )

class Comment(Base):
    """
    Comments on community posts
    """
    __tablename__ = "comments"
    
    id = Column(get_uuid_column(), primary_key=True, default=generate_uuid, index=True)
    post_id = Column(get_uuid_column(), ForeignKey("community_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(get_uuid_column(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_comment_id = Column(get_uuid_column(), ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)  # For nested comments
    
    # Content
    content = Column(Text, nullable=False)
    
    # Moderation
    moderation_status = Column(SQLEnum(PostStatus), default=PostStatus.PENDING, nullable=False, index=True)
    moderation_flags = Column(JSON, nullable=True)
    
    # Engagement
    upvote_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    post = relationship("CommunityPost", back_populates="comments")
    author = relationship("User", back_populates="comments")
    replies = relationship("Comment", remote_side=[id], cascade="all, delete-orphan", single_parent=True)
    
    __table_args__ = (
        Index('idx_comment_post_created', 'post_id', 'created_at'),
        Index('idx_comment_status_created', 'moderation_status', 'created_at'),
    )

class PostVote(Base):
    """
    Upvotes and downvotes for posts
    """
    __tablename__ = "post_votes"
    
    id = Column(get_uuid_column(), primary_key=True, default=generate_uuid, index=True)
    post_id = Column(get_uuid_column(), ForeignKey("community_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(get_uuid_column(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Vote type
    vote_type = Column(String(10), nullable=False)  # 'upvote' or 'downvote'
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    post = relationship("CommunityPost")
    user = relationship("User")
    
    __table_args__ = (
        UniqueConstraint('post_id', 'user_id', name='uq_post_user_vote'),
        Index('idx_vote_post_type', 'post_id', 'vote_type'),
    )

class CommentVote(Base):
    """
    Upvotes and downvotes for comments
    """
    __tablename__ = "comment_votes"
    
    id = Column(get_uuid_column(), primary_key=True, default=generate_uuid, index=True)
    comment_id = Column(get_uuid_column(), ForeignKey("comments.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(get_uuid_column(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Vote type
    vote_type = Column(String(10), nullable=False)  # 'upvote' or 'downvote'
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    comment = relationship("Comment")
    user = relationship("User")
    
    __table_args__ = (
        UniqueConstraint('comment_id', 'user_id', name='uq_comment_user_vote'),
        Index('idx_comment_vote_type', 'comment_id', 'vote_type'),
    )

# ===== PEER MATCHING SYSTEM =====

class UserMatch(Base):
    """
    AI-generated user matches based on similar experiences
    """
    __tablename__ = "user_matches"
    
    id = Column(get_uuid_column(), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(get_uuid_column(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    matched_user_id = Column(get_uuid_column(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Matching algorithm data
    compatibility_score = Column(Float, nullable=False)  # 0.0 to 1.0
    matching_algorithm_version = Column(String(20), nullable=False)  # Track algorithm versions
    
    # Matching criteria that aligned
    shared_experiences = Column(JSON, nullable=True)  # Common themes/experiences
    shared_emotions = Column(JSON, nullable=True)  # Similar emotional patterns
    complementary_strengths = Column(JSON, nullable=True)  # How they can help each other
    
    # Interaction tracking
    connection_initiated = Column(Boolean, default=False)
    connection_accepted = Column(Boolean, nullable=True)
    interaction_count = Column(Integer, default=0)
    last_interaction = Column(DateTime(timezone=True), nullable=True)
    
    # Match quality feedback
    user_rating = Column(Integer, nullable=True)  # 1-5 star rating from user
    match_success = Column(Boolean, nullable=True)  # Did they form a helpful connection?
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Matches can expire
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="user_matches")
    matched_user = relationship("User", foreign_keys=[matched_user_id])
    
    __table_args__ = (
        Index('idx_match_user_score', 'user_id', 'compatibility_score'),
        Index('idx_match_created_score', 'created_at', 'compatibility_score'),
        UniqueConstraint('user_id', 'matched_user_id', name='uq_user_match_pair'),
        CheckConstraint('user_id != matched_user_id', name='check_no_self_match'),
        CheckConstraint('compatibility_score >= 0.0 AND compatibility_score <= 1.0', name='check_compatibility_range'),
    )

# ===== ANALYTICS AND TRACKING =====

class UserAnalytics(Base):
    """
    Analytics for understanding user patterns and improving AI
    """
    __tablename__ = "user_analytics"
    
    id = Column(get_uuid_column(), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(get_uuid_column(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Activity patterns
    total_sessions = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    avg_session_duration_minutes = Column(Float, default=0.0)
    preferred_interaction_times = Column(JSON, nullable=True)  # When user is most active
    
    # Emotional journey tracking
    emotional_trend_data = Column(JSON, nullable=True)  # Encrypted emotional progress over time
    crisis_episodes_count = Column(Integer, default=0)
    improvement_indicators = Column(JSON, nullable=True)  # Positive trend markers
    
    # AI interaction effectiveness
    ai_helpfulness_ratings = Column(JSON, nullable=True)  # User ratings of AI responses
    most_helpful_topics = Column(JSON, nullable=True)  # Topics where AI was most effective
    improvement_areas = Column(JSON, nullable=True)  # Where AI could do better
    
    # Resource utilization
    resources_accessed = Column(JSON, nullable=True)  # Which resources user engaged with
    therapist_sessions_attended = Column(Integer, default=0)
    community_engagement_level = Column(Float, default=0.0)  # 0.0 to 1.0 scale
    
    # Last updated
    last_calculated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_analytics_user_updated', 'user_id', 'last_calculated'),
    )
