import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertTriangle, Clock, TrendingUp, Users, Calendar, CheckCircle } from "lucide-react";
import { toast } from "sonner";

interface DashboardStats {
  active_crisis_alerts: number;
  pending_sessions: number;
  completed_sessions_today: number;
  high_priority_cases: number;
  workload_score: number;
  availability_status: string;
  next_session?: {
    id: string;
    scheduled_for: string;
    session_type: string;
    urgency_level: string;
  };
}

export function TherapistDashboardStats() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      const token = localStorage.getItem("therapist_token");
      const therapistUser = JSON.parse(localStorage.getItem("therapist_user") || "{}");
      
      if (!token || !therapistUser.id) {
        toast.error("Authentication required");
        return;
      }

      const response = await fetch(`http://localhost:8000/therapist-dashboard/overview/${therapistUser.id}`, {
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) throw new Error("Failed to fetch dashboard stats");

      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error("Error fetching dashboard stats:", error);
      toast.error("Failed to load dashboard statistics");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardContent className="p-6">
              <div className="animate-pulse">
                <div className="h-4 bg-muted rounded w-3/4 mb-2"></div>
                <div className="h-8 bg-muted rounded w-1/2"></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!stats) return null;

  const dashboardStats = [
    {
      title: "Active Crisis Alerts",
      value: stats.active_crisis_alerts.toString(),
      description: `${stats.high_priority_cases} high priority`,
      icon: AlertTriangle,
      color: "text-destructive",
    },
    {
      title: "Pending Sessions",
      value: stats.pending_sessions.toString(),
      description: stats.next_session ? `Next: ${new Date(stats.next_session.scheduled_for).toLocaleTimeString()}` : "No upcoming sessions",
      icon: Calendar,
      color: "text-blue-500",
    },
    {
      title: "Completed Today",
      value: stats.completed_sessions_today.toString(),
      description: "Sessions completed",
      icon: CheckCircle,
      color: "text-green-500",
    },
    {
      title: "Workload Score",
      value: `${stats.workload_score}/10`,
      description: stats.workload_score > 7 ? "High load" : stats.workload_score > 4 ? "Moderate load" : "Light load",
      icon: TrendingUp,
      color: stats.workload_score > 7 ? "text-destructive" : stats.workload_score > 4 ? "text-orange-500" : "text-green-500",
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {dashboardStats.map((stat) => {
        const Icon = stat.icon;
        return (
          <Card key={stat.title}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">
                    {stat.title}
                  </p>
                  <p className={`text-2xl font-bold ${stat.color}`}>
                    {stat.value}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {stat.description}
                  </p>
                </div>
                <Icon className={`h-8 w-8 ${stat.color}`} />
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}