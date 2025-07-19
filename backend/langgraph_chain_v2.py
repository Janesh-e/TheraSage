from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Any, Optional
import requests
import json
from datetime import datetime, timedelta
from transformers import pipeline
from db import SessionLocal
from models import ConversationMessage, JournalEntry
from config import OPENROUTER_API_KEY
import re
import time

import logging
logger = logging.getLogger("uvicorn")


class ChatState(TypedDict):
    user_id: str
    text: str
    emotion: str
    confidence: float
    ai_router_decision: str
    ai_emotion_analysis: dict
    therapeutic_readiness: str
    recommended_approach: str
    cbt_strategy: dict
    intervention_timing: str
    techniques_recommended: List[str]
    pattern_interpretation: dict
    should_surface_now: bool
    pattern_introduction_strategy: str
    response: str
    journal_entry: str
    session_messages: List[str]
    conversation_context: dict
    ai_memory: dict

class ModelAlternator:
    def __init__(self, model_list):
        self.models = model_list
        self.current_index = 0
        
    def get_next_model(self):
        """Get the next model in rotation"""
        model = self.models[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.models)
        logger.info(f"Selected model: {model} (index: {self.current_index - 1})")
        return model
    
    def get_current_model(self):
        """Get current model without advancing"""
        return self.models[self.current_index]

# Initialize with two reliable models
model_alternator = ModelAlternator([
    "tngtech/deepseek-r1t2-chimera:free",
    "deepseek/deepseek-r1-0528-qwen3-8b:free"
])

# AI-Powered LLM Interface
class AIDecisionEngine:
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.session = requests.Session()
        self.model_alternator = ModelAlternator([
            "tngtech/deepseek-r1t2-chimera:free",
            "deepseek/deepseek-r1-0528-qwen3-8b:free"
        ])
        
    def call_llm(self, prompt: str, model: str = None, 
                 temperature: float = 0.3, max_tokens: int = 800, cooldown: float = 1.0) -> str:
        """Generic LLM call interface"""
        # Use alternator if no specific model requested
        if model is None:
            model = self.model_alternator.get_next_model()
        try:
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "localhost",
                    "X-Title": "EmotionalCBTChatbot"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=30
            )
            # Log the full response for debugging
            logger.info(f"OpenRouter API Status: {response.status_code}")
            logger.info(f"OpenRouter API Response: {response.text}")
            time.sleep(cooldown)

            return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.info(f"LLM API Error: {e}")
            time.sleep(cooldown)
            return ""
    
    def call_llm_structured(self, prompt: str, model: str = None) -> dict:
        """Call LLM and expect JSON response"""
        try:
            response = self.call_llm(prompt, model, temperature=0.3)
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            logger.info(f"No JSON match for the LLM response")
            return {}
        except:
            logger.info(f"LLM response structuring failed")
            return {}

# Initialize the AI engine
ai_engine = AIDecisionEngine()

def get_conversation_depth_analysis(user_id: str) -> dict:
    """Analyze conversation depth and patterns to avoid loops"""
    history = get_conversation_history(user_id, limit=10)
    
    if not history:
        return {"depth": 0, "question_count": 0, "needs_intervention": False}
    
    # Count questions asked by assistant
    question_count = 0
    for msg in history:
        if msg["role"] == "assistant" and ("?" in msg["content"]):
            question_count += 1
    
    depth = len(history)
    needs_intervention = question_count > 3 or depth > 4
    
    return {
        "depth": depth,
        "question_count": question_count, 
        "needs_intervention": needs_intervention,
        "recent_topics": [msg["content"][:50] for msg in history[-3:]]
    }


