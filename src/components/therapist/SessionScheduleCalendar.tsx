import { useState } from "react";
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

const sessions = [
  {
    id: "S-001",
    date: new Date(2024, 11, 15),
    time: "2:00 PM",
    duration: "50 min",
    patientId: "Patient-X45Y",
    type: "emergency",
    mode: "video",
    status: "confirmed",
    priority: "high",
    meetingLink: "https://meet.example.com/abc123",
  },
  {
    id: "S-002", 
    date: new Date(2024, 11, 15),
    time: "3:00 PM",
    duration: "50 min",
    patientId: "Patient-Z12A",
    type: "follow-up",
    mode: "in-person",
    status: "confirmed",
    priority: "medium",
  },
  {
    id: "S-003",
    date: new Date(2024, 11, 16),
    time: "10:00 AM",
    duration: "30 min",
    patientId: "Patient-B78C", 
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
      return "bg-blue-500 text-white";
    case "check-in":
      return "bg-green-500 text-white";
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

export function SessionScheduleCalendar() {
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(new Date());
  const [isScheduleDialogOpen, setIsScheduleDialogOpen] = useState(false);

  const selectedDateSessions = sessions.filter(
    session => selectedDate && 
    session.date.toDateString() === selectedDate.toDateString()
  );

  const hasSessionOnDate = (date: Date) => {
    return sessions.some(session => 
      session.date.toDateString() === date.toDateString()
    );
  };

  return (
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
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>
                Sessions for {selectedDate?.toLocaleDateString()}
              </CardTitle>
              <CardDescription>
                {selectedDateSessions.length} session(s) scheduled
              </CardDescription>
            </div>
            <Dialog open={isScheduleDialogOpen} onOpenChange={setIsScheduleDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Schedule Session
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-md">
                <DialogHeader>
                  <DialogTitle>Schedule Emergency Session</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>Patient ID</Label>
                    <Input placeholder="Enter patient ID" />
                  </div>
                  <div className="space-y-2">
                    <Label>Session Type</Label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="emergency">Emergency</SelectItem>
                        <SelectItem value="follow-up">Follow-up</SelectItem>
                        <SelectItem value="check-in">Check-in</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Mode</Label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="Select mode" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="video">Video Call</SelectItem>
                        <SelectItem value="phone">Phone Call</SelectItem>
                        <SelectItem value="in-person">In Person</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Time</Label>
                    <Input type="time" />
                  </div>
                  <div className="space-y-2">
                    <Label>Duration (minutes)</Label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="Select duration" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="30">30 minutes</SelectItem>
                        <SelectItem value="50">50 minutes</SelectItem>
                        <SelectItem value="90">90 minutes</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Notes</Label>
                    <Textarea placeholder="Session notes (optional)" />
                  </div>
                  <div className="flex gap-2 pt-4">
                    <Button className="flex-1">Schedule Session</Button>
                    <Button variant="outline" onClick={() => setIsScheduleDialogOpen(false)}>
                      Cancel
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
          </div>
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
                      <Badge variant={session.status === "confirmed" ? "default" : "secondary"}>
                        {session.status}
                      </Badge>
                    </div>
                    
                    <div className="flex gap-2">
                      {session.mode === "video" && session.meetingLink && (
                        <Button size="sm" asChild>
                          <a href={session.meetingLink} target="_blank" rel="noopener noreferrer">
                            <Video className="h-4 w-4 mr-2" />
                            Join Meeting
                          </a>
                        </Button>
                      )}
                      <Button size="sm" variant="outline">
                        <Edit className="h-4 w-4 mr-2" />
                        Edit
                      </Button>
                      <Button size="sm" variant="outline">
                        <Trash2 className="h-4 w-4 mr-2" />
                        Cancel
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}