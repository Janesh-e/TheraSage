
import { useEffect, useState } from "react";

interface ChatBubbleProps {
  message: string;
  isBot: boolean;
  delay?: number;
}

const ChatBubble = ({ message, isBot, delay = 0 }: ChatBubbleProps) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(true);
    }, delay);
    return () => clearTimeout(timer);
  }, [delay]);

  return (
    <div
      className={`flex ${isBot ? 'justify-start' : 'justify-end'} transition-all duration-500 ${
        isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
      }`}
    >
      <div className={`flex items-start space-x-3 max-w-lg ${isBot ? '' : 'flex-row-reverse space-x-reverse'}`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
          isBot 
            ? 'bg-gradient-to-r from-purple-400 to-pink-400' 
            : 'bg-gradient-to-r from-blue-400 to-cyan-400'
        }`}>
          <span className="text-white text-lg">
            {isBot ? '💜' : '🙂'}
          </span>
        </div>
        
        {/* Message Bubble */}
        <div
          className={`px-6 py-4 rounded-3xl shadow-lg border transition-all duration-200 hover:shadow-xl ${
            isBot
              ? 'bg-white/90 text-gray-800 border-gray-100/50 backdrop-blur-sm'
              : 'bg-gradient-to-r from-purple-400 to-pink-400 text-white border-transparent'
          }`}
        >
          <p className="text-base leading-relaxed">{message}</p>
        </div>
      </div>
    </div>
  );
};

export default ChatBubble;