# AI-Powered Emotion Analysis Node
def ai_emotion_analyst(state: ChatState) -> dict:
    """AI-powered comprehensive emotion analysis with contextual understanding"""
    
    user_input = state["text"]
    user_id = state["user_id"]
    
    # Get conversation history for context
    db = SessionLocal()
    history = db.query(ConversationMessage)\
        .filter(ConversationMessage.user_id == user_id)\
        .order_by(ConversationMessage.timestamp.desc())\
        .limit(10)\
        .all()
    db.close()
    
    recent_messages = [msg.message for msg in reversed(history)]
    
    analysis_prompt = f"""
    You are an expert AI therapist analyzing a client's emotional state with deep contextual understanding.
    
    Current message: "{user_input}"
    Recent conversation history: {recent_messages[-5:] if recent_messages else "No prior context"}
    
    Provide a comprehensive emotional analysis in JSON format:
    {{
        "primary_emotion": "primary emotion detected",
        "confidence": 0.95,
        "emotional_complexity": "simple/complex/mixed",
        "underlying_emotions": ["secondary", "tertiary emotions if present"],
        "therapeutic_readiness": "low/medium/high",
        "emotional_intensity": 0.85,
        "vulnerability_level": "closed/cautious/open/very_open",
        "recommended_approach": "supportive/exploratory/interventional/crisis",
        "crisis_indicators": ["any red flags"],
        "emotional_trajectory": "improving/stable/declining/fluctuating",
        "reasoning": "detailed explanation of your assessment"
    }}
    
    Base your analysis on:
    1. Emotional language and intensity
    2. Contextual patterns from conversation history
    3. Readiness for therapeutic intervention
    4. Any concerning patterns or crisis indicators
    """
    
    analysis = ai_engine.call_llm_structured(analysis_prompt)
    
    if not analysis:
        # Fallback basic emotion detection
        emotion_classifier = pipeline("text-classification", 
                                    model="j-hartmann/emotion-english-distilroberta-base")
        basic_emotion = emotion_classifier(user_input)[0]
        analysis = {
            "primary_emotion": basic_emotion["label"],
            "confidence": basic_emotion["score"],
            "therapeutic_readiness": "medium",
            "recommended_approach": "supportive"
        }
    
    return {
        "emotion": analysis.get("primary_emotion", "neutral"),
        "confidence": analysis.get("confidence", 0.5),
        "ai_emotion_analysis": analysis,
        "therapeutic_readiness": analysis.get("therapeutic_readiness", "medium"),
        "recommended_approach": analysis.get("recommended_approach", "supportive")
    }

