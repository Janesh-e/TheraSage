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
You are 'Sage', an emotionally intelligent support companion with knowledge of CBT techniques.
The user has shared enough context about their situation, and you can now provide helpful insights and cbt tools.
Your goal is to:
- Acknowledge and validate their experience
- Gently introduce CBT concepts when appropriate
- Provide practical cbt tools and techniques
- Help them see their situation from new perspectives
- Offer specific, actionable suggestions
- Balance support with gentle guidance
Maintain your warm, friend-like tone while being more solution-oriented.
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
                     conversation_phase: str = "exploring", cbt_info: dict = None):
    """Generate contextually appropriate response based on conversation phase"""
    
    # Save user's message first
    save_message(user_id, "user", user_input)

    # Get conversation history
    conversation_history = get_conversation_history(user_id)
    
    # Build messages for API
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
    
    # Add CBT information if available
    if cbt_info and conversation_phase == "ready_for_cbt":
        cbt_context = f"""
CBT Analysis Results:
- Cognitive distortion detected: {cbt_info.get('distortion', 'None')}
- Suggested CBT tool: {cbt_info.get('cbt_tool', 'None')}

You can gently introduce these concepts if appropriate, but don't force them. Focus on being helpful and supportive.
"""
        context_messages.append({
            "role": "system",
            "content": cbt_context
        })
    
    # Add phase-specific guidance
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