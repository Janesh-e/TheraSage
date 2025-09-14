import { CrisisWorklistTable } from "@/components/therapist/CrisisWorklistTable";
import { TherapistDashboardStats } from "@/components/therapist/TherapistDashboardStats";
import { CrisisAlertsWidget } from "@/components/therapist/CrisisAlertsWidget";
import { UpcomingSessionsWidget } from "@/components/therapist/UpcomingSessionsWidget";
import { WorkloadIndicator } from "@/components/therapist/WorkloadIndicator";
import { AvailabilityToggle } from "@/components/therapist/AvailabilityToggle";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, Clock, TrendingUp, Users } from "lucide-react";

const quickStats = [
  {
    label: "Active Alerts",
    value: "12",
    change: "+3 from yesterday",
    icon: AlertTriangle,
    color: "text-destructive",
  },
  {
    label: "Avg Response Time",
    value: "8 min",
    change: "-2 min from last week",
    icon: Clock,
    color: "text-blue-500",
  },
  {
    label: "Resolution Rate",
    value: "94%",
    change: "+2% from last month",
    icon: TrendingUp,
    color: "text-green-500",
  },
  {
    label: "High Priority",
    value: "5",
    change: "2 critical, 3 high",
    icon: Users,
    color: "text-orange-500",
  },
];

const TherapistCrisis = () => {
  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold text-foreground flex items-center gap-3">
          <AlertTriangle className="h-8 w-8 text-destructive" />
          Crisis Management
        </h1>
        <p className="text-muted-foreground">
          Review and respond to crisis alerts from students across your assigned
          colleges
        </p>
      </div>

      {/* Alert Banner */}
      <div className="bg-gradient-to-r from-destructive/10 to-orange-500/10 rounded-lg p-6">
        <div className="flex items-center gap-2 mb-2">
          <AlertTriangle className="h-5 w-5 text-destructive" />
          <h3 className="font-semibold text-destructive">
            Critical Alerts Require Immediate Attention
          </h3>
        </div>
        <p className="text-sm text-muted-foreground">
          3 critical alerts detected in the last 30 minutes. Review and respond
          to high-priority cases first.
        </p>
        <div className="mt-2 flex gap-2">
          <Badge variant="destructive">Student-A42F - Suicidal Ideation</Badge>
          <Badge variant="destructive">Student-F78K - Self-Harm</Badge>
          <Badge variant="destructive">Student-G34L - Crisis Episode</Badge>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {quickStats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.label}>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">
                      {stat.label}
                    </p>
                    <p className={`text-2xl font-bold ${stat.color}`}>
                      {stat.value}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {stat.change}
                    </p>
                  </div>
                  <Icon className={`h-8 w-8 ${stat.color}`} />
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Main Crisis Worklist */}
      <CrisisWorklistTable />
    </div>
  );
};

const TherapistDashboard = () => {
  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold text-foreground">
          Therapist Dashboard
        </h1>
        <p className="text-muted-foreground">
          Monitor crisis alerts, manage sessions, and track your workload
        </p>
      </div>

      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-primary/10 to-secondary/10 rounded-lg p-6">
        <h2 className="text-2xl font-bold text-foreground mb-2">
          Welcome back, Dr. Smith 👋
        </h2>
        <p className="text-muted-foreground">
          Today is Tuesday, December 12th. You have 3 crisis alerts and 5
          upcoming sessions.
        </p>
      </div>

      {/* Key Metrics */}
      <TherapistDashboardStats />

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column - Alerts and Sessions */}
        <div className="lg:col-span-2 space-y-6">
          <CrisisAlertsWidget />
          <UpcomingSessionsWidget />
        </div>

        {/* Right Column - Status and Controls */}
        <div className="space-y-6">
          <AvailabilityToggle />
          <WorkloadIndicator />
        </div>
      </div>
    </div>
  );
};

export default TherapistCrisis;