# AI-Powered Conversation Router
def ai_conversation_router(state: ChatState) -> dict:
    """AI-powered router that decides the optimal next therapeutic action"""
    
    context = {
        "user_input": state["text"],
        "emotion": state["emotion"],
        "confidence": state["confidence"],
        "therapeutic_readiness": state.get("therapeutic_readiness", "medium"),
        "recommended_approach": state.get("recommended_approach", "supportive"),
        "conversation_context": state.get("conversation_context", {}),
        "ai_emotion_analysis": state.get("ai_emotion_analysis", {})
    }
    
    router_prompt = f"""
    You are an AI therapeutic coordinator. Analyze the client's input and choose ONE action.
    
    CURRENT SITUATION:
    - Client input: "{context['user_input']}"
    - Primary emotion: {context['emotion']} (confidence: {context['confidence']})
    - Therapeutic readiness: {context['therapeutic_readiness']}
    - Recommended approach: {context['recommended_approach']}
    - Emotional complexity: {context['ai_emotion_analysis'].get('emotional_complexity', 'unknown')}
    - Vulnerability level: {context['ai_emotion_analysis'].get('vulnerability_level', 'unknown')}

    DECISION CRITERIA:
    - CBT words detected: "always", "never", "everything", "nothing", "failure", "worthless", "should", "must" etc = cbt_intervention
    - Crisis words: "suicide", "kill myself", "hurt myself", "can't go on" etc = crisis_support  
    - High distress + low context = emotional_support
    - Vague/unclear input = explore_deeper
    - Ready for insights = reflection_guidance
    - Has patterns to discuss = pattern_analysis
    
    ACTION NAMES:
    
    1. "explore_deeper" - Client needs more emotional exploration and context building
    2. "pattern_analysis" - Ready to identify and discuss behavioral/emotional patterns
    3. "cbt_intervention" - Client is ready for cognitive behavioral therapy techniques
    4. "emotional_support" - Client needs validation and emotional support primarily
    5. "crisis_support" - Client shows signs of crisis and needs immediate support
    6. "reflection_guidance" - Guide client toward self-reflection and insight
    
    Consider:
    - Don't rush to CBT if client isn't ready
    - Emotional support should come first for high distress
    - Pattern analysis when there's sufficient emotional data
    - Crisis support takes absolute priority
    
    Respond in JSON format:
    {{
        "chosen_action": "action_name",
        "confidence": 0.85,
        "reasoning": "brief explanation of why this action was chosen",
        "alternative_considered": "second best option if applicable"
    }}"""
    
    # Try to get JSON response
    try:
        response = ai_engine.call_llm(router_prompt, temperature=0.3, max_tokens=150)
        logger.info(f"Raw router response: {response}")
        
        if response and response.strip():
            # Try to parse JSON from response
            router_decision = ai_engine.call_llm_structured(router_prompt)
            
            if router_decision and "chosen_action" in router_decision:
                chosen_action = router_decision["chosen_action"]
                confidence = router_decision.get("confidence", 0.5)
                reasoning = router_decision.get("reasoning", "No reasoning provided")
                
                logger.info(f"Router decision: {chosen_action} (confidence: {confidence})")
                logger.info(f"Router reasoning: {reasoning}")
                
                # Validate the chosen action
                valid_actions = ["explore_deeper", "pattern_analysis", "cbt_intervention", 
                               "emotional_support", "crisis_support", "reflection_guidance"]
                
                if chosen_action in valid_actions:
                    return {"ai_router_decision": chosen_action}
                else:
                    logger.warning(f"Invalid action received: {chosen_action}")
                    
        # If JSON parsing failed, try to extract action from raw response
        logger.warning("JSON parsing failed, trying text extraction")
        return extract_action_from_text(response, context)
        
    except Exception as e:
        logger.error(f"Router LLM call failed: {e}")
        return rule_based_fallback(context)
    
def extract_action_from_text(response: str, context: dict) -> dict:
    """Extract action from text response as fallback"""
    if not response:
        logger.warning("Empty response, using fallback")
        return rule_based_fallback(context)
    
    response_lower = response.lower()
    
    # Look for action names in the response
    valid_actions = ["explore_deeper", "pattern_analysis", "cbt_intervention", 
                    "emotional_support", "crisis_support", "reflection_guidance"]
    
    for action in valid_actions:
        if action in response_lower:
            logger.info(f"Extracted action from text: {action}")
            return {"ai_router_decision": action}
    
    # Look for keywords that might indicate the action
    action_keywords = {
        "explore": "explore_deeper",
        "exploration": "explore_deeper", 
        "pattern": "pattern_analysis",
        "behavioral": "pattern_analysis",
        "cbt": "cbt_intervention",
        "cognitive": "cbt_intervention",
        "support": "emotional_support",
        "validation": "emotional_support",
        "crisis": "crisis_support",
        "emergency": "crisis_support",
        "reflection": "reflection_guidance",
        "insight": "reflection_guidance"
    }
    
    for keyword, action in action_keywords.items():
        if keyword in response_lower:
            logger.info(f"Matched keyword '{keyword}' to action: {action}")
            return {"ai_router_decision": action}
    
    logger.warning("No action found in text, using rule-based fallback")
    return rule_based_fallback(context)

