import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import ChatBubble from "@/components/ChatBubble";
import TypingIndicator from "@/components/TypingIndicator";
import ProgressIndicator from "@/components/ProgressIndicator";
import MainChat from "@/components/MainChat";

interface OnboardingChatProps {
  isSignedUp: boolean;
}

const OnboardingChat = ({ isSignedUp }: OnboardingChatProps) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [showTyping, setShowTyping] = useState(false);
  const [responses, setResponses] = useState<Record<number, string>>({});
  const [chatHistory, setChatHistory] = useState<Array<{ type: 'question' | 'answer', content: string, step: number }>>([]);
  const [showInput, setShowInput] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [showMainChat, setShowMainChat] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

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

  // Auto-scroll to bottom when new messages appear
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, showTyping]);

  useEffect(() => {
    // Show initial greeting after a short delay
    const timer = setTimeout(() => {
      showNextQuestion();
    }, 1000);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    // Handle step changes
    if (currentStep > 0 && currentStep < questions.length) {
      const timer = setTimeout(() => {
        showNextQuestion();
      }, 800);
      return () => clearTimeout(timer);
    }
  }, [currentStep]);

  const showNextQuestion = () => {
    if (currentStep >= questions.length) return;
    
    setShowTyping(true);
    setShowInput(false);
    
    setTimeout(() => {
      setShowTyping(false);
      setChatHistory(prev => [...prev, {
        type: 'question',
        content: questions[currentStep].text,
        step: currentStep
      }]);
      
      // Show input for questions that need it, or auto-advance for greeting
      if (questions[currentStep].type === 'greeting') {
        // Auto-advance from greeting after a delay
        setTimeout(() => {
          setCurrentStep(prev => prev + 1);
        }, 2000);
      } else if (questions[currentStep].hasInput || questions[currentStep].type === 'buttons') {
        setTimeout(() => {
          setShowInput(true);
        }, 500);
      } else if (questions[currentStep].type === 'completion') {
        // Handle completion
        setTimeout(() => {
          setIsComplete(true);
          setTimeout(() => {
            setShowMainChat(true);
          }, 3000);
        }, 1000);
      }
    }, 1500 + Math.random() * 1000); // Variable typing time for natural feel
  };

  const handleResponse = (response: string) => {
    setResponses(prev => ({ ...prev, [currentStep]: response }));
    setChatHistory(prev => [...prev, {
      type: 'answer',
      content: response,
      step: currentStep
    }]);

    setShowInput(false);
    setCurrentStep(prev => prev + 1);
  };

  const handleSkip = () => {
    handleResponse("(skipped)");
  };

  const currentQuestion = questions[currentStep];
  const totalSteps = questions.length - 2; // Exclude greeting and completion
  const currentProgress = Math.max(0, currentStep - 1);

  if (showMainChat) {
    return <MainChat userResponses={responses} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-accent/30 to-secondary/20 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-64 h-64 bg-primary/10 rounded-full animate-pulse blur-3xl"></div>
        <div className="absolute top-40 right-32 w-48 h-48 bg-secondary/10 rounded-full animate-pulse delay-1000 blur-3xl"></div>
        <div className="absolute bottom-32 left-1/4 w-32 h-32 bg-accent/20 rounded-full animate-pulse delay-2000 blur-3xl"></div>
        <div className="absolute top-1/3 right-1/4 w-40 h-40 bg-secondary/15 rounded-full animate-pulse delay-3000 blur-3xl"></div>
      </div>

      {/* Floating decorative elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-32 left-1/4 text-primary/20 text-6xl animate-bounce delay-1000">🌸</div>
        <div className="absolute top-1/2 right-20 text-secondary/25 text-4xl animate-bounce delay-2000">💜</div>
        <div className="absolute bottom-40 left-20 text-accent/30 text-5xl animate-bounce delay-3000">🌙</div>
        <div className="absolute top-1/4 right-1/3 text-secondary/20 text-3xl animate-bounce delay-4000">✨</div>
      </div>

      {/* Sticky Progress Indicator */}
      {currentStep > 0 && currentStep < questions.length - 1 && (
        <div className="sticky top-0 z-20 bg-background/90 backdrop-blur-sm border-b border-border p-4">
          <ProgressIndicator 
            current={currentProgress} 
            total={totalSteps} 
            message={progressMessages[Math.min(Math.floor(currentProgress / 2), progressMessages.length - 1)]}
          />
        </div>
      )}

      <div 
        ref={containerRef}
        className={`max-w-4xl mx-auto p-6 pt-8 relative z-10 transition-all duration-1000 ${
          isComplete ? 'opacity-0 transform scale-95' : 'opacity-100 transform scale-100'
        }`}
      >
        {/* Welcome header for first message */}
        {currentStep === 0 && (
          <div className="text-center mb-8 animate-fade-in">
            <div className="inline-block p-4 bg-card/80 backdrop-blur-sm rounded-3xl shadow-lg border border-border mb-4">
              <h2 className="text-2xl font-light text-card-foreground">Welcome to your safe space</h2>
              <p className="text-muted-foreground mt-2">Let's get to know each other</p>
            </div>
          </div>
        )}
        
        <div className="space-y-8 mb-8">
          {chatHistory.map((message, index) => (
            <div key={index} className="animate-fade-in">
              <ChatBubble
                message={message.content}
                isBot={message.type === 'question'}
                timestamp={new Date()}
              />
            </div>
          ))}
          
          {showTyping && (
            <div className="animate-fade-in">
              <TypingIndicator />
            </div>
          )}
        </div>

        {showInput && currentQuestion && (
          <div className="animate-fade-in sticky bottom-6 z-10">
            <div className="bg-card/90 backdrop-blur-sm rounded-3xl p-6 shadow-xl border border-border max-w-2xl mx-auto">
              {currentQuestion.type === 'input' && (
                <div>
                  <input
                    type="text"
                    placeholder={currentQuestion.placeholder}
                    className="w-full p-4 border-2 border-border rounded-2xl focus:border-primary focus:outline-none focus:ring-4 focus:ring-primary/20 text-lg bg-input text-foreground"
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
                      className="text-gray-400 text-sm mt-3 hover:text-gray-600 transition-colors block mx-auto"
                    >
                      Skip this question
                    </button>
                  )}
                </div>
              )}

              {currentQuestion.type === 'textarea' && (
                <div>
                  <textarea
                    placeholder={currentQuestion.placeholder}
                    className="w-full p-4 border-2 border-border rounded-2xl focus:border-primary focus:outline-none focus:ring-4 focus:ring-primary/20 h-32 resize-none text-lg bg-input text-foreground"
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
                  <div className="flex justify-between items-center mt-3">
                    <span className="text-xs text-gray-500">Press Enter to continue, Shift+Enter for new line</span>
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
                <div className="grid gap-4 sm:grid-cols-2">
                  {currentQuestion.options.map((option, index) => (
                    <Button
                      key={index}
                      onClick={() => handleResponse(option)}
                      variant="outline"
                      className="p-6 text-left justify-start bg-card/90 hover:bg-accent border-2 border-border hover:border-primary/30 rounded-2xl transition-all duration-200 hover:scale-105 hover:shadow-lg text-lg text-card-foreground"
                    >
                      {option}
                    </Button>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Completion message */}
        {isComplete && (
          <div className="text-center animate-fade-in">
            <div className="inline-block p-8 bg-card/90 backdrop-blur-sm rounded-3xl shadow-xl border border-border mb-8">
              <div className="text-6xl mb-6">🎉</div>
              <h2 className="text-3xl font-light text-card-foreground mb-4">
                Welcome to your safe space!
              </h2>
              <p className="text-muted-foreground text-lg">
                I'm {responses[2] || 'here'} whenever you need me, {responses[1] || 'friend'}. 
                Let's start this journey together. 💜
              </p>
              <div className="mt-6">
                <div className="w-16 h-1 bg-gradient-to-r from-primary to-secondary mx-auto rounded-full"></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default OnboardingChat;
