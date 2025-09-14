import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface AuthCardProps {
  onComplete: (isReturningUser: boolean) => void;
  onBack: () => void;
  onSkipToChat?: () => void;
  initialMode?: "signin" | "signup"; // Add this prop
}

const AuthCard = ({
  onComplete,
  onBack,
  onSkipToChat,
  initialMode = "signin",
}: AuthCardProps) => {
  const [isSignUp, setIsSignUp] = useState(initialMode === "signup");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [collegeId, setCollegeId] = useState("");
  const [collegeName, setCollegeName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      if (isSignUp) {
        // Validation for signup
        if (!name.trim()) {
          toast({
            title: "Validation Error",
            description: "Please enter your name.",
            variant: "destructive",
          });
          return;
        }

        if (!collegeId.trim()) {
          toast({
            title: "Validation Error",
            description: "Please enter your College ID.",
            variant: "destructive",
          });
          return;
        }

        if (!collegeName.trim()) {
          toast({
            title: "Validation Error",
            description: "Please enter your College Name.",
            variant: "destructive",
          });
          return;
        }

        // Signup endpoint
        const signupPayload = {
          name: name.trim(),
          email: email.trim().toLowerCase(),
          password,
          college_id: collegeId.trim(),
          college_name: collegeName.trim(),
        };

        const response = await fetch("http://localhost:8000/auth/signup", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(signupPayload),
        });

        const data = await response.json();

        if (response.ok) {
          toast({
            title: "Success!",
            description: "Account created successfully!",
          });

          // Store user info
          localStorage.setItem("user_id", data.id);
          localStorage.setItem("user_name", data.name);
          localStorage.setItem("user_email", data.email);
          localStorage.setItem(
            "anonymous_username",
            data.anonymous_username || ""
          );
          localStorage.setItem("college_name", data.college_name);

          onComplete(false); // New user
        } else {
          toast({
            title: "Signup Error",
            description: data.detail || "Signup failed. Please try again.",
            variant: "destructive",
          });
        }
      } else {
        // Login validation
        if (!email.trim()) {
          toast({
            title: "Validation Error",
            description: "Please enter your email address.",
            variant: "destructive",
          });
          return;
        }

        if (!password) {
          toast({
            title: "Validation Error",
            description: "Please enter your password.",
            variant: "destructive",
          });
          return;
        }

        // Login endpoint - using form data as expected by OAuth2PasswordRequestForm
        const formData = new FormData();
        formData.append("username", email.trim().toLowerCase());
        formData.append("password", password);

        const response = await fetch("http://localhost:8000/auth/login", {
          method: "POST",
          body: formData,
        });

        const data = await response.json();

        if (response.ok) {
          toast({
            title: "Success!",
            description: "Login successful!",
          });

          // Store authentication data
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("user_id", data.user.id);
          localStorage.setItem("user_name", data.user.name);
          localStorage.setItem("user_email", data.user.email);
          localStorage.setItem(
            "anonymous_username",
            data.user.anonymous_username || ""
          );
          localStorage.setItem("college_name", data.user.college_name || "");

          onComplete(true); // Returning user
        } else {
          toast({
            title: "Login Error",
            description:
              data.detail || "Invalid email or password. Please try again.",
            variant: "destructive",
          });
        }
      }
    } catch (error) {
      console.error("Auth error:", error);
      toast({
        title: "Network Error",
        description:
          "Unable to connect to the server. Please check your connection and try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    // In a real app, this would handle Google OAuth
    toast({
      title: "Google Login",
      description: "Google authentication is not yet implemented.",
    });
  };

  // Reset form when switching between login/signup
  const handleToggleMode = () => {
    setIsSignUp(!isSignUp);
    // Clear form fields when switching modes
    setEmail("");
    setPassword("");
    setName("");
    setCollegeId("");
    setCollegeName("");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-accent/20 to-secondary/15 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Button
          variant="ghost"
          onClick={onBack}
          className="mb-6 text-muted-foreground hover:text-foreground"
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
              className="text-primary border-primary/30 hover:bg-accent"
            >
              Skip to Chat (Testing)
            </Button>
          </div>
        )}

        <Card className="shadow-xl border-0 bg-card/90 backdrop-blur-sm">
          <CardHeader className="text-center pb-4">
            <CardTitle className="text-2xl font-light text-card-foreground">
              Welcome to TheraSage 🌸
            </CardTitle>
            <p className="text-muted-foreground text-sm">
              {isSignUp ? "Create your safe space" : "Welcome back"}
            </p>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* Google Login */}
            <Button
              onClick={handleGoogleLogin}
              variant="outline"
              className="w-full py-3 text-card-foreground border-border hover:border-primary/30 hover:bg-accent/50 transition-all duration-300"
              disabled={isLoading}
            >
              <span className="mr-2">🌟</span>
              Continue with Google
            </Button>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-border"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-4 bg-card text-muted-foreground">or</span>
              </div>
            </div>

            {/* Email/Password Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {isSignUp && (
                <>
                  <div>
                    <Input
                      type="text"
                      placeholder="Your full name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="w-full py-3 border-border rounded-xl focus:border-primary focus:ring-primary/20"
                      required
                      disabled={isLoading}
                    />
                  </div>

                  <div>
                    <Input
                      type="text"
                      placeholder="College ID (e.g., STU12345)"
                      value={collegeId}
                      onChange={(e) => setCollegeId(e.target.value)}
                      className="w-full py-3 border-border rounded-xl focus:border-primary focus:ring-primary/20"
                      required
                      disabled={isLoading}
                    />
                  </div>

                  <div>
                    <Input
                      type="text"
                      placeholder="College/University name"
                      value={collegeName}
                      onChange={(e) => setCollegeName(e.target.value)}
                      className="w-full py-3 border-border rounded-xl focus:border-primary focus:ring-primary/20"
                      required
                      disabled={isLoading}
                    />
                  </div>
                </>
              )}

              <div>
                <Input
                  type="email"
                  placeholder="Email address"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full py-3 border-border rounded-xl focus:border-primary focus:ring-primary/20"
                  required
                  disabled={isLoading}
                />
              </div>

              <div>
                <Input
                  type="password"
                  placeholder="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full py-3 border-border rounded-xl focus:border-primary focus:ring-primary/20"
                  required
                  disabled={isLoading}
                  minLength={6}
                />
              </div>

              <Button
                type="submit"
                className="w-full py-3 bg-gradient-to-r from-primary to-secondary hover:from-primary/90 hover:to-secondary/90 text-primary-foreground rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
                disabled={isLoading}
              >
                {isLoading ? (
                  <span className="flex items-center">
                    <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin mr-2"></div>
                    {isSignUp ? "Creating account..." : "Signing in..."}
                  </span>
                ) : (
                  <>
                    {isSignUp ? "Create my safe space ✨" : "Welcome back 💜"}
                  </>
                )}
              </Button>
            </form>

            <div className="text-center">
              <button
                onClick={handleToggleMode}
                className="text-primary hover:text-primary/80 text-sm transition-colors duration-200"
                disabled={isLoading}
              >
                {isSignUp
                  ? "Already have an account? Sign in"
                  : "Need an account? Sign up"}
              </button>
            </div>

            <div className="bg-accent/30 rounded-xl p-4 text-center">
              <p className="text-xs text-muted-foreground">
                🔒 Your information is encrypted and completely private. We'll
                never share your personal details.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AuthCard;