def rule_based_fallback(context: dict, user_id: str = None) -> dict:
    """Enhanced rule-based fallback that considers conversation history"""
    
    logger.info("Using enhanced rule-based fallback routing")
    
    user_input = context.get("user_input", "").lower()
    emotion = context.get("emotion", "").lower()
    confidence = context.get("confidence", 0)
    therapeutic_readiness = context.get("therapeutic_readiness", "medium")
    
    # Get conversation history if user_id provided
    conversation_depth = 0
    recent_topics = []
    if user_id:
        try:
            history = get_conversation_history(user_id, limit=6)
            conversation_depth = len(history)
            recent_topics = [msg.get("content", "").lower() for msg in history[-3:]]
        except:
            pass
    
    # Same crisis detection as before
    crisis_keywords = [
        "suicide", "suicidal", "kill myself", "end it all", "hurt myself", 
        "self harm", "can't go on", "better off dead", "no point living",
        "want to die", "ending my life"
    ]
    
    if any(keyword in user_input for keyword in crisis_keywords):
        logger.info("Enhanced fallback: Crisis keywords detected")
        return {"ai_router_decision": "crisis_support"}
    
    # CBT detection with context
    cbt_keywords = [
        "always", "never", "everything", "nothing", "failure", "worthless",
        "should", "must", "can't do anything", "mess everything"
    ]
    
    if any(keyword in user_input for keyword in cbt_keywords):
        logger.info("Enhanced fallback: CBT keywords detected")
        return {"ai_router_decision": "cbt_intervention"}
    
    # Pattern detection enhanced with conversation history
    pattern_keywords = ["again", "always happens", "every time", "pattern", "repeatedly"]
    has_pattern_words = any(keyword in user_input for keyword in pattern_keywords)
    
    # Check if similar topics mentioned before
    similar_topic_mentioned = False
    if recent_topics:
        key_words = user_input.split()[:5]  # First 5 words as topic indicators
        for topic in recent_topics:
            if any(word in topic for word in key_words if len(word) > 3):
                similar_topic_mentioned = True
                break
    
    if has_pattern_words or (similar_topic_mentioned and conversation_depth >= 3):
        logger.info("Enhanced fallback: Pattern analysis appropriate")
        return {"ai_router_decision": "pattern_analysis"}
    
    # Conversation depth-based decisions
    if conversation_depth >= 4:
        logger.info("Enhanced fallback: Deep conversation - reflection guidance")
        return {"ai_router_decision": "reflection_guidance"}
    
    elif conversation_depth >= 2:
        if emotion in ["sadness", "anger", "fear"] and confidence > 0.6:
            return {"ai_router_decision": "emotional_support"}
        else:
            return {"ai_router_decision": "reflection_guidance"}
    
    # Early conversation logic
    else:
        if len(user_input.strip()) < 15:
            return {"ai_router_decision": "explore_deeper"}
        elif emotion in ["sadness", "anger", "fear"] and confidence > 0.7:
            return {"ai_router_decision": "emotional_support"}
        else:
            return {"ai_router_decision": "explore_deeper"}


# AI-Powered CBT Strategist
def ai_cbt_strategist(state: ChatState) -> dict:
    """AI-powered CBT strategy selection and intervention planning"""
    
    context = {
        "user_input": state["text"],
        "emotion": state["emotion"],
        "session_messages": state.get("session_messages", []),
        "ai_emotion_analysis": state.get("ai_emotion_analysis", {})
    }
    
    # Get recent conversation for context
    full_context = "\n".join(context["session_messages"][-3:] + [context["user_input"]])
    
    strategy_prompt = f"""
    You are an expert CBT therapist analyzing a client's cognitive patterns to recommend specific interventions.
    
    Client context:
    - Current emotional state: {context['emotion']}
    - Current situation: "{context['user_input']}"
    - Recent conversation context: {full_context}
    - Emotional complexity: {context['ai_emotion_analysis'].get('emotional_complexity', 'unknown')}
    - Vulnerability level: {context['ai_emotion_analysis'].get('vulnerability_level', 'unknown')}
    
    Analyze and provide CBT strategy in JSON format:
    {{
        "cognitive_distortions": ["specific distortions identified"],
        "primary_distortion": "most significant distortion",
        "distortion_confidence": 0.85,
        "recommended_techniques": ["specific CBT techniques"],
        "primary_technique": "most appropriate technique",
        "intervention_timing": "immediate/gradual/defer",
        "intervention_approach": "gentle/direct/exploratory",
        "thought_challenging_questions": ["specific questions to ask"],
        "reframing_suggestions": ["alternative perspectives"],
        "behavioral_recommendations": ["actionable steps"],
        "readiness_assessment": "client readiness for this intervention 1-10",
        "reasoning": "detailed explanation of strategy"
    }}
    
    Focus on:
    1. Identifying specific cognitive distortions
    2. Matching appropriate CBT techniques
    3. Assessing client readiness
    4. Providing specific, actionable interventions
    """
    
    cbt_strategy = ai_engine.call_llm_structured(strategy_prompt)
    
    if not cbt_strategy:
        # Fallback basic CBT analysis
        cbt_strategy = {
            "primary_distortion": "none detected",
            "primary_technique": "thought exploration",
            "intervention_timing": "gradual",
            "reasoning": "Insufficient context for detailed CBT analysis"
        }
    
    return {
        "cbt_strategy": cbt_strategy,
        "intervention_timing": cbt_strategy.get("intervention_timing", "gradual"),
        "techniques_recommended": cbt_strategy.get("recommended_techniques", [])
    }

