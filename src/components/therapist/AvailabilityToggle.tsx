import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Clock, PhoneCall, Calendar, MessageSquare } from "lucide-react";
import { useState } from "react";

export function AvailabilityToggle() {
  const [isAvailable, setIsAvailable] = useState(true);
  const [emergencyOnly, setEmergencyOnly] = useState(false);
  const [acceptMessages, setAcceptMessages] = useState(true);
  const [acceptCalls, setAcceptCalls] = useState(true);

  const nextSession = {
    time: "2:00 PM",
    patient: "Patient-X45Y",
    type: "Emergency",
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="h-5 w-5 text-primary" />
          Availability Status
        </CardTitle>
        <CardDescription>Manage your availability and preferences</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Main Availability Toggle */}
        <div className="flex items-center justify-between p-4 rounded-lg border">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-medium">Available for Sessions</span>
              <Badge variant={isAvailable ? "default" : "secondary"}>
                {isAvailable ? "ONLINE" : "OFFLINE"}
              </Badge>
            </div>
            <p className="text-sm text-muted-foreground">
              {isAvailable ? "Accepting new session requests" : "Not accepting new requests"}
            </p>
          </div>
          <Switch
            checked={isAvailable}
            onCheckedChange={setIsAvailable}
          />
        </div>

        {/* Emergency Only Mode */}
        <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
          <div>
            <span className="text-sm font-medium">Emergency Only Mode</span>
            <p className="text-xs text-muted-foreground">Only accept crisis interventions</p>
          </div>
          <Switch
            checked={emergencyOnly}
            onCheckedChange={setEmergencyOnly}
            disabled={!isAvailable}
          />
        </div>

        {/* Communication Preferences */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium">Communication Preferences</h4>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm">Accept Messages</span>
            </div>
            <Switch
              checked={acceptMessages}
              onCheckedChange={setAcceptMessages}
            />
          </div>
          
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <PhoneCall className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm">Accept Emergency Calls</span>
            </div>
            <Switch
              checked={acceptCalls}
              onCheckedChange={setAcceptCalls}
            />
          </div>
        </div>

        {/* Next Session Info */}
        {isAvailable && (
          <div className="bg-primary/10 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <Calendar className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium">Next Session</span>
            </div>
            <div className="text-sm">
              <p><strong>{nextSession.time}</strong> - {nextSession.patient}</p>
              <p className="text-muted-foreground">{nextSession.type}</p>
            </div>
            <Button size="sm" className="mt-2 w-full">
              Prepare for Session
            </Button>
          </div>
        )}

        {/* Quick Actions */}
        <div className="grid grid-cols-2 gap-2">
          <Button variant="outline" size="sm">
            Set Away Message
          </Button>
          <Button variant="outline" size="sm">
            Schedule Break
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}