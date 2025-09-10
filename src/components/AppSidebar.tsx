
import { Home, MessageSquare, BookOpen, BarChart3, Settings, Users, Mail } from "lucide-react";
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
import { ThemeToggle } from "./ThemeToggle";

const navigationItems = [
  {
    title: "Dashboard", 
    url: "/dashboard", 
    icon: BarChart3,
    description: "Your emotional journey"
  },
  {
    title: "Chat", 
    url: "/chat", 
    icon: MessageSquare,
    description: "Talk with TheraSage"
  },
  {
    title: "Journal", 
    url: "/journal", 
    icon: BookOpen,
    description: "Your reflections"
  },
  {
    title: "Messages", 
    url: "/messages", 
    icon: Mail,
    description: "Peer & therapist chats"
  },
  {
    title: "Community", 
    url: "/community", 
    icon: Users,
    description: "Connect with others"
  },
];

const AppSidebar = () => {
  const { state } = useSidebar();
  const isCollapsed = state === "collapsed";

  return (
    <Sidebar className="border-r border-sidebar-border bg-sidebar">
      <SidebarHeader className="px-6 py-5 border-b border-sidebar-border/50">
        <div className="flex items-center space-x-4">
          <div className="w-10 h-10 bg-gradient-to-br from-primary to-secondary rounded-xl flex items-center justify-center shadow-md">
            <span className="text-white text-lg font-bold">T</span>
          </div>
          {!isCollapsed && (
            <div className="flex-1">
              <h2 className="text-lg font-bold text-sidebar-foreground">TheraSage</h2>
              <p className="text-xs text-muted-foreground font-medium">Mental wellness companion</p>
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
                    <NavLink 
                      to={item.url}
                      end
                    >
                      {({ isActive }) => (
                        <div className={`flex items-center space-x-4 px-4 py-3 rounded-xl transition-all duration-200 group ${
                          isActive 
                            ? 'bg-gradient-to-r from-primary/10 to-secondary/10 text-primary shadow-sm border border-primary/20 backdrop-blur-sm' 
                            : 'text-sidebar-foreground/80 hover:bg-sidebar-accent/40 hover:text-sidebar-foreground hover:shadow-sm'
                        }`}>
                          <item.icon className={`w-5 h-5 flex-shrink-0 transition-colors ${isActive ? 'text-primary' : 'text-sidebar-foreground/60 group-hover:text-sidebar-foreground'}`} />
                          {!isCollapsed && (
                            <div className="flex-1 min-w-0">
                              <div className="text-sm font-semibold truncate">{item.title}</div>
                              <div className="text-xs opacity-70 truncate">{item.description}</div>
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
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3 text-muted-foreground hover:text-sidebar-foreground transition-colors cursor-pointer px-2 py-1 rounded-lg hover:bg-sidebar-accent/30">
            <Settings className="w-4 h-4" />
            {!isCollapsed && <span className="text-sm font-medium">Settings</span>}
          </div>
          <ThemeToggle />
        </div>
      </SidebarFooter>
    </Sidebar>
  );
};

export default AppSidebar;
