
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft } from "lucide-react";

interface AuthCardProps {
  onComplete: () => void;
  onBack: () => void;
  onSkipToChat?: () => void;
}

const AuthCard = ({ onComplete, onBack, onSkipToChat }: AuthCardProps) => {
  const [isSignUp, setIsSignUp] = useState(true);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // In a real app, this would handle actual authentication
    onComplete();
  };

  const handleGoogleLogin = () => {
    // In a real app, this would handle Google OAuth
    onComplete();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Button
          variant="ghost"
          onClick={onBack}
          className="mb-6 text-gray-600 hover:text-gray-800"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </Button>

        {/* Skip button for testing */}
        {onSkipToChat && (
          <div className="mb-4 text-center">
            <Button
              onClick={onSkipToChat}
              variant="outline"
              size="sm"
              className="text-purple-600 border-purple-200 hover:bg-purple-50"
            >
              Skip to Chat (Testing)
            </Button>
          </div>
        )}

        <Card className="shadow-xl border-0 bg-white/80 backdrop-blur-sm">
          <CardHeader className="text-center pb-4">
            <CardTitle className="text-2xl font-light text-gray-800">
              Welcome to TheraSage 🌸
            </CardTitle>
            <p className="text-gray-600 text-sm">
              {isSignUp ? "Create your safe space" : "Welcome back"}
            </p>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* Google Login */}
            <Button
              onClick={handleGoogleLogin}
              variant="outline"
              className="w-full py-3 text-gray-700 border-gray-200 hover:border-purple-200 hover:bg-purple-50/50 transition-all duration-300"
            >
              <span className="mr-2">🌟</span>
              Continue with Google
            </Button>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-200"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-4 bg-white text-gray-500">or</span>
              </div>
            </div>

            {/* Email/Password Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {isSignUp && (
                <div>
                  <Input
                    type="text"
                    placeholder="Your name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full py-3 border-gray-200 rounded-xl focus:border-purple-300 focus:ring-purple-200"
                    required
                  />
                </div>
              )}
              
              <div>
                <Input
                  type="email"
                  placeholder="Email address"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full py-3 border-gray-200 rounded-xl focus:border-purple-300 focus:ring-purple-200"
                  required
                />
              </div>
              
              <div>
                <Input
                  type="password"
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full py-3 border-gray-200 rounded-xl focus:border-purple-300 focus:ring-purple-200"
                  required
                />
              </div>

              <Button
                type="submit"
                className="w-full py-3 bg-gradient-to-r from-purple-400 to-pink-400 hover:from-purple-500 hover:to-pink-500 text-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
              >
                {isSignUp ? "Create my safe space ✨" : "Welcome back 💜"}
              </Button>
            </form>

            <div className="text-center">
              <button
                onClick={() => setIsSignUp(!isSignUp)}
                className="text-purple-500 hover:text-purple-600 text-sm transition-colors duration-200"
              >
                {isSignUp 
                  ? "Already have an account? Sign in" 
                  : "Need an account? Sign up"}
              </button>
            </div>

            <div className="bg-purple-50/50 rounded-xl p-4 text-center">
              <p className="text-xs text-gray-600">
                🔒 Your information is encrypted and completely private. 
                We'll never share your personal details.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AuthCard;
