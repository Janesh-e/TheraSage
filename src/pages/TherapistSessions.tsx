import { SessionScheduleCalendar } from "@/components/therapist/SessionScheduleCalendar";
import { UpcomingSessionsWidget } from "@/components/therapist/UpcomingSessionsWidget";

const TherapistSessions = () => {
  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="space-y-2">
        <h1 className="text-3xl font-bold text-foreground">
          Session Management
        </h1>
        <p className="text-muted-foreground">
          Manage and schedule therapy sessions
        </p>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        {/* Main calendar view */}
        <div className="xl:col-span-3">
          <SessionScheduleCalendar />
        </div>

        {/* Sidebar with upcoming sessions */}
        <div className="xl:col-span-1">
          <UpcomingSessionsWidget />
        </div>
      </div>
    </div>
  );
};

export default TherapistSessions;
