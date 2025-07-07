import requests
from memory_store import conversation_memory
from db import SessionLocal
from models import ConversationMessage
from datetime import datetime

OPENROUTER_API_KEY = "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"

# Different system prompts for different conversation phases
SYSTEM_PROMPTS = {
    "exploring": """
You are 'Sage', a warm and empathetic emotional support companion. 
The user has just started sharing with you, and you need to gently explore more about their situation.
Your goal is to:
- Make them feel heard and safe
- Ask gentle, open-ended questions to understand their situation better
- Show genuine curiosity about their experience
- Avoid giving advice yet - focus on understanding first
- Ask questions like "What's been happening?", "Can you tell me more about that?", "How did that make you feel?"
Keep your responses conversational and caring, like a trusted friend who wants to understand.
""",

    "building_context": """
You are 'Sage', a compassionate emotional support companion.
The user has shared some initial information, and you're building a deeper understanding of their situation.
Your goal is to:
- Dig deeper into the specifics of their situation
- Understand the context and background
- Explore their feelings and reactions
- Ask about what led to this situation
- Validate their emotions while gathering more details
- Questions like "What happened next?", "How long has this been going on?", "What's the hardest part for you?"
Continue being warm and supportive while helping them open up more.
""",

    "ready_for_cbt": """
You are 'Sage', a deeply empathetic and emotionally intelligent companion.
The user has shared enough about their situation. Your role now is to gently guide them toward emotional clarity and constructive change — without sounding clinical or instructional.
Your goals are to:
- Acknowledge and validate their emotions with warmth
- Ask thoughtful questions that promote reflection and insight
- Gently challenge unhelpful thought patterns without labeling them
- Suggest new perspectives and more balanced ways of thinking
- Encourage small, realistic steps the user can take
- Weave helpful thinking strategies into the conversation naturally, as a close friend would
Do not mention terms like “CBT”, “distortion”, or “tools.” Instead, embed helpful ideas into your response organically. Avoid sounding like a therapist — you are a trusted friend offering kind, thoughtful guidance.
""",

    "pattern_insights": """
You are 'Sage', a deeply caring and insightful emotional companion.
You have identified some meaningful patterns in the user's emotional experiences over time. Your role is to:
- Gently bring these patterns to their attention in a non-judgmental way
- Help them see these patterns as valuable self-knowledge, not flaws
- Ask curious questions about what they notice about these patterns
- Explore what might be underlying these recurring experiences
- Suggest gentle ways to work with these patterns rather than against them
- Make them feel empowered by this self-awareness
Be warm, non-clinical, and focus on helping them feel understood rather than analyzed. Present patterns as insights to explore together, not problems to fix.
"""
}

def get_conversation_history(user_id: str, limit: int = 20):
    """Get conversation history for context"""
    db = SessionLocal()
    history = db.query(ConversationMessage)\
        .filter(ConversationMessage.user_id == user_id)\
        .order_by(ConversationMessage.timestamp.desc())\
        .limit(limit)\
        .all()
    db.close()

    # Reverse to get chronological order
    history = list(reversed(history))
    
    messages = []
    for msg in history:
        messages.append({
            "role": msg.sender,
            "content": msg.message
        })
    return messages

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


