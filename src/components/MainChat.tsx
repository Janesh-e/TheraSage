import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Send, Paperclip } from "lucide-react";
import ChatBubble from "@/components/ChatBubble";
import TypingIndicator from "@/components/TypingIndicator";
import AppSidebar from "@/components/AppSidebar";
import VoiceRecorder from "@/components/VoiceRecorder";
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar";

interface MainChatProps {
  userResponses: Record<number, string>;
}

const MainChat = ({ userResponses }: MainChatProps) => {
  const [messages, setMessages] = useState<Array<{ type: 'user' | 'bot', content: string, timestamp: Date }>>([]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const userName = userResponses[1] || 'friend';
  const botName = userResponses[2] || 'TheraSage';

  useEffect(() => {
    // Welcome message from the bot
    const welcomeMessage = {
      type: 'bot' as const,
      content: `Hi ${userName}! I'm ${botName}, and I'm so glad we've connected. How are you feeling today? 💜`,
      timestamp: new Date()
    };
    
    setTimeout(() => {
      setMessages([welcomeMessage]);
    }, 1000);
  }, [userName, botName]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const sendToBackend = async (text?: string, audioFile?: Blob) => {
    console.log('Sending to backend:', { hasText: !!text, hasAudio: !!audioFile });
    
    const formData = new FormData();
    formData.append('user_id', 'user_123'); // You can make this dynamic
    
    if (text) {
      formData.append('text', text);
      console.log('Added text to form:', text);
    }
    
    if (audioFile) {
      console.log('Adding audio file:', {
        size: audioFile.size,
        type: audioFile.type,
        name: 'recording.wav'
      });
      formData.append('file', audioFile, 'recording.wav');
    }

    // Debug FormData contents
    console.log('FormData contents:');
    for (const [key, value] of formData.entries()) {
      if (value instanceof File || value instanceof Blob) {
        console.log(`${key}:`, {
          size: value.size,
          type: value.type,
          name: value instanceof File ? value.name : 'blob'
        });
      } else {
        console.log(`${key}:`, value);
      }
    }

    try {
      const response = await fetch('http://localhost:8000/process/', {
        method: 'POST',
        body: formData,
      });

      console.log('Response status:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Response error:', errorText);
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
      }

      const result = await response.json();
      console.log('Backend response:', result);
      return result;
    } catch (error) {
      console.error('Error sending to backend:', error);
      throw error;
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isProcessing) return;

    const userMessage = {
      type: 'user' as const,
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = inputValue;
    setInputValue("");
    setIsProcessing(true);
    setIsTyping(true);

    try {
      const response = await sendToBackend(currentInput);
      
      setIsTyping(false);
      const botResponse = {
        type: 'bot' as const,
        content: response.response || response.message || "I'm here to listen and support you. 🌸",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botResponse]);
    } catch (error) {
      setIsTyping(false);
      const errorResponse = {
        type: 'bot' as const,
        content: "I'm sorry, I'm having trouble connecting right now. Please try again in a moment. 💜",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorResponse]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleVoiceRecording = async (audioBlob: Blob) => {
    console.log('Voice recording received:', {
      size: audioBlob.size,
      type: audioBlob.type
    });
    
    if (isProcessing) {
      console.log('Already processing, ignoring voice input');
      return;
    }

    if (audioBlob.size === 0) {
      console.error('Received empty audio blob');
      alert('Recording failed - no audio data. Please try again.');
      return;
    }

    // Add a placeholder message for the voice input
    const userMessage = {
      type: 'user' as const,
      content: "🎤 Processing voice message...",
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsProcessing(true);
    setIsTyping(true);

    try {
      console.log('Sending voice recording to backend...');
      const response = await sendToBackend(undefined, audioBlob);
      
      setIsTyping(false);
      
      // If there's transcribed text, update the user message
      if (response.text && response.text.trim()) {
        console.log('Received transcription:', response.text);
        setMessages(prev => prev.map((msg, index) => 
          index === prev.length - 1 && msg.type === 'user' 
            ? { ...msg, content: response.text }
            : msg
        ));
      } else {
        console.log('No transcription received or empty text');
        setMessages(prev => prev.map((msg, index) => 
          index === prev.length - 1 && msg.type === 'user' 
            ? { ...msg, content: "🎤 Voice message (no transcription)" }
            : msg
        ));
      }
      
      const botResponse = {
        type: 'bot' as const,
        content: response.response || response.message || "I heard you. Let me think about that. 🌸",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botResponse]);
    } catch (error) {
      console.error('Voice processing error:', error);
      setIsTyping(false);
      
      // Update the placeholder message to show error
      setMessages(prev => prev.map((msg, index) => 
        index === prev.length - 1 && msg.type === 'user' 
          ? { ...msg, content: "🎤 Voice message (processing failed)" }
          : msg
      ));
      
      const errorResponse = {
        type: 'bot' as const,
        content: "I'm sorry, I couldn't process your voice message. Please try again or type your message instead. 💜",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorResponse]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full bg-gradient-to-br from-purple-50/30 via-pink-50/30 to-blue-50/30">
        <AppSidebar />
        
        <SidebarInset className="flex flex-col">
          {/* Header */}
          <div className="bg-white/80 backdrop-blur-sm border-b border-white/50 p-4 sticky top-0 z-10">
            <div className="max-w-4xl mx-auto flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full flex items-center justify-center">
                  <span className="text-white text-lg">💜</span>
                </div>
                <div>
                  <h1 className="text-lg font-medium text-gray-800">{botName}</h1>
                  <p className="text-sm text-gray-500">Always here for you</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-sm text-gray-600">Online</span>
              </div>
            </div>
          </div>

          {/* Messages Container */}
          <div className="flex-1 overflow-y-auto">
            <div className="max-w-4xl mx-auto p-6">
              <div className="space-y-6">
                {messages.map((message, index) => (
                  <ChatBubble
                    key={index}
                    message={message.content}
                    isBot={message.type === 'bot'}
                    delay={0}
                  />
                ))}
                
                {isTyping && <TypingIndicator />}
                <div ref={messagesEndRef} />
              </div>
            </div>
          </div>

          {/* Input Area */}
          <div className="bg-white/80 backdrop-blur-sm border-t border-white/50 p-4 sticky bottom-0">
            <div className="max-w-4xl mx-auto">
              <div className="flex items-end space-x-4">
                <div className="flex-1 bg-white rounded-2xl border-2 border-gray-200 focus-within:border-purple-300 transition-colors">
                  <textarea
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder={`Share your thoughts with ${botName}...`}
                    className="w-full p-4 rounded-2xl resize-none focus:outline-none bg-transparent max-h-32"
                    rows={1}
                    disabled={isProcessing}
                    style={{
                      minHeight: '60px',
                      height: 'auto'
                    }}
                  />
                  <div className="flex items-center justify-between p-2 px-4">
                    <div className="flex items-center space-x-2">
                      <Button variant="ghost" size="sm" className="text-gray-400 hover:text-gray-600">
                        <Paperclip size={18} />
                      </Button>
                      <VoiceRecorder 
                        onRecordingComplete={handleVoiceRecording}
                        disabled={isProcessing}
                      />
                    </div>
                    <span className="text-xs text-gray-400">Press Enter to send, Shift+Enter for new line</span>
                  </div>
                </div>
                <Button
                  onClick={handleSendMessage}
                  disabled={!inputValue.trim() || isProcessing}
                  className="bg-gradient-to-r from-purple-400 to-pink-400 hover:from-purple-500 hover:to-pink-500 text-white rounded-2xl p-4 h-auto disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 hover:scale-105"
                >
                  <Send size={20} />
                </Button>
              </div>
            </div>
          </div>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
};

export default MainChat;
