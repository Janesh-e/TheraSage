import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AlertTriangle, Clock, Eye, Calendar } from "lucide-react";

const crisisAlerts = [
  {
    id: "CA-001",
    anonymousId: "Student-A42F",
    riskLevel: "critical",
    crisisType: "Suicidal Ideation",
    detectedAt: "2 minutes ago",
    confidenceScore: 95,
    college: "University College London",
  },
  {
    id: "CA-002", 
    anonymousId: "Student-B83G",
    riskLevel: "high",
    crisisType: "Severe Depression",
    detectedAt: "15 minutes ago",
    confidenceScore: 87,
    college: "Cambridge University",
  },
  {
    id: "CA-003",
    anonymousId: "Student-C29H",
    riskLevel: "medium",
    crisisType: "Anxiety Attack",
    detectedAt: "1 hour ago",
    confidenceScore: 73,
    college: "Oxford University",
  },
];

const getRiskColor = (risk: string) => {
  switch (risk) {
    case "critical":
      return "bg-destructive text-destructive-foreground";
    case "high":
      return "bg-orange-500 text-white";
    case "medium":
      return "bg-yellow-500 text-white";
    case "low":
      return "bg-green-500 text-white";
    default:
      return "bg-muted text-muted-foreground";
  }
};

export function CrisisAlertsWidget() {
  return (
    <Card className="h-fit">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              Crisis Alerts
            </CardTitle>
            <CardDescription>Urgent cases requiring attention</CardDescription>
          </div>
          <Button variant="outline" size="sm">
            View All
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {crisisAlerts.map((alert) => (
          <div key={alert.id} className="border rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Badge className={getRiskColor(alert.riskLevel)}>
                  {alert.riskLevel.toUpperCase()}
                </Badge>
                <span className="font-medium">{alert.anonymousId}</span>
              </div>
              <div className="flex items-center gap-1 text-sm text-muted-foreground">
                <Clock className="h-3 w-3" />
                {alert.detectedAt}
              </div>
            </div>
            
            <div>
              <p className="font-medium text-sm">{alert.crisisType}</p>
              <p className="text-xs text-muted-foreground">{alert.college}</p>
              <p className="text-xs text-muted-foreground">
                Confidence: {alert.confidenceScore}%
              </p>
            </div>
            
            <div className="flex gap-2">
              <Button size="sm" variant="destructive" className="flex-1">
                <Eye className="h-3 w-3 mr-1" />
                Review
              </Button>
              <Button size="sm" variant="outline" className="flex-1">
                <Calendar className="h-3 w-3 mr-1" />
                Schedule
              </Button>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}