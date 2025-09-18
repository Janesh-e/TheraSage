import React, { useState, useEffect } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  ArrowUpDown,
  Search,
  Eye,
  Calendar,
  CheckCircle,
  AlertTriangle,
  Clock,
  Video,
  Phone,
  MapPin,
} from "lucide-react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Calendar as CalendarComponent } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Textarea } from "@/components/ui/textarea";
import { format } from "date-fns";
import { cn } from "@/lib/utils";

interface CrisisAlert {
  id: string;
  user_anonymous: string;
  crisis_type: string;
  risk_level: string;
  status: string;
  detected_at: string;
  hours_since_detection: number;
  confidence_score: number;
  has_session_scheduled: boolean;
  user_college: string;
  trigger_message?: string;
  detected_indicators?: any;
  risk_factors?: string[];
  main_concerns?: string[];
  cognitive_distortions?: string[];
  urgency_level?: number;
}

interface TherapistUser {
  id: string;
  name: string;
  email: string;
}

interface SessionFormData {
  session_type: string;
  scheduled_for: Date;
  duration_minutes: number;
  meeting_link?: string;
  therapist_id: string;
}

export function CrisisWorklistTable() {
  const [alerts, setAlerts] = useState<CrisisAlert[]>([]);
  const [filteredAlerts, setFilteredAlerts] = useState<CrisisAlert[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [riskFilter, setRiskFilter] = useState("all");
  const [sortBy, setSortBy] = useState("detected_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [loading, setLoading] = useState(true);
  const [selectedAlert, setSelectedAlert] = useState<CrisisAlert | null>(null);
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);
  const [isScheduleOpen, setIsScheduleOpen] = useState(false);
  const [therapistUser, setTherapistUser] = useState<TherapistUser | null>(null);
  const [sessionForm, setSessionForm] = useState<SessionFormData>({
    session_type: "ONLINE_MEET",
    scheduled_for: new Date(),
    duration_minutes: 50,
    meeting_link: "",
    therapist_id: "",
  });
  const [isSchedulingSession, setIsSchedulingSession] = useState(false);

  useEffect(() => {
    // Get therapist user from localStorage
    const therapistData = localStorage.getItem("therapistUser");
    if (!therapistData) {
      toast.error("No therapist session found");
      return;
    }

    const therapist = JSON.parse(therapistData);
    setTherapistUser(therapist);
    setSessionForm(prev => ({ ...prev, therapist_id: therapist.id }));
    fetchAlerts(therapist.id);
  }, []);

  const fetchAlerts = async (therapistId: string) => {
    try {
      setLoading(true);
      const response = await fetch(
        `http://localhost:8000/therapist-dashboard/crisis-worklist/${therapistId}`
      );
      
      if (!response.ok) {
        throw new Error("Failed to fetch crisis alerts");
      }
      
      const data = await response.json();
      setAlerts(data);
      setFilteredAlerts(data);
    } catch (error) {
      console.error("Error fetching alerts:", error);
      toast.error("Failed to load crisis alerts");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let filtered = alerts.filter((alert) =>
      alert.user_anonymous.toLowerCase().includes(searchTerm.toLowerCase()) ||
      alert.crisis_type.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (statusFilter !== "all") {
      filtered = filtered.filter((alert) => alert.status === statusFilter);
    }

    if (riskFilter !== "all") {
      filtered = filtered.filter((alert) => alert.risk_level === riskFilter);
    }

    // Sort alerts
    filtered.sort((a, b) => {
      const aValue = a[sortBy as keyof CrisisAlert];
      const bValue = b[sortBy as keyof CrisisAlert];
      
      if (sortOrder === "asc") {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    setFilteredAlerts(filtered);
  }, [alerts, searchTerm, statusFilter, riskFilter, sortBy, sortOrder]);

  const getRiskLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case "critical":
        return "bg-destructive text-destructive-foreground";
      case "high":
        return "bg-orange-500 text-white";
      case "medium":
        return "bg-yellow-500 text-black";
      case "low":
        return "bg-green-500 text-white";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case "pending":
        return "bg-yellow-500 text-black";
      case "acknowledged":
        return "bg-blue-500 text-white";
      case "escalated":
        return "bg-purple-500 text-white";
      case "resolved":
        return "bg-green-500 text-white";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  const handleAcknowledge = async (alertId: string) => {
    try {
      const therapistData = localStorage.getItem("therapistUser");
      if (!therapistData) return;
      
      const therapist = JSON.parse(therapistData);
      
      const response = await fetch(
        `http://localhost:8000/therapist-dashboard/crisis/${alertId}/quick-response`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            therapist_id: therapist.id,
            response_type: "acknowledge",
            notes: "Crisis acknowledged by therapist"
          }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to acknowledge crisis");
      }

      toast.success("Crisis alert acknowledged successfully");
      fetchAlerts(therapist.id);
    } catch (error) {
      console.error("Error acknowledging crisis:", error);
      toast.error("Failed to acknowledge crisis alert");
    }
  };

  const handleScheduleSession = async () => {
    if (!selectedAlert || !therapistUser) return;
    
    try {
      setIsSchedulingSession(true);
      
      // Validate required fields
      if (sessionForm.session_type === "ONLINE_MEET" && !sessionForm.meeting_link?.trim()) {
        toast.error("Meeting link is required for online sessions");
        return;
      }

      const response = await fetch(
        `http://localhost:8000/therapist-dashboard/crisis/${selectedAlert.id}/create-session`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            session_type: sessionForm.session_type,
            scheduled_for: sessionForm.scheduled_for.toISOString(),
            duration_minutes: sessionForm.duration_minutes,
            meeting_link: sessionForm.session_type === "ONLINE_MEET" ? sessionForm.meeting_link : null,
            therapist_id: sessionForm.therapist_id,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to schedule session");
      }

      toast.success("Session scheduled successfully");
      setIsScheduleOpen(false);
      setSelectedAlert(null);
      fetchAlerts(therapistUser.id);
      
      // Reset form
      setSessionForm({
        session_type: "ONLINE_MEET",
        scheduled_for: new Date(),
        duration_minutes: 50,
        meeting_link: "",
        therapist_id: therapistUser.id,
      });
    } catch (error) {
      console.error("Error scheduling session:", error);
      toast.error(error instanceof Error ? error.message : "Failed to schedule session");
    } finally {
      setIsSchedulingSession(false);
    }
  };

  const openScheduleModal = (alert: CrisisAlert) => {
    setSelectedAlert(alert);
    setIsScheduleOpen(true);
  };

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(field);
      setSortOrder("desc");
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <div className="text-muted-foreground">Loading crisis alerts...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-destructive" />
          Crisis Worklist
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Filters */}
          <div className="flex flex-col md:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by student or crisis type..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="acknowledged">Acknowledged</SelectItem>
                <SelectItem value="escalated">Escalated</SelectItem>
                <SelectItem value="resolved">Resolved</SelectItem>
              </SelectContent>
            </Select>
            <Select value={riskFilter} onValueChange={setRiskFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Risk Level" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Risk</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="low">Low</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Table */}
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>
                    <Button variant="ghost" onClick={() => handleSort("user_anonymous")}>
                      Student
                      <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button variant="ghost" onClick={() => handleSort("crisis_type")}>
                      Crisis Type
                      <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button variant="ghost" onClick={() => handleSort("risk_level")}>
                      Risk Level
                      <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button variant="ghost" onClick={() => handleSort("status")}>
                      Status
                      <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button variant="ghost" onClick={() => handleSort("detected_at")}>
                      Detected
                      <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                  </TableHead>
                  <TableHead>Hours Ago</TableHead>
                  <TableHead>Confidence</TableHead>
                  <TableHead>Session</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredAlerts.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                      No crisis alerts found
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredAlerts.map((alert) => (
                    <TableRow key={alert.id}>
                      <TableCell className="font-medium">
                        {alert.user_anonymous}
                      </TableCell>
                      <TableCell>
                        <span className="capitalize">{alert.crisis_type.replace('_', ' ')}</span>
                      </TableCell>
                      <TableCell>
                        <Badge className={getRiskLevelColor(alert.risk_level)}>
                          {alert.risk_level}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={getStatusColor(alert.status)}>
                          {alert.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {new Date(alert.detected_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell>{alert.hours_since_detection}</TableCell>
                      <TableCell>{alert.confidence_score}</TableCell>
                      <TableCell>
                        {alert.has_session_scheduled ? (
                          <Badge className="bg-green-500 text-white">Scheduled</Badge>
                        ) : (
                          <Badge variant="outline">Not Scheduled</Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-8 w-8 p-0"
                            onClick={() => handleAcknowledge(alert.id)}
                            disabled={alert.status === "acknowledged"}
                          >
                            <CheckCircle className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-8 w-8 p-0"
                            onClick={() => openScheduleModal(alert)}
                            disabled={alert.has_session_scheduled}
                            title={alert.has_session_scheduled ? "Session already scheduled" : "Schedule session"}
                          >
                            <Calendar className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            className="h-8 w-8 p-0"
                            onClick={() => {
                              setSelectedAlert(alert);
                              setIsDetailsOpen(true);
                            }}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </div>

        {/* Crisis Details Dialog */}
        <Dialog open={isDetailsOpen} onOpenChange={setIsDetailsOpen}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Crisis Alert Details</DialogTitle>
              <DialogDescription>
                Detailed information about the crisis alert
              </DialogDescription>
            </DialogHeader>
            {selectedAlert && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-sm font-medium">Student</Label>
                    <p className="text-sm text-muted-foreground">{selectedAlert.user_anonymous}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">College</Label>
                    <p className="text-sm text-muted-foreground">{selectedAlert.user_college}</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Crisis Type</Label>
                    <p className="text-sm text-muted-foreground capitalize">
                      {selectedAlert.crisis_type.replace('_', ' ')}
                    </p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Risk Level</Label>
                    <Badge className={getRiskLevelColor(selectedAlert.risk_level)}>
                      {selectedAlert.risk_level}
                    </Badge>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Confidence Score</Label>
                    <p className="text-sm text-muted-foreground">{selectedAlert.confidence_score}%</p>
                  </div>
                  <div>
                    <Label className="text-sm font-medium">Urgency Level</Label>
                    <p className="text-sm text-muted-foreground">{selectedAlert.urgency_level || "Not specified"}</p>
                  </div>
                </div>

                {selectedAlert.trigger_message && (
                  <div>
                    <Label className="text-sm font-medium">Trigger Message</Label>
                    <p className="text-sm text-muted-foreground bg-muted p-3 rounded-md">
                      {selectedAlert.trigger_message}
                    </p>
                  </div>
                )}

                {selectedAlert.risk_factors && selectedAlert.risk_factors.length > 0 && (
                  <div>
                    <Label className="text-sm font-medium">Risk Factors</Label>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {selectedAlert.risk_factors.map((factor, index) => (
                        <Badge key={index} variant="secondary">
                          {factor}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {selectedAlert.main_concerns && selectedAlert.main_concerns.length > 0 && (
                  <div>
                    <Label className="text-sm font-medium">Main Concerns</Label>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {selectedAlert.main_concerns.map((concern, index) => (
                        <Badge key={index} variant="outline">
                          {concern}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {selectedAlert.cognitive_distortions && selectedAlert.cognitive_distortions.length > 0 && (
                  <div>
                    <Label className="text-sm font-medium">Cognitive Distortions</Label>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {selectedAlert.cognitive_distortions.map((distortion, index) => (
                        <Badge key={index} variant="destructive">
                          {distortion}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Session Scheduling Dialog */}
        <Dialog open={isScheduleOpen} onOpenChange={setIsScheduleOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Schedule Therapy Session</DialogTitle>
              <DialogDescription>
                Schedule a session for crisis alert from {selectedAlert?.user_anonymous}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Session Type</Label>
                <Select
                  value={sessionForm.session_type}
                  onValueChange={(value) =>
                    setSessionForm(prev => ({ ...prev, session_type: value }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ONLINE_MEET">
                      <div className="flex items-center gap-2">
                        <Video className="h-4 w-4" />
                        Online Meeting
                      </div>
                    </SelectItem>
                    <SelectItem value="PHONE_CALL">
                      <div className="flex items-center gap-2">
                        <Phone className="h-4 w-4" />
                        Phone Call
                      </div>
                    </SelectItem>
                    <SelectItem value="IN_PERSON">
                      <div className="flex items-center gap-2">
                        <MapPin className="h-4 w-4" />
                        In Person
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Scheduled Date & Time</Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      variant="outline"
                      className={cn(
                        "w-full justify-start text-left font-normal",
                        !sessionForm.scheduled_for && "text-muted-foreground"
                      )}
                    >
                      <Calendar className="mr-2 h-4 w-4" />
                      {sessionForm.scheduled_for
                        ? format(sessionForm.scheduled_for, "PPP p")
                        : "Pick a date"}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <CalendarComponent
                      mode="single"
                      selected={sessionForm.scheduled_for}
                      onSelect={(date) =>
                        date && setSessionForm(prev => ({ ...prev, scheduled_for: date }))
                      }
                      disabled={(date) => date < new Date()}
                      initialFocus
                      className="pointer-events-auto"
                    />
                  </PopoverContent>
                </Popover>
                <div className="mt-2">
                  <Input
                    type="time"
                    value={format(sessionForm.scheduled_for, "HH:mm")}
                    onChange={(e) => {
                      const [hours, minutes] = e.target.value.split(":");
                      const newDate = new Date(sessionForm.scheduled_for);
                      newDate.setHours(parseInt(hours), parseInt(minutes));
                      setSessionForm(prev => ({ ...prev, scheduled_for: newDate }));
                    }}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Duration (minutes)</Label>
                <Select
                  value={sessionForm.duration_minutes.toString()}
                  onValueChange={(value) =>
                    setSessionForm(prev => ({ ...prev, duration_minutes: parseInt(value) }))
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="30">30 minutes</SelectItem>
                    <SelectItem value="50">50 minutes</SelectItem>
                    <SelectItem value="90">90 minutes</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {sessionForm.session_type === "ONLINE_MEET" && (
                <div className="space-y-2">
                  <Label>Meeting Link *</Label>
                  <Input
                    type="url"
                    placeholder="https://meet.google.com/..."
                    value={sessionForm.meeting_link}
                    onChange={(e) =>
                      setSessionForm(prev => ({ ...prev, meeting_link: e.target.value }))
                    }
                  />
                </div>
              )}

              <div className="flex gap-2 pt-4">
                <Button
                  onClick={handleScheduleSession}
                  disabled={isSchedulingSession}
                  className="flex-1"
                >
                  {isSchedulingSession ? (
                    <>
                      <Clock className="mr-2 h-4 w-4 animate-spin" />
                      Scheduling...
                    </>
                  ) : (
                    "Schedule Session"
                  )}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setIsScheduleOpen(false)}
                  disabled={isSchedulingSession}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  );
}
