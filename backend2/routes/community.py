from fastapi import APIRouter, HTTPException, Depends, status, Query, Body
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from db import get_db
from models import (
    User, Community, CommunityPost, Comment, CommunityMembership, 
    PostVote, CommentVote, ModerationAction,
    PostStatus, RiskLevel
)
from content_moderation_manager import ContentModerationManager
from pydantic import BaseModel

router = APIRouter(
    prefix="/community",
    tags=["community"],
)

# ===== PYDANTIC MODELS =====

class CommunityCreate(BaseModel):
    title: str
    description: str
    rules: Optional[str] = None
    is_public: bool = True
    require_approval: bool = False

class CommunityResponse(BaseModel):
    id: str
    title: str
    description: str
    rules: Optional[str]
    creator_id: str
    creator_username: str
    college_id: str
    is_public: bool
    member_count: int
    post_count: int
    is_member: Optional[bool] = None
    is_moderator: Optional[bool] = None
    created_at: datetime

class CommunityPostCreate(BaseModel):
    title: str
    content: str
    community_id: Optional[str] = None  # Can post to general feed or specific community

class CommunityPostResponse(BaseModel):
    id: str
    title: str
    content: str
    author_username: str
    community_title: Optional[str]
    upvote_count: int
    comment_count: int
    user_vote: Optional[str] = None  # 'upvote', 'downvote', or None
    created_at: datetime
    moderation_status: str

class CommentCreate(BaseModel):
    content: str
    parent_comment_id: Optional[str] = None

class CommentResponse(BaseModel):
    id: str
    content: str
    author_username: str
    upvote_count: int
    user_vote: Optional[str] = None
    replies: List['CommentResponse'] = []
    created_at: datetime

class VoteRequest(BaseModel):
    vote_type: str  # 'upvote' or 'downvote'

# ===== COMMUNITY MANAGEMENT =====

