import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Clock, Video, MapPin, Phone } from "lucide-react";

const upcomingSessions = [
  {
    id: "S-001",
    patientId: "Patient-X45Y",
    time: "2:00 PM",
    duration: "50 min",
    type: "emergency",
    mode: "video",
    status: "confirmed",
    priority: "high",
  },
  {
    id: "S-002",
    patientId: "Patient-Z12A",
    time: "3:00 PM",
    duration: "50 min",
    type: "follow-up",
    mode: "in-person",
    status: "confirmed",
    priority: "medium",
  },
  {
    id: "S-003",
    patientId: "Patient-B78C",
    time: "4:30 PM",
    duration: "30 min",
    type: "check-in",
    mode: "phone",
    status: "pending",
    priority: "low",
  },
];

const getTypeColor = (type: string) => {
  switch (type) {
    case "emergency":
      return "bg-destructive text-destructive-foreground";
    case "follow-up":
      return "bg-primary text-primary-foreground";
    case "check-in":
      return "bg-emerald-500 text-white dark:bg-emerald-600";
    default:
      return "bg-muted text-muted-foreground";
  }
};

const getModeIcon = (mode: string) => {
  switch (mode) {
    case "video":
      return Video;
    case "in-person":
      return MapPin;
    case "phone":
      return Phone;
    default:
      return Clock;
  }
};

export function UpcomingSessionsWidget() {
  return (
    <Card className="h-fit">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-primary" />
              Upcoming Sessions
            </CardTitle>
            <CardDescription>Today's schedule</CardDescription>
          </div>
          <Button variant="outline" size="sm">
            View Calendar
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {upcomingSessions.map((session) => {
          const ModeIcon = getModeIcon(session.mode);
          return (
            <div key={session.id} className="border rounded-lg p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Badge className={getTypeColor(session.type)}>
                    {session.type}
                  </Badge>
                  <span className="font-medium">{session.patientId}</span>
                </div>
                <div className="flex items-center gap-2">
                  <ModeIcon className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">{session.time}</span>
                </div>
              </div>

              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <span>Duration: {session.duration}</span>
                <Badge
                  variant={
                    session.status === "confirmed" ? "default" : "secondary"
                  }
                >
                  {session.status}
                </Badge>
              </div>

              <div className="flex gap-2">
                <Button size="sm" className="flex-1">
                  Start Session
                </Button>
                <Button size="sm" variant="outline">
                  Reschedule
                </Button>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
