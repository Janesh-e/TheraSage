
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
      <div
        className={`max-w-xs lg:max-w-md px-4 py-3 rounded-2xl shadow-md ${
          isBot
            ? 'bg-white text-gray-800 border border-gray-100'
            : 'bg-gradient-to-r from-purple-400 to-pink-400 text-white'
        }`}
      >
        <p className="text-sm leading-relaxed">{message}</p>
      </div>
    </div>
  );
};

export default ChatBubble;
