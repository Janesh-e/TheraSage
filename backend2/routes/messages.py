from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from db import get_db
from models import ChatSession, ChatMessage, MessageRole, User
from schemas import ChatMessageResponse
from ai_agent import process_ai_conversation
from stt_utils import transcribe_audio
from vad_utils import is_speech
from authenticate_utils import get_current_user
from uuid import uuid4
import requests
import os

router = APIRouter(
    prefix="/messages",
    tags=["messages"],
)

UPLOAD_FOLDER = "temp_audio"

@router.post("/send", response_model=ChatMessageResponse)
async def send_message(
    session_id: str = Form(...),
    content: Optional[str] = Form(None),
    message_type: str = Form("text"),
    audio_file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Accepts either text (form field `content`) or an audio file (form field `audio_file`).
    If `audio_file` is provided, calls our internal transcription to transcribe.
    Saves user message, invokes AI, saves AI message, and returns the AI message.
    """
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == str(current_user.id)
    ).first()
    
    if not session:
        raise HTTPException(404, "Session not found or access denied")

    # Resolve content
    text_content = None
    transcription_metadata = {}

    if audio_file:
        # Handle voice message processing
        orig_name = audio_file.filename
        tmp_name = f"{uuid4().hex}_{orig_name}"
        raw_path = os.path.join(UPLOAD_FOLDER, tmp_name)
        
        with open(raw_path, "wb") as f:
            f.write(await audio_file.read())

        # Convert to WAV mono 16kHz 16-bit
        wav_path = raw_path.rsplit(".", 1)[0] + "_converted.wav"
        from pydub import AudioSegment
        sound = AudioSegment.from_file(raw_path)
        sound = sound.set_channels(1).set_frame_rate(16000).set_sample_width(2)
        sound.export(wav_path, format="wav")

        # Voice Activity Detection
        try:
            if not is_speech(wav_path):
                raise HTTPException(400, "No speech detected")
        except ValueError as e:
            raise HTTPException(400, str(e))

        # Transcribe
        text_content = transcribe_audio(wav_path)
        transcription_metadata = {
            "original_filename": orig_name,
            "audio_duration": len(sound) / 1000.0,  # seconds
            "transcription_method": "whisper"
        }

        # Cleanup
        for p in (raw_path, wav_path):
            try:
                os.remove(p)
            except:
                pass
                
    elif content:
        text_content = content
    else:
        raise HTTPException(400, "Either content or audio_file must be provided")

    # Process through AI agent with full database updates
    try:
        # Try to use OpenRouter API directly for faster response
        api_key = os.getenv("OPENROUTER_API_KEY")
        
        if api_key:
            # Call OpenRouter API directly
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek/deepseek-chat-v3.1:free",
                    "messages": [
                        {
                            "role": "system", 
                            "content": "You are TheraSage, a compassionate AI therapist specialized in emotional support. Respond warmly and helpfully to users' concerns. Keep responses concise but caring."
                        },
                        {
                            "role": "user", 
                            "content": text_content
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 150
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response_content = result['choices'][0]['message']['content']
                
                # Save user message
                next_order = (session.total_messages or 0) + 1
                user_message = ChatMessage(
                    session_id=session_id,
                    content=text_content,
                    role=MessageRole.USER,
                    message_order=next_order,
                    created_at=datetime.utcnow()
                )
                db.add(user_message)
                
                # Save AI response
                next_order += 1
                ai_message = ChatMessage(
                    session_id=session_id,
                    content=ai_response_content,
                    role=MessageRole.ASSISTANT,
                    message_order=next_order,
                    created_at=datetime.utcnow(),
                    ai_model_used="deepseek/deepseek-chat-v3.1:free",
                    confidence_score=0.9
                )
                db.add(ai_message)
                
                # Update session
                session.total_messages = next_order
                session.last_message_at = datetime.utcnow()
                current_user.last_activity = datetime.utcnow()
                
                db.commit()

                return ChatMessageResponse(
                    id=str(ai_message.id),
                    content=ai_message.content,
                    role=ai_message.role.value,
                    message_order=ai_message.message_order,
                    created_at=ai_message.created_at,
                    sentiment_score=None,
                    risk_indicators={}
                )
            else:
                print(f"OpenRouter API error: {response.status_code} - {response.text}")
        
        # Fallback if API fails
        next_order = (session.total_messages or 0) + 1
        
        # Save user message
        user_message = ChatMessage(
            session_id=session_id,
            content=text_content,
            role=MessageRole.USER,
            message_order=next_order,
            created_at=datetime.utcnow()
        )
        db.add(user_message)
        
        # Create thoughtful fallback response
        next_order += 1
        ai_response_content = "I hear you, and I want you to know that your feelings are completely valid. It sounds like you're going through something important. Can you tell me more about what's on your mind? 💜"
        
        ai_message = ChatMessage(
            session_id=session_id,
            content=ai_response_content,
            role=MessageRole.ASSISTANT,
            message_order=next_order,
            created_at=datetime.utcnow(),
            ai_model_used="fallback",
            confidence_score=0.7
        )
        db.add(ai_message)
        
        # Update session
        session.total_messages = next_order
        session.last_message_at = datetime.utcnow()
        current_user.last_activity = datetime.utcnow()
        
        db.commit()

        return ChatMessageResponse(
            id=str(ai_message.id),
            content=ai_message.content,
            role=ai_message.role.value,
            message_order=ai_message.message_order,
            created_at=ai_message.created_at,
            sentiment_score=None,
            risk_indicators={}
        )
        
    except Exception as e:
        print(f"Message processing error: {e}")
        # Fallback with database logging
        print(f"AI processing error: {e}")
        
        # Create fallback response and save to DB
        next_order = (session.total_messages or 0) + 1
        
        fallback_message = ChatMessage(
            session_id=session_id,
            content="I'm having trouble processing your message right now. Could you try again?",
            role=MessageRole.ASSISTANT,
            message_order=next_order,
            created_at=datetime.utcnow(),
            ai_model_used="fallback",
            confidence_score=0.0
        )
        
        db.add(fallback_message)
        session.total_messages = next_order
        session.last_message_at = datetime.utcnow()
        
        # Update user activity
        current_user.last_activity = datetime.utcnow()
        
        db.commit()
        
        return ChatMessageResponse(
            id=str(fallback_message.id),
            content=fallback_message.content,
            role="assistant",
            message_order=next_order,
            created_at=fallback_message.created_at,
            sentiment_score=None,
            risk_indicators={"error": "processing_failed"}
        )

@router.get("/session/{session_id}", response_model=List[ChatMessageResponse])
async def get_messages(
    session_id: str,
    limit: int = Query(10, gt=0, le=100),
    before: Optional[str] = Query(None),
    include_metadata: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Paginated loading of messages in a session.
    - `limit` controls how many messages to return (default 10).
    - `before` is the message_id cursor: return messages older than that.
    """
    # Verify session
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == str(current_user.id)
    ).first()
    if not session:
        raise HTTPException(404, "Session not found or access denied")
    
    current_user.last_activity = datetime.utcnow()
    db.commit()
    
    query = db.query(ChatMessage).filter(ChatMessage.session_id == session_id)

    if before:
        # find the order of the message with id=before
        before_msg = db.query(ChatMessage).filter(
            ChatMessage.id == before,
            ChatMessage.session_id == session_id
        ).first()
        if not before_msg:
            raise HTTPException(404, "Cursor message not found")
        query = query.filter(ChatMessage.message_order < before_msg.message_order)
    
    msgs = query.order_by(ChatMessage.message_order.desc()).limit(limit).all()
    # return in chronological order
    msgs.reverse()

    messages = []
    for m in msgs:
        message_data = {
            "id": str(m.id),
            "content": m.content,
            "role": m.role.value,
            "message_order": m.message_order,
            "created_at": m.created_at,
            "sentiment_score": m.sentiment_score,
            "risk_indicators": m.risk_indicators or {}
        }

        if include_metadata and m.role == MessageRole.ASSISTANT:
            message_data.update({
                "ai_model_used": m.ai_model_used,
                "response_time_ms": m.response_time_ms,
                "confidence_score": m.confidence_score,
                "emotion_analysis": m.emotion_analysis
            })
        
        messages.append(ChatMessageResponse(**message_data))

    return messages


