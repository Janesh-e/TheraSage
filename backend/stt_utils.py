import whisper

model = whisper.load_model("base")  # you can use "small", "medium", "large"

def transcribe_audio(audio_path):
    result = model.transcribe(audio_path)
    return result["text"]
