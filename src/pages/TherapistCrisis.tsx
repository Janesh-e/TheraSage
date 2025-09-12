import { CrisisWorklistTable } from "@/components/therapist/CrisisWorklistTable";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
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
      <div className="bg-gradient-to-r from-destructive/10 to-orange-500/10 rounded-lg p-6">
        <h2 className="text-2xl font-bold text-foreground mb-2 flex items-center gap-2">
          <AlertTriangle className="h-6 w-6 text-destructive" />
          Crisis Management Dashboard
        </h2>
        <p className="text-muted-foreground">
          Monitor and respond to crisis alerts from students across your assigned colleges.
        </p>
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
                    <p className="text-sm text-muted-foreground">{stat.label}</p>
                    <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
                    <p className="text-xs text-muted-foreground">{stat.change}</p>
                  </div>
                  <Icon className={`h-8 w-8 ${stat.color}`} />
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Crisis Alerts Priority Banner */}
      <div className="bg-destructive/10 border-l-4 border-destructive rounded-lg p-4">
        <div className="flex items-center gap-2 mb-2">
          <AlertTriangle className="h-5 w-5 text-destructive" />
          <h3 className="font-semibold text-destructive">Critical Alerts Require Immediate Attention</h3>
        </div>
        <p className="text-sm text-muted-foreground">
          3 critical alerts detected in the last 30 minutes. Review and respond to high-priority cases first.
        </p>
        <div className="mt-2 flex gap-2">
          <Badge variant="destructive">Student-A42F - Suicidal Ideation</Badge>
          <Badge variant="destructive">Student-F78K - Self-Harm</Badge>
          <Badge variant="destructive">Student-G34L - Crisis Episode</Badge>
        </div>
      </div>

      {/* Main Crisis Worklist */}
      <CrisisWorklistTable />
    </div>
  );
};

export default TherapistCrisis;