import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  AlertTriangle,
  Clock,
  CheckCircle,
  Users,
  TrendingUp,
  Calendar,
} from "lucide-react";

const stats = [
  {
    title: "Active Crisis Alerts",
    value: "3",
    description: "Requiring immediate attention",
    icon: AlertTriangle,
    trend: "+2 from yesterday",
    status: "critical",
  },
  {
    title: "Pending Sessions",
    value: "12",
    description: "Scheduled for today",
    icon: Clock,
    trend: "2 emergency slots available",
    status: "warning",
  },
  {
    title: "Completed Sessions",
    value: "8",
    description: "Finished today",
    icon: CheckCircle,
    trend: "+1 from yesterday",
    status: "success",
  },
  {
    title: "High Priority Cases",
    value: "5",
    description: "Active monitoring",
    icon: Users,
    trend: "No change from yesterday",
    status: "info",
  },
];

const getStatusColor = (status: string) => {
  switch (status) {
    case "critical":
      return "text-destructive";
    case "warning":
      return "text-amber-500 dark:text-amber-400";
    case "success":
      return "text-emerald-500 dark:text-emerald-400";
    default:
      return "text-primary";
  }
};

const getStatusBg = (status: string) => {
  switch (status) {
    case "critical":
      return "bg-destructive/10";
    case "warning":
      return "bg-amber-500/10";
    case "success":
      return "bg-emerald-500/10";
    default:
      return "bg-primary/10";
  }
};

export function TherapistDashboardStats() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => {
        const Icon = stat.icon;
        return (
          <Card key={stat.title} className="hover:shadow-md transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {stat.title}
              </CardTitle>
              <div className={`p-2 rounded-lg ${getStatusBg(stat.status)}`}>
                <Icon className={`h-4 w-4 ${getStatusColor(stat.status)}`} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground">
                {stat.description}
              </p>
              <div className="mt-2">
                <Badge variant="outline" className="text-xs">
                  {stat.trend}
                </Badge>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
