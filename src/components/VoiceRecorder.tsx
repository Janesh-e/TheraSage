import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Mic, Square } from "lucide-react";

interface VoiceRecorderProps {
  onRecordingChange: (isRecording: boolean) => void;
  onTranscriptionBlob: (blob: Blob) => void;
  disabled?: boolean;
}

const VoiceRecorder = ({
  onRecordingChange,
  onTranscriptionBlob,
  disabled,
}: VoiceRecorderProps) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const startRecording = async () => {
    try {
      console.log("Starting voice recording...");

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      streamRef.current = stream;
      console.log("Got media stream:", stream);

      // Use a more compatible MIME type
      let mimeType = "audio/webm";
      if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
        mimeType = "audio/webm;codecs=opus";
      } else if (MediaRecorder.isTypeSupported("audio/mp4")) {
        mimeType = "audio/mp4";
      } else if (MediaRecorder.isTypeSupported("audio/wav")) {
        mimeType = "audio/wav";
      }

      console.log("Using MIME type:", mimeType);

      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        console.log("Data available:", event.data.size);
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        console.log(
          "Recording stopped, chunks:",
          audioChunksRef.current.length
        );

        if (audioChunksRef.current.length === 0) {
          console.error("No audio chunks recorded");
          alert("No audio was recorded. Please try again.");
          return;
        }

        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        console.log("Created audio blob:", audioBlob.size, "bytes");

        if (audioBlob.size === 0) {
          console.error("Audio blob is empty");
          alert("Recording failed - no audio data captured.");
          return;
        }

        // Convert to WAV format
        try {
          const wavBlob = await convertToWav(audioBlob);
          console.log("Converted to WAV:", wavBlob.size, "bytes");
          onTranscriptionBlob(wavBlob);
        } catch (error) {
          console.error("Error converting to WAV:", error);
          // Fallback to original format
          console.log("Using original format as fallback");
          onTranscriptionBlob(audioBlob);
        }

        // Clean up stream
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => {
            track.stop();
            console.log("Stopped track:", track.kind);
          });
          streamRef.current = null;
        }
      };

      mediaRecorder.onerror = (event) => {
        console.error("MediaRecorder error:", event);
      };

      mediaRecorder.start(1000); // Collect data every second
      console.log("MediaRecorder started");
      setIsRecording(true);
      setRecordingTime(0);

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } catch (error) {
      console.error("Error accessing microphone:", error);
      alert(
        "Unable to access microphone. Please check your permissions and try again."
      );
    }
  };

  const stopRecording = () => {
    console.log("Stopping recording...");

    if (mediaRecorderRef.current && isRecording) {
      if (mediaRecorderRef.current.state === "recording") {
        mediaRecorderRef.current.stop();
      }
      setIsRecording(false);

      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  const convertToWav = async (audioBlob: Blob): Promise<Blob> => {
    console.log("Converting to WAV...");

    const arrayBuffer = await audioBlob.arrayBuffer();
    const audioContext = new (window.AudioContext ||
      (window as any).webkitAudioContext)({
      sampleRate: 16000,
    });

    try {
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
      console.log("Audio decoded:", {
        channels: audioBuffer.numberOfChannels,
        length: audioBuffer.length,
        sampleRate: audioBuffer.sampleRate,
        duration: audioBuffer.duration,
      });

      // Convert to mono 16kHz
      const channels = audioBuffer.numberOfChannels;
      const length = audioBuffer.length;
      const sampleRate = 16000;

      let audioData;
      if (channels === 1) {
        audioData = audioBuffer.getChannelData(0);
      } else {
        // Mix stereo to mono
        const left = audioBuffer.getChannelData(0);
        const right = audioBuffer.getChannelData(1);
        audioData = new Float32Array(length);
        for (let i = 0; i < length; i++) {
          audioData[i] = (left[i] + right[i]) / 2;
        }
      }

      // Resample if needed (simplified - assumes same sample rate for now)
      const resampledData = audioData;

      // Convert float32 to int16
      const int16Data = new Int16Array(resampledData.length);
      for (let i = 0; i < resampledData.length; i++) {
        const sample = Math.max(-1, Math.min(1, resampledData[i]));
        int16Data[i] = sample * 32767;
      }

      // Create WAV file
      const wavBuffer = createWavFile(int16Data, sampleRate);
      const wavBlob = new Blob([wavBuffer], { type: "audio/wav" });

      console.log("WAV conversion complete:", wavBlob.size, "bytes");
      return wavBlob;
    } finally {
      await audioContext.close();
    }
  };

  const createWavFile = (
    audioData: Int16Array,
    sampleRate: number
  ): ArrayBuffer => {
    const buffer = new ArrayBuffer(44 + audioData.length * 2);
    const view = new DataView(buffer);

    // WAV header
    const writeString = (offset: number, string: string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };

    writeString(0, "RIFF");
    view.setUint32(4, 36 + audioData.length * 2, true);
    writeString(8, "WAVE");
    writeString(12, "fmt ");
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true); // PCM
    view.setUint16(22, 1, true); // Mono
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true); // Byte rate
    view.setUint16(32, 2, true); // Block align
    view.setUint16(34, 16, true); // Bits per sample
    writeString(36, "data");
    view.setUint32(40, audioData.length * 2, true);

    // Audio data
    const offset = 44;
    for (let i = 0; i < audioData.length; i++) {
      view.setInt16(offset + i * 2, audioData[i], true);
    }

    return buffer;
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="flex items-center space-x-2">
      {!isRecording ? (
        <Button
          onClick={startRecording}
          disabled={disabled}
          variant="ghost"
          size="sm"
          className="text-muted-foreground hover:text-primary hover:bg-accent transition-colors"
        >
          <Mic size={18} />
        </Button>
      ) : (
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-2 bg-red-50 text-red-600 px-3 py-1 rounded-full">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium">
              {formatTime(recordingTime)}
            </span>
          </div>
          <Button
            onClick={stopRecording}
            variant="ghost"
            size="sm"
            className="text-red-500 hover:text-red-700 hover:bg-red-50"
          >
            <Square size={18} />
          </Button>
        </div>
      )}
    </div>
  );
};

export default VoiceRecorder;
