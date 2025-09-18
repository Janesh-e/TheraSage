import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Calendar } from "@/components/ui/calendar";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { CalendarIcon, Clock, Video, MapPin, Phone, Plus, Edit, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { format, addDays } from "date-fns";
import { toast } from "sonner";
import { SessionManagement } from "./SessionManagement";

interface ScheduleSession {
  id: string;
  scheduled_for: string;
  duration_minutes: number;
  session_type: string;
  status: string;
  urgency_level: string;
  meeting_link?: string;
  user_info?: {
    anonymous_username: string;
    college_name: string;
  };
  crisis_info?: {
    crisis_type: string;
    risk_level: string;
  };
}

const getUrgencyColor = (urgency: string) => {
  switch (urgency) {
    case "CRITICAL":
      return "bg-destructive text-destructive-foreground";
    case "HIGH":
      return "bg-orange-500 text-white";
    case "MEDIUM":
      return "bg-blue-500 text-white";
    case "LOW":
      return "bg-green-500 text-white";
    default:
      return "bg-muted text-muted-foreground";
  }
};

const getSessionTypeIcon = (type: string) => {
  switch (type) {
    case "ONLINE_MEET":
      return Video;
    case "IN_PERSON":
      return MapPin;
    case "PHONE_CALL":
      return Phone;
    default:
      return Clock;
  }
};

export function SessionScheduleCalendar() {
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(new Date());
  const [sessions, setSessions] = useState<ScheduleSession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTherapistSchedule();
  }, []);

  const fetchTherapistSchedule = async () => {
    try {
      setLoading(true);
      const therapistData = localStorage.getItem("therapistUser");
      if (!therapistData) {
        toast.error("No therapist session found");
        return;
      }

      const therapist = JSON.parse(therapistData);
      const response = await fetch(
        `http://localhost:8000/therapist-dashboard/session-schedule/${therapist.id}?days_ahead=14`
      );

      if (!response.ok) {
        throw new Error("Failed to fetch schedule");
      }

      const data = await response.json();
      setSessions(data.sessions || []);
    } catch (error) {
      console.error("Error fetching schedule:", error);
      toast.error("Failed to load schedule");
    } finally {
      setLoading(false);
    }
  };

  const selectedDateSessions = sessions.filter(
    session => selectedDate && 
    new Date(session.scheduled_for).toDateString() === selectedDate.toDateString()
  );

  const hasSessionOnDate = (date: Date) => {
    return sessions.some(session => 
      new Date(session.scheduled_for).toDateString() === date.toDateString()
    );
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-3">
          <CardContent className="flex items-center justify-center py-8">
            <div className="text-muted-foreground">Loading schedule...</div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Calendar */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CalendarIcon className="h-5 w-5 text-primary" />
              Session Calendar
            </CardTitle>
            <CardDescription>Select a date to view sessions</CardDescription>
          </CardHeader>
          <CardContent>
            <Calendar
              mode="single"
              selected={selectedDate}
              onSelect={setSelectedDate}
              className={cn("w-full pointer-events-auto")}
              modifiers={{
                hasSession: (date) => hasSessionOnDate(date)
              }}
              modifiersStyles={{
                hasSession: {
                  backgroundColor: "hsl(var(--primary))",
                  color: "hsl(var(--primary-foreground))",
                  borderRadius: "4px"
                }
              }}
            />
          </CardContent>
        </Card>

        {/* Sessions for Selected Date */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>
              Sessions for {selectedDate?.toLocaleDateString()}
            </CardTitle>
            <CardDescription>
              {selectedDateSessions.length} session(s) scheduled
            </CardDescription>
          </CardHeader>
          <CardContent>
            {selectedDateSessions.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <CalendarIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No sessions scheduled for this date</p>
              </div>
            ) : (
              <div className="space-y-4">
                {selectedDateSessions.map((session) => {
                  const SessionIcon = getSessionTypeIcon(session.session_type);
                  return (
                    <div key={session.id} className="border rounded-lg p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge className={getUrgencyColor(session.urgency_level)}>
                            {session.urgency_level}
                          </Badge>
                          <span className="font-medium">
                            {session.user_info?.anonymous_username || "Anonymous"}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <SessionIcon className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm font-medium">
                            {format(new Date(session.scheduled_for), "p")}
                          </span>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between text-sm text-muted-foreground">
                        <span>Duration: {session.duration_minutes} min</span>
                        <Badge variant={session.status === "SCHEDULED" ? "default" : "secondary"}>
                          {session.status.replace("_", " ")}
                        </Badge>
                      </div>

                      {session.crisis_info && (
                        <div className="text-sm text-muted-foreground">
                          Crisis: {session.crisis_info.crisis_type} ({session.crisis_info.risk_level})
                        </div>
                      )}
                      
                      <div className="flex gap-2">
                        {session.session_type === "ONLINE_MEET" && session.meeting_link && (
                          <Button size="sm" asChild>
                            <a href={session.meeting_link} target="_blank" rel="noopener noreferrer">
                              <Video className="h-4 w-4 mr-2" />
                              Join Meeting
                            </a>
                          </Button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Session Management Component */}
      <SessionManagement />
    </div>
  );
}