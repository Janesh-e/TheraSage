import React, { useState, useEffect } from "react";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Wifi, WifiOff, AlertTriangle, CheckCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface LLMStatus {
  default_mode: string;
  online: {
    available: boolean;
    service: string;
    models: string[];
    api_key_configured: boolean;
  };
  offline: {
    available: boolean;
    service: string;
    base_url: string;
    model: string;
    models_installed: string[];
  };
}

interface LLMToggleProps {
  mode: "online" | "offline";
  onModeChange: (mode: "online" | "offline") => void;
  className?: string;
}

const LLMToggle: React.FC<LLMToggleProps> = ({
  mode,
  onModeChange,
  className,
}) => {
  const [status, setStatus] = useState<LLMStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchLLMStatus();
    // Check status every 30 seconds
    const interval = setInterval(fetchLLMStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchLLMStatus = async () => {
    try {
      const response = await fetch("http://localhost:8000/llm-status/");
      if (response.ok) {
        const statusData = await response.json();
        setStatus(statusData);
      }
    } catch (error) {
      console.error("Failed to fetch LLM status:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleModeChange = async (checked: boolean) => {
    const newMode = checked ? "online" : "offline";

    // Check if the target mode is available
    if (status) {
      if (newMode === "online" && !status.online.available) {
        alert(
          "Online mode is not available. Please check your API configuration."
        );
        return;
      }
      if (newMode === "offline" && !status.offline.available) {
        alert(
          "Offline mode is not available. Please ensure Ollama is running with the required model."
        );
        return;
      }
    }

    onModeChange(newMode);

    // Optionally notify the backend
    try {
      await fetch("http://localhost:8000/set-llm-mode/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mode: newMode }),
      });
    } catch (error) {
      console.error("Failed to set LLM mode:", error);
    }
  };

  const getStatusIcon = (modeType: "online" | "offline") => {
    if (isLoading) return null;
    if (!status) return <AlertTriangle className="w-3 h-3 text-secondary" />;

    const isAvailable =
      modeType === "online"
        ? status.online.available
        : status.offline.available;

    if (isAvailable) {
      return <CheckCircle className="w-3 h-3 text-primary" />;
    } else {
      return <AlertTriangle className="w-3 h-3 text-destructive" />;
    }
  };

  const getStatusColor = (modeType: "online" | "offline") => {
    if (isLoading) return "text-muted-foreground";
    if (!status) return "text-secondary";

    const isAvailable =
      modeType === "online"
        ? status.online.available
        : status.offline.available;
    const isActive = mode === modeType;

    if (isActive && isAvailable) return "text-primary font-medium";
    if (isActive && !isAvailable) return "text-destructive font-medium";
    if (isAvailable) return "text-foreground";
    return "text-muted-foreground";
  };

  return (
    <div
      className={cn(
        "flex items-center space-x-3 bg-card rounded-lg p-2 shadow-sm border border-border",
        className
      )}
    >
      <span
        className={`text-xs font-medium px-2 py-1 rounded-md transition-colors ${
          mode === "offline" ? "bg-red-500 text-white" : "text-muted-foreground"
        }`}
      >
        Offline
      </span>

      <Switch
        id="llm-mode"
        checked={mode === "online"}
        onCheckedChange={handleModeChange}
        className={`${
          mode === "online"
            ? "data-[state=checked]:bg-green-500"
            : "data-[state=unchecked]:bg-red-500"
        }`}
        disabled={isLoading}
      />

      <span
        className={`text-xs font-medium px-2 py-1 rounded-md transition-colors ${
          mode === "online"
            ? "bg-green-500 text-white"
            : "text-muted-foreground"
        }`}
      >
        Online
      </span>
    </div>
  );
};

export default LLMToggle;
