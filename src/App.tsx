import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Download, Search, Plus } from "lucide-react";
import { ThemeProvider } from "./components/ThemeProvider";
import Layout from "./components/Layout";
import TherapistLayout from "./components/TherapistLayout";
import Index from "./pages/Index";
import Dashboard from "./pages/Dashboard";
import NotFound from "./pages/NotFound";
import ChatPage from "./pages/ChatPage";
import Journal from "./pages/Journal";
import Messages from "./pages/Messages";
import Community from "./pages/Community";
import ResourceHub from "./pages/ResourceHub";
import TherapistDashboard from "./pages/TherapistDashboard";
import TherapistCrisis from "./pages/TherapistCrisis";
import TherapistSessions from "./pages/TherapistSessions";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider defaultTheme="light" storageKey="therasage-ui-theme">
      <TooltipProvider>
        <BrowserRouter>
          <div className="min-h-screen w-full bg-background text-foreground overflow-x-hidden">
            <Routes>
              <Route path="/" element={<Index />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route
                path="/journal"
                element={
                  <Layout
                    title="Your Journal"
                    description="Reflecting on your emotional journey"
                  >
                    <Journal />
                  </Layout>
                }
              />
              <Route
                path="/messages"
                element={
                  <Layout
                    title="Messages"
                    description="Connect with peers anonymously or communicate with your assigned therapist"
                  >
                    <Messages />
                  </Layout>
                }
              />
              <Route
                path="/community"
                element={
                  <Layout
                    title="Communities"
                    description="Connect with others on similar journeys"
                    action={
                      <div className="flex items-center gap-4">
                        <div className="relative">
                          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                          <Input
                            placeholder="Search communities..."
                            className="pl-10 w-80 bg-card border-border focus:border-primary"
                          />
                        </div>
                        <Button className="bg-primary hover:bg-primary/90 text-primary-foreground shadow-md hover:shadow-lg transition-all duration-200">
                          <Plus className="h-4 w-4 mr-2" />
                          Create Post
                        </Button>
                      </div>
                    }
                  >
                    <Community />
                  </Layout>
                }
              />
              <Route
                path="/dashboard"
                element={
                  <Layout
                    title="Your Emotional Journey"
                    description="A safe space to reflect, grow, and understand yourself better"
                    action={
                      <Button
                        variant="outline"
                        className="bg-card shadow-sm border-border hover:bg-accent hover:border-primary/20 transition-all duration-200"
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Export Data
                      </Button>
                    }
                  >
                    <Dashboard />
                  </Layout>
                }
              />
              <Route
                path="/resources"
                element={
                  <Layout
                    title="Resource Hub"
                    description="Discover articles, audiobooks, and videos to support your mental health journey"
                  >
                    <ResourceHub />
                  </Layout>
                }
              />
              
              {/* Therapist Routes */}
              <Route
                path="/therapist/dashboard"
                element={
                  <TherapistLayout
                    title="Therapist Dashboard"
                    description="Monitor crisis alerts, manage sessions, and track your workload"
                  >
                    <TherapistDashboard />
                  </TherapistLayout>
                }
              />
              <Route
                path="/therapist/crisis"
                element={
                  <TherapistLayout
                    title="Crisis Management"
                    description="Review and respond to crisis alerts from students"
                  >
                    <TherapistCrisis />
                  </TherapistLayout>
                }
              />
              <Route
                path="/therapist/sessions"
                element={
                  <TherapistLayout
                    title="Session Management"
                    description="Manage and schedule therapy sessions"
                  >
                    <TherapistSessions />
                  </TherapistLayout>
                }
              />
              
              <Route path="*" element={<NotFound />} />
            </Routes>
          </div>

          {/* Toast notifications positioned properly */}
          <Toaster />
          <Sonner />
        </BrowserRouter>
      </TooltipProvider>
    </ThemeProvider>
  </QueryClientProvider>
);

export default App;