# AI-Powered Pattern Interpreter
def ai_pattern_interpreter(state: ChatState) -> dict:
    """AI-powered pattern interpretation and therapeutic significance assessment"""
    
    user_id = state["user_id"]
    
    # Get pattern data from database
    patterns = get_user_patterns(user_id)
    
    if not patterns:
        return {
            "pattern_interpretation": {},
            "should_surface_now": False,
            "pattern_introduction_strategy": "wait_for_more_data"
        }
    
    interpretation_prompt = f"""
    You are an expert pattern analyst interpreting emotional and behavioral patterns for therapeutic insight.
    
    Client patterns identified:
    {json.dumps(patterns, indent=2)}
    
    Current conversation context:
    - Current input: "{state['text']}"
    - Current emotion: {state['emotion']}
    - Therapeutic readiness: {state.get('therapeutic_readiness', 'medium')}
    
    Analyze these patterns and provide insights in JSON format:
    {{
        "most_significant_pattern": "description of most important pattern",
        "pattern_relevance": "how relevant to current conversation 1-10",
        "therapeutic_significance": "low/medium/high",
        "client_readiness_for_patterns": "ready/needs_preparation/not_ready",
        "surface_now": true/false,
        "introduction_strategy": "direct/gradual/exploratory/defer",
        "pattern_insights": ["key insights about the patterns"],
        "therapeutic_questions": ["questions to explore patterns"],
        "connection_to_current_state": "how patterns relate to current emotion/situation",
        "intervention_recommendations": ["specific ways to work with patterns"],
        "timing_rationale": "why now is/isn't the right time to discuss patterns"
    }}
    
    Consider:
    - Don't overwhelm client with too many patterns at once
    - Connect patterns to current emotional state
    - Assess if client is emotionally ready for pattern discussion
    - Provide specific ways to explore patterns therapeutically
    """
    
    interpretation = ai_engine.call_llm_structured(interpretation_prompt)
    
    if not interpretation:
        interpretation = {
            "surface_now": False,
            "introduction_strategy": "wait_for_more_data",
            "therapeutic_significance": "low"
        }
    
    return {
        "pattern_interpretation": interpretation,
        "should_surface_now": interpretation.get("surface_now", False),
        "pattern_introduction_strategy": interpretation.get("introduction_strategy", "defer")
    }

