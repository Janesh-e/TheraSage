
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Calendar, Download, Heart, Activity, BookOpen, Brain, Target, Shield, MessageSquare } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import AppSidebar from "@/components/AppSidebar";
import { SidebarProvider } from "@/components/ui/sidebar";

// Mock data for demonstration
const moodData = [
  { date: 'Mon', mood: 7, energy: 6 },
  { date: 'Tue', mood: 5, energy: 4 },
  { date: 'Wed', mood: 8, energy: 7 },
  { date: 'Thu', mood: 6, energy: 5 },
  { date: 'Fri', mood: 9, energy: 8 },
  { date: 'Sat', mood: 7, energy: 6 },
  { date: 'Sun', mood: 8, energy: 7 },
];

const activityData = [
  { time: '6AM', sessions: 1 },
  { time: '9AM', sessions: 2 },
  { time: '12PM', sessions: 3 },
  { time: '3PM', sessions: 4 },
  { time: '6PM', sessions: 6 },
  { time: '9PM', sessions: 8 },
  { time: '12AM', sessions: 5 },
];

const journalEntries = [
  { date: '2024-01-15', title: 'Morning Reflection', preview: 'Feeling grateful for the small moments today...' },
  { date: '2024-01-14', title: 'Evening Thoughts', preview: 'Had a challenging day but learned something new about myself...' },
  { date: '2024-01-13', title: 'Breakthrough Moment', preview: 'Finally understood why I react the way I do in certain situations...' },
];

const cbtExercises = [
  { name: 'Thought Record', used: 12, helpfulness: 8 },
  { name: 'Gratitude Practice', used: 8, helpfulness: 9 },
  { name: 'Breathing Exercise', used: 15, helpfulness: 7 },
  { name: 'Cognitive Reframing', used: 6, helpfulness: 8 },
];

const emotionWords = [
  { word: 'grateful', size: 24, color: '#10B981' },
  { word: 'anxious', size: 20, color: '#F59E0B' },
  { word: 'peaceful', size: 22, color: '#3B82F6' },
  { word: 'hopeful', size: 18, color: '#8B5CF6' },
  { word: 'overwhelmed', size: 16, color: '#EF4444' },
  { word: 'content', size: 20, color: '#06B6D4' },
  { word: 'reflective', size: 14, color: '#84CC16' },
  { word: 'curious', size: 16, color: '#F97316' },
];

