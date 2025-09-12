import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Search, Filter, Eye, Calendar, CheckCircle, ArrowUpDown } from "lucide-react";

const crisisData = [
  {
    id: "CA-001",
    anonymousId: "Student-A42F",
    riskLevel: "critical",
    crisisType: "Suicidal Ideation",
    detectedAt: "2023-12-12T14:30:00",
    timeSince: "2 minutes",
    confidenceScore: 95,
    college: "University College London",
    status: "pending",
    priority: "critical",
  },
  {
    id: "CA-002",
    anonymousId: "Student-B83G", 
    riskLevel: "high",
    crisisType: "Severe Depression",
    detectedAt: "2023-12-12T14:15:00",
    timeSince: "15 minutes",
    confidenceScore: 87,
    college: "Cambridge University",
    status: "acknowledged",
    priority: "high",
  },
  {
    id: "CA-003",
    anonymousId: "Student-C29H",
    riskLevel: "medium",
    crisisType: "Anxiety Attack",
    detectedAt: "2023-12-12T13:30:00",
    timeSince: "1 hour",
    confidenceScore: 73,
    college: "Oxford University",
    status: "in-progress",
    priority: "medium",
  },
  {
    id: "CA-004",
    anonymousId: "Student-D15K",
    riskLevel: "high",
    crisisType: "Self-Harm Indicators",
    detectedAt: "2023-12-12T12:45:00",
    timeSince: "2 hours",
    confidenceScore: 82,
    college: "Imperial College London",
    status: "scheduled",
    priority: "high",
  },
  {
    id: "CA-005",
    anonymousId: "Student-E67M",
    riskLevel: "low",
    crisisType: "Academic Stress",
    detectedAt: "2023-12-12T11:20:00",
    timeSince: "3 hours",
    confidenceScore: 65,
    college: "King's College London",
    status: "resolved",
    priority: "low",
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

const getStatusColor = (status: string) => {
  switch (status) {
    case "pending":
      return "bg-red-100 text-red-800";
    case "acknowledged":
      return "bg-yellow-100 text-yellow-800";
    case "in-progress":
      return "bg-blue-100 text-blue-800";
    case "scheduled":
      return "bg-purple-100 text-purple-800";
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
  const [sortBy, setSortBy] = useState("detectedAt");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  const filteredData = crisisData
    .filter(item => {
      const matchesSearch = item.anonymousId.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           item.crisisType.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           item.college.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = statusFilter === "all" || item.status === statusFilter;
      const matchesRisk = riskFilter === "all" || item.riskLevel === riskFilter;
      return matchesSearch && matchesStatus && matchesRisk;
    })
    .sort((a, b) => {
      let aValue = a[sortBy as keyof typeof a];
      let bValue = b[sortBy as keyof typeof b];
      
      if (sortBy === "detectedAt") {
        aValue = new Date(a.detectedAt).getTime();
        bValue = new Date(b.detectedAt).getTime();
      }
      
      if (sortOrder === "asc") {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortBy(column);
      setSortOrder("desc");
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Crisis Worklist</CardTitle>
        <CardDescription>
          Manage and respond to crisis alerts from students
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Filters */}
        <div className="flex flex-col gap-4 mb-6 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by student ID, crisis type, or college..."
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
                <SelectItem value="in-progress">In Progress</SelectItem>
                <SelectItem value="scheduled">Scheduled</SelectItem>
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
                  <Button variant="ghost" onClick={() => handleSort("anonymousId")} className="p-0 h-auto font-medium">
                    Student ID
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </TableHead>
                <TableHead>Crisis Type</TableHead>
                <TableHead>
                  <Button variant="ghost" onClick={() => handleSort("riskLevel")} className="p-0 h-auto font-medium">
                    Risk Level
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </TableHead>
                <TableHead>
                  <Button variant="ghost" onClick={() => handleSort("detectedAt")} className="p-0 h-auto font-medium">
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
              {filteredData.map((crisis) => (
                <TableRow key={crisis.id}>
                  <TableCell className="font-medium">{crisis.anonymousId}</TableCell>
                  <TableCell>{crisis.crisisType}</TableCell>
                  <TableCell>
                    <Badge className={getRiskColor(crisis.riskLevel)}>
                      {crisis.riskLevel.toUpperCase()}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div>
                      <div className="text-sm">{crisis.timeSince} ago</div>
                      <div className="text-xs text-muted-foreground">
                        {new Date(crisis.detectedAt).toLocaleTimeString()}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm font-medium">{crisis.confidenceScore}%</div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className={getStatusColor(crisis.status)}>
                      {crisis.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm">{crisis.college}</TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button size="sm" variant="outline">
                        <Eye className="h-3 w-3" />
                      </Button>
                      <Button size="sm" variant="outline">
                        <Calendar className="h-3 w-3" />
                      </Button>
                      <Button size="sm" variant="outline">
                        <CheckCircle className="h-3 w-3" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {/* Pagination could be added here */}
        <div className="mt-4 text-sm text-muted-foreground">
          Showing {filteredData.length} of {crisisData.length} alerts
        </div>
      </CardContent>
    </Card>
  );
}