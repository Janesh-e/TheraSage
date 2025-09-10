import { motion } from "framer-motion";
import { format } from "date-fns";

interface ChatBubbleProps {
  message: string;
  isBot: boolean;
  timestamp: Date;
}

const ChatBubble = ({ message, isBot, timestamp }: ChatBubbleProps) => {
  const variants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
  };

  // Safely handle timestamp - use current date if invalid
  const getFormattedTime = () => {
    try {
      const date = timestamp ? new Date(timestamp) : new Date();
      // Check if date is valid
      if (isNaN(date.getTime())) {
        return format(new Date(), "h:mm a");
      }
      return format(date, "h:mm a");
    } catch (error) {
      console.warn("Invalid timestamp in ChatBubble:", timestamp, error);
      return format(new Date(), "h:mm a");
    }
  };

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={variants}
      transition={{ duration: 0.3 }}
      className={`flex items-start gap-3 ${isBot ? "" : "flex-row-reverse"}`}
    >
      <div
        className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center font-bold shadow-sm ${
          isBot ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground"
        }`}
      >
        {isBot ? "🤖" : "👤"}
      </div>
      <div
        className={`relative max-w-md lg:max-w-lg px-4 py-3 rounded-xl shadow-sm ${
          isBot
            ? "bg-card text-card-foreground rounded-bl-none border border-border"
            : "bg-primary text-primary-foreground rounded-br-none"
        }`}
      >
        <p className="text-sm leading-relaxed whitespace-pre-wrap">{message}</p>
        <time
          className={`text-xs mt-2 block ${
            isBot ? "text-muted-foreground" : "text-primary-foreground/70"
          }`}
        >
          {getFormattedTime()}
        </time>
      </div>
    </motion.div>
  );
};

export default ChatBubble;
