import { useState } from "react";
import AuthCard from "@/components/AuthCard";
import OnboardingChat from "@/components/OnboardingChat";
import MainChat from "@/components/MainChat";
import { Button } from "@/components/ui/button";
import {
  MessageCircle,
  Shield,
  Heart,
  Users,
  ChevronDown,
  Menu,
  X,
  Brain,
  Stethoscope,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const Index = () => {
  const [currentView, setCurrentView] = useState<
    "landing" | "auth" | "onboarding" | "chat"
  >("landing");
  const [isSignedUp, setIsSignedUp] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [authMode, setAuthMode] = useState<"signin" | "signup">("signin"); // Add this state

  const handleStartChat = () => {
    setCurrentView("onboarding");
  };

  const handleSignUp = () => {
    setAuthMode("signup"); // Set to signup mode
    setCurrentView("auth");
  };

  const handleLogin = () => {
    setAuthMode("signin"); // Set to signin mode
    setCurrentView("auth");
  };

  const handleAuthComplete = (isReturningUser: boolean) => {
    setIsSignedUp(true);
    if (isReturningUser) {
      setCurrentView("chat");
    } else {
      setCurrentView("onboarding");
    }
  };

  const handleSkipToChat = () => {
    setIsSignedUp(true);
    setCurrentView("chat");
  };

  if (currentView === "auth") {
    return (
      <AuthCard
        initialMode={authMode} // Use the authMode state instead of hardcoded "signin"
        onComplete={handleAuthComplete}
        onBack={() => setCurrentView("landing")}
        onSkipToChat={handleSkipToChat}
      />
    );
  }

  if (currentView === "onboarding") {
    return <OnboardingChat isSignedUp={isSignedUp} />;
  }

  if (currentView === "chat") {
    return <MainChat userResponses={{}} />;
  }

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    element?.scrollIntoView({ behavior: "smooth" });
    setIsMobileMenuOpen(false);
  };

  const fadeInUp = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.6 },
  };

  const staggerChildren = {
    animate: {
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 bg-background/95 backdrop-blur-sm border-b border-border z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-foreground">
                Thera<span className="text-primary">Sage</span>
              </h1>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center space-x-8">
              <button
                onClick={() => scrollToSection("about")}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                About
              </button>
              <button
                onClick={() => scrollToSection("features")}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                Features
              </button>
              <button
                onClick={() => scrollToSection("faq")}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                FAQ
              </button>
            </nav>

            {/* Desktop Action Buttons */}
            <div className="hidden md:flex items-center space-x-4">
              <Button
                onClick={() => (window.location.href = "/therapist/dashboard")}
                variant="outline"
                className="text-emerald-600 border-emerald-600 hover:bg-emerald-50 hover:text-emerald-700 dark:text-emerald-400 dark:border-emerald-400 dark:hover:bg-emerald-950"
              >
                <Stethoscope className="w-4 h-4 mr-2" />
                Therapist Portal
              </Button>
              <Button
                onClick={handleStartChat}
                className="bg-primary hover:bg-primary/90 text-primary-foreground"
              >
                Get Started
              </Button>
              <Button onClick={handleLogin} variant="outline">
                Login
              </Button>
              <Button onClick={handleSignUp} variant="outline">
                Sign Up
              </Button>
            </div>

            {/* Mobile menu button */}
            <button
              className="md:hidden"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            >
              {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>

          {/* Mobile Navigation */}
          <AnimatePresence>
            {isMobileMenuOpen && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="md:hidden py-4 border-t border-border"
              >
                <div className="flex flex-col space-y-4">
                  <button
                    onClick={() => scrollToSection("about")}
                    className="text-left text-muted-foreground hover:text-foreground transition-colors"
                  >
                    About
                  </button>
                  <button
                    onClick={() => scrollToSection("features")}
                    className="text-left text-muted-foreground hover:text-foreground transition-colors"
                  >
                    Features
                  </button>
                  <button
                    onClick={() => scrollToSection("faq")}
                    className="text-left text-muted-foreground hover:text-foreground transition-colors"
                  >
                    FAQ
                  </button>
                  <div className="flex flex-col space-y-2 pt-4 border-t border-border">
                    <Button
                      onClick={() =>
                        (window.location.href = "/therapist/dashboard")
                      }
                      variant="outline"
                      className="w-full text-emerald-600 border-emerald-600 hover:bg-emerald-50"
                    >
                      <Stethoscope className="w-4 h-4 mr-2" />
                      Therapist Portal
                    </Button>
                    <Button
                      onClick={handleStartChat}
                      className="bg-primary hover:bg-primary/90 text-primary-foreground w-full"
                    >
                      Get Started
                    </Button>
                    <div className="flex space-x-2">
                      <Button
                        onClick={handleLogin}
                        variant="outline"
                        className="flex-1"
                      >
                        Login
                      </Button>
                      <Button
                        onClick={handleSignUp}
                        variant="outline"
                        className="flex-1"
                      >
                        Sign Up
                      </Button>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </header>

      {/* Hero Section */}
      <section className="pt-24 pb-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <motion.div
            className="text-center max-w-4xl mx-auto"
            initial="initial"
            animate="animate"
            variants={staggerChildren}
          >
            <motion.div variants={fadeInUp} className="mb-8">
              <h1 className="text-4xl md:text-6xl font-bold text-foreground mb-6 leading-tight">
                We're here to listen,{" "}
                <span className="text-primary">always</span> 💜
              </h1>
              <p className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
                A safe space where you can share your thoughts, feelings, and
                find gentle support whenever you need it.
              </p>
            </motion.div>

            <motion.div variants={fadeInUp} className="mb-12">
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button
                  onClick={handleStartChat}
                  size="lg"
                  className="bg-primary hover:bg-primary/90 text-primary-foreground px-8 py-4 text-lg"
                >
                  Start chatting instantly ✨
                </Button>
              </div>
            </motion.div>

            <motion.div
              variants={fadeInUp}
              className="bg-card/90 backdrop-blur-sm rounded-xl p-8 shadow-lg border border-border max-w-2xl mx-auto"
            >
              <div className="flex items-center justify-center mb-4">
                <Shield className="w-8 h-8 text-primary mr-3" />
                <h3 className="text-xl font-semibold text-card-foreground">
                  Your privacy is sacred
                </h3>
              </div>
              <p className="text-muted-foreground leading-relaxed">
                Everything you share is completely private and secure. We're
                here to support you, not judge you. Your emotional safety is our
                top priority.
              </p>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* About Section */}
      <section id="about" className="py-16 bg-accent/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-3xl md:text-4xl font-bold text-foreground mb-4"
            >
              About TheraSage
            </motion.h2>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed"
            >
              We believe everyone deserves access to mental health support,
              whenever they need it, without barriers or judgment.
            </motion.p>
          </div>

          <div className="grid md:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <h3 className="text-2xl font-semibold text-foreground mb-4">
                Our Mission
              </h3>
              <p className="text-muted-foreground leading-relaxed mb-6">
                TheraSage combines cutting-edge AI with evidence-based
                therapeutic techniques to provide personalized mental health
                support that's available 24/7.
              </p>
              <p className="text-muted-foreground leading-relaxed">
                Whether you're dealing with stress, anxiety, depression, or just
                need someone to talk to, we're here to listen and help guide you
                towards better mental wellness.
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="grid grid-cols-2 gap-4"
            >
              <div className="bg-card p-6 rounded-lg text-center shadow-md">
                <div className="text-2xl font-bold text-primary mb-2">24/7</div>
                <div className="text-sm text-muted-foreground">
                  Always Available
                </div>
              </div>
              <div className="bg-card p-6 rounded-lg text-center shadow-md">
                <div className="text-2xl font-bold text-primary mb-2">100%</div>
                <div className="text-sm text-muted-foreground">
                  Private & Secure
                </div>
              </div>
              <div className="bg-card p-6 rounded-lg text-center shadow-md">
                <div className="text-2xl font-bold text-primary mb-2">AI</div>
                <div className="text-sm text-muted-foreground">
                  Powered Support
                </div>
              </div>
              <div className="bg-card p-6 rounded-lg text-center shadow-md">
                <div className="text-2xl font-bold text-primary mb-2">Free</div>
                <div className="text-sm text-muted-foreground">
                  No Cost to Start
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-16 bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-3xl md:text-4xl font-bold text-foreground mb-4"
            >
              Why Choose TheraSage?
            </motion.h2>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed"
            >
              We're dedicated to providing you with the best support possible.
              Here's what makes us stand out:
            </motion.p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="bg-card p-8 rounded-2xl shadow-lg border border-border/50 hover:shadow-xl transition-all duration-300"
            >
              <div className="flex items-center gap-4 mb-4">
                <Button
                  size="icon"
                  variant="secondary"
                  className="w-16 h-16 rounded-full bg-primary/10 hover:bg-primary/20 text-primary"
                >
                  <Brain className="w-8 h-8" />
                </Button>
              </div>
              <h3 className="text-xl font-semibold text-card-foreground mb-3">
                AI-Powered Support
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Our advanced AI understands your emotions and provides
                personalized guidance tailored to your unique mental health
                journey.
              </p>
            </motion.div>

            {/* Feature 2 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="bg-card p-8 rounded-2xl shadow-lg border border-border/50 hover:shadow-xl transition-all duration-300"
            >
              <div className="flex items-center gap-4 mb-4">
                <Button
                  size="icon"
                  variant="secondary"
                  className="w-16 h-16 rounded-full bg-primary/10 hover:bg-primary/20 text-primary"
                >
                  <Heart className="w-8 h-8" />
                </Button>
              </div>
              <h3 className="text-xl font-semibold text-card-foreground mb-3">
                24/7 Availability
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Whether it's 3 AM or during a busy day, we're always here when
                you need support. Mental health doesn't follow a schedule.
              </p>
            </motion.div>

            {/* Feature 3 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="bg-card p-8 rounded-2xl shadow-lg border border-border/50 hover:shadow-xl transition-all duration-300"
            >
              <div className="flex items-center gap-4 mb-4">
                <Button
                  size="icon"
                  variant="secondary"
                  className="w-16 h-16 rounded-full bg-primary/10 hover:bg-primary/20 text-primary"
                >
                  <Shield className="w-8 h-8" />
                </Button>
              </div>
              <h3 className="text-xl font-semibold text-card-foreground mb-3">
                Privacy & Security
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Everything you share is completely private and secure. We're
                here to support you, not judge you. Your emotional safety is our
                top priority.
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="py-16 bg-accent/5">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-3xl md:text-4xl font-bold text-foreground mb-4"
            >
              Frequently Asked Questions
            </motion.h2>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed"
            >
              Have questions? We have answers. Here are some of the most common
              questions we receive:
            </motion.p>
          </div>

          <div className="space-y-4">
            <FAQItem
              question="Is my data safe with TheraSage?"
              answer="Absolutely. We prioritize your privacy and data security. All your data is encrypted and we have strict policies in place to protect your information."
            />
            <FAQItem
              question="Can I use TheraSage anonymously?"
              answer="Yes, you can choose to remain anonymous. We offer various levels of anonymity to ensure you feel safe and secure while using our platform."
            />
            <FAQItem
              question="What if I need immediate help?"
              answer="If you are in crisis or need immediate help, we strongly encourage you to contact emergency services or a crisis hotline in your area. TheraSage is not a substitute for professional emergency assistance."
            />
            <FAQItem
              question="How does the AI therapy work?"
              answer="Our AI uses natural language processing and evidence-based therapeutic techniques to provide personalized support. It's trained on therapeutic methods like CBT and DBT, but it's designed to complement, not replace, professional therapy."
            />
          </div>
        </div>
      </section>

      {/* Final CTA Section */}
      <section className="py-16 bg-primary/5">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-6">
              Ready to start your journey?
            </h2>
            <p className="text-xl text-muted-foreground mb-8">
              Take the first step towards better mental health today
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                onClick={handleStartChat}
                size="lg"
                className="bg-primary hover:bg-primary/90 text-primary-foreground px-8 py-4"
              >
                Start chatting now
              </Button>
              <Button
                onClick={handleSignUp}
                size="lg"
                variant="outline"
                className="px-8 py-4"
              >
                Create an account
              </Button>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

// FAQ Item Component
const FAQItem = ({
  question,
  answer,
}: {
  question: string;
  answer: string;
}) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <motion.div
      className="bg-card rounded-lg border border-border overflow-hidden shadow-sm"
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.4 }}
    >
      <button
        className="w-full px-6 py-4 text-left flex justify-between items-center hover:bg-muted/50 transition-colors"
        onClick={() => setIsOpen(!isOpen)}
      >
        <h3 className="font-semibold text-foreground">{question}</h3>
        <ChevronDown
          className={`w-5 h-5 text-muted-foreground transition-transform ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="px-6 pb-4"
          >
            <p className="text-muted-foreground leading-relaxed">{answer}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default Index;
