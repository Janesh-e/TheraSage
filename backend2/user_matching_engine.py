import os
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_, desc
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import TruncatedSVD
import requests
from collections import defaultdict, Counter

from models import (
    User, ChatSession, ChatMessage, UserMatch, UserAnalytics,
    MessageRole, RiskLevel, PostStatus, CommunityPost, Comment
)
from dotenv import load_dotenv

load_dotenv()

class UserMatchingEngine:
    """
    Advanced user matching system for peer support using multiple similarity algorithms:
    1. Conversation Content Similarity (TF-IDF + Cosine)
    2. Emotional Pattern Similarity 
    3. Behavioral Pattern Similarity
    4. Risk Level and Concern Matching
    5. Hybrid Weighted Scoring
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = "deepseek/deepseek-chat-v3.1:free"
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Matching weights for hybrid algorithm
        self.weights = {
            'conversation_similarity': 0.35,  # Content similarity
            'emotional_similarity': 0.25,    # Emotional patterns
            'behavioral_similarity': 0.20,   # Activity patterns
            'risk_compatibility': 0.15,      # Risk level matching
            'demographic_bonus': 0.05        # Age, college bonus
        }
        
        # Similarity thresholds
        self.min_similarity_threshold = 0.3
        self.high_similarity_threshold = 0.7
        
    async def generate_user_matches(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Generate matches for a specific user using hybrid matching algorithm
        """
        target_user = self.db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise ValueError(f"User {user_id} not found")
        
        # Get potential candidates from same college
        candidates = self._get_matching_candidates(user_id, target_user.college_id)
        
        if not candidates:
            return []
        
        # Calculate comprehensive similarity scores
        similarity_scores = []
        
        for candidate in candidates:
            try:
                # Calculate multi-dimensional similarity
                scores = await self._calculate_comprehensive_similarity(target_user, candidate)
                
                # Calculate final weighted score
                final_score = self._calculate_weighted_score(scores)
                
                if final_score >= self.min_similarity_threshold:
                    similarity_scores.append({
                        'candidate': candidate,
                        'final_score': final_score,
                        'detailed_scores': scores,
                        'match_reasons': self._generate_match_reasons(scores)
                    })
            
            except Exception as e:
                print(f"Error calculating similarity for candidate {candidate.id}: {e}")
                continue
        
        # Sort by similarity score and return top matches
        similarity_scores.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Create match records in database
        matches = []
        for i, match_data in enumerate(similarity_scores[:limit]):
            match_record = await self._create_match_record(
                target_user, match_data['candidate'], match_data, i + 1
            )
            matches.append(match_record)
        
        return matches
    
    def _get_matching_candidates(self, target_user_id: str, college_id: str, max_candidates: int = 100) -> List[User]:
        """
        Get potential matching candidates with filtering criteria
        """
        # Get users from same college, exclude self, get active users
        base_query = self.db.query(User).filter(
            and_(
                User.college_id == college_id,
                User.id != target_user_id,
                User.is_active == True,
                User.last_activity >= datetime.utcnow() - timedelta(days=30)  # Active in last 30 days
            )
        )
        
        # Prioritize users with chat activity
        candidates = base_query.join(ChatSession).filter(
            ChatSession.total_messages >= 5  # Minimum conversation data
        ).distinct().limit(max_candidates).all()
        
        return candidates
    
    async def _calculate_comprehensive_similarity(self, user1: User, user2: User) -> Dict[str, float]:
        """
        Calculate similarity across multiple dimensions
        """
        scores = {}
        
        # 1. Conversation Content Similarity
        scores['conversation_similarity'] = await self._calculate_conversation_similarity(user1, user2)
        
        # 2. Emotional Pattern Similarity
        scores['emotional_similarity'] = await self._calculate_emotional_similarity(user1, user2)
        
        # 3. Behavioral Pattern Similarity
        scores['behavioral_similarity'] = self._calculate_behavioral_similarity(user1, user2)
        
        # 4. Risk Level Compatibility
        scores['risk_compatibility'] = self._calculate_risk_compatibility(user1, user2)
        
        # 5. Demographic Similarity Bonus
        scores['demographic_bonus'] = self._calculate_demographic_similarity(user1, user2)
        
        return scores
    
    async def _calculate_conversation_similarity(self, user1: User, user2: User) -> float:
        """
        Calculate similarity based on conversation content using TF-IDF and cosine similarity
        """
        try:
            # Get conversation content for both users
            user1_content = self._get_user_conversation_content(user1.id)
            user2_content = self._get_user_conversation_content(user2.id)
            
            if not user1_content or not user2_content:
                return 0.0
            
            # Use TF-IDF to vectorize conversation content
            vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2),  # Include bigrams
                min_df=1,
                max_df=0.95
            )
            
            # Fit and transform both texts
            tfidf_matrix = vectorizer.fit_transform([user1_content, user2_content])
            
            # Calculate cosine similarity
            similarity_matrix = cosine_similarity(tfidf_matrix)
            conversation_similarity = similarity_matrix[0, 1]
            
            return float(conversation_similarity)
            
        except Exception as e:
            print(f"Error calculating conversation similarity: {e}")
            return 0.0
    
    def _get_user_conversation_content(self, user_id: str, limit: int = 50) -> str:
        """
        Get recent conversation content for a user
        """
        # Get recent user messages from all sessions
        messages = self.db.query(ChatMessage).join(ChatSession).filter(
            and_(
                ChatSession.user_id == user_id,
                ChatMessage.role == MessageRole.USER,
                ChatMessage.created_at >= datetime.utcnow() - timedelta(days=30)
            )
        ).order_by(ChatMessage.created_at.desc()).limit(limit).all()
        
        # Combine message content
        content_parts = [msg.content for msg in messages if msg.content]
        return " ".join(content_parts)
    
    async def _calculate_emotional_similarity(self, user1: User, user2: User) -> float:
        """
        Calculate similarity based on emotional patterns and mental health themes
        """
        try:
            # Get emotional analysis data from messages
            user1_emotions = self._get_user_emotional_patterns(user1.id)
            user2_emotions = self._get_user_emotional_patterns(user2.id)
            
            if not user1_emotions or not user2_emotions:
                return 0.0
            
            # Calculate similarity between emotional patterns
            emotion_similarity = self._calculate_emotional_vector_similarity(
                user1_emotions, user2_emotions
            )
            
            return emotion_similarity
            
        except Exception as e:
            print(f"Error calculating emotional similarity: {e}")
            return 0.0
    
    def _get_user_emotional_patterns(self, user_id: str) -> Dict[str, float]:
        """
        Extract emotional patterns from user's conversation history
        """
        # Get messages with emotion analysis
        messages = self.db.query(ChatMessage).join(ChatSession).filter(
            and_(
                ChatSession.user_id == user_id,
                ChatMessage.role == MessageRole.USER,
                ChatMessage.emotion_analysis.isnot(None),
                ChatMessage.created_at >= datetime.utcnow() - timedelta(days=30)
            )
        ).all()
        
        if not messages:
            return {}
        
        # Aggregate emotional states
        emotion_counts = defaultdict(float)
        sentiment_scores = []
        
        for msg in messages:
            if msg.emotion_analysis:
                emotional_state = msg.emotion_analysis.get('emotional_state', 'neutral')
                emotion_counts[emotional_state] += 1
                
                if msg.sentiment_score is not None:
                    sentiment_scores.append(msg.sentiment_score)
        
        # Normalize emotion counts and add metrics
        total_messages = len(messages)
        emotional_pattern = {}
        
        for emotion, count in emotion_counts.items():
            emotional_pattern[emotion] = count / total_messages
        
        # Add aggregated metrics
        if sentiment_scores:
            emotional_pattern['avg_sentiment'] = np.mean(sentiment_scores)
            emotional_pattern['sentiment_variability'] = np.std(sentiment_scores)
        
        return emotional_pattern
    
    def _calculate_emotional_vector_similarity(self, emotions1: Dict[str, float], emotions2: Dict[str, float]) -> float:
        """
        Calculate cosine similarity between emotional pattern vectors
        """
        # Get all unique emotional states
        all_emotions = set(emotions1.keys()) | set(emotions2.keys())
        
        if not all_emotions:
            return 0.0
        
        # Create vectors
        vector1 = np.array([emotions1.get(emotion, 0.0) for emotion in all_emotions])
        vector2 = np.array([emotions2.get(emotion, 0.0) for emotion in all_emotions])
        
        # Calculate cosine similarity
        dot_product = np.dot(vector1, vector2)
        norms = np.linalg.norm(vector1) * np.linalg.norm(vector2)
        
        if norms == 0:
            return 0.0
        
        return dot_product / norms
    
    def _calculate_behavioral_similarity(self, user1: User, user2: User) -> float:
        """
        Calculate similarity based on activity patterns and usage behavior
        """
        try:
            # Get behavioral metrics for both users
            user1_behavior = self._get_user_behavioral_metrics(user1.id)
            user2_behavior = self._get_user_behavioral_metrics(user2.id)
            
            if not user1_behavior or not user2_behavior:
                return 0.0
            
            # Calculate behavioral similarity
            behavioral_similarity = self._calculate_behavioral_vector_similarity(
                user1_behavior, user2_behavior
            )
            
            return behavioral_similarity
            
        except Exception as e:
            print(f"Error calculating behavioral similarity: {e}")
            return 0.0
    
    def _get_user_behavioral_metrics(self, user_id: str) -> Dict[str, float]:
        """
        Extract behavioral patterns from user activity
        """
        # Get session statistics
        sessions = self.db.query(ChatSession).filter(
            and_(
                ChatSession.user_id == user_id,
                ChatSession.created_at >= datetime.utcnow() - timedelta(days=30)
            )
        ).all()
        
        if not sessions:
            return {}
        
        # Calculate behavioral metrics
        metrics = {}
        
        # Session patterns
        metrics['avg_session_length'] = np.mean([s.total_messages or 0 for s in sessions])
        metrics['total_sessions'] = len(sessions)
        metrics['avg_messages_per_session'] = np.mean([s.total_messages or 0 for s in sessions])
        
        # Timing patterns (hour of day analysis)
        session_hours = [s.created_at.hour for s in sessions]
        if session_hours:
            metrics['preferred_morning'] = sum(1 for h in session_hours if 6 <= h < 12) / len(session_hours)
            metrics['preferred_evening'] = sum(1 for h in session_hours if 18 <= h < 24) / len(session_hours)
            metrics['preferred_night'] = sum(1 for h in session_hours if 0 <= h < 6) / len(session_hours)
        
        # Risk progression
        risk_levels = [s.current_risk_level for s in sessions if s.current_risk_level]
        if risk_levels:
            metrics['avg_risk_level'] = np.mean([self._risk_level_to_numeric(r) for r in risk_levels])
        
        return metrics
    
    def _risk_level_to_numeric(self, risk_level: RiskLevel) -> float:
        """Convert risk level enum to numeric value"""
        mapping = {
            RiskLevel.LOW: 1.0,
            RiskLevel.MEDIUM: 2.0,
            RiskLevel.HIGH: 3.0,
            RiskLevel.CRITICAL: 4.0
        }
        return mapping.get(risk_level, 1.0)
    
    def _calculate_behavioral_vector_similarity(self, behavior1: Dict[str, float], behavior2: Dict[str, float]) -> float:
        """
        Calculate similarity between behavioral pattern vectors
        """
        # Get common behavioral metrics
        common_metrics = set(behavior1.keys()) & set(behavior2.keys())
        
        if not common_metrics:
            return 0.0
        
        # Create normalized vectors
        vector1 = np.array([behavior1[metric] for metric in common_metrics])
        vector2 = np.array([behavior2[metric] for metric in common_metrics])
        
        # Normalize vectors
        scaler = StandardScaler()
        if len(vector1) > 1:
            vector1 = scaler.fit_transform(vector1.reshape(-1, 1)).flatten()
            vector2 = scaler.transform(vector2.reshape(-1, 1)).flatten()
        
        # Calculate cosine similarity
        dot_product = np.dot(vector1, vector2)
        norms = np.linalg.norm(vector1) * np.linalg.norm(vector2)
        
        if norms == 0:
            return 0.0
        
        return dot_product / norms
    
    def _calculate_risk_compatibility(self, user1: User, user2: User) -> float:
        """
        Calculate compatibility based on risk levels and mental health concerns
        """
        try:
            # Get recent risk assessments
            user1_risk = self._get_user_risk_profile(user1.id)
            user2_risk = self._get_user_risk_profile(user2.id)
            
            if not user1_risk or not user2_risk:
                return 0.5  # Neutral compatibility if no data
            
            # Calculate risk compatibility
            risk_compatibility = self._calculate_risk_level_compatibility(
                user1_risk, user2_risk
            )
            
            return risk_compatibility
            
        except Exception as e:
            print(f"Error calculating risk compatibility: {e}")
            return 0.5
    
    def _get_user_risk_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's risk profile and mental health concerns
        """
        # Get recent sessions with risk data
        sessions = self.db.query(ChatSession).filter(
            and_(
                ChatSession.user_id == user_id,
                ChatSession.current_risk_level.isnot(None),
                ChatSession.last_risk_assessment >= datetime.utcnow() - timedelta(days=30)
            )
        ).order_by(ChatSession.last_risk_assessment.desc()).limit(10).all()
        
        if not sessions:
            return {}
        
        # Extract risk patterns
        risk_levels = [s.current_risk_level for s in sessions]
        risk_scores = [s.risk_score or 0 for s in sessions]
        
        # Get risk indicators from messages
        risk_indicators = []
        messages = self.db.query(ChatMessage).join(ChatSession).filter(
            and_(
                ChatSession.user_id == user_id,
                ChatMessage.risk_indicators.isnot(None),
                ChatMessage.created_at >= datetime.utcnow() - timedelta(days=30)
            )
        ).all()
        
        for msg in messages:
            if msg.risk_indicators:
                risk_indicators.extend(msg.risk_indicators.get('risk_factors', []))
        
        return {
            'current_risk_level': risk_levels[0] if risk_levels else RiskLevel.LOW,
            'avg_risk_score': np.mean(risk_scores) if risk_scores else 0.0,
            'risk_indicators': Counter(risk_indicators),
            'risk_stability': np.std([self._risk_level_to_numeric(r) for r in risk_levels]) if len(risk_levels) > 1 else 0.0
        }
    
    def _calculate_risk_level_compatibility(self, risk1: Dict[str, Any], risk2: Dict[str, Any]) -> float:
        """
        Calculate compatibility between two risk profiles
        """
        # Current risk level compatibility (similar levels are better)
        level1 = self._risk_level_to_numeric(risk1.get('current_risk_level', RiskLevel.LOW))
        level2 = self._risk_level_to_numeric(risk2.get('current_risk_level', RiskLevel.LOW))
        
        level_diff = abs(level1 - level2)
        level_compatibility = max(0, 1 - (level_diff / 3))  # Normalize to 0-1
        
        # Risk indicator similarity
        indicators1 = risk1.get('risk_indicators', Counter())
        indicators2 = risk2.get('risk_indicators', Counter())
        
        if indicators1 or indicators2:
            # Jaccard similarity for risk indicators
            set1 = set(indicators1.keys())
            set2 = set(indicators2.keys())
            
            if set1 or set2:
                intersection = len(set1 & set2)
                union = len(set1 | set2)
                indicator_similarity = intersection / union if union > 0 else 0
            else:
                indicator_similarity = 1.0
        else:
            indicator_similarity = 1.0
        
        # Combine scores
        compatibility = 0.6 * level_compatibility + 0.4 * indicator_similarity
        
        return compatibility
    
    def _calculate_demographic_similarity(self, user1: User, user2: User) -> float:
        """
        Calculate demographic similarity bonus
        """
        similarity_score = 0.0
        
        # Same college bonus (already filtered, but good to confirm)
        if user1.college_id == user2.college_id:
            similarity_score += 0.5
        
        # Account creation time proximity (similar time on platform)
        time_diff = abs((user1.created_at - user2.created_at).days)
        if time_diff <= 30:  # Created within 30 days of each other
            similarity_score += 0.3
        elif time_diff <= 90:  # Within 90 days
            similarity_score += 0.1
        
        # Activity recency
        if user1.last_activity and user2.last_activity:
            activity_diff = abs((user1.last_activity - user2.last_activity).days)
            if activity_diff <= 7:  # Both active in last week
                similarity_score += 0.2
        
        return min(similarity_score, 1.0)
    
    def _calculate_weighted_score(self, scores: Dict[str, float]) -> float:
        """
        Calculate final weighted similarity score
        """
        weighted_score = 0.0
        
        for dimension, weight in self.weights.items():
            score = scores.get(dimension, 0.0)
            weighted_score += weight * score
        
        return weighted_score
    
    def _generate_match_reasons(self, scores: Dict[str, float]) -> List[str]:
        """
        Generate human-readable reasons for the match
        """
        reasons = []
        
        if scores.get('conversation_similarity', 0) > 0.6:
            reasons.append("Similar conversation topics and concerns")
        
        if scores.get('emotional_similarity', 0) > 0.6:
            reasons.append("Similar emotional experiences and patterns")
        
        if scores.get('behavioral_similarity', 0) > 0.6:
            reasons.append("Similar app usage and communication style")
        
        if scores.get('risk_compatibility', 0) > 0.7:
            reasons.append("Compatible support needs and risk levels")
        
        if scores.get('demographic_bonus', 0) > 0.5:
            reasons.append("Similar background and platform experience")
        
        if not reasons:
            reasons.append("Potential for mutual support and understanding")
        
        return reasons
    
    async def _create_match_record(self, user1: User, user2: User, match_data: Dict[str, Any], rank: int) -> Dict[str, Any]:
        """
        Create match record in database
        """
        # Check if match already exists
        existing_match = self.db.query(UserMatch).filter(
            and_(
                UserMatch.user_id == user1.id,
                UserMatch.matched_user_id == user2.id
            )
        ).first()
        
        if existing_match:
            # Update existing match
            existing_match.compatibility_score = match_data['final_score']
            existing_match.shared_experiences = match_data['match_reasons']
            existing_match.matching_algorithm_version = "v2.0_hybrid"
            self.db.commit()
            match_record = existing_match
        else:
            # Create new match
            match_record = UserMatch(
                user_id=user1.id,
                matched_user_id=user2.id,
                compatibility_score=match_data['final_score'],
                matching_algorithm_version="v2.0_hybrid",
                shared_experiences=match_data['match_reasons'],
                shared_emotions=list(match_data['detailed_scores'].keys()),
                complementary_strengths=self._identify_complementary_strengths(match_data['detailed_scores'])
            )
            
            self.db.add(match_record)
            self.db.commit()
            self.db.refresh(match_record)
        
        # Format response
        return {
            'id': str(match_record.id),
            'matched_user_id': str(user2.id),
            'matched_user_username': user2.anonymous_username,
            'compatibility_score': match_record.compatibility_score,
            'rank': rank,
            'match_reasons': match_record.shared_experiences,
            'detailed_scores': match_data['detailed_scores'],
            'created_at': match_record.created_at,
            'algorithm_version': match_record.matching_algorithm_version
        }
    
    def _identify_complementary_strengths(self, scores: Dict[str, float]) -> List[str]:
        """
        Identify areas where users might complement each other
        """
        strengths = []
        
        if scores.get('emotional_similarity', 0) > 0.5:
            strengths.append("Emotional understanding and empathy")
        
        if scores.get('behavioral_similarity', 0) > 0.5:
            strengths.append("Similar coping strategies")
        
        if scores.get('conversation_similarity', 0) > 0.4:
            strengths.append("Shared interests and concerns")
        
        return strengths
    
    async def get_user_matches(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get existing matches for a user
        """
        matches = self.db.query(UserMatch).filter(
            UserMatch.user_id == user_id
        ).order_by(UserMatch.compatibility_score.desc()).limit(limit).all()
        
        result = []
        for match in matches:
            matched_user = self.db.query(User).filter(User.id == match.matched_user_id).first()
            if matched_user and matched_user.is_active:
                result.append({
                    'id': str(match.id),
                    'matched_user_id': str(matched_user.id),
                    'matched_user_username': matched_user.anonymous_username,
                    'compatibility_score': match.compatibility_score,
                    'match_reasons': match.shared_experiences or [],
                    'connection_initiated': match.connection_initiated,
                    'connection_accepted': match.connection_accepted,
                    'created_at': match.created_at,
                    'expires_at': match.expires_at
                })
        
        return result
    
    async def initiate_connection(self, match_id: str) -> Dict[str, Any]:
        """
        Initiate connection with a matched user
        """
        match = self.db.query(UserMatch).filter(UserMatch.id == match_id).first()
        if not match:
            raise ValueError("Match not found")
        
        if match.connection_initiated:
            raise ValueError("Connection already initiated")
        
        match.connection_initiated = True
        match.interaction_count += 1
        match.last_interaction = datetime.utcnow()
        
        self.db.commit()
        
        return {
            'message': 'Connection initiated successfully',
            'match_id': str(match.id),
            'next_step': 'Wait for the other user to accept your connection request'
        }
    
    async def respond_to_connection(self, match_id: str, accepted: bool) -> Dict[str, Any]:
        """
        Respond to a connection request
        """
        match = self.db.query(UserMatch).filter(UserMatch.id == match_id).first()
        if not match:
            raise ValueError("Match not found")
        
        if not match.connection_initiated:
            raise ValueError("No connection request to respond to")
        
        match.connection_accepted = accepted
        match.interaction_count += 1
        match.last_interaction = datetime.utcnow()
        
        self.db.commit()
        
        if accepted:
            return {
                'message': 'Connection accepted! You can now message each other.',
                'match_id': str(match.id),
                'status': 'connected'
            }
        else:
            return {
                'message': 'Connection declined.',
                'match_id': str(match.id),
                'status': 'declined'
            }