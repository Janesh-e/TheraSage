from emotion_utils import detect_emotion
from transformers import pipeline
import re

sentiment_pipeline = pipeline("sentiment-analysis")

NEGATIVE_WORDS = set([
    "fail", "hopeless", "useless", "can't", "tired", "exhausted", "messed up", 
    "overwhelmed", "worthless", "ashamed", "nothing works", "i'm done", "why bother",
    "depressed", "anxious", "stressed", "worried", "scared", "afraid", "sad",
    "angry", "frustrated", "disappointed", "hurt", "broken", "lost", "confused"
])

POSITIVE_WORDS = set([
    "good", "great", "happy", "excited", "joy", "wonderful", "amazing", "fantastic",
    "love", "grateful", "thankful", "blessed", "optimistic", "hopeful", "confident",
    "proud", "satisfied", "content", "peaceful", "calm", "relaxed"
])

INTENSITY_AMPLIFIERS = set([
    "very", "extremely", "incredibly", "absolutely", "completely", "totally",
    "really", "so", "quite", "rather", "pretty", "fairly", "somewhat",
    "always", "never", "everything", "nothing", "everyone", "nobody"
])

def emotional_density(text: str) -> float:
    """Calculate the density of emotional words in text"""
    words = re.findall(r'\b\w+\b', text.lower())
    if not words:
        return 0.0
    
    emotional_words = NEGATIVE_WORDS | POSITIVE_WORDS
    emotional_count = sum(1 for word in words if word in emotional_words)
    return emotional_count / len(words)

def calculate_emotional_intensity(messages: list[str]) -> float:
    """Calculate overall emotional intensity from messages"""
    if not messages:
        return 0.0
    
    full_text = " ".join(messages).lower()
    words = re.findall(r'\b\w+\b', full_text)
    
    if not words:
        return 0.0
    
    intensity_score = 0.0
    
    # Factor 1: Emotional word density
    emotional_density_score = emotional_density(full_text)
    intensity_score += emotional_density_score * 0.4
    
    # Factor 2: Intensity amplifiers
    amplifier_count = sum(1 for word in words if word in INTENSITY_AMPLIFIERS)
    amplifier_score = min(amplifier_count / len(words) * 10, 1.0)  # Cap at 1.0
    intensity_score += amplifier_score * 0.3
    
    # Factor 3: Repetition of emotional themes
    repetition_score = 1.0 - (len(set(messages)) / len(messages))
    intensity_score += repetition_score * 0.2
    
    # Factor 4: Length and detail (more detail often indicates higher emotional investment)
    avg_length = sum(len(msg.split()) for msg in messages) / len(messages)
    length_score = min(avg_length / 50, 1.0)  # Normalize to 0-1
    intensity_score += length_score * 0.1
    
    return min(intensity_score, 1.0)  # Cap at 1.0

def repetition_score(messages: list[str]) -> float:
    """Calculate how repetitive the messages are"""
    if not messages:
        return 1.0
    return len(set(messages)) / len(messages)

def analyze_session_depth(messages: list[str]) -> dict:
    """Analyze the depth and emotional content of a session"""
    if not messages:
        return {
            "should_reflect": False,
            "emotion": "neutral",
            "emotion_confidence": 0.0,
            "sentiment": "NEUTRAL",
            "sentiment_score": 0.0,
            "density": 0.0,
            "repetition": 1.0
        }
    
    full_text = "\n".join(messages)
    
    # Get emotion detection
    emotion_result = detect_emotion(full_text)
    
    # Get sentiment analysis
    sentiment_result = sentiment_pipeline(full_text[:512])[0]
    
    # Calculate metrics
    density = emotional_density(full_text)
    rep_score = repetition_score(messages)
    
    # Determine if reflection is needed
    should_reflect = (
        emotion_result["emotion"] in ["sadness", "anger", "fear"] and
        emotion_result["confidence"] > 0.6 and
        density > 0.04 and
        rep_score < 0.9 and
        sentiment_result["label"] == "NEGATIVE" and
        sentiment_result["score"] > 0.7
    )

    return {
        "should_reflect": should_reflect,
        "emotion": emotion_result["label"],
        "emotion_confidence": emotion_result["score"],
        "sentiment": sentiment_result["label"],
        "sentiment_score": sentiment_result["score"],
        "density": density,
        "repetition": rep_score
    }

def analyze_conversation_readiness(messages: list[str]) -> dict:
    """Analyze if conversation is ready for CBT intervention"""
    if not messages:
        return {
            "ready_for_cbt": False,
            "confidence": 0.0,
            "reasons": []
        }
    
    full_text = " ".join(messages).lower()
    readiness_score = 0.0
    reasons = []
    
    # Factor 1: Sufficient context (message count and length)
    if len(messages) >= 3:
        readiness_score += 0.2
        reasons.append("Sufficient message exchange")
    
    avg_length = sum(len(msg.split()) for msg in messages) / len(messages)
    if avg_length > 15:
        readiness_score += 0.2
        reasons.append("Detailed messages provided")
    
    # Factor 2: Specific situation mentioned
    situation_indicators = [
        "today", "yesterday", "this morning", "last night", "at work",
        "my boss", "my friend", "happened", "told me", "said to me"
    ]
    
    if any(indicator in full_text for indicator in situation_indicators):
        readiness_score += 0.3
        reasons.append("Specific situation described")
    
    # Factor 3: Emotional clarity
    emotion_result = detect_emotion(full_text)
    if emotion_result["confidence"] > 0.6:
        readiness_score += 0.2
        reasons.append(f"Clear emotional state: {emotion_result['label']}")
    
    # Factor 4: Problem-focused language
    problem_words = [
        "problem", "issue", "trouble", "difficult", "hard", "struggle",
        "challenge", "worry", "concern", "bothering", "upset"
    ]
    
    if any(word in full_text for word in problem_words):
        readiness_score += 0.1
        reasons.append("Problem-focused language detected")
    
    return {
        "ready_for_cbt": readiness_score >= 0.5,
        "confidence": readiness_score,
        "reasons": reasons
    }
