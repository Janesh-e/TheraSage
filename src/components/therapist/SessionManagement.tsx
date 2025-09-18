import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Video,
  Phone,
  MapPin,
  Clock,
  Edit,
  CheckCircle,
  XCircle,
  Calendar,
  User,
} from "lucide-react";
import { format } from "date-fns";
import { toast } from "sonner";

interface TherapistSession {
  id: string;
  user_id: string;
  crisis_alert_id?: string;
  session_type: string;
  urgency_level: string;
  requested_at: string;
  scheduled_for: string;
  duration_minutes: number;
  external_therapist_id: string;
  meeting_link?: string;
  status: string;
  attended?: boolean;
  session_notes?: string;
  follow_up_needed: boolean;
  next_session_recommended?: string;
  completed_at?: string;
  cancelled_at?: string;
  created_at: string;
}

interface SessionUpdateData {
  attended?: boolean;
  session_notes?: string;
  follow_up_needed?: boolean;
  next_session_recommended?: string;
  status?: string;
}

const getStatusColor = (status: string) => {
  switch (status.toLowerCase()) {
    case "scheduled":
      return "bg-blue-500 text-white";
    case "in_progress":
      return "bg-yellow-500 text-white";
    case "completed":
      return "bg-green-500 text-white";
    case "cancelled":
      return "bg-red-500 text-white";
    case "no_show":
      return "bg-gray-500 text-white";
    default:
      return "bg-muted text-muted-foreground";
  }
};

const getSessionTypeIcon = (type: string) => {
  switch (type.toLowerCase()) {
    case "online_meet":
      return Video;
    case "phone_call":
      return Phone;
    case "in_person":
      return MapPin;
    default:
      return Clock;
  }
};

