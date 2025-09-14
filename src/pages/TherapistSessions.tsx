import TherapistLayout from "@/components/TherapistLayout";
import { SessionScheduleCalendar } from "@/components/therapist/SessionScheduleCalendar";
import { UpcomingSessionsWidget } from "@/components/therapist/UpcomingSessionsWidget";

const TherapistSessions = () => {
  return (
    <TherapistLayout
      title="Session Management"
      description="Manage and schedule therapy sessions"
    >
      <div className="p-6 space-y-6">
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
    </TherapistLayout>
  );
};

export default TherapistSessions;