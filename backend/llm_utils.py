import requests
from memory_store import conversation_memory
from db import SessionLocal
from models import ConversationMessage
from datetime import datetime

OPENROUTER_API_KEY = "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"

SYSTEM_PROMPT = """
You are 'Sage', a human-like emotional support companion. 
You speak like a kind, emotionally aware friend — not a therapist, not a formal assistant.
You don't rush to solve problems; instead, you make people feel heard and safe.
Let the person open up. Ask natural questions like “What’s been happening lately?” or “That sounds rough — want to talk about it?”.
Speak casually, warmly, and reflectively — like a real friend on a call.
"""

def get_conversation_history(user_id: str):
    db = SessionLocal()
    history = db.query(ConversationMessage)\
        .filter(ConversationMessage.user_id == user_id)\
        .order_by(ConversationMessage.timestamp.asc())\
        .all()
    db.close()

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history:
        messages.append({
            "role": msg.sender,
            "content": msg.message
        })
    return messages

def save_message(user_id: str, sender: str, message: str):
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


def generate_response(user_id: str, user_message: str, emotion: str, cbt_tool: str = None):
    '''
    if user_id not in conversation_memory:
        conversation_memory[user_id] = []
    
    # Append current user message
    conversation_memory[user_id].append({"role": "user", "content": user_message})

    # Build message history
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_memory[user_id]
    '''
    # Save user's message
    save_message(user_id, "user", user_message)

    # Build prompt from history
    messages = get_conversation_history(user_id)

    if emotion:
        messages.append({
            "role": "system",
            "content": f"The user's current emotion is '{emotion}'."
        })
    if cbt_tool:
        messages.append({
            "role": "system",
            "content": f"CBT Tool suggestion: {cbt_tool}"
        })


    # Add current user message to last
    messages.append({"role": "user", "content": user_message})

    prompt = f"""
User message: {user_message}
Detected emotion: {emotion}

Generate a warm, emotionally intelligent response. Be comforting, supportive, and empathetic.
"""

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "mistralai/mistral-7b-instruct",
            "messages": messages
        }
    )

    try:
        assistant_msg = response.json()["choices"][0]["message"]["content"]
        # Save assistant response to memory
        # conversation_memory[user_id].append({"role": "assistant", "content": assistant_msg})
        save_message(user_id, "assistant", assistant_msg)
        return assistant_msg
    except Exception as e:
        print("OpenRouter API error:", response.json())
        raise RuntimeError("LLM response failed.") from e
