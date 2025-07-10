
import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar";
import AppSidebar from "@/components/AppSidebar";
import { Calendar, Heart, MessageSquare, Clock } from "lucide-react";
import { format } from "date-fns";

interface JournalEntry {
  id: number;
  user_id: string;
  entry_type: string;
  content: string;
  timestamp: string;
}

const Journal = () => {
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchJournalEntries();
  }, []);

  const fetchJournalEntries = async () => {
    try {
      setLoading(true);
      // This will be the API call when the backend route is ready
      // const response = await fetch('/journals/');
      // const data = await response.json();
      // setEntries(data);
      
      // Mock data for now - remove this when backend is ready
      const mockData: JournalEntry[] = [
        {
          id: 1,
          user_id: "user_123",
          entry_type: "emotional_checkin",
          content: "💭 Emotional Check-in - 2025-07-10 21:03\n\nEmotion: sadness (confidence: 0.97)\nPhase: exploring\n\nUser shared: hey there. im feeling a bit tired and exhausted today...",
          timestamp: "2025-07-10T21:03:00Z"
        },
        {
          id: 2,
          user_id: "user_123",
          entry_type: "cbt_summary",
          content: "💭 CBT Session Summary - 2025-07-09 14:30\n\nThought Pattern: Catastrophizing\nEmotion: anxiety (confidence: 0.89)\n\nUser shared: I keep thinking about worst case scenarios at work...",
          timestamp: "2025-07-09T14:30:00Z"
        },
        {
          id: 3,
          user_id: "user_123",
          entry_type: "positive_reflection",
          content: "🌟 Positive Reflection - 2025-07-08 16:45\n\nGratitude: Family support\nMood: hopeful\n\nUser shared: Today I realized how much my family means to me...",
          timestamp: "2025-07-08T16:45:00Z"
        }
      ];
      setEntries(mockData);
    } catch (err) {
      setError("Failed to load journal entries");
      console.error("Error fetching journal entries:", err);
    } finally {
      setLoading(false);
    }
  };

  const getEntryTypeDisplay = (type: string) => {
    switch (type) {
      case "emotional_checkin":
        return { label: "Emotional Check-in", icon: Heart, color: "bg-pink-100 text-pink-700" };
      case "cbt_summary":
        return { label: "CBT Session", icon: MessageSquare, color: "bg-blue-100 text-blue-700" };
      case "positive_reflection":
        return { label: "Positive Reflection", icon: Calendar, color: "bg-green-100 text-green-700" };
      default:
        return { label: "Journal Entry", icon: MessageSquare, color: "bg-gray-100 text-gray-700" };
    }
  };

  const extractRelevantContent = (content: string) => {
    // Extract the user shared part and limit length
    const userSharedMatch = content.match(/User shared: (.+)/);
    if (userSharedMatch) {
      const userContent = userSharedMatch[1];
      return userContent.length > 120 ? `${userContent.substring(0, 120)}...` : userContent;
    }
    
    // Fallback to first meaningful line
    const lines = content.split('\n').filter(line => line.trim() && !line.includes('💭'));
    const firstMeaningfulLine = lines.find(line => !line.includes(':') || line.includes('User shared:'));
    
    if (firstMeaningfulLine) {
      return firstMeaningfulLine.length > 120 ? `${firstMeaningfulLine.substring(0, 120)}...` : firstMeaningfulLine;
    }
    
    return content.length > 120 ? `${content.substring(0, 120)}...` : content;
  };

  const extractEmotion = (content: string) => {
    const emotionMatch = content.match(/Emotion: (\w+)/);
    return emotionMatch ? emotionMatch[1] : null;
  };

  if (loading) {
    return (
      <SidebarProvider>
        <div className="min-h-screen flex w-full">
          <AppSidebar />
          <SidebarInset className="flex-1">
            <div className="container mx-auto p-6">
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">Loading your journals...</p>
              </div>
            </div>
          </SidebarInset>
        </div>
      </SidebarProvider>
    );
  }

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <AppSidebar />
        <SidebarInset className="flex-1">
          <div className="container mx-auto p-6 max-w-4xl">
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-800 mb-2">Your Journal</h1>
              <p className="text-gray-600">Reflecting on your emotional journey</p>
            </div>

            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                {error}
              </div>
            )}

            {entries.length === 0 ? (
              <Card className="text-center py-12">
                <CardContent>
                  <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-800 mb-2">No journal entries yet</h3>
                  <p className="text-gray-600">Start chatting with TheraSage to create your first journal entry!</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-6">
                {entries.map((entry) => {
                  const entryType = getEntryTypeDisplay(entry.entry_type);
                  const IconComponent = entryType.icon;
                  const emotion = extractEmotion(entry.content);
                  const relevantContent = extractRelevantContent(entry.content);
                  
                  return (
                    <Card key={entry.id} className="hover:shadow-lg transition-shadow duration-200">
                      <CardHeader className="pb-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <div className={`p-2 rounded-full ${entryType.color}`}>
                              <IconComponent className="h-5 w-5" />
                            </div>
                            <div>
                              <CardTitle className="text-lg">{entryType.label}</CardTitle>
                              <div className="flex items-center space-x-4 mt-1">
                                <div className="flex items-center text-sm text-gray-500">
                                  <Clock className="h-4 w-4 mr-1" />
                                  {format(new Date(entry.timestamp), "MMM d, yyyy 'at' h:mm a")}
                                </div>
                                {emotion && (
                                  <Badge variant="secondary" className="text-xs">
                                    {emotion}
                                  </Badge>
                                )}
                              </div>
                            </div>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <p className="text-gray-700 leading-relaxed">
                          {relevantContent}
                        </p>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </div>
        </SidebarInset>
      </div>
    </SidebarProvider>
  );
};

export default Journal;
