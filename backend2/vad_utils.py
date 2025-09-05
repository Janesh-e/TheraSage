import webrtcvad
import wave
import contextlib

def is_speech(audio_path, aggressiveness=2):
    vad = webrtcvad.Vad(aggressiveness)
    with contextlib.closing(wave.open(audio_path, 'rb')) as wf:
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
            raise ValueError("Audio must be WAV (mono, 16-bit, 16kHz)")

        frames = wf.readframes(wf.getnframes())
        frame_duration = 30  # ms
        frame_size = int(wf.getframerate() * frame_duration / 1000) * 2
        speech_detected = any(
            vad.is_speech(frames[i:i + frame_size], wf.getframerate())
            for i in range(0, len(frames), frame_size)
        )
    return speech_detected
