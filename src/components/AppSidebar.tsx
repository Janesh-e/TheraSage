
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
    <Sidebar className="border-r border-white/50 bg-white/60 backdrop-blur-sm">
      <SidebarHeader className="p-4">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-gradient-to-r from-purple-400 to-pink-400 rounded-full flex items-center justify-center">
            <span className="text-white text-sm">💜</span>
          </div>
          {!isCollapsed && (
            <div>
              <h2 className="text-lg font-medium text-gray-800">TheraSage</h2>
              <p className="text-xs text-gray-500">Your emotional companion</p>
            </div>
          )}
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel className="text-gray-600 font-medium">
            {!isCollapsed ? "Navigation" : ""}
          </SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navigationItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <NavLink 
                      to={item.url}
                      end
                      className={({ isActive }) => 
                        `flex items-center space-x-3 px-3 py-2.5 rounded-2xl transition-all duration-200 ${
                          isActive 
                            ? 'bg-gradient-to-r from-purple-100 to-pink-100 text-purple-700 shadow-sm' 
                            : 'text-gray-600 hover:bg-white/80 hover:text-gray-800'
                        }`
                      }
                    >
                      <item.icon className="w-5 h-5 flex-shrink-0" />
                      {!isCollapsed && (
                        <div>
                          <div className="font-medium">{item.title}</div>
                          <div className="text-xs opacity-70">{item.description}</div>
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

      <SidebarFooter className="p-4">
        <div className="flex items-center space-x-3 text-gray-500">
          <Settings className="w-4 h-4" />
          {!isCollapsed && <span className="text-sm">Settings</span>}
        </div>
      </SidebarFooter>
    </Sidebar>
  );
};

export default AppSidebar;