# AI-Powered Response Generator
def ai_response_generator(state: ChatState) -> dict:
    """AI-powered contextual response generation based on therapeutic decision"""
    
    user_id = state["user_id"]
    router_decision = state.get("ai_router_decision", "emotional_support")
    
    # Build context for response generation
    context = {
        "user_input": state["text"],
        "emotion": state["emotion"],
        "confidence": state["confidence"],
        "router_decision": router_decision,
        "ai_emotion_analysis": state.get("ai_emotion_analysis", {}),
        "cbt_strategy": state.get("cbt_strategy", {}),
        "pattern_interpretation": state.get("pattern_interpretation", {}),
        "should_surface_patterns": state.get("should_surface_now", False)
    }
    
    # Get conversation history to check if this is early conversation
    conversation_history = get_conversation_history(user_id)
    is_early_conversation = len(conversation_history) < 3
    
    # Build specialized prompt based on router decision
    if router_decision == "crisis_support":
        system_prompt = """You are Sage, a calm crisis support companion. 
        
        Be direct, caring, and focused on safety. Don't use flowery language.
        Ask specific questions about their safety and current situation.
        Keep responses short and practical."""
        
    elif router_decision == "cbt_intervention":
        cbt_info = context["cbt_strategy"]
        system_prompt = f"""You are Sage, a skilled therapeutic companion. The client is ready for CBT intervention.
        
        CBT Context:
        - Primary cognitive distortion: {cbt_info.get('primary_distortion', 'none')}
        - Recommended technique: {cbt_info.get('primary_technique', 'exploration')}
        - Intervention approach: {cbt_info.get('intervention_approach', 'gentle')}
        - Thought challenging questions: {cbt_info.get('thought_challenging_questions', [])}
        
        Guide the client through CBT techniques naturally, without using clinical terminology. 
        Help them examine their thoughts and develop more balanced perspectives. Don't be overly emotional or flowery"""
        
    elif router_decision == "pattern_analysis":
        pattern_info = context["pattern_interpretation"]
        system_prompt = f"""You are Sage, an observant companion who notices patterns. You've identified meaningful patterns.
        
        Pattern Context:
        - Most significant pattern: {pattern_info.get('most_significant_pattern', 'none')}
        - Pattern insights: {pattern_info.get('pattern_insights', [])}
        - Connection to current state: {pattern_info.get('connection_to_current_state', 'none')}
        
        Gently introduce these patterns as insights for self-discovery or ask specific questions to explore these patterns."""
        
    elif router_decision == "explore_deeper":
        system_prompt = """You are Sage, a curious companion who wants to understand better.
        
        Be naturally curious, not overly sympathetic.
        Ask specific, practical questions about their situation.
        Keep responses short and focused on getting more information."""
        
    elif router_decision == "reflection_guidance":
        system_prompt = """You are Sage, a thoughtful companion who helps people think things through.
        
        Ask questions that help them examine their situation.
        Be supportive but not overly emotional.
        Focus on practical reflection."""
        
    else:  # emotional_support
        system_prompt = """You are Sage, a supportive companion who listens well.
        
        Be warm but not overly dramatic.
        Offer validation without excessive emotional language.
        Ask follow-up questions to understand better."""
    
    # Generate response with context awareness
    if is_early_conversation:
        context_instruction = "This seems to be early in your conversation. Focus on understanding their situation better by asking specific questions rather than giving extensive advice."
    else:
        context_instruction = "You have context from previous conversations. You can provide more specific guidance."

    # Generate response
    response_prompt = f"""
    {system_prompt}
    
    CURRENT SITUATION:
    - Client's message: "{context['user_input']}"
    - Detected emotion: {context['emotion']} (confidence: {context['confidence']})
    - Emotional complexity: {context['ai_emotion_analysis'].get('emotional_complexity', 'unknown')}
    - Vulnerability level: {context['ai_emotion_analysis'].get('vulnerability_level', 'unknown')}
    
    CONVERSATION HISTORY: {conversation_history[-6:] if conversation_history else "No prior context"}
    
    RESPONSE GUIDELINES:
    - Be natural and human-like, not overly emotional
    - Use 1-2 sentences maximum unless crisis situation
    - Ask a specific follow-up question if you need more context
    - Avoid flowery language like "beautiful soul", "holding space", etc.
    - Be direct but kind
    - Don't use excessive formatting or emojis

    Respond just like a normal human in a natural, conversational tone:
    """
    
    response = ai_engine.call_llm(response_prompt, temperature=0.8, max_tokens=500)
    
    # Save conversation
    save_message(user_id, "user", context["user_input"])
    save_message(user_id, "assistant", response)
    
    return {"response": response}

