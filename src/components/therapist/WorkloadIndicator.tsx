import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Activity, TrendingUp, TrendingDown } from "lucide-react";

const workloadData = {
  currentLoad: 75,
  maxCapacity: 100,
  activeCases: 24,
  weeklyHours: 38,
  maxWeeklyHours: 45,
  efficiency: 87,
  burnoutRisk: "medium",
};

const getWorkloadColor = (percentage: number) => {
  if (percentage >= 90) return "text-destructive";
  if (percentage >= 70) return "text-orange-500";
  if (percentage >= 50) return "text-yellow-500";
  return "text-green-500";
};

const getWorkloadBg = (percentage: number) => {
  if (percentage >= 90) return "bg-destructive";
  if (percentage >= 70) return "bg-orange-500";
  if (percentage >= 50) return "bg-yellow-500";
  return "bg-green-500";
};

const getBurnoutColor = (risk: string) => {
  switch (risk) {
    case "high":
      return "bg-destructive text-destructive-foreground";
    case "medium":
      return "bg-orange-500 text-white";
    case "low":
      return "bg-green-500 text-white";
    default:
      return "bg-muted text-muted-foreground";
  }
};

export function WorkloadIndicator() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-primary" />
          Workload Dashboard
        </CardTitle>
        <CardDescription>Monitor your capacity and well-being</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Current Workload */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Current Workload</span>
            <span className={`text-sm font-bold ${getWorkloadColor(workloadData.currentLoad)}`}>
              {workloadData.currentLoad}%
            </span>
          </div>
          <Progress 
            value={workloadData.currentLoad} 
            className="h-3"
          />
          <p className="text-xs text-muted-foreground mt-1">
            {workloadData.activeCases} active cases
          </p>
        </div>

        {/* Weekly Hours */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Weekly Hours</span>
            <span className="text-sm font-bold">
              {workloadData.weeklyHours}/{workloadData.maxWeeklyHours}h
            </span>
          </div>
          <Progress 
            value={(workloadData.weeklyHours / workloadData.maxWeeklyHours) * 100} 
            className="h-3"
          />
        </div>

        {/* Efficiency & Burnout Risk */}
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-3 rounded-lg bg-muted/50">
            <div className="flex items-center justify-center gap-1 mb-1">
              <TrendingUp className="h-4 w-4 text-green-500" />
              <span className="text-sm font-medium">Efficiency</span>
            </div>
            <div className="text-lg font-bold text-green-500">
              {workloadData.efficiency}%
            </div>
          </div>
          
          <div className="text-center p-3 rounded-lg bg-muted/50">
            <div className="flex items-center justify-center gap-1 mb-1">
              <TrendingDown className="h-4 w-4 text-orange-500" />
              <span className="text-sm font-medium">Burnout Risk</span>
            </div>
            <Badge className={getBurnoutColor(workloadData.burnoutRisk)}>
              {workloadData.burnoutRisk.toUpperCase()}
            </Badge>
          </div>
        </div>

        {/* Recommendations */}
        <div className="bg-accent/50 rounded-lg p-3">
          <p className="text-sm font-medium mb-1">💡 Recommendations</p>
          <ul className="text-xs text-muted-foreground space-y-1">
            <li>• Consider blocking 2 hours for admin work</li>
            <li>• Schedule a 15-minute break between sessions</li>
            <li>• Review high-intensity cases for delegation</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}