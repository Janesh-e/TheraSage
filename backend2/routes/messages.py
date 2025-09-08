from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from db import get_db
from models import ChatSession, ChatMessage, MessageRole
from schemas import ChatMessageResponse
from ai_agent import process_ai_conversation
from stt_utils import transcribe_audio
from vad_utils import is_speech
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
    user_id: str = Form(...),
    session_id: str = Form(...),
    text: Optional[str] = Form(None),
    voice: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Accepts either text (form field `text`) or a voice file (form field `voice`).
    If `voice` is provided, calls our internal /stt/ endpoint to transcribe.
    Saves user message, invokes AI, saves AI message, and returns the AI message.
    """
    # Resolve content
    if voice:
        # save uploaded file
        orig_name = voice.filename
        tmp_name = f"{uuid4().hex}_{orig_name}"
        raw_path = os.path.join(UPLOAD_FOLDER, tmp_name)
        with open(raw_path, "wb") as f:
            f.write(await voice.read())

        # convert to WAV mono 16kHz 16-bit
        wav_path = raw_path.rsplit(".", 1)[0] + "_converted.wav"
        from pydub import AudioSegment
        sound = AudioSegment.from_file(raw_path)
        sound = sound.set_channels(1).set_frame_rate(16000).set_sample_width(2)
        sound.export(wav_path, format="wav")
        # VAD
        try:
            if not is_speech(wav_path):
                raise HTTPException(400, "No speech detected")
        except ValueError as e:
            raise HTTPException(400, str(e))

        # Transcribe
        content = transcribe_audio(wav_path)

        # cleanup
        for p in (raw_path, wav_path):
            try: os.remove(p)
            except: pass
    elif text:
        content = text
    else:
        raise HTTPException(400, "Either text or voice must be provided")
    
    # Process through AI agent (this also persists in DB internally)
    result = await process_ai_conversation(db, user_id, session_id, content)
    
    # Return the AI response message
    return ChatMessageResponse(
        id="",
        content=result["response"],
        role="assistant",
        message_order=0,
        created_at=None,
        sentiment_score=None,
        risk_indicators=None
    )

@router.get("/{session_id}", response_model=List[ChatMessageResponse])
async def get_messages(
    session_id: UUID,
    user_id: str = Query(...),
    limit: int = Query(10, gt=0, le=100),
    before: Optional[UUID] = Query(None),
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
        ChatSession.user_id == user_id
    ).first()
    if not session:
        raise HTTPException(404, "Session not found or access denied")
    
    query = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    )
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
    
    return [
        ChatMessageResponse(
            id=str(m.id),
            content=m.content,
            role=m.role.value,
            message_order=m.message_order,
            created_at=m.created_at,
            sentiment_score=m.sentiment_score,
            risk_indicators=m.risk_indicators
        )
        for m in msgs
    ]
