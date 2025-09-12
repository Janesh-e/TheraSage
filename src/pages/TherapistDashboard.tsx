import { TherapistDashboardStats } from "@/components/therapist/TherapistDashboardStats";
import { CrisisAlertsWidget } from "@/components/therapist/CrisisAlertsWidget";
import { UpcomingSessionsWidget } from "@/components/therapist/UpcomingSessionsWidget";
import { WorkloadIndicator } from "@/components/therapist/WorkloadIndicator";
import { AvailabilityToggle } from "@/components/therapist/AvailabilityToggle";

const TherapistDashboard = () => {
  return (
    <div className="space-y-6 p-6">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-primary/10 to-secondary/10 rounded-lg p-6">
        <h2 className="text-2xl font-bold text-foreground mb-2">
          Welcome back, Dr. Smith 👋
        </h2>
        <p className="text-muted-foreground">
          Today is Tuesday, December 12th. You have 3 crisis alerts and 5 upcoming sessions.
        </p>
      </div>

      {/* Key Metrics */}
      <TherapistDashboardStats />

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column - Alerts and Sessions */}
        <div className="lg:col-span-2 space-y-6">
          <CrisisAlertsWidget />
          <UpcomingSessionsWidget />
        </div>

        {/* Right Column - Status and Controls */}
        <div className="space-y-6">
          <AvailabilityToggle />
          <WorkloadIndicator />
        </div>
      </div>
    </div>
  );
};

export default TherapistDashboard;