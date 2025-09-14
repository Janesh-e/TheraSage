import React from "react";
import { SidebarProvider } from "@/components/ui/sidebar";
import { TherapistSidebar } from "@/components/TherapistSidebar";

interface TherapistLayoutProps {
  children: React.ReactNode;
}

const TherapistLayout = ({ children }: TherapistLayoutProps) => {
  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full overflow-x-hidden">
        <TherapistSidebar />
        <main className="flex-1 min-w-0 bg-background">{children}</main>
      </div>
    </SidebarProvider>
  );
};

export default TherapistLayout;
