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
  const [currentSessionId, setCurrentSessionId] = useState<string | null>("1");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);

  const userName = userResponses[1] || "friend";
  const botName = userResponses[2] || "TheraSage";

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

  useEffect(() => {
    const welcomeMessage = {
      type: "bot" as const,
      content: `Hi ${userName}! I'm ${botName}, your personal guide to emotional well-being. How are you feeling today? 💜`,
      timestamp: new Date(),
    };
    setTimeout(() => setMessages([welcomeMessage]), 500);
  }, [userName, botName]);

  const scrollToBottom = (behavior: "smooth" | "auto" = "smooth") => {
    messagesEndRef.current?.scrollIntoView({ behavior });
  };

  useEffect(() => {
    scrollToBottom("auto");
  }, [messages.length]);

  const handleScroll = () => {
    if (chatContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } =
        chatContainerRef.current;
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 100;
      setShowScrollToBottom(!isAtBottom);
    }
  };

  const sendToBackend = async (text?: string, audioFile?: Blob) => {
    setIsTyping(true);
    const formData = new FormData();
    formData.append("user_id", "user123");
    formData.append("mode", llmMode);
    if (text) formData.append("text", text);
    if (audioFile) formData.append("file", audioFile, "recording.wav");

    try {
      const response = await fetch("http://localhost:8000/process/", {
        method: "POST",
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
      const botResponse = {
        type: "bot" as const,
        content:
          response.response || response.message || "I'm here to listen. 🌸",
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
      if (response.text && response.text.trim()) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg === userMessage ? { ...msg, content: response.text } : msg
          )
        );
      }
      const botResponse = {
        type: "bot" as const,
        content:
          response.response ||
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

  const handleSessionSelect = (sessionId: string) => {
    setCurrentSessionId(sessionId);
    // In a real app, you would load messages for this session
    // For now, we'll just clear the current messages
    setMessages([{
      type: "bot" as const,
      content: `Hi ${userName}! I'm ${botName}, your personal guide to emotional well-being. How are you feeling today? 💜`,
      timestamp: new Date(),
    }]);
  };

  const handleNewSession = () => {
    setMessages([]);
    setCurrentSessionId(null);
  };

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
                        llmMode === "online" ? "bg-green-500" : "bg-primary"
                      }`}
                    ></div>
                    <span className="text-sm text-muted-foreground font-medium">
                      {llmMode === "online" ? "Online" : "Offline"}
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <LLMToggle mode={llmMode} onModeChange={setLlmMode} />
                <ReadAloudToggle enabled={readAloud} onToggle={setReadAloud} />
              </div>
            </div>
          </header>

          <div
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
          </div>

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