# AI-Powered Journaling Node
def ai_journal_writer(state: ChatState) -> dict:
    """AI-powered intelligent journaling based on therapeutic significance"""
    
    user_id = state["user_id"]
    router_decision = state.get("ai_router_decision", "emotional_support")
    
    # Determine if this interaction is worth journaling
    journal_prompt = f"""
    Analyze this therapeutic interaction to determine if it should be journaled and what insights to capture:
    
    Interaction context:
    - Client input: "{state['text']}"
    - Emotion detected: {state['emotion']} (confidence: {state['confidence']})
    - Therapeutic action taken: {router_decision}
    - AI emotion analysis: {state.get('ai_emotion_analysis', {})}
    - CBT strategy used: {state.get('cbt_strategy', {})}
    - Pattern insights: {state.get('pattern_interpretation', {})}
    
    Provide journaling decision in JSON format:
    {{
        "should_journal": true/false,
        "journal_type": "emotional_checkin/cbt_session/pattern_recognition/crisis_support/breakthrough_moment",
        "significance_level": "low/medium/high",
        "key_insights": ["insights worth preserving"],
        "therapeutic_progress": "description of any progress made",
        "follow_up_needed": "any follow-up recommendations",
        "reasoning": "why this interaction is/isn't worth journaling"
    }}
    """
    
    journal_decision = ai_engine.call_llm_structured(journal_prompt)
    
    if not journal_decision or not journal_decision.get("should_journal", False):
        return {"journal_entry": ""}
    
    # Generate comprehensive journal entry
    journal_entry = f"""
    📝 Therapeutic Session - {datetime.now().strftime('%Y-%m-%d %H:%M')}
    
    Client State:
    - Primary emotion: {state['emotion']} (confidence: {state['confidence']})
    - Therapeutic readiness: {state.get('therapeutic_readiness', 'unknown')}
    - Vulnerability level: {state.get('ai_emotion_analysis', {}).get('vulnerability_level', 'unknown')}
    
    Therapeutic Action: {router_decision}
    
    Key Insights:
    {chr(10).join(f"- {insight}" for insight in journal_decision.get('key_insights', []))}
    
    Client Input: "{state['text']}"
    
    Therapeutic Progress: {journal_decision.get('therapeutic_progress', 'Session logged')}
    
    Follow-up Needed: {journal_decision.get('follow_up_needed', 'Continue monitoring')}
    
    Significance: {journal_decision.get('significance_level', 'medium')}
    """
    
    # Save to database
    save_journal(user_id, journal_entry, journal_decision.get("journal_type", "emotional_checkin"))
    
    return {"journal_entry": journal_entry}

# Helper Functions
def get_conversation_history(user_id: str, limit: int = 10) -> List[dict]:
    """Get conversation history for context"""
    db = SessionLocal()
    history = db.query(ConversationMessage)\
        .filter(ConversationMessage.user_id == user_id)\
        .order_by(ConversationMessage.timestamp.desc())\
        .limit(limit)\
        .all()
    db.close()
    
    return [{"role": msg.sender, "content": msg.message} for msg in reversed(history)]

def save_message(user_id: str, sender: str, message: str):
    """Save message to database"""
    db = SessionLocal()
    msg = ConversationMessage(
        user_id=user_id,
        sender=sender,
        message=message,
        timestamp=datetime.utcnow()
    )
    db.add(msg)
    db.commit()
    db.close()

def save_journal(user_id: str, content: str, entry_type: str):
    """Save journal entry to database"""
    db = SessionLocal()
    journal = JournalEntry(
        user_id=user_id,
        entry_type=entry_type,
        content=content,
        timestamp=datetime.utcnow()
    )
    db.add(journal)
    db.commit()
    db.close()

