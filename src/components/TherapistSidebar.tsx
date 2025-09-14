import {
  Activity,
  AlertTriangle,
  Calendar,
  Home,
  Users,
  FileText,
  LogOut,
} from "lucide-react";
import { NavLink } from "react-router-dom";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarFooter,
  useSidebar,
} from "@/components/ui/sidebar";
import { TherapistSettings } from "@/components/therapist/TherapistSettings";

const navigationItems = [
  {
    title: "Dashboard",
    url: "/therapist/dashboard",
    icon: Home,
    description: "Overview & metrics",
  },
  {
    title: "Crisis Alerts",
    url: "/therapist/crisis",
    icon: AlertTriangle,
    description: "Urgent interventions",
  },
  {
    title: "Sessions",
    url: "/therapist/sessions",
    icon: Calendar,
    description: "Schedule & manage",
  },
  {
    title: "Patients",
    url: "/therapist/patients",
    icon: Users,
    description: "Patient records",
  },
  {
    title: "Reports",
    url: "/therapist/reports",
    icon: FileText,
    description: "Analytics & insights",
  },
];

export function TherapistSidebar() {
  const { state } = useSidebar();
  const isCollapsed = state === "collapsed";

  return (
    <Sidebar className="border-r border-sidebar-border bg-sidebar">
      <SidebarHeader className="px-6 py-5 border-b border-sidebar-border/50">
        <div className="flex items-center space-x-4">
          <div className="w-10 h-10 bg-gradient-to-br from-primary to-destructive rounded-xl flex items-center justify-center shadow-md">
            <Activity className="h-5 w-5 text-white" />
          </div>
          {!isCollapsed && (
            <div className="flex-1 h-11">
              <h2 className="text-sm font-semibold text-sidebar-foreground">
                TheraSage
              </h2>
              <p className="text-[10px] text-muted-foreground font-normal leading-none">
                Therapist Portal
              </p>
            </div>
          )}
        </div>
      </SidebarHeader>

      <SidebarContent className="px-4 py-6">
        <SidebarGroup>
          <SidebarGroupLabel className="text-sidebar-foreground/70 text-xs font-semibold uppercase tracking-wider px-3 mb-4">
            {!isCollapsed ? "Navigation" : ""}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="space-y-2">
              {navigationItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <NavLink to={item.url} end>
                      {({ isActive }) => (
                        <div
                          className={`flex items-center space-x-4 px-4 py-3 rounded-xl transition-all duration-200 group ${
                            isActive
                              ? "bg-gradient-to-r from-primary/10 to-destructive/10 text-primary shadow-sm border border-primary/20 backdrop-blur-sm"
                              : "text-sidebar-foreground/80 hover:bg-sidebar-accent/40 hover:text-sidebar-foreground hover:shadow-sm"
                          }`}
                        >
                          <item.icon
                            className={`w-5 h-5 flex-shrink-0 transition-colors ${
                              isActive
                                ? "text-primary"
                                : "text-sidebar-foreground/60 group-hover:text-sidebar-foreground"
                            }`}
                          />
                          {!isCollapsed && (
                            <div className="flex-1 min-w-0">
                              <div className="text-sm font-semibold truncate">
                                {item.title}
                              </div>
                              <div className="text-xs opacity-70 truncate">
                                {item.description}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="px-6 py-4 border-t border-sidebar-border/50">
        <div className="space-y-3">
          {/* Settings Component */}
          <div className="flex items-center justify-between">
            <TherapistSettings isCollapsed={isCollapsed} />
          </div>

          {/* Exit Portal Button */}
          <div className="pt-2 border-t border-sidebar-border/30">
            <button
              onClick={() => (window.location.href = "/")}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 group text-destructive hover:bg-destructive/10 hover:shadow-sm ${
                isCollapsed ? "justify-center" : ""
              }`}
            >
              <LogOut className="w-5 h-5 flex-shrink-0" />
              {!isCollapsed && (
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-semibold truncate">
                    Exit Portal
                  </div>
                  <div className="text-xs opacity-70 truncate">
                    Return to main site
                  </div>
                </div>
              )}
            </button>
          </div>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
