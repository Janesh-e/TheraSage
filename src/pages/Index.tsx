
import { useState } from "react";
import AuthCard from "@/components/AuthCard";
import OnboardingChat from "@/components/OnboardingChat";

const Index = () => {
  const [currentView, setCurrentView] = useState<'landing' | 'auth' | 'onboarding'>('landing');
  const [isSignedUp, setIsSignedUp] = useState(false);

  const handleStartChat = () => {
    setCurrentView('onboarding');
  };

  const handleSignUp = () => {
    setCurrentView('auth');
  };

  const handleAuthComplete = () => {
    setIsSignedUp(true);
    setCurrentView('onboarding');
  };

  if (currentView === 'auth') {
    return <AuthCard onComplete={handleAuthComplete} onBack={() => setCurrentView('landing')} />;
  }

  if (currentView === 'onboarding') {
    return <OnboardingChat isSignedUp={isSignedUp} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50 flex items-center justify-center p-4">
      {/* Floating elements for visual interest */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-32 h-32 bg-purple-200/30 rounded-full animate-pulse"></div>
        <div className="absolute top-40 right-32 w-24 h-24 bg-pink-200/30 rounded-full animate-pulse delay-1000"></div>
        <div className="absolute bottom-32 left-1/4 w-20 h-20 bg-blue-200/30 rounded-full animate-pulse delay-2000"></div>
      </div>

      <div className="max-w-2xl mx-auto text-center relative z-10 animate-fade-in">
        {/* Logo/Brand */}
        <div className="mb-8">
          <h1 className="text-5xl font-light text-gray-800 mb-4 tracking-wide">
            Thera<span className="text-purple-500 font-medium">Sage</span>
          </h1>
          <div className="w-24 h-1 bg-gradient-to-r from-purple-300 to-pink-300 mx-auto rounded-full"></div>
        </div>

        {/* Main Message */}
        <div className="mb-12 space-y-4">
          <h2 className="text-3xl md:text-4xl font-light text-gray-700 leading-relaxed">
            We're here to listen, always. 💜
          </h2>
          <p className="text-lg text-gray-600 max-w-lg mx-auto leading-relaxed">
            A safe space where you can share your thoughts, feelings, and find gentle support whenever you need it.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="space-y-4 mb-12">
          <button
            onClick={handleStartChat}
            className="w-full max-w-sm bg-gradient-to-r from-purple-400 to-pink-400 text-white px-8 py-4 rounded-full text-lg font-medium shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 hover:from-purple-500 hover:to-pink-500"
          >
            Start chatting instantly ✨
          </button>
          
          <button
            onClick={handleSignUp}
            className="w-full max-w-sm bg-white text-gray-700 px-8 py-4 rounded-full text-lg font-medium shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 border border-gray-200 hover:border-purple-200"
          >
            Sign up for personalized help 🌸
          </button>
        </div>

        {/* Privacy Reassurance */}
        <div className="bg-white/60 backdrop-blur-sm rounded-3xl p-6 shadow-lg border border-white/50">
          <div className="flex items-center justify-center mb-3">
            <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center mr-3">
              <span className="text-green-600 text-sm">🔒</span>
            </div>
            <h3 className="text-lg font-medium text-gray-700">Your privacy is sacred</h3>
          </div>
          <p className="text-gray-600 text-sm leading-relaxed">
            Everything you share is completely private and secure. We're here to support you, 
            not judge you. Your emotional safety is our top priority.
          </p>
        </div>

        {/* Subtle encouragement */}
        <p className="text-gray-500 text-sm mt-8 italic">
          Take your time. There's no pressure here. 🌿
        </p>
      </div>
    </div>
  );
};

export default Index;
