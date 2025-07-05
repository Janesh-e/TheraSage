from db import SessionLocal
from models import ConversationMessage
from datetime import datetime, timedelta
from depth_analyzer import analyze_session_depth, calculate_emotional_intensity
import re

class SessionManager:
    def __init__(self, user_id: str, lookback_minutes: int = 10):
        self.user_id = user_id
        self.lookback = timedelta(minutes=lookback_minutes)
        self.db = SessionLocal()

    def get_recent_user_messages(self, limit=10):
        """Get recent user messages within the lookback period"""
        now = datetime.utcnow()
        recent_messages = self.db.query(ConversationMessage)\
            .filter(
                ConversationMessage.user_id == self.user_id,
                ConversationMessage.sender == "user",
                ConversationMessage.timestamp >= now - self.lookback
            )\
            .order_by(ConversationMessage.timestamp.desc())\
            .limit(limit)\
            .all()
        return list(reversed([m.message for m in recent_messages]))
    
    def get_conversation_turn_count(self) -> int:
        """Count conversation turns in current session"""
        now = datetime.utcnow()
        turn_count = self.db.query(ConversationMessage)\
            .filter(
                ConversationMessage.user_id == self.user_id,
                ConversationMessage.timestamp >= now - self.lookback
            )\
            .count()
        return turn_count // 2  # Divide by 2 since each turn has user + assistant messages
    
    def analyze_conversation_depth(self) -> dict:
        """Analyze how deep the conversation has gone"""
        messages = self.get_recent_user_messages()
        if not messages:
            return {
                "context_depth": 0,
                "emotional_intensity": 0.0,
                "has_specific_situation": False,
                "recent_messages": []
            }

        # Calculate context depth based on multiple factors
        context_depth = self._calculate_context_depth(messages)
        emotional_intensity = calculate_emotional_intensity(messages)
        has_specific_situation = self._detect_specific_situation(messages)

        return {
            "context_depth": context_depth,
            "emotional_intensity": emotional_intensity,
            "has_specific_situation": has_specific_situation,
            "recent_messages": messages,
            "turn_count": self.get_conversation_turn_count()
        }
    
    def _calculate_context_depth(self, messages: list[str]) -> int:
        """Calculate context depth based on message content and patterns"""
        if not messages:
            return 0
        
        depth_score = 0
        combined_text = " ".join(messages).lower()
        
        # Factor 1: Message length and detail
        avg_length = sum(len(msg.split()) for msg in messages) / len(messages)
        if avg_length > 10:
            depth_score += 1
        if avg_length > 20:
            depth_score += 1
            
        # Factor 2: Number of messages (conversation turns)
        if len(messages) >= 2:
            depth_score += 1
        if len(messages) >= 4:
            depth_score += 1
            
        # Factor 3: Emotional depth indicators
        deep_emotion_words = [
            "feel", "feeling", "felt", "emotion", "heart", "soul", "deep", "really",
            "honestly", "truly", "actually", "always", "never", "everywhere",
            "everything", "nothing", "everyone", "nobody"
        ]
        
        emotion_count = sum(1 for word in deep_emotion_words if word in combined_text)
        if emotion_count >= 3:
            depth_score += 1
        if emotion_count >= 6:
            depth_score += 1
            
        # Factor 4: Specific situation indicators
        situation_words = [
            "happened", "today", "yesterday", "this morning", "last night",
            "at work", "at home", "with my", "my boss", "my friend", "my family",
            "relationship", "job", "school", "money", "health"
        ]
        
        situation_count = sum(1 for word in situation_words if word in combined_text)
        if situation_count >= 2:
            depth_score += 1
            
        # Factor 5: Vulnerability indicators
        vulnerable_phrases = [
            "i'm scared", "i'm worried", "i don't know", "i'm confused",
            "i'm struggling", "i'm having trouble", "i can't handle",
            "i'm overwhelmed", "i'm stressed", "i'm anxious"
        ]
        
        vulnerable_count = sum(1 for phrase in vulnerable_phrases if phrase in combined_text)
        if vulnerable_count >= 1:
            depth_score += 1
            
        return min(depth_score, 6)  # Cap at 6 for maximum depth
    
    def _detect_specific_situation(self, messages: list[str]) -> bool:
        """Detect if user has shared a specific situation or just general feelings"""
        combined_text = " ".join(messages).lower()
        
        # Look for specific situation indicators
        situation_patterns = [
            r'\b(today|yesterday|this morning|last night|this week)\b',
            r'\b(at work|at home|at school|in class|at the office)\b',
            r'\b(my \w+|with my|told me|said to me)\b',
            r'\b(happened|occurred|went|did|said|told)\b.*\b(to me|with me|at me)\b',
            r'\b(argument|fight|disagreement|conflict|problem|issue)\b',
        ]
        
        for pattern in situation_patterns:
            if re.search(pattern, combined_text):
                return True
                
        return False

    def analyze_session(self) -> dict:
        """Legacy method for backward compatibility"""
        messages = self.get_recent_user_messages()
        if not messages:
            return {"should_reflect": False}

        analysis = analyze_session_depth(messages)
        return {
            "should_reflect": analysis["should_reflect"],
            "emotion": analysis["emotion"],
            "confidence": analysis["emotion_confidence"],
            "sentiment": analysis["sentiment"],
            "density": analysis["density"],
            "repetition": analysis["repetition"],
            "messages": messages,
        }

    def close(self):
        self.db.close()
