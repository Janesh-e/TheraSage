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
} from "lucide-react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

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
  trigger_message: string;
  detected_indicators: string[];
  risk_factors: string[];
  main_concerns: string[];
  cognitive_distortions: string[];
  urgency_level: string;
}

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

const getStatusColor = (status: string) => {
  switch (status) {
    case "pending":
      return "bg-red-100 text-red-800";
    case "acknowledged":
      return "bg-yellow-100 text-yellow-800";
    case "escalated":
      return "bg-blue-100 text-blue-800";
    case "resolved":
      return "bg-green-100 text-green-800";
    default:
      return "bg-gray-100 text-gray-800";
  }
};

export function CrisisWorklistTable() {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [riskFilter, setRiskFilter] = useState("all");
  const [sortColumn, setSortColumn] = useState<string>("");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [crisisData, setCrisisData] = useState<CrisisAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCrisis, setSelectedCrisis] = useState<CrisisAlert | null>(null);
  const [schedulingSession, setSchedulingSession] = useState(false);
  const [sessionDate, setSessionDate] = useState("");
  const [sessionTime, setSessionTime] = useState("");
  const [viewDetailsOpen, setViewDetailsOpen] = useState(false);

  useEffect(() => {
    fetchCrisisWorklist();
  }, [statusFilter, riskFilter]);

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 1) {
      const minutes = Math.round(diffInHours * 60);
      return `${minutes}m ago`;
    } else if (diffInHours < 24) {
      return `${Math.round(diffInHours)}h ago`;
    } else {
      const days = Math.round(diffInHours / 24);
      return `${days}d ago`;
    }
  };

  const fetchCrisisWorklist = async () => {
    try {
      const token = localStorage.getItem("therapist_token");
      const therapistUser = JSON.parse(localStorage.getItem("therapist_user") || "{}");

      if (!token || !therapistUser.id) {
        toast.error("Authentication required");
        return;
      }

      const url = new URL(`http://localhost:8000/therapist-dashboard/crisis-worklist/${therapistUser.id}`);
      if (statusFilter !== "all") url.searchParams.append("status_filter", statusFilter);
      if (riskFilter !== "all") url.searchParams.append("risk_filter", riskFilter);

      const response = await fetch(url.toString(), {
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (response.status === 401) {
        toast.error("Authentication expired. Please login again.");
        localStorage.removeItem("therapist_token");
        localStorage.removeItem("therapist_user");
        window.location.href = "/therapist/login";
        return;
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error("Failed to fetch crisis worklist");
      }

      const data = await response.json();
      setCrisisData(data);
    } catch (error) {
      console.error("Error fetching crisis worklist:", error);
      toast.error(error.message || "Failed to load crisis worklist");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickResponse = async (alertId: string, responseType: string) => {
    try {
      const token = localStorage.getItem("therapist_token");
      const therapistUser = JSON.parse(localStorage.getItem("therapist_user") || "{}");

      const response = await fetch(`http://localhost:8000/therapist-dashboard/crisis/${alertId}/quick-response`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          response_type: responseType,
          therapist_id: therapistUser.id,
        }),
      });

      if (!response.ok) throw new Error("Failed to send response");

      toast.success(`Crisis alert ${responseType}d successfully`);
      fetchCrisisWorklist(); // Refresh the list
    } catch (error) {
      console.error("Error sending quick response:", error);
      toast.error("Failed to send response");
    }
  };

  const handleScheduleSession = async () => {
    if (!selectedCrisis || !sessionDate || !sessionTime) {
      toast.error("Please fill in all session details");
      return;
    }

    setSchedulingSession(true);
    try {
      const token = localStorage.getItem("therapist_token");
      const therapistUser = JSON.parse(localStorage.getItem("therapist_user") || "{}");

      const scheduledFor = new Date(`${sessionDate}T${sessionTime}`).toISOString();

      const response = await fetch(`http://localhost:8000/therapist-dashboard/crisis/${selectedCrisis.id}/quick-response`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          response_type: "schedule_session",
          therapist_id: therapistUser.id,
          scheduled_for: scheduledFor,
          duration_minutes: 50,
          session_type: "crisis",
        }),
      });

      if (!response.ok) throw new Error("Failed to schedule session");

      toast.success("Session scheduled successfully");
      setSelectedCrisis(null);
      setSessionDate("");
      setSessionTime("");
      fetchCrisisWorklist();
    } catch (error) {
      console.error("Error scheduling session:", error);
      toast.error("Failed to schedule session");
    } finally {
      setSchedulingSession(false);
    }
  };

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortColumn(column);
      setSortOrder("desc");
    }
  };

  // Filter and sort data
  const filteredData = crisisData
    .filter((item) => {
      const matchesSearch = item.user_anonymous
        .toLowerCase()
        .includes(searchTerm.toLowerCase());
      const matchesStatus = statusFilter === "all" || item.status === statusFilter;
      const matchesRisk = riskFilter === "all" || item.risk_level === riskFilter;
      return matchesSearch && matchesStatus && matchesRisk;
    })
    .sort((a, b) => {
      if (!sortColumn) return 0;

      let aValue: any = a[sortColumn as keyof CrisisAlert];
      let bValue: any = b[sortColumn as keyof CrisisAlert];

      // Handle date sorting
      if (sortColumn === "detected_at") {
        aValue = new Date(aValue).getTime();
        bValue = new Date(bValue).getTime();
      }

      if (aValue < bValue) return sortOrder === "asc" ? -1 : 1;
      if (aValue > bValue) return sortOrder === "asc" ? 1 : -1;
      return 0;
    });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Crisis Worklist</CardTitle>
      </CardHeader>
      <CardContent>
        {/* Filters */}
        <div className="flex flex-col gap-4 mb-6 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by student ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>

          <div className="flex gap-2">
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-32">
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
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Risk Level" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Risks</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="low">Low</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Table */}
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>
                  <Button
                    variant="ghost"
                    className="h-8 p-0 hover:bg-muted/50"
                    onClick={() => handleSort("user_anonymous")}
                  >
                    Student ID
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </TableHead>
                <TableHead>Crisis Type</TableHead>
                <TableHead>
                  <Button
                    variant="ghost"
                    className="h-8 p-0 hover:bg-muted/50"
                    onClick={() => handleSort("risk_level")}
                  >
                    Risk Level
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </TableHead>
                <TableHead>
                  <Button
                    variant="ghost"
                    className="h-8 p-0 hover:bg-muted/50"
                    onClick={() => handleSort("detected_at")}
                  >
                    Detected
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </TableHead>
                <TableHead>Confidence</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>College</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center">
                    Loading crisis alerts...
                  </TableCell>
                </TableRow>
              ) : filteredData.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center">
                    No crisis alerts found
                  </TableCell>
                </TableRow>
              ) : (
                filteredData.map((crisis) => (
                  <TableRow key={crisis.id} className="hover:bg-muted/50">
                    <TableCell className="font-medium">
                      {crisis.user_anonymous}
                    </TableCell>
                    <TableCell>{crisis.crisis_type.replace(/_/g, ' ')}</TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={getRiskColor(crisis.risk_level)}
                      >
                        {crisis.risk_level.toUpperCase()}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{formatTimeAgo(crisis.detected_at)}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <div className="w-8 h-2 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary"
                            style={{ width: `${crisis.confidence_score * 100}%` }}
                          />
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {Math.round(crisis.confidence_score > 1 ? crisis.confidence_score : crisis.confidence_score * 100)}%
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={getStatusColor(crisis.status)}
                      >
                        {crisis.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {crisis.user_college}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Dialog open={viewDetailsOpen} onOpenChange={setViewDetailsOpen}>
                          <DialogTrigger asChild>
                            <Button 
                              size="sm" 
                              variant="outline" 
                              title="View Details"
                              onClick={() => setSelectedCrisis(crisis)}
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
                            <DialogHeader>
                              <DialogTitle>Crisis Alert Details</DialogTitle>
                              <DialogDescription>
                                Detailed information for {selectedCrisis?.user_anonymous}
                              </DialogDescription>
                            </DialogHeader>
                            {selectedCrisis && (
                              <div className="space-y-6">
                                {/* Basic Information */}
                                <div className="grid grid-cols-2 gap-4">
                                  <div>
                                    <Label className="text-sm font-medium">Student ID</Label>
                                    <p className="text-sm text-muted-foreground">{selectedCrisis.user_anonymous}</p>
                                  </div>
                                  <div>
                                    <Label className="text-sm font-medium">College</Label>
                                    <p className="text-sm text-muted-foreground">{selectedCrisis.user_college}</p>
                                  </div>
                                  <div>
                                    <Label className="text-sm font-medium">Crisis Type</Label>
                                    <p className="text-sm text-muted-foreground">{selectedCrisis.crisis_type.replace(/_/g, ' ')}</p>
                                  </div>
                                  <div>
                                    <Label className="text-sm font-medium">Risk Level</Label>
                                    <Badge className={getRiskColor(selectedCrisis.risk_level)}>
                                      {selectedCrisis.risk_level.toUpperCase()}
                                    </Badge>
                                  </div>
                                  <div>
                                    <Label className="text-sm font-medium">Urgency Level</Label>
                                    <p className="text-sm text-muted-foreground">{selectedCrisis.urgency_level}</p>
                                  </div>
                                  <div>
                                    <Label className="text-sm font-medium">Confidence Score</Label>
                                    <p className="text-sm text-muted-foreground">
                                      {Math.round(selectedCrisis.confidence_score > 1 ? selectedCrisis.confidence_score : selectedCrisis.confidence_score * 100)}%
                                    </p>
                                  </div>
                                  <div>
                                    <Label className="text-sm font-medium">Detected</Label>
                                    <p className="text-sm text-muted-foreground">{formatTimeAgo(selectedCrisis.detected_at)}</p>
                                  </div>
                                  <div>
                                    <Label className="text-sm font-medium">Status</Label>
                                    <Badge className={getStatusColor(selectedCrisis.status)}>
                                      {selectedCrisis.status}
                                    </Badge>
                                  </div>
                                </div>

                                {/* Trigger Message */}
                                <div>
                                  <Label className="text-sm font-medium">Trigger Message</Label>
                                  <div className="mt-2 p-3 bg-muted rounded-md">
                                    <p className="text-sm">{selectedCrisis.trigger_message}</p>
                                  </div>
                                </div>

                                {/* Detected Indicators */}
                                {selectedCrisis.detected_indicators?.length > 0 && (
                                  <div>
                                    <Label className="text-sm font-medium">Detected Indicators</Label>
                                    <div className="mt-2 flex flex-wrap gap-2">
                                      {selectedCrisis.detected_indicators.map((indicator, index) => (
                                        <Badge key={index} variant="outline" className="bg-red-50 text-red-700 border-red-200">
                                          {indicator}
                                        </Badge>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Risk Factors */}
                                {selectedCrisis.risk_factors?.length > 0 && (
                                  <div>
                                    <Label className="text-sm font-medium">Risk Factors</Label>
                                    <div className="mt-2 flex flex-wrap gap-2">
                                      {selectedCrisis.risk_factors.map((factor, index) => (
                                        <Badge key={index} variant="outline" className="bg-orange-50 text-orange-700 border-orange-200">
                                          {factor}
                                        </Badge>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Main Concerns */}
                                {selectedCrisis.main_concerns?.length > 0 && (
                                  <div>
                                    <Label className="text-sm font-medium">Main Concerns</Label>
                                    <div className="mt-2 flex flex-wrap gap-2">
                                      {selectedCrisis.main_concerns.map((concern, index) => (
                                        <Badge key={index} variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                                          {concern}
                                        </Badge>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Cognitive Distortions */}
                                {selectedCrisis.cognitive_distortions?.length > 0 && (
                                  <div>
                                    <Label className="text-sm font-medium">Cognitive Distortions</Label>
                                    <div className="mt-2 flex flex-wrap gap-2">
                                      {selectedCrisis.cognitive_distortions.map((distortion, index) => (
                                        <Badge key={index} variant="outline" className="bg-purple-50 text-purple-700 border-purple-200">
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
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button
                              size="sm"
                              variant="outline"
                              title="Schedule Session"
                              onClick={() => setSelectedCrisis(crisis)}
                              disabled={crisis.has_session_scheduled}
                            >
                              <Calendar className="h-4 w-4" />
                            </Button>
                          </DialogTrigger>
                          <DialogContent>
                            <DialogHeader>
                              <DialogTitle>Schedule Therapy Session</DialogTitle>
                              <DialogDescription>
                                Schedule a session for {selectedCrisis?.user_anonymous} - {selectedCrisis?.crisis_type}
                              </DialogDescription>
                            </DialogHeader>
                            <div className="space-y-4">
                              <div>
                                <Label htmlFor="session-date">Date</Label>
                                <Input
                                  id="session-date"
                                  type="date"
                                  value={sessionDate}
                                  onChange={(e) => setSessionDate(e.target.value)}
                                  min={new Date().toISOString().split('T')[0]}
                                />
                              </div>
                              <div>
                                <Label htmlFor="session-time">Time</Label>
                                <Input
                                  id="session-time"
                                  type="time"
                                  value={sessionTime}
                                  onChange={(e) => setSessionTime(e.target.value)}
                                />
                              </div>
                              <Button
                                onClick={handleScheduleSession}
                                disabled={schedulingSession}
                                className="w-full"
                              >
                                {schedulingSession ? "Scheduling..." : "Schedule Session"}
                              </Button>
                            </div>
                          </DialogContent>
                        </Dialog>
                        <Button
                          size="sm"
                          variant="outline"
                          title="Acknowledge"
                          onClick={() => handleQuickResponse(crisis.id, "acknowledge")}
                          disabled={crisis.status === "acknowledged"}
                        >
                          <CheckCircle className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {/* Results count */}
        <div className="mt-4 text-sm text-muted-foreground">
          Showing {filteredData.length} of {crisisData.length} alerts
        </div>
      </CardContent>
    </Card>
  );
}