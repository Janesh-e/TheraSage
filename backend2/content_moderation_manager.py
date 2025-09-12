import os
import json
import requests
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from models import ModerationAction, User, Community
from dotenv import load_dotenv

load_dotenv()

class ContentModerationManager:
    """
    AI-powered content moderation using DeepSeek via OpenRouter
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "deepseek/deepseek-chat-v3.1:free"
    
    async def moderate_content(
        self, 
        content: str, 
        content_type: str,  # 'post' or 'comment'
        author_id: str,
        community_id: Optional[str] = None,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Moderate content using AI and return moderation decision
        
        Returns:
        {
            "approved": bool,
            "reason": str,
            "confidence": float,
            "categories": dict,
            "action_required": bool,
            "moderation_action_id": str (if content blocked)
        }
        """
        
        try:
            # Create comprehensive moderation prompt
            moderation_prompt = self._create_moderation_prompt(content, title)
            
            # Call DeepSeek for analysis
            analysis_result = await self._analyze_content_with_ai(moderation_prompt)
            
            # Make moderation decision
            moderation_decision = self._make_moderation_decision(analysis_result)
            
            # Log moderation action if content needs intervention
            if not moderation_decision["approved"]:
                moderation_action = await self._create_moderation_record(
                    content_type=content_type,
                    content_id="pending",  # Will be updated when post/comment is created
                    original_content=content,
                    author_id=author_id,
                    community_id=community_id,
                    analysis_result=analysis_result,
                    decision=moderation_decision
                )
                moderation_decision["moderation_action_id"] = str(moderation_action.id)
            
            return moderation_decision
            
        except Exception as e:
            print(f"Content moderation error: {e}")
            # Default to approval if moderation fails (fail-safe)
            return {
                "approved": True,
                "reason": "Moderation service temporarily unavailable",
                "confidence": 0.0,
                "categories": {},
                "action_required": False,
                "error": str(e)
            }
    
    def _create_moderation_prompt(self, content: str, title: Optional[str] = None) -> str:
        """Create comprehensive prompt for content moderation"""
        
        full_text = content
        if title:
            full_text = f"Title: {title}\n\nContent: {content}"
        
        return f"""
        You are an expert content moderator for a college mental health support platform. Analyze this user-generated content and determine if it should be approved or blocked.

        CONTENT TO ANALYZE:
        "{full_text}"

        MODERATION CRITERIA - Block content that contains:
        1. HATE SPEECH: Attacks against race, gender, sexuality, religion, disability
        2. HARASSMENT: Targeted bullying, threats, doxxing, stalking behavior  
        3. HARMFUL CONTENT: Self-harm instructions, dangerous activities, illegal content
        4. EXPLICIT CONTENT: Graphic violence, sexual content inappropriate for college platform
        5. SPAM/SCAM: Promotional spam, scams, repeated meaningless content
        6. MISINFORMATION: False medical/mental health advice, conspiracy theories
        7. PRIVACY VIOLATIONS: Personal information sharing, unauthorized photos

        IMPORTANT CONTEXT:
        - This is a mental health support platform for college students
        - Users may discuss depression, anxiety, stress - this is ALLOWED and ENCOURAGED
        - Emotional expression, venting, seeking help is NORMAL and should be APPROVED
        - Only block content that is genuinely harmful, not just sad or distressing
        - False positives harm students seeking help - be conservative with blocking

        Respond with EXACTLY this JSON format (no additional text):
        {{
            "should_block": true/false,
            "confidence": 0.0-1.0,
            "primary_reason": "specific reason if blocked",
            "categories": {{
                "hate_speech": 0.0-1.0,
                "harassment": 0.0-1.0,
                "harmful_content": 0.0-1.0,
                "explicit_content": 0.0-1.0,
                "spam": 0.0-1.0,
                "misinformation": 0.0-1.0,
                "privacy_violation": 0.0-1.0
            }},
            "reasoning": "brief explanation of decision"
        }}
        """
    
    async def _analyze_content_with_ai(self, prompt: str) -> Dict[str, Any]:
        """Send content to DeepSeek for analysis"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert content moderator. Always respond with valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 500
        }
        
        response = requests.post(self.base_url, headers=headers, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        
        # Parse JSON response
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Fallback parsing if JSON is malformed
            return {
                "should_block": False,
                "confidence": 0.0,
                "primary_reason": "Analysis parsing failed",
                "categories": {},
                "reasoning": "Could not parse AI response"
            }
    
    def _make_moderation_decision(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Make final moderation decision based on AI analysis"""
        
        should_block = analysis.get("should_block", False)
        confidence = analysis.get("confidence", 0.0)
        categories = analysis.get("categories", {})
        
        # Additional confidence threshold check
        if confidence < 0.6 and should_block:
            # Low confidence blocks should be approved (err on side of caution)
            should_block = False
            
        # Check if any category score is dangerously high
        high_risk_categories = ["hate_speech", "harassment", "harmful_content"]
        max_risk_score = max([categories.get(cat, 0.0) for cat in high_risk_categories])
        
        if max_risk_score > 0.8:
            should_block = True
            confidence = max(confidence, max_risk_score)
        
        return {
            "approved": not should_block,
            "reason": analysis.get("primary_reason", "Content violates community guidelines"),
            "confidence": confidence,
            "categories": categories,
            "action_required": should_block,
            "ai_reasoning": analysis.get("reasoning", "AI analysis completed")
        }
    
    async def _create_moderation_record(
        self,
        content_type: str,
        content_id: str,
        original_content: str,
        author_id: str,
        community_id: Optional[str],
        analysis_result: Dict[str, Any],
        decision: Dict[str, Any]
    ) -> ModerationAction:
        """Create moderation action record in database"""
        
        action_type = "auto_removed" if not decision["approved"] else "flagged"
        
        moderation_action = ModerationAction(
            content_type=content_type,
            content_id=content_id,
            action_type=action_type,
            reason=decision["reason"],
            ai_confidence=decision["confidence"],
            detected_categories=decision["categories"],
            toxicity_scores=analysis_result,
            original_content=original_content,
            moderator_id=None,  # Automated action
            community_id=community_id,
            author_id=author_id,
            can_appeal=True
        )
        
        self.db.add(moderation_action)
        self.db.commit()
        self.db.refresh(moderation_action)
        
        return moderation_action
    
    async def get_user_moderation_history(
        self, 
        user_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get user's moderation history for transparency"""
        
        actions = self.db.query(ModerationAction).filter(
            ModerationAction.author_id == user_id
        ).order_by(ModerationAction.created_at.desc()).limit(limit).all()
        
        history = []
        for action in actions:
            history.append({
                "id": str(action.id),
                "content_type": action.content_type,
                "action_type": action.action_type,
                "reason": action.reason,
                "created_at": action.created_at,
                "can_appeal": action.can_appeal,
                "appeal_submitted": action.appeal_submitted,
                "resolved": action.appeal_resolved,
                "confidence": action.ai_confidence,
                "content_preview": action.original_content[:100] + "..." if len(action.original_content) > 100 else action.original_content
            })
        
        return history
    
    async def submit_appeal(
        self, 
        moderation_action_id: str, 
        user_id: str, 
        appeal_reason: str
    ) -> Dict[str, Any]:
        """Allow users to appeal moderation decisions"""
        
        action = self.db.query(ModerationAction).filter(
            ModerationAction.id == moderation_action_id,
            ModerationAction.author_id == user_id
        ).first()
        
        if not action:
            return {
                "success": False,
                "message": "Moderation action not found or access denied"
            }
        
        if not action.can_appeal:
            return {
                "success": False,
                "message": "This action cannot be appealed"
            }
        
        if action.appeal_submitted:
            return {
                "success": False,
                "message": "Appeal already submitted"
            }
        
        # Mark appeal as submitted
        action.appeal_submitted = True
        
        # Store appeal reason in response_actions
        if not action.response_actions:
            action.response_actions = {}
        action.response_actions["appeal_reason"] = appeal_reason
        action.response_actions["appeal_submitted_at"] = datetime.utcnow().isoformat()
        
        self.db.commit()
        
        return {
            "success": True,
            "message": "Appeal submitted successfully. It will be reviewed by human moderators.",
            "appeal_id": str(action.id)
        }
    
    def get_community_moderation_stats(self, community_id: str) -> Dict[str, Any]:
        """Get moderation statistics for a community"""
        
        from sqlalchemy import func
        from datetime import timedelta
        
        # Recent moderation actions (last 30 days)
        recent_cutoff = datetime.utcnow() - timedelta(days=30)
        
        recent_actions = self.db.query(ModerationAction).filter(
            ModerationAction.community_id == community_id,
            ModerationAction.created_at >= recent_cutoff
        ).all()
        
        stats = {
            "total_actions_30d": len(recent_actions),
            "auto_removals": len([a for a in recent_actions if a.action_type == "auto_removed"]),
            "pending_appeals": len([a for a in recent_actions if a.appeal_submitted and not a.appeal_resolved]),
            "categories": {}
        }
        
        # Category breakdown
        categories = ["hate_speech", "harassment", "harmful_content", "explicit_content", "spam"]
        for category in categories:
            count = len([a for a in recent_actions if a.detected_categories and a.detected_categories.get(category, 0) > 0.5])
            stats["categories"][category] = count
        
        return stats