def generate_response(user_id: str, user_input: str, emotion: str, 
                     conversation_phase: str = "exploring", cbt_info: dict = None, pattern_info: dict = None):
    """Generate contextually appropriate response based on conversation phase"""
    
    # Save user's message first
    save_message(user_id, "user", user_input)

    # Get conversation history
    conversation_history = get_conversation_history(user_id)

    # Determine which system prompt to use and build message for API
    if pattern_info:
        system_prompt = SYSTEM_PROMPTS.get("pattern_insights", SYSTEM_PROMPTS["exploring"])
    else:
        system_prompt = SYSTEM_PROMPTS.get(conversation_phase, SYSTEM_PROMPTS["exploring"])

    messages = [{"role": "system", "content": system_prompt}]
    
    # Add recent conversation history (last 10 messages)
    messages.extend(conversation_history[-10:])
    
    # Add current context
    context_messages = []
    
    if emotion:
        context_messages.append({
            "role": "system",
            "content": f"The user's current emotion is detected as '{emotion}'. Be sensitive to this."
        })
    
    # Add pattern information if available
    if pattern_info:
        pattern_context = f"""
You've identified some meaningful patterns in this user's emotional experiences:
Pattern Summary: {pattern_info.get('summary', 'No summary available')}
Key insights to potentially explore:
"""
        recommendations = pattern_info.get('recommendations', [])
        for i, rec in enumerate(recommendations[:3], 1):  # Limit to top 3
            pattern_context += f"\n{i}. {rec}"
            
        pattern_context += """

Present these insights gently and conversationally. Don't overwhelm them with all patterns at once - pick the most relevant one to explore based on their current message. Frame patterns as interesting discoveries about themselves, not problems to solve.
"""  
        context_messages.append({
            "role": "system",
            "content": pattern_context
        })
    
    # Add CBT information if available
    elif cbt_info and conversation_phase == "ready_for_cbt":
        cbt_context = f"""
The user may be experiencing:
- A thinking pattern such as: {cbt_info.get('distortion', 'None')}
- A helpful approach might be: {cbt_info.get('cbt_tool', 'None')}

Rather than labeling or explaining these concepts, gently guide the user using natural conversation. Use empathetic rephrasing, helpful questions, and relatable suggestions that reflect the principles behind these techniques.
"""
        context_messages.append({
            "role": "system",
            "content": cbt_context
        })
    
    # Add phase-specific guidance (unless we're in pattern mode)
    if not pattern_info:
        phase_guidance = {
            "exploring": "Ask gentle questions to understand their situation better. Don't rush to solutions.",
            "building_context": "Dig deeper into their specific situation. Help them elaborate on what's happening.",
            "ready_for_cbt": "You now have enough context to provide helpful insights and CBT tools if appropriate."
        }
        
        if conversation_phase in phase_guidance:
            context_messages.append({
                "role": "system",
                "content": phase_guidance[conversation_phase]
            })
    
    # Add context messages
    messages.extend(context_messages)
    
    # Add the current user input
    messages.append({"role": "user", "content": user_input})

    # Make API call
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "mistralai/mistral-7b-instruct",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 300
        }
    )

    try:
        assistant_msg = response.json()["choices"][0]["message"]["content"]
        
        # Save assistant response
        save_message(user_id, "assistant", assistant_msg)
        
        return assistant_msg
        
    except Exception as e:
        print("OpenRouter API error:", response.text)
        # Fallback response based on phase
        fallback_responses = {
            "exploring": "I'm here to listen. Can you tell me more about what's been on your mind?",
            "building_context": "That sounds challenging. Can you help me understand what's been the most difficult part for you?",
            "ready_for_cbt": "I can see you're going through a lot. Let's work through this together - what feels most overwhelming right now?"
        }
        
        fallback_msg = fallback_responses.get(conversation_phase, "I'm here to support you. What would you like to talk about?")
        save_message(user_id, "assistant", fallback_msg)
        return fallback_msg
    
# Helper function to determine if user needs more exploration
def needs_more_context(user_input: str, conversation_history: list) -> bool:
    """Determine if we need to ask more questions before providing advice"""
    # Simple heuristic - can be made more sophisticated
    if len(conversation_history) < 4:  # Less than 2 full turns
        return True
    
    # Check if input is very short and vague
    if len(user_input.split()) < 5:
        return True
    
    # Check if recent messages lack specificity
    recent_user_messages = [msg["content"] for msg in conversation_history[-6:] if msg["role"] == "user"]
    if not recent_user_messages:
        return True
    
    # Look for specific situation indicators
    specific_indicators = ["today", "yesterday", "happened", "told me", "at work", "my boss", "my friend"]
    has_specifics = any(indicator in " ".join(recent_user_messages).lower() for indicator in specific_indicators)
    
    return not has_specifics