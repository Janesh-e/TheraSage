import { useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Calendar,
  Download,
  Heart,
  Activity,
  BookOpen,
  Brain,
  Target,
  Shield,
  MessageSquare,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";

// Mock data for demonstration
const moodData = [
  { date: "Mon", mood: 7, energy: 6 },
  { date: "Tue", mood: 5, energy: 4 },
  { date: "Wed", mood: 8, energy: 7 },
  { date: "Thu", mood: 6, energy: 5 },
  { date: "Fri", mood: 9, energy: 8 },
  { date: "Sat", mood: 7, energy: 6 },
  { date: "Sun", mood: 8, energy: 7 },
];

const activityData = [
  { time: "6AM", sessions: 1 },
  { time: "9AM", sessions: 2 },
  { time: "12PM", sessions: 3 },
  { time: "3PM", sessions: 4 },
  { time: "6PM", sessions: 6 },
  { time: "9PM", sessions: 8 },
  { time: "12AM", sessions: 5 },
];

const journalEntries = [
  {
    date: "2024-01-15",
    title: "Morning Reflection",
    preview: "Feeling grateful for the small moments today...",
  },
  {
    date: "2024-01-14",
    title: "Evening Thoughts",
    preview: "Had a challenging day but learned something new about myself...",
  },
  {
    date: "2024-01-13",
    title: "Breakthrough Moment",
    preview:
      "Finally understood why I react the way I do in certain situations...",
  },
];

const cbtExercises = [
  { name: "Thought Record", used: 12, helpfulness: 8 },
  { name: "Gratitude Practice", used: 8, helpfulness: 9 },
  { name: "Breathing Exercise", used: 15, helpfulness: 7 },
  { name: "Cognitive Reframing", used: 6, helpfulness: 8 },
];

const emotionWords = [
  { word: "grateful", size: 24, color: "var(--color-chart-1)" },
  { word: "anxious", size: 20, color: "var(--color-chart-2)" },
  { word: "peaceful", size: 22, color: "var(--color-chart-3)" },
  { word: "hopeful", size: 18, color: "var(--color-chart-4)" },
  { word: "overwhelmed", size: 16, color: "var(--color-destructive)" },
  { word: "content", size: 20, color: "var(--color-chart-5)" },
  { word: "reflective", size: 14, color: "var(--color-chart-1)" },
  { word: "curious", size: 16, color: "var(--color-chart-2)" },
];

const Dashboard = () => {
  const [selectedTimeframe, setSelectedTimeframe] = useState("week");

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-accent/5 to-secondary/5">
      <div className="p-6 max-w-7xl mx-auto space-y-6">
        {/* Top Row - Mood Timeline & Activity Pattern */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Mood Timeline */}
          <Card className="bg-card border border-border shadow-md rounded-lg p-6">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center text-lg font-semibold text-card-foreground">
                <Heart className="w-5 h-5 mr-3 text-primary" />
                Mood Timeline
              </CardTitle>
              <CardDescription className="text-body-sm text-muted-foreground mt-1">
                Your emotional patterns over time
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={moodData}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="var(--color-border)"
                  />
                  <XAxis
                    dataKey="date"
                    stroke="var(--color-muted-foreground)"
                  />
                  <YAxis
                    domain={[0, 10]}
                    stroke="var(--color-muted-foreground)"
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "var(--color-card)",
                      border: "1px solid var(--color-border)",
                      borderRadius: "var(--radius-lg)",
                      boxShadow: "var(--shadow-lg)",
                      fontSize: "var(--text-body-small)",
                      padding: "var(--spacing-md)",
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="mood"
                    stroke={"var(--orange-primary)"}
                    strokeWidth={3}
                    dot={{
                      fill: "var(--orange-primary)",
                      strokeWidth: 2,
                      r: 4,
                    }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Activity Pattern */}
          <Card className="bg-card/90 backdrop-blur-sm border-border shadow-lg rounded-xl">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center text-card-foreground">
                <Activity className="w-5 h-5 mr-2 text-orange-500" />
                Activity Pattern
              </CardTitle>
              <CardDescription>
                When you're most active in seeking support
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={activityData}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="var(--color-border)"
                  />
                  <XAxis
                    dataKey="time"
                    stroke="var(--color-muted-foreground)"
                  />
                  <YAxis stroke="var(--color-muted-foreground)" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "var(--color-card)",
                      border: "1px solid var(--color-border)",
                      borderRadius: "var(--radius-lg)",
                      boxShadow: "var(--shadow-lg)",
                      fontSize: "var(--text-body-small)",
                      padding: "var(--spacing-md)",
                    }}
                  />
                  <Bar
                    dataKey="sessions"
                    fill={"var(--orange-primary)"}
                    radius={[8, 8, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* Middle Row - Journal & CBT Toolkit */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Journal Viewer */}
          <Card className="bg-card/90 backdrop-blur-sm border-border shadow-lg rounded-xl">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center text-card-foreground">
                <BookOpen className="w-5 h-5 mr-2 text-green-500" />
                Recent Reflections
              </CardTitle>
              <CardDescription>Your journey in words</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {journalEntries.map((entry, index) => (
                <div
                  key={index}
                  className="p-4 bg-gradient-to-r from-purple-50/50 to-pink-50/50 rounded-2xl border border-purple-100/50"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-card-foreground">
                      {entry.title}
                    </h4>
                    <span className="text-xs text-gray-500">{entry.date}</span>
                  </div>
                  <p className="text-sm text-gray-600 leading-relaxed">
                    {entry.preview}
                  </p>
                </div>
              ))}
              <Button
                variant="ghost"
                className="w-full mt-4 text-purple-600 hover:bg-purple-50"
              >
                View All Entries
              </Button>
            </CardContent>
          </Card>

          {/* CBT Toolkit History */}
          <Card className="bg-card/90 backdrop-blur-sm border-border shadow-lg rounded-xl">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center text-card-foreground">
                <Brain className="w-5 h-5 mr-2 text-indigo-500" />
                CBT Toolkit Usage
              </CardTitle>
              <CardDescription>Tools that have helped you most</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {cbtExercises.map((exercise, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-gradient-to-r from-blue-50/50 to-indigo-50/50 rounded-2xl border border-blue-100/50"
                >
                  <div>
                    <h4 className="font-medium text-card-foreground">
                      {exercise.name}
                    </h4>
                    <p className="text-sm text-gray-600">
                      Used {exercise.used} times
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-semibold text-indigo-600">
                      {exercise.helpfulness}/10
                    </div>
                    <div className="text-xs text-gray-500">Helpfulness</div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Bottom Row - Emotion Cloud & Goals */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Emotion Word Cloud */}
          <Card className="bg-card border border-border shadow-md rounded-lg p-6 lg:col-span-2">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center text-lg font-semibold text-card-foreground">
                <MessageSquare className="w-5 h-5 mr-3 text-primary" />
                Emotion Word Cloud
              </CardTitle>
              <CardDescription>
                Most frequent emotions and words you've shared
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 py-8">
                {emotionWords.map((word, index) => (
                  <div
                    key={index}
                    className="bg-card/50 p-4 rounded-lg border border-border shadow-sm flex items-center justify-center aspect-square transition-all duration-200 hover:bg-accent hover:shadow-md hover:-translate-y-1"
                  >
                    <span
                      className="font-medium cursor-pointer text-center text-lg" // Standardized font size
                      style={{
                        color: word.color,
                      }}
                    >
                      {word.word}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Goal Tracker & Privacy */}
          <div className="space-y-6">
            {/* Goal Tracker */}
            <Card className="bg-card/90 backdrop-blur-sm border-border shadow-lg rounded-xl">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center text-gray-800">
                  <Target className="w-5 h-5 mr-2 text-orange-500" />
                  This Week
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">
                      Journal Sessions
                    </span>
                    <span className="text-sm font-medium">3/3 ✨</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="h-2 rounded-full w-full"
                      style={{ backgroundColor: "var(--orange-primary)" }}
                    ></div>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Check-ins</span>
                    <span className="text-sm font-medium">5/7</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="h-2 rounded-full"
                      style={{
                        backgroundColor: "var(--orange-primary)",
                        width: "71%",
                      }}
                    ></div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Privacy Reminder */}
            <Card className="bg-card/90 backdrop-blur-sm border-border shadow-lg rounded-xl">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center text-gray-800">
                  <Shield className="w-5 h-5 mr-2 text-emerald-500" />
                  Your Privacy
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-gray-600 leading-relaxed mb-4">
                  Everything here is completely private and belongs to you. Your
                  thoughts, emotions, and reflections are secure.
                </p>
                <div className="flex items-center text-xs text-emerald-600">
                  <Shield className="w-3 h-3 mr-1" />
                  End-to-end encrypted
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Reflection Prompts */}
        <Card className="bg-gradient-to-r from-accent/10 via-primary/5 to-secondary/10 border border-border shadow-md rounded-lg p-6">
          <CardHeader className="pb-4">
            <CardTitle className="flex items-center text-lg font-semibold text-card-foreground">
              <Calendar className="w-5 h-5 mr-3 text-primary" />
              Today's Reflection Prompt
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8">
              <p className="text-body text-muted-foreground font-normal mb-6 italic leading-relaxed">
                "What has been feeling different lately? Take a moment to notice
                any shifts in your emotional landscape."
              </p>
              <Button
                className="rounded-lg px-8 py-3 shadow-sm hover:shadow-md transition-all duration-200"
                style={{
                  backgroundColor: "var(--orange-primary)",
                  color: "var(--orange-primary-foreground)",
                }}
              >
                <span className="text-button font-medium">Reflect on This</span>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