@router.get("/{session_id}/stats")
async def get_message_stats(
    session_id: UUID,
    user_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Get detailed message statistics for a session"""
    
    # Verify session access
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id
    ).first()
    
    if not session:
        raise HTTPException(404, "Session not found or access denied")

    # Get message statistics
    from sqlalchemy import func, case
    
    stats = db.query(
        func.count(ChatMessage.id).label('total_messages'),
        func.count(case([(ChatMessage.role == MessageRole.USER, 1)])).label('user_messages'),
        func.count(case([(ChatMessage.role == MessageRole.ASSISTANT, 1)])).label('ai_messages'),
        func.avg(ChatMessage.sentiment_score).label('avg_sentiment'),
        func.avg(ChatMessage.response_time_ms).label('avg_response_time'),
        func.min(ChatMessage.created_at).label('first_message'),
        func.max(ChatMessage.created_at).label('last_message')
    ).filter(ChatMessage.session_id == session_id).first()

    # Get risk indicators summary
    risk_messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id,
        ChatMessage.risk_indicators != None
    ).all()
    
    all_risk_factors = []
    all_cognitive_distortions = []
    
    for msg in risk_messages:
        if msg.risk_indicators:
            all_risk_factors.extend(msg.risk_indicators.get('risk_factors', []))
            all_cognitive_distortions.extend(msg.risk_indicators.get('cognitive_distortions', []))

    return {
        "session_id": str(session_id),
        "total_messages": stats.total_messages or 0,
        "user_messages": stats.user_messages or 0,
        "ai_messages": stats.ai_messages or 0,
        "average_sentiment": round(stats.avg_sentiment or 0.0, 3),
        "average_response_time_ms": round(stats.avg_response_time or 0.0, 1),
        "first_message": stats.first_message,
        "last_message": stats.last_message,
        "unique_risk_factors": list(set(all_risk_factors)),
        "unique_cognitive_distortions": list(set(all_cognitive_distortions)),
        "messages_with_risk_indicators": len(risk_messages)
    }

# Search messages
@router.get("/{session_id}/search")
async def search_messages(
    session_id: UUID,
    query: str = Query(..., min_length=3),
    user_id: str = Query(...),
    limit: int = Query(10, gt=0, le=50),
    db: Session = Depends(get_db)
):
    """Search messages in a session"""
    
    # Verify session access
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id
    ).first()
    
    if not session:
        raise HTTPException(404, "Session not found or access denied")

    # Search messages (case-insensitive)
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id,
        ChatMessage.content.ilike(f"%{query}%")
    ).order_by(ChatMessage.message_order.desc()).limit(limit).all()

    return [
        {
            "id": str(m.id),
            "content": m.content,
            "role": m.role.value,
            "message_order": m.message_order,
            "created_at": m.created_at,
            "relevance_snippet": m.content[:200] + "..." if len(m.content) > 200 else m.content
        }
        for m in messages
    ]
