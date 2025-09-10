import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Calendar, Heart, MessageSquare, Clock } from "lucide-react";
import { format } from "date-fns";

interface JournalEntry {
  id: number;
  user_id: string;
  entry_type: string;
  content: string;
  timestamp: string;
}

const mockEntries: JournalEntry[] = [
  {
    id: 1,
    user_id: "mock_user",
    entry_type: "cbt_summary",
    content:
      "User shared: I've been feeling really anxious about my upcoming presentation. I'm worried I'll forget what to say. Emotion: Anxious",
    timestamp: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
  },
  {
    id: 2,
    user_id: "mock_user",
    entry_type: "emotional_checkin",
    content:
      "User shared: Today was a good day. I felt productive and content with my work. Emotion: Content",
    timestamp: new Date(Date.now() - 2 * 86400000).toISOString(), // 2 days ago
  },
  {
    id: 3,
    user_id: "mock_user",
    entry_type: "positive_reflection",
    content:
      "User shared: I'm grateful for my friends. They really supported me this week. Emotion: Grateful",
    timestamp: new Date(Date.now() - 3 * 86400000).toISOString(), // 3 days ago
  },
];

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
      const userId = localStorage.getItem("user_id");

      if (!userId) {
        setError("User not authenticated. Displaying mock data.");
        setEntries(mockEntries); // Load mock data if user is not found
        return;
      }

      const response = await fetch(`http://localhost:8000/journals/${userId}`);
      if (!response.ok) {
        throw new Error(
          `Failed to fetch journal entries (status: ${response.status})`
        );
      }

      const data = await response.json();
      setEntries(data.journals || []);
      if (data.journals.length === 0) {
        setError(null);
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "An unknown error occurred";
      setError(
        `Failed to load journal entries: ${errorMessage}. Displaying mock data as a fallback.`
      );
      setEntries(mockEntries); // Load mock data on error
      console.error("Error fetching journal entries:", err);
    } finally {
      setLoading(false);
    }
  };

  const getEntryTypeDisplay = (type: string) => {
    switch (type) {
      case "emotional_checkin":
        return {
          label: "Emotional Check-in",
          icon: Heart,
          color: "bg-secondary/10 text-secondary",
        };
      case "cbt_summary":
        return {
          label: "CBT Session",
          icon: MessageSquare,
          color: "bg-primary/10 text-primary",
        };
      case "positive_reflection":
        return {
          label: "Positive Reflection",
          icon: Calendar,
          color: "bg-accent text-accent-foreground",
        };
      default:
        return {
          label: "Journal Entry",
          icon: MessageSquare,
          color: "bg-muted text-muted-foreground",
        };
    }
  };

  const extractRelevantContent = (content: string) => {
    const userSharedMatch = content.match(/User shared: (.+)/);
    if (userSharedMatch) {
      const userContent = userSharedMatch[1];
      return userContent.length > 120
        ? `${userContent.substring(0, 120)}...`
        : userContent;
    }

    const lines = content
      .split("\n")
      .filter((line) => line.trim() && !line.includes("💭"));
    const firstMeaningfulLine = lines.find(
      (line) => !line.includes(":") || line.includes("User shared:")
    );

    if (firstMeaningfulLine) {
      return firstMeaningfulLine.length > 120
        ? `${firstMeaningfulLine.substring(0, 120)}...`
        : firstMeaningfulLine;
    }

    return content.length > 120 ? `${content.substring(0, 120)}...` : content;
  };

  const extractEmotion = (content: string) => {
    const emotionMatch = content.match(/Emotion: (\w+)/);
    return emotionMatch ? emotionMatch[1] : null;
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading your journals...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      {error && (
        <div className="mb-6 p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg text-yellow-700 dark:text-yellow-400">
          {error}
        </div>
      )}

      {entries.length === 0 && !loading ? (
        <Card className="text-center py-12 bg-card">
          <CardContent>
            <MessageSquare className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">
              No journal entries yet
            </h3>
            <p className="text-muted-foreground">
              Start chatting with TheraSage to create your first journal entry!
            </p>
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
              <Card
                key={entry.id}
                className="hover:shadow-lg transition-shadow duration-200 bg-card"
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={`p-2 rounded-full ${entryType.color}`}>
                        <IconComponent className="h-5 w-5" />
                      </div>
                      <div>
                        <CardTitle className="text-lg text-foreground">
                          {entryType.label}
                        </CardTitle>
                        <div className="flex items-center space-x-4 mt-1">
                          <div className="flex items-center text-sm text-muted-foreground">
                            <Clock className="h-4 w-4 mr-1" />
                            {format(
                              new Date(entry.timestamp),
                              "MMM d, yyyy 'at' h:mm a"
                            )}
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
                  <p className="text-foreground/90 leading-relaxed">
                    {relevantContent}
                  </p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default Journal;
