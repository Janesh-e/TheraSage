import React from "react";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import AppSidebar from "@/components/AppSidebar";

interface LayoutProps {
  children: React.ReactNode;
  title?: string;
  description?: string;
  action?: React.ReactNode;
}

const Layout = ({ children, title, description, action }: LayoutProps) => {
  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full overflow-x-hidden">
        <AppSidebar />
        <main className="flex-1 min-w-0 flex flex-col">
          <header className="border-b border-border bg-background/80 backdrop-blur-sm px-6 py-4 shadow-sm sticky top-0 z-20">
            <div className="flex items-center gap-4">
              <SidebarTrigger className="p-2 hover:bg-accent rounded-lg transition-colors" />
              {(title || description || action) && (
                <div className="flex-1 flex items-center justify-between min-w-0">
                  <div className="flex-1 min-w-0">
                    {title && (
                      <h1 className="text-2xl font-bold text-foreground truncate">
                        {title}
                      </h1>
                    )}
                    {description && (
                      <p className="text-sm text-muted-foreground">
                        {description}
                      </p>
                    )}
                  </div>
                  {action && <div className="flex-shrink-0">{action}</div>}
                </div>
              )}
            </div>
          </header>
          <div className="flex-1 min-w-0 overflow-y-auto">{children}</div>
        </main>
      </div>
    </SidebarProvider>
  );
};

export default Layout;
