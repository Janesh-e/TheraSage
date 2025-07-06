
import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Send, Mic, Paperclip } from "lucide-react";
import ChatBubble from "@/components/ChatBubble";
import TypingIndicator from "@/components/TypingIndicator";
import AppSidebar from "@/components/AppSidebar";
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar";

interface MainChatProps {
  userResponses: Record<number, string>;
}

const MainChat = ({ userResponses }: MainChatProps) => {
  const [messages, setMessages] = useState<Array<{ type: 'user' | 'bot', content: string, timestamp: Date }>>([]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
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

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;

    const userMessage = {
      type: 'user' as const,
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue("");
    setIsTyping(true);

    // Simulate bot response
    setTimeout(() => {
      setIsTyping(false);
      const botResponse = {
        type: 'bot' as const,
        content: "Thank you for sharing that with me. I'm here to listen and support you. How does that make you feel? 🌸",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botResponse]);
    }, 1500 + Math.random() * 1000);
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
                      <Button variant="ghost" size="sm" className="text-gray-400 hover:text-gray-600">
                        <Mic size={18} />
                      </Button>
                    </div>
                    <span className="text-xs text-gray-400">Press Enter to send, Shift+Enter for new line</span>
                  </div>
                </div>
                <Button
                  onClick={handleSendMessage}
                  disabled={!inputValue.trim()}
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
