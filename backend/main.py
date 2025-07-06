from fastapi import FastAPI, UploadFile, Form, File, Body
import os
from stt_utils import transcribe_audio
from vad_utils import is_speech
from emotion_utils import detect_emotion
from langgraph_chain import flow
from pydub import AudioSegment
import shutil
from uuid import uuid4
from fastapi.responses import JSONResponse
from typing import Optional
from pydub import AudioSegment
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.post("/stt/")
async def speech_to_text(file: UploadFile = File(...)):
    try:
        # Generate unique file path
        original_filename = file.filename
        base_filename = f"{uuid4().hex}_{original_filename}"
        filepath = os.path.join(UPLOAD_FOLDER, base_filename)

        # Save uploaded file
        with open(filepath, "wb") as f:
            content = await file.read()
            f.write(content)

        # Convert to WAV mono 16-bit 16kHz for VAD and Whisper
        wav_path = os.path.splitext(filepath)[0] + "_converted.wav"
        sound = AudioSegment.from_file(filepath)
        sound = sound.set_channels(1).set_frame_rate(16000).set_sample_width(2)
        sound.export(wav_path, format="wav")

        # Voice Activity Detection
        if not is_speech(wav_path):
            return JSONResponse({
                "text": "",
                "message": "No speech detected",
                "filename": base_filename
            })

        # Transcribe
        transcription = transcribe_audio(wav_path)

        return JSONResponse({
            "text": transcription,
            "message": "Speech transcribed successfully",
            "filename": base_filename
        })

    except Exception as e:
        return JSONResponse(
            {"error": "Failed to process audio", "details": str(e)},
            status_code=500
        )

@app.post("/detect_emotion/")
async def analyze_emotion(text: str = Body(..., embed=True)):
    result = detect_emotion(text)
    return result

@app.post("/chat/")
async def process_chat(user_id: str = Body(...), text: str = Body(..., embed=True)):
    result = flow.invoke({"user_id": user_id, "text": text})
    return result

@app.post("/process/")
async def unified_input_handler(
    user_id: str = Form(...),
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    try:
        # --- Case 1: Voice Input ---
        if file is not None:
            # Save file
            original_filename = file.filename
            base_filename = f"{uuid4().hex}_{original_filename}"
            filepath = os.path.join(UPLOAD_FOLDER, base_filename)

            with open(filepath, "wb") as f:
                content = await file.read()
                f.write(content)

            # Convert to WAV mono 16kHz 16-bit
            wav_path = os.path.splitext(filepath)[0] + "_converted.wav"
            sound = AudioSegment.from_file(filepath)
            sound = sound.set_channels(1).set_frame_rate(16000).set_sample_width(2)
            sound.export(wav_path, format="wav")

            # VAD check
            if not is_speech(wav_path):
                return JSONResponse({
                    "text": "",
                    "message": "No speech detected",
                    "filename": base_filename
                })

            # Transcribe
            text = transcribe_audio(wav_path)

        # --- Case 2: Text Input ---
        if not text or text.strip() == "":
            return JSONResponse({
                "error": "No valid input provided. Either text or audio must be given."
            }, status_code=400)

        # --- Run through LangGraph Flow ---
        result = flow.invoke({"user_id": user_id, "text": text})
        return result

    except Exception as e:
        return JSONResponse(
            {"error": "Failed to process input", "details": str(e)},
            status_code=500
        )