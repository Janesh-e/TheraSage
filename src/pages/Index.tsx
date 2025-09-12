import { useState } from "react";
import AuthCard from "@/components/AuthCard";
import OnboardingChat from "@/components/OnboardingChat";
import MainChat from "@/components/MainChat";

const Index = () => {
  const [currentView, setCurrentView] = useState<'landing' | 'auth' | 'onboarding' | 'chat'>('landing');
  const [isSignedUp, setIsSignedUp] = useState(false);

  const handleStartChat = () => {
    setCurrentView('onboarding');
  };

  const handleSignUp = () => {
    setCurrentView('auth');
  };

  const handleAuthComplete = (isReturningUser: boolean) => {
    setIsSignedUp(true);
    // If user is logging in (returning user), skip onboarding
    if (isReturningUser) {
      setCurrentView('chat');
    } else {
      // If user is signing up (new user), go to onboarding
      setCurrentView('onboarding');
    }
  };

  const handleSkipToChat = () => {
    setIsSignedUp(true);
    setCurrentView('chat');
  };

  if (currentView === 'auth') {
    return <AuthCard onComplete={handleAuthComplete} onBack={() => setCurrentView('landing')} onSkipToChat={handleSkipToChat} />;
  }

  if (currentView === 'onboarding') {
    return <OnboardingChat isSignedUp={isSignedUp} />;
  }

  if (currentView === 'chat') {
    return <MainChat userResponses={{}} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-accent/20 to-secondary/15 flex items-center justify-center p-4">
      {/* Floating elements for visual interest */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-32 h-32 bg-primary/20 rounded-full animate-pulse"></div>
        <div className="absolute top-40 right-32 w-24 h-24 bg-secondary/20 rounded-full animate-pulse delay-1000"></div>
        <div className="absolute bottom-32 left-1/4 w-20 h-20 bg-accent/30 rounded-full animate-pulse delay-2000"></div>
      </div>

      <div className="max-w-2xl mx-auto text-center relative z-10 animate-fade-in">
        {/* Logo/Brand */}
        <div className="mb-2xl">
          <h1 className="text-display-lg font-bold text-foreground mb-lg tracking-tight">
            Thera<span className="text-primary font-bold">Sage</span>
          </h1>
          <div className="w-24 h-1 bg-gradient-to-r from-primary to-secondary mx-auto rounded-full"></div>
        </div>

        {/* Main Message */}
        <div className="mb-2xl space-y-lg">
          <h2 className="text-3xl md:text-4xl font-light text-foreground/90 leading-relaxed">
            We're here to listen, always. 💜
          </h2>
          <p className="text-body text-muted-foreground max-w-lg mx-auto leading-relaxed">
            A safe space where you can share your thoughts, feelings, and find gentle support whenever you need it.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="space-y-lg mb-2xl">
          <button
            onClick={handleStartChat}
            className="w-full max-w-sm bg-gradient-to-r from-primary to-secondary text-primary-foreground px-xl py-lg rounded-lg text-button font-medium shadow-md hover:shadow-lg transition-all duration-300 hover:scale-105 hover:from-primary/90 hover:to-secondary/90"
          >
            Start chatting instantly ✨
          </button>
          
          <button
            onClick={handleSignUp}
            className="w-full max-w-sm bg-card text-card-foreground px-xl py-lg rounded-lg text-button font-medium shadow-md hover:shadow-lg transition-all duration-300 hover:scale-105 border border-border hover:border-primary/30"
          >
            Sign up for personalized help 🌸
          </button>
          
          <div className="pt-md border-t border-border/50">
            <p className="text-body-sm text-muted-foreground mb-md">Healthcare professional?</p>
            <button
              onClick={() => window.location.href = '/therapist/dashboard'}
              className="w-full max-w-sm bg-accent text-accent-foreground px-xl py-lg rounded-lg text-button font-medium shadow-md hover:shadow-lg transition-all duration-300 hover:scale-105 border border-accent-foreground/20 hover:border-accent-foreground/40"
            >
              Therapist Portal 🏥
            </button>
          </div>
        </div>

        {/* Privacy Reassurance */}
        <div className="bg-card/90 backdrop-blur-sm rounded-lg p-xl shadow-md border border-border">
          <div className="flex items-center justify-center mb-md">
            <div className="w-8 h-8 bg-accent rounded-full flex items-center justify-center mr-md">
              <span className="text-accent-foreground text-body-sm">🔒</span>
            </div>
            <h3 className="text-heading-md font-semibold text-card-foreground">Your privacy is sacred</h3>
          </div>
          <p className="text-body-sm text-muted-foreground leading-relaxed">
            Everything you share is completely private and secure. We're here to support you, 
            not judge you. Your emotional safety is our top priority.
          </p>
        </div>

        {/* Subtle encouragement */}
        <p className="text-body-sm text-muted-foreground mt-xl italic">
          Take your time. There's no pressure here. 🌿
        </p>
      </div>
    </div>
  );
};

export default Index;