@router.post("/communities", response_model=CommunityResponse)
async def create_community(
    community_data: CommunityCreate,
    user_id: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Create a new community"""
    
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if community title already exists in this college
    existing_community = db.query(Community).filter(
        and_(
            Community.title == community_data.title,
            Community.college_id == user.college_id,
            Community.is_active == True
        )
    ).first()
    
    if existing_community:
        raise HTTPException(
            status_code=400, 
            detail="A community with this title already exists in your college"
        )
    
    # Create community
    new_community = Community(
        title=community_data.title,
        description=community_data.description,
        rules=community_data.rules,
        creator_id=user_id,
        college_id=user.college_id,
        is_public=community_data.is_public,
        require_approval=community_data.require_approval,
        member_count=1  # Creator is first member
    )
    
    db.add(new_community)
    db.flush()  # Get the ID
    
    # Add creator as first member
    membership = CommunityMembership(
        user_id=user_id,
        community_id=new_community.id,
        is_moderator=True  # Creator is automatically a moderator
    )
    
    db.add(membership)
    db.commit()
    db.refresh(new_community)
    
    return CommunityResponse(
        id=str(new_community.id),
        title=new_community.title,
        description=new_community.description,
        rules=new_community.rules,
        creator_id=str(new_community.creator_id),
        creator_username=user.anonymous_username,
        college_id=new_community.college_id,
        is_public=new_community.is_public,
        member_count=new_community.member_count,
        post_count=new_community.post_count,
        is_member=True,
        is_moderator=True,
        created_at=new_community.created_at
    )

@router.get("/communities", response_model=List[CommunityResponse])
async def get_communities(
    user_id: str = Query(...),
    college_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    my_communities: bool = Query(False),
    limit: int = Query(20, le=50),
    skip: int = Query(0),
    db: Session = Depends(get_db)
):
    """Get communities with filtering options"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    query = db.query(Community).options(joinedload(Community.creator)).filter(
        Community.is_active == True
    )
    
    # Filter by college (default to user's college)
    target_college = college_id if college_id else user.college_id
    query = query.filter(Community.college_id == target_college)
    
    # Show only public communities unless user is member
    if not my_communities:
        query = query.filter(Community.is_public == True)
    
    # Search filter
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Community.title.ilike(search_term),
                Community.description.ilike(search_term)
            )
        )
    
    # My communities filter
    if my_communities:
        user_community_ids = db.query(CommunityMembership.community_id).filter(
            CommunityMembership.user_id == user_id
        ).subquery()
        query = query.filter(Community.id.in_(user_community_ids))
    
    communities = query.order_by(
        Community.member_count.desc(),
        Community.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    # Get user memberships for these communities
    community_ids = [str(c.id) for c in communities]
    user_memberships = db.query(CommunityMembership).filter(
        and_(
            CommunityMembership.user_id == user_id,
            CommunityMembership.community_id.in_(community_ids)
        )
    ).all()
    
    membership_map = {str(m.community_id): m for m in user_memberships}
    
    # Format response
    response_communities = []
    for community in communities:
        membership = membership_map.get(str(community.id))
        
        response_communities.append(CommunityResponse(
            id=str(community.id),
            title=community.title,
            description=community.description,
            rules=community.rules,
            creator_id=str(community.creator_id),
            creator_username=community.creator.anonymous_username,
            college_id=community.college_id,
            is_public=community.is_public,
            member_count=community.member_count,
            post_count=community.post_count,
            is_member=membership is not None,
            is_moderator=membership.is_moderator if membership else False,
            created_at=community.created_at
        ))
    
    return response_communities

@router.post("/communities/{community_id}/join")
async def join_community(
    community_id: UUID,
    user_id: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Join a community"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found")
    
    # Check if already a member
    existing_membership = db.query(CommunityMembership).filter(
        and_(
            CommunityMembership.user_id == user_id,
            CommunityMembership.community_id == community_id
        )
    ).first()
    
    if existing_membership:
        raise HTTPException(status_code=400, detail="Already a member of this community")
    
    # Create membership
    membership = CommunityMembership(
        user_id=user_id,
        community_id=community_id
    )
    
    db.add(membership)
    
    # Update community member count
    community.member_count += 1
    
    db.commit()
    
    return {
        "message": "Successfully joined community",
        "community_id": str(community_id),
        "member_count": community.member_count
    }

# ===== POST MANAGEMENT =====

@router.post("/posts", response_model=CommunityPostResponse)
async def create_post(
    post_data: CommunityPostCreate,
    user_id: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Create a new community post with AI moderation"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    community = None
    if post_data.community_id:
        community = db.query(Community).filter(Community.id == post_data.community_id).first()
        if not community:
            raise HTTPException(status_code=404, detail="Community not found")
        
        # Check if user is a member
        membership = db.query(CommunityMembership).filter(
            and_(
                CommunityMembership.user_id == user_id,
                CommunityMembership.community_id == post_data.community_id
            )
        ).first()
        
        if not membership:
            raise HTTPException(status_code=403, detail="Must be a member to post in this community")
    
    # AI Content Moderation
    moderation_manager = ContentModerationManager(db)
    try:
        moderation_result = await moderation_manager.moderate_content(
            content=post_data.content,
            content_type="post",
            author_id=user_id,
            community_id=post_data.community_id,
            title=post_data.title
        )
    except Exception as e:
        # If moderation fails, allow post but flag for human review
        moderation_result = {
            "approved": True,
            "reason": "Moderation service temporarily unavailable",
            "confidence": 0.0,
            "categories": {},
            "action_required": False
        }
    
    # Determine post status based on moderation
    if not moderation_result["approved"]:
        # Content blocked by AI
        return {
            "error": "Content blocked",
            "reason": moderation_result["reason"],
            "can_appeal": True,
            "moderation_action_id": moderation_result.get("moderation_action_id"),
            "message": "Your post was automatically blocked for violating community guidelines. You can appeal this decision."
        }
    
    # Create post
    new_post = CommunityPost(
        title=post_data.title,
        content=post_data.content,
        author_id=user_id,
        community_id=post_data.community_id,
        college_id=user.college_id,
        moderation_status=PostStatus.APPROVED,  # Approved by AI
        toxicity_score=max(moderation_result["categories"].values()) if moderation_result["categories"] else 0.0,
        harmful_categories=moderation_result["categories"]
    )
    
    db.add(new_post)
    
    # Update community post count if posted to specific community
    if community:
        community.post_count += 1
    
    db.commit()
    db.refresh(new_post)
    
    # Update moderation record with actual post ID
    if moderation_result.get("moderation_action_id"):
        moderation_action = db.query(ModerationAction).filter(
            ModerationAction.id == moderation_result["moderation_action_id"]
        ).first()
        if moderation_action:
            moderation_action.content_id = str(new_post.id)
            db.commit()
    
    return CommunityPostResponse(
        id=str(new_post.id),
        title=new_post.title,
        content=new_post.content,
        author_username=user.anonymous_username,
        community_title=community.title if community else None,
        upvote_count=0,
        comment_count=0,
        user_vote=None,
        created_at=new_post.created_at,
        moderation_status=new_post.moderation_status.value
    )

@router.get("/posts", response_model=List[CommunityPostResponse])
async def get_posts(
    user_id: str = Query(...),
    community_id: Optional[str] = Query(None),
    sort_by: str = Query("recent", regex="^(recent|popular|controversial)$"),
    limit: int = Query(20, le=50),
    skip: int = Query(0),
    db: Session = Depends(get_db)
):
    """Get community posts with filtering and sorting"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Build query
    query = db.query(CommunityPost).options(
        joinedload(CommunityPost.author),
        joinedload(CommunityPost.community)
    ).filter(
        and_(
            CommunityPost.moderation_status == PostStatus.APPROVED,
            CommunityPost.college_id == user.college_id
        )
    )
    
    # Community filter
    if community_id:
        query = query.filter(CommunityPost.community_id == community_id)
    
    # Sorting
    if sort_by == "recent":
        query = query.order_by(CommunityPost.created_at.desc())
    elif sort_by == "popular":
        query = query.order_by(CommunityPost.upvote_count.desc(), CommunityPost.created_at.desc())
    elif sort_by == "controversial":
        # Posts with many votes but similar upvote/downvote counts
        query = query.order_by(
            func.abs(CommunityPost.upvote_count - CommunityPost.downvote_count).asc(),
            CommunityPost.created_at.desc()
        )
    
    posts = query.offset(skip).limit(limit).all()
    
    # Get user votes for these posts
    post_ids = [str(p.id) for p in posts]
    user_votes = db.query(PostVote).filter(
        and_(
            PostVote.user_id == user_id,
            PostVote.post_id.in_(post_ids)
        )
    ).all()
    
    vote_map = {str(v.post_id): v.vote_type for v in user_votes}
    
    # Format response
    response_posts = []
    for post in posts:
        response_posts.append(CommunityPostResponse(
            id=str(post.id),
            title=post.title,
            content=post.content,
            author_username=post.author.anonymous_username,
            community_title=post.community.title if post.community else None,
            upvote_count=post.upvote_count,
            comment_count=post.comment_count,
            user_vote=vote_map.get(str(post.id)),
            created_at=post.created_at,
            moderation_status=post.moderation_status.value
        ))
    
    return response_posts

# ===== VOTING SYSTEM =====

@router.post("/posts/{post_id}/vote")
async def vote_on_post(
    post_id: UUID,
    vote_data: VoteRequest,
    user_id: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Vote on a post (upvote or downvote)"""
    
    if vote_data.vote_type not in ["upvote", "downvote"]:
        raise HTTPException(status_code=400, detail="Invalid vote type")
    
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check existing vote
    existing_vote = db.query(PostVote).filter(
        and_(
            PostVote.post_id == post_id,
            PostVote.user_id == user_id
        )
    ).first()
    
    if existing_vote:
        if existing_vote.vote_type == vote_data.vote_type:
            # Remove vote (toggle)
            db.delete(existing_vote)
            if vote_data.vote_type == "upvote":
                post.upvote_count -= 1
            else:
                post.upvote_count += 1  # Remove downvote increases net upvotes
        else:
            # Change vote type
            existing_vote.vote_type = vote_data.vote_type
            existing_vote.updated_at = datetime.utcnow()
            # Adjust counts (removing old vote and adding new one)
            if vote_data.vote_type == "upvote":
                post.upvote_count += 2  # Remove downvote (-1) and add upvote (+1)
            else:
                post.upvote_count -= 2  # Remove upvote (-1) and add downvote (-1)
    else:
        # New vote
        new_vote = PostVote(
            post_id=post_id,
            user_id=user_id,
            vote_type=vote_data.vote_type
        )
        db.add(new_vote)
        
        if vote_data.vote_type == "upvote":
            post.upvote_count += 1
        else:
            post.upvote_count -= 1
    
    db.commit()
    
    return {
        "message": f"Vote {'updated' if existing_vote else 'added'} successfully",
        "new_upvote_count": post.upvote_count,
        "user_vote": vote_data.vote_type if not (existing_vote and existing_vote.vote_type == vote_data.vote_type) else None
    }

# ===== COMMENT SYSTEM =====

@router.post("/posts/{post_id}/comments", response_model=CommentResponse)
async def create_comment(
    post_id: UUID,
    comment_data: CommentCreate,
    user_id: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Create a comment on a post with AI moderation"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # AI Content Moderation for comment
    moderation_manager = ContentModerationManager(db)
    try:
        moderation_result = await moderation_manager.moderate_content(
            content=comment_data.content,
            content_type="comment",
            author_id=user_id,
            community_id=str(post.community_id) if post.community_id else None
        )
    except Exception:
        moderation_result = {"approved": True}
    
    # Block comment if flagged
    if not moderation_result["approved"]:
        return {
            "error": "Comment blocked",
            "reason": moderation_result["reason"],
            "can_appeal": True,
            "moderation_action_id": moderation_result.get("moderation_action_id")
        }
    
    # Create comment
    new_comment = Comment(
        content=comment_data.content,
        post_id=post_id,
        author_id=user_id,
        parent_comment_id=comment_data.parent_comment_id,
        moderation_status=PostStatus.APPROVED
    )
    
    db.add(new_comment)
    
    # Update post comment count
    post.comment_count += 1
    
    db.commit()
    db.refresh(new_comment)
    
    return CommentResponse(
        id=str(new_comment.id),
        content=new_comment.content,
        author_username=user.anonymous_username,
        upvote_count=0,
        user_vote=None,
        replies=[],
        created_at=new_comment.created_at
    )

# ===== MODERATION ROUTES =====

@router.get("/moderation/history/{user_id}")
async def get_user_moderation_history(
    user_id: str,
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db)
):
    """Get user's moderation history"""
    
    moderation_manager = ContentModerationManager(db)
    history = await moderation_manager.get_user_moderation_history(user_id, limit)
    
    return {
        "user_id": user_id,
        "moderation_history": history,
        "total_actions": len(history)
    }

@router.post("/moderation/appeal/{moderation_action_id}")
async def submit_moderation_appeal(
    moderation_action_id: UUID,
    appeal_data: Dict[str, str] = Body(...),
    user_id: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """Submit appeal for moderation action"""
    
    moderation_manager = ContentModerationManager(db)
    result = await moderation_manager.submit_appeal(
        moderation_action_id=str(moderation_action_id),
        user_id=user_id,
        appeal_reason=appeal_data.get("reason", "No reason provided")
    )
    
    return result