def get_user_patterns(user_id: str) -> dict:
    """Get user's emotional patterns from database"""
    db = SessionLocal()
    
    # Get recent emotional data
    cutoff_date = datetime.utcnow() - timedelta(days=14)
    journal_entries = db.query(JournalEntry)\
        .filter(JournalEntry.user_id == user_id)\
        .filter(JournalEntry.timestamp >= cutoff_date)\
        .order_by(JournalEntry.timestamp)\
        .all()
    
    db.close()
    
    if not journal_entries:
        return {}
    
    # Simple pattern analysis
    emotions = []
    for entry in journal_entries:
        emotion_match = re.search(r'emotion:\s*(\w+)', entry.content.lower())
        if emotion_match:
            emotions.append(emotion_match.group(1))
    
    if not emotions:
        return {}
    
    from collections import Counter
    emotion_counts = Counter(emotions)
    
    return {
        "recurring_emotions": dict(emotion_counts),
        "total_entries": len(journal_entries),
        "analysis_period": "14 days",
        "most_frequent_emotion": emotion_counts.most_common(1)[0] if emotion_counts else None
    }

# Routing Functions
def route_after_analysis(state: ChatState) -> str:
    """Route based on AI emotion analysis results"""
    crisis_indicators = state.get("ai_emotion_analysis", {}).get("crisis_indicators", [])
    '''if crisis_indicators:
        return "crisis_support"
    return "router"'''
    user_input_lower = state["text"].lower()
    
    # Only route to crisis if there are genuine crisis keywords
    actual_crisis_keywords = ["suicide", "kill myself", "end it all", "hurt myself", 
                             "can't go on", "better off dead", "no point living"]
    
    has_crisis_indicators = (crisis_indicators and 
                           any(keyword in user_input_lower for keyword in actual_crisis_keywords))
    
    if has_crisis_indicators:
        logger.info("Genuine crisis indicators detected, routing to crisis support")
        return "crisis_support"
    
    return "router"

def route_after_router(state: ChatState) -> str:
    """Route based on AI router decision"""
    decision = state.get("ai_router_decision", "emotional_support")
    
    if decision == "cbt_intervention":
        return "cbt_strategist"
    elif decision == "pattern_analysis":
        return "pattern_interpreter"
    else:
        return "response_generator"

def route_after_cbt(state: ChatState) -> str:
    """Route after CBT analysis"""
    return "response_generator"

def route_after_patterns(state: ChatState) -> str:
    """Route after pattern analysis"""
    return "response_generator"

def should_journal(state: ChatState) -> str:
    """Determine if we should journal this interaction"""
    # Always attempt journaling - the AI will decide if it's worth it
    return "journal"

# Build the LangGraph
builder = StateGraph(ChatState)

# Add all AI-powered nodes
builder.add_node("ai_emotion_analyst", ai_emotion_analyst)
builder.add_node("ai_conversation_router", ai_conversation_router)
builder.add_node("ai_cbt_strategist", ai_cbt_strategist)
builder.add_node("ai_pattern_interpreter", ai_pattern_interpreter)
builder.add_node("ai_response_generator", ai_response_generator)
builder.add_node("ai_journal_writer", ai_journal_writer)

# Set entry point
builder.set_entry_point("ai_emotion_analyst")

# Define the AI-driven flow
builder.add_conditional_edges(
    "ai_emotion_analyst",
    route_after_analysis,
    {
        "crisis_support": "ai_response_generator",
        "router": "ai_conversation_router"
    }
)

builder.add_conditional_edges(
    "ai_conversation_router",
    route_after_router,
    {
        "cbt_strategist": "ai_cbt_strategist",
        "pattern_interpreter": "ai_pattern_interpreter",
        "response_generator": "ai_response_generator"
    }
)

builder.add_conditional_edges(
    "ai_cbt_strategist",
    route_after_cbt,
    {
        "response_generator": "ai_response_generator"
    }
)

builder.add_conditional_edges(
    "ai_pattern_interpreter",
    route_after_patterns,
    {
        "response_generator": "ai_response_generator"
    }
)

builder.add_conditional_edges(
    "ai_response_generator",
    should_journal,
    {
        "journal": "ai_journal_writer"
    }
)

builder.add_edge("ai_journal_writer", END)

# Compile the graph
flow_v2 = builder.compile()