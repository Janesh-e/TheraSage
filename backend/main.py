from fastapi import FastAPI, UploadFile, File, Body
import os
from stt_utils import transcribe_audio
from vad_utils import is_speech
from emotion_utils import detect_emotion
from langgraph_chain import flow
from pydub import AudioSegment

app = FastAPI()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.post("/stt/")
async def speech_to_text(file: UploadFile = File(...)):
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)

    # Save uploaded file
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)

    # Convert to WAV mono 16-bit 16kHz for VAD
    wav_path = os.path.splitext(filepath)[0] + "_converted.wav"
    sound = AudioSegment.from_file(filepath)
    sound = sound.set_channels(1).set_frame_rate(16000).set_sample_width(2)
    sound.export(wav_path, format="wav")

    # Check if speech is present
    if not is_speech(wav_path):
        return {"text": "", "message": "No speech detected"}

    # Transcribe
    transcription = transcribe_audio(wav_path)
    return {"text": transcription}


@app.post("/detect_emotion/")
async def analyze_emotion(text: str = Body(..., embed=True)):
    result = detect_emotion(text)
    return result

@app.post("/chat/")
async def process_chat(user_id: str = Body(...), text: str = Body(..., embed=True)):
    result = flow.invoke({"user_id": user_id, "text": text})
    return result