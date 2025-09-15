from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import os
import requests
from db import get_db

router = APIRouter(
    prefix="/llm-status",
    tags=["llm-status"],
)

@router.get("/")
async def get_llm_status():
    """Check if LLM services are available"""
    
    # Check OpenRouter API status
    openrouter_status = "offline"
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if api_key:
        try:
            # Test OpenRouter API with a simple request
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek/deepseek-chat-v3.1:free",
                    "messages": [{"role": "user", "content": "test"}],
                    "max_tokens": 1
                },
                timeout=5
            )
            if response.status_code == 200:
                openrouter_status = "online"
            else:
                print(f"OpenRouter API test failed: {response.status_code}")
        except Exception as e:
            print(f"OpenRouter API test error: {e}")
    
    # Check environment mode
    llm_mode = os.getenv("LLM_MODE", "online")
    
    return {
        "status": "online" if openrouter_status == "online" else "fallback",
        "openrouter_api": openrouter_status,
        "mode": llm_mode,
        "model": "deepseek/deepseek-chat-v3.1:free",
        "features": {
            "text_generation": openrouter_status == "online",
            "conversation": openrouter_status == "online",
            "emotional_support": True,
            "crisis_detection": openrouter_status == "online"
        }
    }