const Dashboard = () => {
  const [selectedTimeframe, setSelectedTimeframe] = useState('week');

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full bg-gradient-to-br from-purple-50/30 via-pink-50/30 to-blue-50/30">
        <AppSidebar />
        
        <main className="flex-1 overflow-auto">
          <div className="p-6 max-w-7xl mx-auto space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
              <div>
                <h1 className="text-3xl font-light text-gray-800 mb-2">Your Emotional Journey 🌸</h1>
                <p className="text-gray-600">A safe space to reflect, grow, and understand yourself better</p>
              </div>
              <Button variant="outline" className="bg-white/80 backdrop-blur-sm border-purple-200 hover:bg-purple-50">
                <Download className="w-4 h-4 mr-2" />
                Export Data
              </Button>
            </div>

            {/* Top Row - Mood Timeline & Activity Pattern */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Mood Timeline */}
              <Card className="bg-white/80 backdrop-blur-sm border-white/50 shadow-lg rounded-3xl">
                <CardHeader className="pb-4">
                  <CardTitle className="flex items-center text-gray-800">
                    <Heart className="w-5 h-5 mr-2 text-pink-500" />
                    Mood Timeline
                  </CardTitle>
                  <CardDescription>Your emotional patterns over time</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={250}>
                    <LineChart data={moodData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="date" stroke="#9CA3AF" />
                      <YAxis domain={[0, 10]} stroke="#9CA3AF" />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'rgba(255, 255, 255, 0.95)',
                          border: 'none',
                          borderRadius: '12px',
                          boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)'
                        }}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="mood" 
                        stroke="url(#moodGradient)" 
                        strokeWidth={3}
                        dot={{ fill: '#8B5CF6', strokeWidth: 2, r: 4 }}
                      />
                      <defs>
                        <linearGradient id="moodGradient" x1="0" y1="0" x2="1" y2="0">
                          <stop offset="0%" stopColor="#8B5CF6" />
                          <stop offset="100%" stopColor="#EC4899" />
                        </linearGradient>
                      </defs>
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Activity Pattern */}
              <Card className="bg-white/80 backdrop-blur-sm border-white/50 shadow-lg rounded-3xl">
                <CardHeader className="pb-4">
                  <CardTitle className="flex items-center text-gray-800">
                    <Activity className="w-5 h-5 mr-2 text-blue-500" />
                    Activity Pattern
                  </CardTitle>
                  <CardDescription>When you're most active in seeking support</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={activityData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="time" stroke="#9CA3AF" />
                      <YAxis stroke="#9CA3AF" />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'rgba(255, 255, 255, 0.95)',
                          border: 'none',
                          borderRadius: '12px',
                          boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)'
                        }}
                      />
                      <Bar dataKey="sessions" fill="url(#activityGradient)" radius={[8, 8, 0, 0]} />
                      <defs>
                        <linearGradient id="activityGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#3B82F6" />
                          <stop offset="100%" stopColor="#06B6D4" />
                        </linearGradient>
                      </defs>
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>

            {/* Middle Row - Journal & CBT Toolkit */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Journal Viewer */}
              <Card className="bg-white/80 backdrop-blur-sm border-white/50 shadow-lg rounded-3xl">
                <CardHeader className="pb-4">
                  <CardTitle className="flex items-center text-gray-800">
                    <BookOpen className="w-5 h-5 mr-2 text-green-500" />
                    Recent Reflections
                  </CardTitle>
                  <CardDescription>Your journey in words</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {journalEntries.map((entry, index) => (
                    <div key={index} className="p-4 bg-gradient-to-r from-purple-50/50 to-pink-50/50 rounded-2xl border border-purple-100/50">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-gray-800">{entry.title}</h4>
                        <span className="text-xs text-gray-500">{entry.date}</span>
                      </div>
                      <p className="text-sm text-gray-600 leading-relaxed">{entry.preview}</p>
                    </div>
                  ))}
                  <Button variant="ghost" className="w-full mt-4 text-purple-600 hover:bg-purple-50">
                    View All Entries
                  </Button>
                </CardContent>
              </Card>

              {/* CBT Toolkit History */}
              <Card className="bg-white/80 backdrop-blur-sm border-white/50 shadow-lg rounded-3xl">
                <CardHeader className="pb-4">
                  <CardTitle className="flex items-center text-gray-800">
                    <Brain className="w-5 h-5 mr-2 text-indigo-500" />
                    CBT Toolkit Usage
                  </CardTitle>
                  <CardDescription>Tools that have helped you most</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {cbtExercises.map((exercise, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gradient-to-r from-blue-50/50 to-indigo-50/50 rounded-2xl border border-blue-100/50">
                      <div>
                        <h4 className="font-medium text-gray-800">{exercise.name}</h4>
                        <p className="text-sm text-gray-600">Used {exercise.used} times</p>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-semibold text-indigo-600">{exercise.helpfulness}/10</div>
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
              <Card className="bg-white/80 backdrop-blur-sm border-white/50 shadow-lg rounded-3xl lg:col-span-2">
                <CardHeader className="pb-4">
                  <CardTitle className="flex items-center text-gray-800">
                    <MessageSquare className="w-5 h-5 mr-2 text-cyan-500" />
                    Emotion Word Cloud
                  </CardTitle>
                  <CardDescription>Most frequent emotions and words you've shared</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap items-center justify-center gap-4 py-8">
                    {emotionWords.map((word, index) => (
                      <span 
                        key={index}
                        className="font-medium cursor-pointer hover:scale-110 transition-transform duration-200"
                        style={{ 
                          fontSize: `${word.size}px`, 
                          color: word.color,
                        }}
                      >
                        {word.word}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Goal Tracker & Privacy */}
              <div className="space-y-6">
                {/* Goal Tracker */}
                <Card className="bg-white/80 backdrop-blur-sm border-white/50 shadow-lg rounded-3xl">
                  <CardHeader className="pb-4">
                    <CardTitle className="flex items-center text-gray-800">
                      <Target className="w-5 h-5 mr-2 text-orange-500" />
                      This Week
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Journal Sessions</span>
                        <span className="text-sm font-medium">3/3 ✨</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className="bg-gradient-to-r from-green-400 to-green-500 h-2 rounded-full w-full"></div>
                      </div>
                    </div>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Check-ins</span>
                        <span className="text-sm font-medium">5/7</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div className="bg-gradient-to-r from-blue-400 to-blue-500 h-2 rounded-full w-5/7"></div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Privacy Reminder */}
                <Card className="bg-white/80 backdrop-blur-sm border-white/50 shadow-lg rounded-3xl">
                  <CardHeader className="pb-4">
                    <CardTitle className="flex items-center text-gray-800">
                      <Shield className="w-5 h-5 mr-2 text-emerald-500" />
                      Your Privacy
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600 leading-relaxed mb-4">
                      Everything here is completely private and belongs to you. Your thoughts, emotions, and reflections are secure.
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
            <Card className="bg-gradient-to-r from-purple-100/50 via-pink-100/50 to-blue-100/50 backdrop-blur-sm border-white/50 shadow-lg rounded-3xl">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center text-gray-800">
                  <Calendar className="w-5 h-5 mr-2 text-violet-500" />
                  Today's Reflection Prompt
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-6">
                  <p className="text-lg text-gray-700 font-light mb-4 italic">
                    "What has been feeling different lately? Take a moment to notice any shifts in your emotional landscape."
                  </p>
                  <Button className="bg-gradient-to-r from-purple-400 to-pink-400 hover:from-purple-500 hover:to-pink-500 text-white rounded-full px-8">
                    Reflect on This
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </main>
      </div>
    </SidebarProvider>
  );
};

export default Dashboard;
