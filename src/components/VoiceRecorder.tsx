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

  const checkMicrophonePermissions = async (): Promise<boolean> => {
    try {
      // Check if getUserMedia is supported
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.error("getUserMedia is not supported");
        return false;
      }

      // Try to enumerate devices to check if microphone exists
      try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const audioDevices = devices.filter(
          (device) => device.kind === "audioinput"
        );
        console.log("Available audio input devices:", audioDevices.length);

        if (audioDevices.length === 0) {
          alert(
            "No microphone devices found. Please connect a microphone and try again."
          );
          return false;
        }
      } catch (enumError) {
        console.warn("Could not enumerate devices:", enumError);
        // Continue anyway
      }

      // Check permission status if supported
      try {
        const permissionStatus = await navigator.permissions.query({
          name: "microphone" as PermissionName,
        });
        console.log("Microphone permission status:", permissionStatus.state);

        if (permissionStatus.state === "denied") {
          alert(
            "Microphone permission is denied. Please enable microphone access in your browser settings and refresh the page."
          );
          return false;
        }
      } catch (permError) {
        console.warn("Could not check permission status:", permError);
        // Continue anyway, as some browsers don't support permissions API
      }

      return true;
    } catch (error) {
      console.error("Error checking microphone permissions:", error);
      return false;
    }
  };

  const startRecording = async () => {
    // Check permissions first
    const hasPermissions = await checkMicrophonePermissions();
    if (!hasPermissions) {
      return;
    }

    try {
      console.log("Starting voice recording...");

      // Check if getUserMedia is supported
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error("getUserMedia is not supported in this browser");
      }

      // Check microphone permission first
      try {
        const permissionStatus = await navigator.permissions.query({
          name: "microphone" as PermissionName,
        });
        console.log("Microphone permission status:", permissionStatus.state);

        if (permissionStatus.state === "denied") {
          throw new Error(
            "Microphone permission denied. Please enable microphone access in your browser settings."
          );
        }
      } catch (permError) {
        console.warn("Could not check permission status:", permError);
        // Continue anyway, as some browsers don't support permissions API
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      streamRef.current = stream;
      console.log("Got media stream:", stream);

      // Check if stream has audio tracks
      const audioTracks = stream.getAudioTracks();
      if (audioTracks.length === 0) {
        throw new Error("No audio tracks available in the media stream");
      }

      console.log(
        "Audio tracks:",
        audioTracks.map((track) => ({
          label: track.label,
          kind: track.kind,
          enabled: track.enabled,
          muted: track.muted,
        }))
      );

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

      // Provide specific error messages based on error type
      let errorMessage = "Unable to access microphone. ";

      if (error instanceof Error) {
        if (
          error.name === "NotAllowedError" ||
          error.name === "PermissionDeniedError"
        ) {
          errorMessage +=
            "Permission denied. Please click on the microphone icon in your browser's address bar and allow microphone access, then try again.";
        } else if (
          error.name === "NotFoundError" ||
          error.name === "DevicesNotFoundError"
        ) {
          errorMessage +=
            "No microphone found. Please check that a microphone is connected and try again.";
        } else if (
          error.name === "NotReadableError" ||
          error.name === "TrackStartError"
        ) {
          errorMessage +=
            "Microphone is already in use by another application. Please close other applications using the microphone and try again.";
        } else if (
          error.name === "OverconstrainedError" ||
          error.name === "ConstraintNotSatisfiedError"
        ) {
          errorMessage +=
            "Microphone settings not supported. Trying with default settings...";

          // Try with simpler constraints
          try {
            const simpleStream = await navigator.mediaDevices.getUserMedia({
              audio: true,
            });
            streamRef.current = simpleStream;
            console.log("Got simple media stream:", simpleStream);

            const mediaRecorder = new MediaRecorder(simpleStream);
            audioChunksRef.current = [];

            mediaRecorder.ondataavailable = (event) => {
              if (event.data.size > 0) {
                audioChunksRef.current.push(event.data);
              }
            };

            mediaRecorder.onstop = async () => {
              const audioBlob = new Blob(audioChunksRef.current, {
                type: "audio/webm",
              });
              try {
                const wavBlob = await convertToWav(audioBlob);
                onTranscriptionBlob(wavBlob);
              } catch (convertError) {
                console.error("Error converting to WAV:", convertError);
                onTranscriptionBlob(audioBlob);
              }

              if (streamRef.current) {
                streamRef.current.getTracks().forEach((track) => track.stop());
                streamRef.current = null;
              }
            };

            mediaRecorder.onerror = (event) => {
              console.error("MediaRecorder error:", event);
            };

            mediaRecorderRef.current = mediaRecorder;
            mediaRecorder.start(1000);
            console.log("MediaRecorder started with simple constraints");
            setIsRecording(true);
            setRecordingTime(0);

            timerRef.current = setInterval(() => {
              setRecordingTime((prev) => prev + 1);
            }, 1000);

            return; // Exit successfully
          } catch (fallbackError) {
            console.error("Fallback recording failed:", fallbackError);
            errorMessage += " Fallback also failed.";
          }
        } else if (error.name === "NotSupportedError") {
          errorMessage +=
            "Your browser doesn't support audio recording. Please use a modern browser like Chrome, Firefox, or Edge.";
        } else {
          errorMessage += `Error: ${error.message}`;
        }
      } else {
        errorMessage += "An unknown error occurred. Please try again.";
      }

      alert(errorMessage);
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
          className="text-gray-500 hover:text-blue-600 hover:bg-blue-50 dark:text-gray-400 dark:hover:text-blue-400 dark:hover:bg-blue-950/30 transition-all duration-200 rounded-md p-2"
          title="Start voice recording"
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
