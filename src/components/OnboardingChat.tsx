
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import ChatBubble from "@/components/ChatBubble";
import TypingIndicator from "@/components/TypingIndicator";
import ProgressIndicator from "@/components/ProgressIndicator";

interface OnboardingChatProps {
  isSignedUp: boolean;
}

const OnboardingChat = ({ isSignedUp }: OnboardingChatProps) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [showTyping, setShowTyping] = useState(false);
  const [responses, setResponses] = useState<Record<number, string>>({});
  const [chatHistory, setChatHistory] = useState<Array<{ type: 'question' | 'answer', content: string, step: number }>>([]);

  const questions = [
    {
      text: "👋 Hey there, I'm really glad you're here.",
      type: "greeting" as const,
      hasInput: false
    },
    {
      text: "🧠 What should I call you? 😊",
      type: "input" as const,
      hasInput: true,
      placeholder: "Your name..."
    },
    {
      text: "💬 And what would you like to call me? (Choose any name you'd like!)",
      type: "input" as const,
      hasInput: true,
      placeholder: "Any name you like..."
    },
    {
      text: "⚧️ How do you identify yourself?",
      type: "buttons" as const,
      hasInput: false,
      options: ["Male", "Female", "Non-binary", "Prefer not to say"]
    },
    {
      text: "🌼 Would you like to share anything about yourself that might help me support you better?",
      type: "textarea" as const,
      hasInput: true,
      placeholder: "Share as much or as little as you'd like... (optional)",
      optional: true
    },
    {
      text: "🕐 When during the day do you usually feel most in need of support?",
      type: "buttons" as const,
      hasInput: false,
      options: ["Morning ☀️", "Afternoon 🌤️", "Evening 🌅", "Late Night 🌙", "It varies 🔄"]
    },
    {
      text: "📔 Do you want to keep a private journal with me? I'll remember things you want me to, and nothing else 🗒️",
      type: "buttons" as const,
      hasInput: false,
      options: ["Yes, I'd love that! 📝", "Maybe later 🤔", "No thanks 💭"]
    },
    {
      text: "🧘 One last thing! If things ever feel heavy, should I offer resources or someone to talk to?",
      type: "buttons" as const,
      hasInput: false,
      options: ["Yes, please help me connect 🤝", "Just be here for me 💜", "I'll let you know 💫"]
    },
    {
      text: "🎉 That's all for now. I'm here whenever you're ready.",
      type: "completion" as const,
      hasInput: false
    }
  ];

  const progressMessages = [
    "Just getting to know you... 😊",
    "A few more questions... 🌸",
    "Almost there! 🌟",
    "Last few things... ✨",
    "You're doing great! 💜"
  ];

  useEffect(() => {
    // Show initial greeting after a short delay
    const timer = setTimeout(() => {
      showNextQuestion();
    }, 1000);
    return () => clearTimeout(timer);
  }, []);

  const showNextQuestion = () => {
    if (currentStep < questions.length) {
      setShowTyping(true);
      
      setTimeout(() => {
        setShowTyping(false);
        setChatHistory(prev => [...prev, {
          type: 'question',
          content: questions[currentStep].text,
          step: currentStep
        }]);
      }, 1500 + Math.random() * 1000); // Variable typing time for natural feel
    }
  };

  const handleResponse = (response: string) => {
    setResponses(prev => ({ ...prev, [currentStep]: response }));
    setChatHistory(prev => [...prev, {
      type: 'answer',
      content: response,
      step: currentStep
    }]);

    setCurrentStep(prev => prev + 1);
    
    // Show next question after a brief pause
    setTimeout(() => {
      showNextQuestion();
    }, 800);
  };

  const handleSkip = () => {
    handleResponse("(skipped)");
  };

  const currentQuestion = questions[currentStep];
  const totalSteps = questions.length - 2; // Exclude greeting and completion
  const currentProgress = Math.max(0, currentStep - 1);

  if (currentStep >= questions.length) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50 flex items-center justify-center p-4">
        <div className="max-w-2xl mx-auto text-center animate-fade-in">
          <div className="text-6xl mb-6">🎉</div>
          <h2 className="text-3xl font-light text-gray-800 mb-4">
            Welcome to your safe space!
          </h2>
          <p className="text-gray-600 mb-8">
            I'm {responses[2] || 'here'} whenever you need me, {responses[1] || 'friend'}. 
            Let's start this journey together. 💜
          </p>
          <Button className="bg-gradient-to-r from-purple-400 to-pink-400 hover:from-purple-500 hover:to-pink-500 text-white px-8 py-4 rounded-full text-lg font-medium shadow-lg hover:shadow-xl transition-all duration-300">
            Begin chatting ✨
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50">
      <div className="max-w-2xl mx-auto p-4 pt-8">
        {currentStep > 0 && currentStep < questions.length - 1 && (
          <ProgressIndicator 
            current={currentProgress} 
            total={totalSteps} 
            message={progressMessages[Math.min(Math.floor(currentProgress / 2), progressMessages.length - 1)]}
          />
        )}
        
        <div className="space-y-6 mb-6">
          {chatHistory.map((message, index) => (
            <ChatBubble
              key={index}
              message={message.content}
              isBot={message.type === 'question'}
              delay={index * 100}
            />
          ))}
          
          {showTyping && <TypingIndicator />}
        </div>

        {!showTyping && currentStep < questions.length && currentQuestion && (
          <div className="animate-fade-in">
            {currentQuestion.type === 'input' && (
              <div className="bg-white rounded-2xl p-4 shadow-lg border border-gray-100">
                <input
                  type="text"
                  placeholder={currentQuestion.placeholder}
                  className="w-full p-3 border border-gray-200 rounded-xl focus:border-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-100"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && e.currentTarget.value.trim()) {
                      handleResponse(e.currentTarget.value);
                      e.currentTarget.value = '';
                    }
                  }}
                  autoFocus
                />
                {currentQuestion.optional && (
                  <button
                    onClick={handleSkip}
                    className="text-gray-400 text-sm mt-2 hover:text-gray-600 transition-colors"
                  >
                    Skip this question
                  </button>
                )}
              </div>
            )}

            {currentQuestion.type === 'textarea' && (
              <div className="bg-white rounded-2xl p-4 shadow-lg border border-gray-100">
                <textarea
                  placeholder={currentQuestion.placeholder}
                  className="w-full p-3 border border-gray-200 rounded-xl focus:border-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-100 h-24 resize-none"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      if (e.currentTarget.value.trim()) {
                        handleResponse(e.currentTarget.value);
                        e.currentTarget.value = '';
                      }
                    }
                  }}
                  autoFocus
                />
                <div className="flex justify-between items-center mt-2">
                  <span className="text-xs text-gray-400">Press Enter to continue, Shift+Enter for new line</span>
                  {currentQuestion.optional && (
                    <button
                      onClick={handleSkip}
                      className="text-gray-400 text-sm hover:text-gray-600 transition-colors"
                    >
                      Skip this question
                    </button>
                  )}
                </div>
              </div>
            )}

            {currentQuestion.type === 'buttons' && currentQuestion.options && (
              <div className="grid gap-3">
                {currentQuestion.options.map((option, index) => (
                  <Button
                    key={index}
                    onClick={() => handleResponse(option)}
                    variant="outline"
                    className="p-4 text-left justify-start bg-white hover:bg-purple-50 border-gray-200 hover:border-purple-200 rounded-xl transition-all duration-200 hover:scale-105"
                  >
                    {option}
                  </Button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default OnboardingChat;
