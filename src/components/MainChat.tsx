import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Send, ArrowDown } from "lucide-react";
import ChatBubble from "@/components/ChatBubble";
import TypingIndicator from "@/components/TypingIndicator";
import AppSidebar from "@/components/AppSidebar";
import ChatSessionsSidebar from "@/components/ChatSessionsSidebar";
import VoiceRecorder from "@/components/VoiceRecorder";
import ReadAloudToggle from "@/components/ReadAloudToggle";
import LLMToggle from "@/components/LLMToggle";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { cleanTextForSpeech } from "@/utils/textUtils";
import Textarea from "react-textarea-autosize";
import { motion, AnimatePresence } from "framer-motion";

interface Message {
  type: "user" | "bot";
  content: string;
  timestamp: Date;
}

interface MainChatProps {
  userResponses: Record<number, string>;
}

const MainChat = ({ userResponses }: MainChatProps) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [readAloud, setReadAloud] = useState(true);
  const [llmMode, setLlmMode] = useState<"online" | "offline">("online");
  const [showScrollToBottom, setShowScrollToBottom] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [authError, setAuthError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  const userName = userResponses[1] || "friend";
  const botName = userResponses[2] || "TheraSage";

  // Helper function to safely create Date objects
  const safeCreateDate = (date?: string | Date): Date => {
    if (!date) return new Date();

    if (date instanceof Date) {
      return isNaN(date.getTime()) ? new Date() : date;
    }

    try {
      const parsed = new Date(date);
      return isNaN(parsed.getTime()) ? new Date() : parsed;
    } catch {
      return new Date();
    }
  };

  const speakText = (text: string) => {
    if (!readAloud || !("speechSynthesis" in window)) return;
    speechSynthesis.cancel();
    const cleanedText = cleanTextForSpeech(text);
    if (!cleanedText.trim()) return;
    const utterance = new SpeechSynthesisUtterance(cleanedText);
    utterance.rate = 0.9;
    utterance.pitch = 1;
    utterance.volume = 0.8;
    const voices = speechSynthesis.getVoices();
    const preferredVoice = voices.find(
      (voice) =>
        voice.name.includes("Female") ||
        voice.name.includes("Samantha") ||
        voice.lang.startsWith("en")
    );
    if (preferredVoice) utterance.voice = preferredVoice;
    speechSynthesis.speak(utterance);
  };

  // Initialize with welcome message
  const initializeWelcomeMessage = () => {
    const welcomeMessage = {
      type: "bot" as const,
      content: `Hi ${userName}! I'm ${botName}, your personal guide to emotional well-being. How are you feeling today? 💜`,
      timestamp: new Date(),
    };
    setMessages([welcomeMessage]);
  };

  // Create a new session
  const createNewSession = async (): Promise<string | null> => {
    try {
      const token = localStorage.getItem("access_token");

      if (!token) {
        throw new Error("Authentication credentials missing");
      }

      const response = await fetch(`http://localhost:8000/sessions/`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title: null,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          `HTTP ${response.status}: ${
            errorData.detail || "Failed to create session"
          }`
        );
      }

      const newSession = await response.json();
      return newSession.id;
    } catch (error) {
      console.error("Error creating session:", error);
      setError(`Failed to create chat session: ${error.message}`);
      return null;
    }
  };

  const sendToBackend = async (text?: string, audioFile?: Blob) => {
    setIsTyping(true);
    const formData = new FormData();
    const userId = localStorage.getItem("user_id") || "anonymous";

    formData.append("user_id", userId);
    formData.append("session_id", currentSessionId || "");

    if (text) {
      formData.append("content", text);
      formData.append("message_type", "text");
    }
    if (audioFile) {
      formData.append("audio_file", audioFile, "recording.wav");
      formData.append("message_type", "audio");
    }

    try {
      const token = localStorage.getItem("access_token");
      const response = await fetch("http://localhost:8000/messages/send", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok)
        throw new Error(`HTTP error! status: ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error("Error sending to backend:", error);
      throw error;
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim() || isRecording) return;

    // If no session exists, create one
    if (!currentSessionId) {
      const newSessionId = await createNewSession();
      if (newSessionId) {
        setCurrentSessionId(newSessionId);
      } else {
        console.error("Failed to create session");
        return;
      }
    }

    const userMessage = {
      type: "user" as const,
      content: input,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    const currentInput = input;
    setInput("");

    try {
      const response = await sendToBackend(currentInput);
      console.log("Backend response:", response); // Debug log
      const botResponse = {
        type: "bot" as const,
        content:
          response.content ||
          response.ai_response ||
          response.message ||
          "I'm here to listen. 🌸",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botResponse]);
      speakText(botResponse.content);
    } catch (error) {
      const errorResponse = {
        type: "bot" as const,
        content: "I'm sorry, something went wrong. Please try again. 💜",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorResponse]);
      speakText(errorResponse.content);
    } finally {
      setIsTyping(false);
    }
  };

  const handleVoiceSend = async (audioBlob: Blob) => {
    if (audioBlob.size === 0) return;

    // If no session exists, create one
    if (!currentSessionId) {
      const newSessionId = await createNewSession();
      if (newSessionId) {
        setCurrentSessionId(newSessionId);
      } else {
        console.error("Failed to create session");
        return;
      }
    }

    const userMessage = {
      type: "user" as const,
      content: "🎤 Voice message...",
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsRecording(true);
    setIsTyping(true);

    try {
      const response = await sendToBackend(undefined, audioBlob);
      if (response.transcribed_text && response.transcribed_text.trim()) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg === userMessage
              ? { ...msg, content: response.transcribed_text }
              : msg
          )
        );
      }
      const botResponse = {
        type: "bot" as const,
        content:
          response.content ||
          response.ai_response ||
          response.message ||
          "I heard you. Let me think. 🌸",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botResponse]);
      speakText(botResponse.content);
    } catch (error) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg === userMessage
            ? { ...msg, content: "🎤 Voice message (failed)" }
            : msg
        )
      );
      const errorResponse = {
        type: "bot" as const,
        content: "I couldn't process your voice message. Please try again. 💜",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorResponse]);
      speakText(errorResponse.content);
    } finally {
      setIsRecording(false);
      setIsTyping(false);
    }
  };

  const loadSessionMessages = async (sessionId: string) => {
    try {
      const token = localStorage.getItem("access_token");
      const response = await fetch(
        `http://localhost:8000/messages/session/${sessionId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (response.ok) {
        const messages = await response.json();
        console.log("Loaded messages:", messages); // Debug log
        if (messages && messages.length > 0) {
          const formattedMessages = messages.map((msg: any) => ({
            type: msg.role === "user" ? "user" : "bot",
            content: msg.content,
            timestamp: safeCreateDate(msg.created_at),
          }));
          setMessages(formattedMessages);
        } else {
          // If no messages found, show welcome message
          initializeWelcomeMessage();
        }
      } else {
        // If session not found or error, show welcome message
        initializeWelcomeMessage();
      }
    } catch (error) {
      console.error("Error loading session messages:", error);
      initializeWelcomeMessage();
    }
  };

  const handleSessionSelect = (sessionId: string) => {
    setCurrentSessionId(sessionId);
    loadSessionMessages(sessionId);
  };

  const handleNewSession = async () => {
    // Create a new session
    const newSessionId = await createNewSession();
    if (newSessionId) {
      setCurrentSessionId(newSessionId);
      // Show welcome message for new session
      initializeWelcomeMessage();
    } else {
      console.error("Failed to create new session");
      // Fallback: clear current session and show welcome
      setCurrentSessionId(null);
      initializeWelcomeMessage();
    }
  };

  const scrollToBottom = (behavior: "smooth" | "auto" = "smooth") => {
    messagesEndRef.current?.scrollIntoView({ behavior });
  };

  const handleScroll = () => {
    if (chatContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } =
        chatContainerRef.current;
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 100;
      setShowScrollToBottom(!isAtBottom);
    }
  };

  // Single useEffect for initialization
  useEffect(() => {
    const initializeChat = async () => {
      try {
        // Validate authentication
        const token = localStorage.getItem("access_token");
        const userId = localStorage.getItem("user_id");

        if (!token || !userId) {
          setAuthError("Authentication required. Please log in again.");
          setIsLoading(false);
          return;
        }

        // Clear any previous auth errors
        setAuthError(null);

        // If not initialized yet, set up welcome message and create session
        if (!isInitialized) {
          // Create initial session if none exists
          if (!currentSessionId) {
            const newSessionId = await createNewSession();
            if (newSessionId) {
              setCurrentSessionId(newSessionId);
            }
          }

          // Show welcome message
          initializeWelcomeMessage();
          setIsInitialized(true);
        }

        setIsLoading(false);
      } catch (error) {
        console.error("Initialization error:", error);
        setError("Failed to initialize chat. Please refresh the page.");
        setIsLoading(false);
      }
    };

    initializeChat();
  }, [userName, botName, isInitialized, currentSessionId]);

  // Separate useEffect for scrolling
  useEffect(() => {
    scrollToBottom("auto");
  }, [messages.length]);

  // Early returns for error states
  if (authError) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-red-600 mb-2">
            Authentication Error
          </h2>
          <p className="text-gray-600">{authError}</p>
          <button
            onClick={() => (window.location.href = "/login")}
            className="mt-4 px-4 py-2 bg-primary text-white rounded"
          >
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center max-w-md">
          <h2 className="text-xl font-semibold text-red-600 mb-2">Error</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <div className="space-x-2">
            <button
              onClick={() => {
                setError(null);
                setIsInitialized(false);
                setIsLoading(true);
              }}
              className="px-4 py-2 bg-primary text-white rounded"
            >
              Retry
            </button>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-gray-500 text-white rounded"
            >
              Refresh Page
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-2"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <SidebarProvider>
      <div className="flex h-screen w-full bg-background overflow-hidden">
        <AppSidebar />
        <ChatSessionsSidebar
          currentSessionId={currentSessionId}
          onSessionSelect={handleSessionSelect}
          onNewSession={handleNewSession}
        />
        <div className="flex-1 flex flex-col min-w-0">
          <header className="flex-shrink-0 border-b border-border bg-background/80 backdrop-blur-sm px-6 py-[19px] shadow-sm">
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center space-x-4">
                <SidebarTrigger className="p-2 hover:bg-accent rounded-lg transition-colors" />
                <div className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center shadow-md">
                  <span className="text-xl font-bold text-white">T</span>
                </div>
                <div>
                  <h1 className="text-lg font-bold text-foreground">
                    {botName}
                  </h1>
                  <div className="flex items-center space-x-2">
                    <div
                      className={`w-2.5 h-2.5 rounded-full shadow-sm ${
                        llmMode === "online" ? "bg-green-500" : "bg-red-500"
                      }`}
                    ></div>
                    <span className="text-sm text-muted-foreground font-medium">
                      {llmMode === "online" ? "Online" : "Offline"}
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <LLMToggle mode={llmMode} onModeChange={setLlmMode} />
                <ReadAloudToggle enabled={readAloud} onToggle={setReadAloud} />
              </div>
            </div>
          </header>
          <main
            className="flex-1 overflow-y-auto"
            ref={chatContainerRef}
            onScroll={handleScroll}
          >
            <div className="max-w-4xl mx-auto px-4 py-6">
              <AnimatePresence initial={false}>
                <motion.div layout className="space-y-6">
                  {messages.map((msg, index) => (
                    <ChatBubble
                      key={index}
                      message={msg.content}
                      isBot={msg.type === "bot"}
                      timestamp={msg.timestamp}
                    />
                  ))}
                </motion.div>
              </AnimatePresence>
              {isTyping && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </div>
          </main>
          <footer className="flex-shrink-0 border-t border-border bg-background/80 backdrop-blur-sm px-6 py-4 shadow-lg">
            <div className="max-w-4xl mx-auto">
              <div className="flex items-end space-x-3">
                <div className="flex-1 relative">
                  <Textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage();
                      }
                    }}
                    placeholder={
                      isRecording ? "🎤 Recording..." : "Type your message..."
                    }
                    className="w-full p-4 pr-16 border border-border rounded-xl shadow-sm focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all duration-200 bg-card text-foreground resize-none"
                    minRows={1}
                    maxRows={5}
                    disabled={isRecording}
                  />
                  <div className="absolute right-3 top-3">
                    <VoiceRecorder
                      onRecordingChange={setIsRecording}
                      onTranscriptionBlob={handleVoiceSend}
                    />
                  </div>
                </div>
                <Button
                  onClick={handleSendMessage}
                  className="bg-primary hover:bg-primary/90 text-primary-foreground rounded-xl w-12 h-12 flex items-center justify-center shadow-md hover:shadow-lg transition-all duration-200 flex-shrink-0"
                  disabled={!input.trim() && !isRecording}
                  size="icon"
                >
                  <Send className="w-5 h-5" />
                </Button>
              </div>
            </div>
          </footer>
          <AnimatePresence>
            {showScrollToBottom && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                className="absolute bottom-24 right-8"
              >
                <Button
                  onClick={() => scrollToBottom()}
                  className="rounded-full bg-white/70 backdrop-blur-sm text-gray-700 hover:bg-white shadow-lg"
                  size="icon"
                  variant="outline"
                >
                  <ArrowDown className="w-5 h-5" />
                </Button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default MainChat;
