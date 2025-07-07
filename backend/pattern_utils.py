from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional
from db import SessionLocal
from models import ConversationMessage, JournalEntry
from sqlalchemy import and_, func
import re

class PatternRecognizer:
    def __init__(self):
        self.emotion_synonyms = {
            'anxious': ['worried', 'nervous', 'stressed', 'overwhelmed', 'panicked'],
            'sad': ['depressed', 'down', 'low', 'upset', 'disappointed'],
            'angry': ['frustrated', 'irritated', 'mad', 'annoyed', 'furious'],
            'lonely': ['isolated', 'alone', 'disconnected', 'abandoned'],
            'confused': ['lost', 'uncertain', 'unclear', 'puzzled'],
            'hopeless': ['defeated', 'discouraged', 'pessimistic', 'despairing']
        }
        
        self.trigger_keywords = {
            'work': ['job', 'boss', 'colleague', 'workplace', 'office', 'meeting'],
            'relationship': ['partner', 'boyfriend', 'girlfriend', 'spouse', 'friend', 'family'],
            'social': ['people', 'social', 'party', 'gathering', 'public', 'crowd'],
            'health': ['sick', 'tired', 'pain', 'doctor', 'medical', 'illness'],
            'money': ['financial', 'money', 'bills', 'debt', 'budget', 'expensive'],
            'family': ['mom', 'dad', 'parent', 'sibling', 'child', 'family'],
            'self': ['myself', 'worthless', 'failure', 'stupid', 'ugly', 'inadequate']
        }

    def analyze_emotional_patterns(self, user_id: str, days_back: int = 14) -> Dict:
        """Analyze emotional patterns over the specified time period"""
        db = SessionLocal()
        
        # Get cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Get conversation messages from the time period
        messages = db.query(ConversationMessage)\
            .filter(and_(
                ConversationMessage.user_id == user_id,
                ConversationMessage.sender == 'user',
                ConversationMessage.timestamp >= cutoff_date
            ))\
            .order_by(ConversationMessage.timestamp)\
            .all()
        
        # Get journal entries for emotion data
        journal_entries = db.query(JournalEntry)\
            .filter(and_(
                JournalEntry.user_id == user_id,
                JournalEntry.timestamp >= cutoff_date
            ))\
            .order_by(JournalEntry.timestamp)\
            .all()
        
        db.close()
        
        # Extract emotions and triggers
        emotions_over_time = self._extract_emotions_from_entries(journal_entries)
        triggers_over_time = self._extract_triggers_from_messages(messages)
        
        # Analyze patterns
        patterns = self._detect_patterns(emotions_over_time, triggers_over_time, days_back)
        
        return patterns

    def _extract_emotions_from_entries(self, journal_entries: List[JournalEntry]) -> List[Dict]:
        """Extract emotions from journal entries with updated parsing for new format"""
        emotions = []
        
        for entry in journal_entries:
            # Handle both CBT session and emotional check-in formats
            if entry.entry_type == "cbt_session":
                # Parse CBT session format: "Emotion detected: sadness (confidence: 0.98)"
                emotion_match = re.search(r'Emotion detected:\s*(\w+)\s*\(confidence:\s*([\d.]+)\)', entry.content)
                if emotion_match:
                    emotion = emotion_match.group(1).lower()
                    confidence = float(emotion_match.group(2))
                    
                    # Also extract cognitive distortion if present
                    distortion_match = re.search(r'Cognitive distortion:\s*([^\n]+)', entry.content)
                    distortion = distortion_match.group(1).strip() if distortion_match else None
                    
                    emotions.append({
                        'emotion': emotion,
                        'confidence': confidence,
                        'timestamp': entry.timestamp,
                        'entry_type': entry.entry_type,
                        'distortion': distortion
                    })
            
            elif entry.entry_type == "emotional_checkin":
                # Parse emotional check-in format: "Emotion: sadness (confidence: 0.98)"
                emotion_match = re.search(r'Emotion:\s*(\w+)\s*\(confidence:\s*([\d.]+)\)', entry.content)
                if emotion_match:
                    emotion = emotion_match.group(1).lower()
                    confidence = float(emotion_match.group(2))
                    
                    # Extract conversation phase if present
                    phase_match = re.search(r'Phase:\s*(\w+)', entry.content)
                    phase = phase_match.group(1) if phase_match else 'unknown'
                    
                    # Extract user shared content for additional context
                    user_shared_match = re.search(r'User shared:\s*(.+?)(?:\.\.\.|$)', entry.content, re.DOTALL)
                    user_shared = user_shared_match.group(1).strip() if user_shared_match else ''
                    
                    emotions.append({
                        'emotion': emotion,
                        'confidence': confidence,
                        'timestamp': entry.timestamp,
                        'entry_type': entry.entry_type,
                        'phase': phase,
                        'user_shared': user_shared
                    })
            
            else:
                # Fallback: try to parse any emotion pattern in the content
                emotion_patterns = [
                    r'Emotion[^:]*:\s*(\w+)\s*\(confidence:\s*([\d.]+)\)',
                    r'Emotion[^:]*:\s*(\w+).*?confidence[^:]*:\s*([\d.]+)',
                    r'(\w+)\s*\(confidence:\s*([\d.]+)\)'
                ]
                
                for pattern in emotion_patterns:
                    emotion_match = re.search(pattern, entry.content, re.IGNORECASE)
                    if emotion_match:
                        emotion = emotion_match.group(1).lower()
                        confidence = float(emotion_match.group(2))
                        
                        emotions.append({
                            'emotion': emotion,
                            'confidence': confidence,
                            'timestamp': entry.timestamp,
                            'entry_type': entry.entry_type or 'unknown'
                        })
                        break
        
        return emotions

    def _extract_triggers_from_messages(self, messages: List[ConversationMessage]) -> List[Dict]:
        """Extract potential triggers from user messages"""
        triggers = []
        
        for message in messages:
            detected_triggers = []
            message_lower = message.message.lower()
            
            # Check for trigger keywords
            for trigger_category, keywords in self.trigger_keywords.items():
                if any(keyword in message_lower for keyword in keywords):
                    detected_triggers.append(trigger_category)
            
            if detected_triggers:
                triggers.append({
                    'triggers': detected_triggers,
                    'timestamp': message.timestamp,
                    'message': message.message[:100]  # First 100 chars for context
                })
        
        return triggers

    def _detect_patterns(self, emotions: List[Dict], triggers: List[Dict], days_back: int) -> Dict:
        """Detect recurring patterns in emotions and triggers"""
        patterns = {
            'recurring_emotions': {},
            'recurring_triggers': {},
            'emotional_cycles': [],
            'trigger_emotion_correlations': {},
            'cbt_patterns': {},
            'confidence_trends': {},
            'recommendations': []
        }
        
        # Group emotions by type and count occurrences
        emotion_counts = Counter()
        emotion_dates = defaultdict(list)
        confidence_by_emotion = defaultdict(list)
        cbt_distortions = Counter()
        
        for emotion_data in emotions:
            emotion = emotion_data['emotion']
            timestamp = emotion_data['timestamp']
            confidence = emotion_data['confidence']
            
            # Count main emotion and synonyms
            emotion_counts[emotion] += 1
            emotion_dates[emotion].append(timestamp)
            confidence_by_emotion[emotion].append(confidence)
            
            # Track CBT distortions if present
            if emotion_data.get('distortion') and emotion_data['distortion'] != 'None identified':
                cbt_distortions[emotion_data['distortion']] += 1
            
            # Check for synonym patterns
            for main_emotion, synonyms in self.emotion_synonyms.items():
                if emotion in synonyms:
                    emotion_counts[main_emotion] += 1
                    emotion_dates[main_emotion].append(timestamp)
                    confidence_by_emotion[main_emotion].append(confidence)
        
        # Identify recurring emotions (appeared 3+ times)
        recurring_emotions = {
            emotion: count for emotion, count in emotion_counts.items() 
            if count >= 3
        }
        
        # Analyze confidence trends
        confidence_trends = {}
        for emotion, confidences in confidence_by_emotion.items():
            if len(confidences) >= 2:
                avg_confidence = sum(confidences) / len(confidences)
                confidence_trends[emotion] = {
                    'average_confidence': round(avg_confidence, 2),
                    'highest_confidence': max(confidences),
                    'lowest_confidence': min(confidences),
                    'trend': 'increasing' if confidences[-1] > confidences[0] else 'decreasing'
                }
        
        # Analyze trigger patterns
        trigger_counts = Counter()
        for trigger_data in triggers:
            for trigger in trigger_data['triggers']:
                trigger_counts[trigger] += 1
        
        recurring_triggers = {
            trigger: count for trigger, count in trigger_counts.items() 
            if count >= 2
        }
        
        # Detect emotional cycles (same emotion recurring within short periods)
        cycles = self._detect_emotional_cycles(emotion_dates, days_back)
        
        # Correlate triggers with emotions
        correlations = self._correlate_triggers_emotions(emotions, triggers)
        
        patterns.update({
            'recurring_emotions': recurring_emotions,
            'recurring_triggers': recurring_triggers,
            'emotional_cycles': cycles,
            'trigger_emotion_correlations': correlations,
            'cbt_patterns': dict(cbt_distortions) if cbt_distortions else {},
            'confidence_trends': confidence_trends,
            'analysis_period': f"{days_back} days",
            'total_emotional_events': len(emotions)
        })
        
        # Generate recommendations
        patterns['recommendations'] = self._generate_recommendations(patterns)
        
        return patterns

    def _detect_emotional_cycles(self, emotion_dates: Dict, days_back: int) -> List[Dict]:
        """Detect if emotions are recurring in cycles"""
        cycles = []
        
        for emotion, dates in emotion_dates.items():
            if len(dates) < 3:
                continue
                
            # Sort dates
            dates.sort()
            
            # Check for patterns (e.g., every few days)
            intervals = []
            for i in range(1, len(dates)):
                interval = (dates[i] - dates[i-1]).days
                intervals.append(interval)
            
            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                
                # If emotion occurs regularly (every 3-7 days), flag as cycle
                if 2 <= avg_interval <= 7 and len(dates) >= 3:
                    cycles.append({
                        'emotion': emotion,
                        'frequency': f"Every ~{avg_interval:.1f} days",
                        'occurrences': len(dates),
                        'last_occurrence': dates[-1],
                        'pattern_strength': 'high' if len(dates) >= 4 else 'moderate'
                    })
        
        return cycles

    def _correlate_triggers_emotions(self, emotions: List[Dict], triggers: List[Dict]) -> Dict:
        """Find correlations between triggers and emotions"""
        correlations = defaultdict(list)
        
        # For each emotion, find triggers that occurred within 24 hours
        for emotion_data in emotions:
            emotion = emotion_data['emotion']
            emotion_time = emotion_data['timestamp']
            
            for trigger_data in triggers:
                trigger_time = trigger_data['timestamp']
                time_diff = abs((emotion_time - trigger_time).total_seconds() / 3600)  # hours
                
                if time_diff <= 24:  # Within 24 hours
                    for trigger in trigger_data['triggers']:
                        correlations[f"{trigger} → {emotion}"].append({
                            'trigger_time': trigger_time,
                            'emotion_time': emotion_time,
                            'time_gap_hours': time_diff
                        })
        
        # Filter correlations that appear multiple times
        significant_correlations = {
            pattern: occurrences for pattern, occurrences in correlations.items()
            if len(occurrences) >= 2
        }
        
        return significant_correlations

    def _generate_recommendations(self, patterns: Dict) -> List[str]:
        """Generate personalized recommendations based on patterns"""
        recommendations = []
        
        recurring_emotions = patterns['recurring_emotions']
        cycles = patterns['emotional_cycles']
        correlations = patterns['trigger_emotion_correlations']
        cbt_patterns = patterns['cbt_patterns']
        confidence_trends = patterns['confidence_trends']
        
        # Recommendations for recurring emotions
        for emotion, count in recurring_emotions.items():
            if count >= 3:
                recommendations.append(
                    f"I've noticed you've felt {emotion} {count} times recently. "
                    f"Would you like to explore what might be behind this pattern?"
                )
        
        # Recommendations for emotional cycles
        for cycle in cycles:
            emotion = cycle['emotion']
            frequency = cycle['frequency']
            recommendations.append(
                f"You seem to experience {emotion} feelings {frequency}. "
                f"Recognizing this pattern might help us work on prevention strategies."
            )
        
        # Recommendations for trigger-emotion correlations
        for pattern, occurrences in correlations.items():
            if len(occurrences) >= 3:
                recommendations.append(
                    f"I notice a pattern: {pattern.replace('→', 'often leads to')} feelings. "
                    f"This has happened {len(occurrences)} times. Want to explore coping strategies?"
                )
        
        # Recommendations for CBT patterns
        if cbt_patterns:
            most_common_distortion = max(cbt_patterns.items(), key=lambda x: x[1])
            recommendations.append(
                f"Your most common cognitive distortion is '{most_common_distortion[0]}' "
                f"({most_common_distortion[1]} times). Let's work on recognizing and challenging this pattern."
            )
        
        # Recommendations for confidence trends
        for emotion, trend_data in confidence_trends.items():
            if trend_data['average_confidence'] >= 0.8:
                recommendations.append(
                    f"You're becoming very aware of your {emotion} feelings "
                    f"(avg confidence: {trend_data['average_confidence']}). This self-awareness is a great strength."
                )
        
        # General recommendations
        if not recommendations:
            recommendations.append(
                "I'm learning about your emotional patterns. Keep sharing with me to help identify useful insights."
            )
        
        return recommendations

    def should_surface_pattern(self, patterns: Dict) -> bool:
        """Determine if patterns are significant enough to surface to user"""
        recurring_emotions = patterns['recurring_emotions']
        cycles = patterns['emotional_cycles']
        correlations = patterns['trigger_emotion_correlations']
        cbt_patterns = patterns['cbt_patterns']
        
        # Surface if we have significant patterns
        return (
            len(recurring_emotions) > 0 or
            len(cycles) > 0 or
            len(correlations) > 0 or
            len(cbt_patterns) > 0
        )

    def get_pattern_summary(self, patterns: Dict) -> str:
        """Generate a user-friendly summary of patterns"""
        if not self.should_surface_pattern(patterns):
            return None
        
        summary_parts = []
        
        # Most frequent emotion
        recurring_emotions = patterns['recurring_emotions']
        if recurring_emotions:
            top_emotion = max(recurring_emotions.items(), key=lambda x: x[1])
            summary_parts.append(f"Your most frequent emotion has been '{top_emotion[0]}' ({top_emotion[1]} times)")
        
        # Cycles
        cycles = patterns['emotional_cycles']
        if cycles:
            strongest_cycle = max(cycles, key=lambda x: x['occurrences'])
            summary_parts.append(f"You tend to feel {strongest_cycle['emotion']} {strongest_cycle['frequency']}")
        
        # Correlations
        correlations = patterns['trigger_emotion_correlations']
        if correlations:
            top_correlation = max(correlations.items(), key=lambda x: len(x[1]))
            summary_parts.append(f"Pattern noticed: {top_correlation[0].replace('→', ' often leads to')}")
        
        # CBT patterns
        cbt_patterns = patterns['cbt_patterns']
        if cbt_patterns:
            top_distortion = max(cbt_patterns.items(), key=lambda x: x[1])
            summary_parts.append(f"Common thinking pattern: {top_distortion[0]} ({top_distortion[1]} times)")
        
        if summary_parts:
            return "🔍 **Pattern Insights**: " + " | ".join(summary_parts)
        
        return None