export function SessionManagement() {
  const [sessions, setSessions] = useState<TherapistSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSession, setSelectedSession] = useState<TherapistSession | null>(null);
  const [isUpdateDialogOpen, setIsUpdateDialogOpen] = useState(false);
  const [updateData, setUpdateData] = useState<SessionUpdateData>({});
  const [isUpdating, setIsUpdating] = useState(false);
  const [statusFilter, setStatusFilter] = useState("all");

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      setLoading(true);
      const therapistData = localStorage.getItem("therapistUser");
      if (!therapistData) {
        toast.error("No therapist session found");
        return;
      }

      const response = await fetch(
        `http://localhost:8000/therapist-dashboard/sessions?limit=50${
          statusFilter !== "all" ? `&status=${statusFilter}` : ""
        }`
      );

      if (!response.ok) {
        throw new Error("Failed to fetch sessions");
      }

      const data = await response.json();
      setSessions(data);
    } catch (error) {
      console.error("Error fetching sessions:", error);
      toast.error("Failed to load sessions");
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateSession = async () => {
    if (!selectedSession) return;

    try {
      setIsUpdating(true);
      const response = await fetch(
        `http://localhost:8000/therapist-dashboard/sessions/${selectedSession.id}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(updateData),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to update session");
      }

      toast.success("Session updated successfully");
      setIsUpdateDialogOpen(false);
      setSelectedSession(null);
      setUpdateData({});
      fetchSessions();
    } catch (error) {
      console.error("Error updating session:", error);
      toast.error("Failed to update session");
    } finally {
      setIsUpdating(false);
    }
  };

  const openUpdateDialog = (session: TherapistSession) => {
    setSelectedSession(session);
    setUpdateData({
      attended: session.attended,
      session_notes: session.session_notes || "",
      follow_up_needed: session.follow_up_needed,
      next_session_recommended: session.next_session_recommended,
      status: session.status,
    });
    setIsUpdateDialogOpen(true);
  };

  const markAsCompleted = async (sessionId: string) => {
    try {
      const response = await fetch(
        `http://localhost:8000/therapist-dashboard/sessions/${sessionId}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ status: "completed" }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to mark as completed");
      }

      toast.success("Session marked as completed");
      fetchSessions();
    } catch (error) {
      console.error("Error marking session as completed:", error);
      toast.error("Failed to mark session as completed");
    }
  };

  const filteredSessions = sessions.filter((session) => {
    if (statusFilter === "all") return true;
    return session.status.toLowerCase() === statusFilter.toLowerCase();
  });

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <div className="text-muted-foreground">Loading sessions...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Session Management</CardTitle>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Sessions</SelectItem>
                <SelectItem value="scheduled">Scheduled</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="cancelled">Cancelled</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {filteredSessions.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Calendar className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No sessions found</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Scheduled</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Urgency</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredSessions.map((session) => {
                  const SessionIcon = getSessionTypeIcon(session.session_type);
                  return (
                    <TableRow key={session.id}>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="font-medium">
                            {format(new Date(session.scheduled_for), "PPP")}
                          </span>
                          <span className="text-sm text-muted-foreground">
                            {format(new Date(session.scheduled_for), "p")}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <SessionIcon className="h-4 w-4" />
                          <span className="capitalize">
                            {session.session_type.replace("_", " ").toLowerCase()}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>{session.duration_minutes} min</TableCell>
                      <TableCell>
                        <Badge className={getStatusColor(session.status)}>
                          {session.status.replace("_", " ")}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={
                            session.urgency_level === "CRITICAL"
                              ? "destructive"
                              : session.urgency_level === "HIGH"
                              ? "secondary"
                              : "outline"
                          }
                        >
                          {session.urgency_level}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {session.status === "scheduled" && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => markAsCompleted(session.id)}
                            >
                              <CheckCircle className="h-4 w-4 mr-1" />
                              Complete
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => openUpdateDialog(session)}
                          >
                            <Edit className="h-4 w-4 mr-1" />
                            Update
                          </Button>
                          {session.meeting_link && (
                            <Button size="sm" asChild>
                              <a
                                href={session.meeting_link}
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                <Video className="h-4 w-4 mr-1" />
                                Join
                              </a>
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Update Session Dialog */}
      <Dialog open={isUpdateDialogOpen} onOpenChange={setIsUpdateDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Update Session</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Status</Label>
              <Select
                value={updateData.status || ""}
                onValueChange={(value) =>
                  setUpdateData((prev) => ({ ...prev, status: value }))
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="scheduled">Scheduled</SelectItem>
                  <SelectItem value="in_progress">In Progress</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="cancelled">Cancelled</SelectItem>
                  <SelectItem value="no_show">No Show</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="attended"
                checked={updateData.attended || false}
                onCheckedChange={(checked) =>
                  setUpdateData((prev) => ({ ...prev, attended: checked }))
                }
              />
              <Label htmlFor="attended">Patient attended session</Label>
            </div>

            <div className="space-y-2">
              <Label>Session Notes</Label>
              <Textarea
                placeholder="Enter session notes..."
                value={updateData.session_notes || ""}
                onChange={(e) =>
                  setUpdateData((prev) => ({
                    ...prev,
                    session_notes: e.target.value,
                  }))
                }
                rows={4}
              />
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="follow-up"
                checked={updateData.follow_up_needed || false}
                onCheckedChange={(checked) =>
                  setUpdateData((prev) => ({ ...prev, follow_up_needed: checked }))
                }
              />
              <Label htmlFor="follow-up">Follow-up session needed</Label>
            </div>

            {updateData.follow_up_needed && (
              <div className="space-y-2">
                <Label>Next Session Recommended</Label>
                <Input
                  type="datetime-local"
                  value={
                    updateData.next_session_recommended
                      ? new Date(updateData.next_session_recommended)
                          .toISOString()
                          .slice(0, 16)
                      : ""
                  }
                  onChange={(e) =>
                    setUpdateData((prev) => ({
                      ...prev,
                      next_session_recommended: e.target.value
                        ? new Date(e.target.value).toISOString()
                        : undefined,
                    }))
                  }
                />
              </div>
            )}

            <div className="flex gap-2 pt-4">
              <Button
                onClick={handleUpdateSession}
                disabled={isUpdating}
                className="flex-1"
              >
                {isUpdating ? (
                  <>
                    <Clock className="mr-2 h-4 w-4 animate-spin" />
                    Updating...
                  </>
                ) : (
                  "Update Session"
                )}
              </Button>
              <Button
                variant="outline"
                onClick={() => setIsUpdateDialogOpen(false)}
                disabled={isUpdating}
              >
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}