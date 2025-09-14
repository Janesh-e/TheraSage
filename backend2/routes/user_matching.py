from fastapi import APIRouter, HTTPException, Depends, status, Query, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from db import get_db
from models import User, UserMatch, ChatSession
from user_matching_engine import UserMatchingEngine
from pydantic import BaseModel

router = APIRouter(
    prefix="/user-matching",
    tags=["user-matching"],
)

# Pydantic models for requests/responses

class MatchGenerationRequest(BaseModel):
    regenerate: bool = False
    limit: int = 10

class MatchResponse(BaseModel):
    id: str
    matched_user_id: str
    matched_user_username: str
    compatibility_score: float
    rank: int
    match_reasons: List[str]
    detailed_scores: Dict[str, float]
    connection_initiated: bool
    connection_accepted: Optional[bool]
    created_at: datetime
    algorithm_version: str

class ConnectionRequest(BaseModel):
    action: str  # "initiate" or "respond"
    accepted: Optional[bool] = None  # Required for "respond" action

class MatchStatsResponse(BaseModel):
    total_matches: int
    high_quality_matches: int  # Score > 0.7
    connected_matches: int
    pending_connections: int
    avg_compatibility_score: float

# ===== MATCH GENERATION =====

@router.post("/generate/{user_id}")
async def generate_user_matches(
    user_id: str,
    request: MatchGenerationRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    Generate new matches for a user using the hybrid matching algorithm
    """
    # Verify user exists and is active
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User account is not active")
    
    # Check if user has sufficient conversation data
    session_count = db.query(ChatSession).filter(
        and_(
            ChatSession.user_id == user_id,
            ChatSession.total_messages >= 3
        )
    ).count()
    
    if session_count == 0:
        raise HTTPException(
            status_code=400,
            detail="Insufficient conversation data. Please have at least one conversation with 3+ messages before seeking matches."
        )
    
    # Check for existing matches if not regenerating
    if not request.regenerate:
        existing_matches = db.query(UserMatch).filter(
            and_(
                UserMatch.user_id == user_id,
                UserMatch.created_at >= datetime.utcnow() - timedelta(hours=24)
            )
        ).count()
        
        if existing_matches > 0:
            raise HTTPException(
                status_code=400,
                detail="Matches were already generated in the last 24 hours. Use regenerate=true to create new matches."
            )
    
    # Initialize matching engine
    matching_engine = UserMatchingEngine(db)
    
    try:
        # Generate matches
        matches = await matching_engine.generate_user_matches(
            user_id=user_id,
            limit=request.limit
        )
        
        if not matches:
            return {
                "message": "No compatible matches found at this time. Try again later as more users join.",
                "matches": [],
                "suggestions": [
                    "Continue having conversations to improve matching accuracy",
                    "Check back in a few days as more students join the platform",
                    "Consider exploring community posts for peer interaction"
                ]
            }
        
        return {
            "message": f"Found {len(matches)} potential matches",
            "matches": matches,
            "matching_criteria": {
                "conversation_similarity": "Based on topics and concerns discussed",
                "emotional_similarity": "Based on emotional patterns and experiences", 
                "behavioral_similarity": "Based on app usage and communication style",
                "risk_compatibility": "Based on support needs and mental health status"
            },
            "generated_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(days=7)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating matches: {str(e)}"
        )

@router.get("/matches/{user_id}", response_model=List[MatchResponse])
async def get_user_matches(
    user_id: str,
    limit: int = Query(20, le=50),
    include_expired: bool = Query(False),
    min_score: float = Query(0.0, ge=0.0, le=1.0),
    db: Session = Depends(get_db)
):
    """
    Get existing matches for a user
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Build query
    query = db.query(UserMatch).options(
        joinedload(UserMatch.matched_user)
    ).filter(UserMatch.user_id == user_id)
    
    # Apply filters
    if not include_expired:
        query = query.filter(
            or_(
                UserMatch.expires_at.is_(None),
                UserMatch.expires_at >= datetime.utcnow()
            )
        )
    
    if min_score > 0:
        query = query.filter(UserMatch.compatibility_score >= min_score)
    
    # Execute query
    matches = query.order_by(
        UserMatch.compatibility_score.desc()
    ).limit(limit).all()
    
    # Format response
    response_matches = []
    for i, match in enumerate(matches, 1):
        if match.matched_user and match.matched_user.is_active:
            response_matches.append(MatchResponse(
                id=str(match.id),
                matched_user_id=str(match.matched_user_id),
                matched_user_username=match.matched_user.anonymous_username,
                compatibility_score=match.compatibility_score,
                rank=i,
                match_reasons=match.shared_experiences or [],
                detailed_scores={
                    'conversation_similarity': 0.0,  # Would need to recalculate or store
                    'emotional_similarity': 0.0,
                    'behavioral_similarity': 0.0,
                    'risk_compatibility': 0.0,
                    'demographic_bonus': 0.0
                },
                connection_initiated=match.connection_initiated,
                connection_accepted=match.connection_accepted,
                created_at=match.created_at,
                algorithm_version=match.matching_algorithm_version
            ))
    
    return response_matches

@router.get("/match/{match_id}/details")
async def get_match_details(
    match_id: UUID,
    user_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific match
    """
    match = db.query(UserMatch).options(
        joinedload(UserMatch.user),
        joinedload(UserMatch.matched_user)
    ).filter(
        and_(
            UserMatch.id == match_id,
            UserMatch.user_id == user_id
        )
    ).first()
    
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    # Get additional context about the matched user (anonymized)
    matched_user = match.matched_user
    if not matched_user or not matched_user.is_active:
        raise HTTPException(status_code=404, detail="Matched user not found or inactive")
    
    # Get some general activity metrics (anonymized)
    recent_activity = db.query(ChatSession).filter(
        and_(
            ChatSession.user_id == matched_user.id,
            ChatSession.created_at >= datetime.utcnow() - timedelta(days=30)
        )
    ).count()
    
    return {
        "match_id": str(match.id),
        "matched_user": {
            "id": str(matched_user.id),
            "anonymous_username": matched_user.anonymous_username,
            "college_name": matched_user.college_name,
            "member_since": matched_user.created_at,
            "last_active": "Recently active" if matched_user.last_activity and 
                           matched_user.last_activity >= datetime.utcnow() - timedelta(days=7) 
                           else "Active this month",
            "recent_conversation_count": recent_activity
        },
        "compatibility_score": match.compatibility_score,
        "match_reasons": match.shared_experiences or [],
        "shared_experiences": match.shared_experiences or [],
        "complementary_strengths": match.complementary_strengths or [],
        "connection_status": {
            "initiated": match.connection_initiated,
            "accepted": match.connection_accepted,
            "interaction_count": match.interaction_count,
            "last_interaction": match.last_interaction
        },
        "matching_info": {
            "algorithm_version": match.matching_algorithm_version,
            "created_at": match.created_at,
            "expires_at": match.expires_at
        }
    }

# ===== CONNECTION MANAGEMENT =====

@router.post("/connect/{match_id}")
async def manage_connection(
    match_id: UUID,
    connection_request: ConnectionRequest,
    user_id: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """
    Initiate or respond to a connection request
    """
    match = db.query(UserMatch).filter(UserMatch.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    # Verify user is part of this match
    if str(match.user_id) != user_id and str(match.matched_user_id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized for this match")
    
    matching_engine = UserMatchingEngine(db)
    
    try:
        if connection_request.action == "initiate":
            if str(match.user_id) != user_id:
                raise HTTPException(status_code=403, detail="Only the original user can initiate connection")
            
            result = await matching_engine.initiate_connection(str(match_id))
            return result
            
        elif connection_request.action == "respond":
            if str(match.matched_user_id) != user_id:
                raise HTTPException(status_code=403, detail="Only the matched user can respond to connection")
            
            if connection_request.accepted is None:
                raise HTTPException(status_code=400, detail="'accepted' field is required for respond action")
            
            result = await matching_engine.respond_to_connection(
                str(match_id), 
                connection_request.accepted
            )
            return result
        
        else:
            raise HTTPException(status_code=400, detail="Invalid action. Use 'initiate' or 'respond'")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error managing connection: {str(e)}")

@router.get("/connections/{user_id}")
async def get_user_connections(
    user_id: str,
    status: Optional[str] = Query(None, regex="^(pending|connected|all)$"),
    limit: int = Query(20, le=50),
    db: Session = Depends(get_db)
):
    """
    Get user's connections and their status
    """
    # Base query - matches where user is either the initiator or recipient
    query = db.query(UserMatch).options(
        joinedload(UserMatch.user),
        joinedload(UserMatch.matched_user)
    ).filter(
        or_(
            UserMatch.user_id == user_id,
            UserMatch.matched_user_id == user_id
        )
    )
    
    # Apply status filter
    if status == "pending":
        query = query.filter(
            and_(
                UserMatch.connection_initiated == True,
                UserMatch.connection_accepted.is_(None)
            )
        )
    elif status == "connected":
        query = query.filter(UserMatch.connection_accepted == True)
    
    connections = query.order_by(UserMatch.last_interaction.desc()).limit(limit).all()
    
    result = []
    for connection in connections:
        # Determine the other user in the connection
        if str(connection.user_id) == user_id:
            other_user = connection.matched_user
            connection_role = "initiator"
        else:
            other_user = connection.user
            connection_role = "recipient"
        
        if other_user and other_user.is_active:
            # Determine connection status
            if connection.connection_accepted == True:
                conn_status = "connected"
            elif connection.connection_initiated and connection.connection_accepted is None:
                conn_status = "pending"
            elif connection.connection_accepted == False:
                conn_status = "declined"
            else:
                conn_status = "not_initiated"
            
            result.append({
                "match_id": str(connection.id),
                "other_user": {
                    "id": str(other_user.id),
                    "anonymous_username": other_user.anonymous_username,
                    "college_name": other_user.college_name
                },
                "connection_status": conn_status,
                "connection_role": connection_role,
                "compatibility_score": connection.compatibility_score,
                "interaction_count": connection.interaction_count,
                "last_interaction": connection.last_interaction,
                "created_at": connection.created_at
            })
    
    return {
        "connections": result,
        "total_count": len(result),
        "status_filter": status or "all"
    }

# ===== STATISTICS AND ANALYTICS =====

@router.get("/stats/{user_id}", response_model=MatchStatsResponse)
async def get_matching_statistics(
    user_id: str,
    days_back: int = Query(30, le=365),
    db: Session = Depends(get_db)
):
    """
    Get matching statistics for a user
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
    
    # Get match statistics
    base_query = db.query(UserMatch).filter(
        and_(
            UserMatch.user_id == user_id,
            UserMatch.created_at >= cutoff_date
        )
    )
    
    total_matches = base_query.count()
    high_quality_matches = base_query.filter(UserMatch.compatibility_score >= 0.7).count()
    connected_matches = base_query.filter(UserMatch.connection_accepted == True).count()
    pending_connections = base_query.filter(
        and_(
            UserMatch.connection_initiated == True,
            UserMatch.connection_accepted.is_(None)
        )
    ).count()
    
    # Calculate average compatibility score
    avg_score = db.query(func.avg(UserMatch.compatibility_score)).filter(
        and_(
            UserMatch.user_id == user_id,
            UserMatch.created_at >= cutoff_date
        )
    ).scalar() or 0.0
    
    return MatchStatsResponse(
        total_matches=total_matches,
        high_quality_matches=high_quality_matches,
        connected_matches=connected_matches,
        pending_connections=pending_connections,
        avg_compatibility_score=round(avg_score, 3)
    )

@router.get("/system/stats")
async def get_system_matching_statistics(
    college_id: Optional[str] = Query(None),
    days_back: int = Query(30, le=365),
    db: Session = Depends(get_db)
):
    """
    Get system-wide matching statistics (for admin/analytics)
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
    
    base_query = db.query(UserMatch).filter(UserMatch.created_at >= cutoff_date)
    
    if college_id:
        base_query = base_query.join(User).filter(User.college_id == college_id)
    
    # System statistics
    total_matches_created = base_query.count()
    successful_connections = base_query.filter(UserMatch.connection_accepted == True).count()
    pending_connections = base_query.filter(
        and_(
            UserMatch.connection_initiated == True,
            UserMatch.connection_accepted.is_(None)
        )
    ).count()
    
    # Quality metrics
    high_quality_matches = base_query.filter(UserMatch.compatibility_score >= 0.7).count()
    avg_compatibility = db.query(func.avg(UserMatch.compatibility_score)).filter(
        UserMatch.created_at >= cutoff_date
    ).scalar() or 0.0
    
    # Active users with matches
    users_with_matches = db.query(UserMatch.user_id).filter(
        UserMatch.created_at >= cutoff_date
    ).distinct().count()
    
    return {
        "period_days": days_back,
        "college_filter": college_id,
        "matching_activity": {
            "total_matches_created": total_matches_created,
            "successful_connections": successful_connections,
            "pending_connections": pending_connections,
            "connection_success_rate": round(
                (successful_connections / total_matches_created * 100) if total_matches_created > 0 else 0, 2
            )
        },
        "quality_metrics": {
            "high_quality_matches": high_quality_matches,
            "avg_compatibility_score": round(avg_compatibility, 3),
            "high_quality_rate": round(
                (high_quality_matches / total_matches_created * 100) if total_matches_created > 0 else 0, 2
            )
        },
        "user_engagement": {
            "users_with_matches": users_with_matches,
            "avg_matches_per_user": round(
                total_matches_created / users_with_matches if users_with_matches > 0 else 0, 1
            )
        }
    }

# ===== FEEDBACK AND IMPROVEMENT =====

@router.post("/feedback/{match_id}")
async def submit_match_feedback(
    match_id: UUID,
    feedback_data: Dict[str, Any] = Body(...),
    user_id: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """
    Submit feedback on a match to improve the algorithm
    """
    match = db.query(UserMatch).filter(
        and_(
            UserMatch.id == match_id,
            or_(
                UserMatch.user_id == user_id,
                UserMatch.matched_user_id == user_id
            )
        )
    ).first()
    
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    # Validate feedback
    rating = feedback_data.get("rating")
    if rating is not None and (rating < 1 or rating > 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    
    # Update match record
    if rating:
        match.user_rating = rating
    
    success = feedback_data.get("match_success")
    if success is not None:
        match.match_success = success
    
    # Store additional feedback in response_actions or similar field
    if not hasattr(match, 'feedback') or not match.feedback:
        match.feedback = {}
    
    match.feedback.update({
        f"feedback_{datetime.utcnow().isoformat()}": {
            "rating": rating,
            "success": success,
            "comments": feedback_data.get("comments", ""),
            "user_id": user_id
        }
    })
    
    db.commit()
    
    return {
        "message": "Feedback submitted successfully",
        "match_id": str(match_id),
        "thank_you": "Your feedback helps improve our matching algorithm for everyone!"
    }