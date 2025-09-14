import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Settings as SettingsIcon,
  X,
  Sun,
  Moon,
  Monitor,
  Palette,
  Volume2,
  VolumeX,
  Bell,
  BellOff,
  Shield,
  RefreshCw,
} from "lucide-react";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useTheme } from "@/hooks/use-theme";
import { colorSchemes } from "@/components/ThemeProvider";
import { motion, AnimatePresence } from "framer-motion";
import { createPortal } from "react-dom";

interface TherapistSettingsProps {
  isCollapsed?: boolean;
}

export function TherapistSettings({
  isCollapsed = false,
}: TherapistSettingsProps) {
  const [isOpen, setIsOpen] = useState(false);
  const { theme, setTheme, colorScheme, setColorScheme } = useTheme();

  // Additional settings state
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [crisisAlerts, setCrisisAlerts] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [secureMode, setSecureMode] = useState(true);

  const toggleTheme = () => {
    setTheme(theme === "light" ? "dark" : "light");
  };

  const handleSettingsClick = () => {
    setIsOpen(!isOpen);
  };

  return (
    <>
      {/* Settings Button with Sun/Moon Toggle */}
      <div className="flex items-center justify-between w-full">
        <div
          className="flex items-center space-x-3 text-muted-foreground hover:text-foreground transition-colors cursor-pointer px-2 py-1 rounded-lg hover:bg-accent/50"
          onClick={handleSettingsClick}
        >
          <SettingsIcon className="w-4 h-4" />
          {!isCollapsed && (
            <span className="text-sm font-medium">Settings</span>
          )}
        </div>

        {/* Sun/Moon Toggle Button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={toggleTheme}
          className="h-8 w-8 p-0 hover:bg-accent"
        >
          {theme === "light" ? (
            <Moon className="h-4 w-4" />
          ) : (
            <Sun className="h-4 w-4" />
          )}
          <span className="sr-only">Toggle theme</span>
        </Button>
      </div>

      {/* Modal Portal */}
      {isOpen &&
        createPortal(
          <div
            style={{
              position: "fixed",
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              zIndex: 9998,
            }}
          >
            {/* Background blur overlay */}
            <AnimatePresence>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-background/60 backdrop-blur-md"
                style={{
                  position: "fixed",
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  zIndex: 9998,
                  backdropFilter: "blur(8px)",
                  WebkitBackdropFilter: "blur(8px)",
                }}
                onClick={() => setIsOpen(false)}
              />
            </AnimatePresence>

            {/* Settings Modal */}
            <AnimatePresence>
              <motion.div
                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9, y: 20 }}
                transition={{ type: "spring", damping: 25, stiffness: 300 }}
                className="fixed inset-0 flex items-center justify-center z-[9999] p-4"
                style={{
                  position: "fixed",
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  zIndex: 9999,
                }}
              >
                <div className="w-[600px] max-w-[90vw] max-h-[80vh] overflow-y-auto rounded-2xl border bg-card p-8 text-card-foreground shadow-2xl">
                  <div className="grid gap-8">
                    {/* Header */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="p-2 bg-primary/10 rounded-xl">
                            <SettingsIcon className="h-6 w-6 text-primary" />
                          </div>
                          <div>
                            <h2 className="text-2xl font-bold text-foreground">
                              Therapist Settings
                            </h2>
                            <p className="text-sm text-muted-foreground">
                              Customize your portal experience
                            </p>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-10 w-10 p-0 hover:bg-accent rounded-xl"
                          onClick={() => setIsOpen(false)}
                        >
                          <X className="h-5 w-5" />
                          <span className="sr-only">Close</span>
                        </Button>
                      </div>
                    </div>

                    {/* Appearance Settings */}
                    <div className="space-y-6">
                      <div className="space-y-4">
                        <div className="flex items-center space-x-2">
                          <Palette className="h-5 w-5 text-primary" />
                          <h3 className="text-lg font-semibold text-foreground">
                            Appearance
                          </h3>
                        </div>

                        {/* Theme Mode */}
                        <div className="space-y-3">
                          <Label className="text-sm font-medium">
                            Theme Mode
                          </Label>
                          <RadioGroup
                            value={theme}
                            onValueChange={setTheme}
                            className="grid grid-cols-3 gap-4"
                          >
                            <div className="flex items-center space-x-2">
                              <RadioGroupItem value="light" id="light" />
                              <Label
                                htmlFor="light"
                                className="flex items-center space-x-2 cursor-pointer"
                              >
                                <Sun className="h-4 w-4" />
                                <span>Light</span>
                              </Label>
                            </div>
                            <div className="flex items-center space-x-2">
                              <RadioGroupItem value="dark" id="dark" />
                              <Label
                                htmlFor="dark"
                                className="flex items-center space-x-2 cursor-pointer"
                              >
                                <Moon className="h-4 w-4" />
                                <span>Dark</span>
                              </Label>
                            </div>
                            <div className="flex items-center space-x-2">
                              <RadioGroupItem value="system" id="system" />
                              <Label
                                htmlFor="system"
                                className="flex items-center space-x-2 cursor-pointer"
                              >
                                <Monitor className="h-4 w-4" />
                                <span>System</span>
                              </Label>
                            </div>
                          </RadioGroup>
                        </div>

                        {/* Color Scheme */}
                        <div className="space-y-3">
                          <Label className="text-sm font-medium">
                            Color Scheme
                          </Label>
                          <Select
                            value={colorScheme}
                            onValueChange={setColorScheme}
                          >
                            <SelectTrigger className="w-full">
                              <SelectValue placeholder="Select a color scheme" />
                            </SelectTrigger>
                            <SelectContent
                              className="z-[10000]"
                              position="popper"
                            >
                              {Object.keys(colorSchemes).map((scheme) => (
                                <SelectItem key={scheme} value={scheme}>
                                  <div className="flex items-center space-x-3">
                                    <div
                                      className="w-4 h-4 rounded-full border border-border"
                                      style={{
                                        backgroundColor: `hsl(${
                                          colorSchemes[
                                            scheme as keyof typeof colorSchemes
                                          ].primary
                                        })`,
                                      }}
                                    />
                                    <span className="capitalize font-medium">
                                      {scheme}
                                    </span>
                                  </div>
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      </div>

                      {/* Professional Settings */}
                      <div className="space-y-4 border-t pt-6">
                        <div className="flex items-center space-x-2">
                          <Shield className="h-5 w-5 text-primary" />
                          <h3 className="text-lg font-semibold text-foreground">
                            Professional Settings
                          </h3>
                        </div>

                        <div className="grid gap-4">
                          <div className="flex items-center justify-between">
                            <div className="space-y-1">
                              <Label className="text-sm font-medium">
                                Crisis Alert Notifications
                              </Label>
                              <p className="text-xs text-muted-foreground">
                                Receive immediate notifications for crisis
                                situations
                              </p>
                            </div>
                            <Switch
                              checked={crisisAlerts}
                              onCheckedChange={setCrisisAlerts}
                            />
                          </div>

                          <div className="flex items-center justify-between">
                            <div className="space-y-1">
                              <Label className="text-sm font-medium">
                                Secure Mode
                              </Label>
                              <p className="text-xs text-muted-foreground">
                                Enhanced security for patient data access
                              </p>
                            </div>
                            <Switch
                              checked={secureMode}
                              onCheckedChange={setSecureMode}
                            />
                          </div>

                          <div className="flex items-center justify-between">
                            <div className="space-y-1">
                              <Label className="text-sm font-medium">
                                Auto-refresh Dashboard
                              </Label>
                              <p className="text-xs text-muted-foreground">
                                Automatically update data every 30 seconds
                              </p>
                            </div>
                            <Switch
                              checked={autoRefresh}
                              onCheckedChange={setAutoRefresh}
                            />
                          </div>
                        </div>
                      </div>

                      {/* Notification Settings */}
                      <div className="space-y-4 border-t pt-6">
                        <div className="flex items-center space-x-2">
                          <Bell className="h-5 w-5 text-primary" />
                          <h3 className="text-lg font-semibold text-foreground">
                            Notifications
                          </h3>
                        </div>

                        <div className="grid gap-4">
                          <div className="flex items-center justify-between">
                            <div className="space-y-1">
                              <Label className="text-sm font-medium">
                                General Notifications
                              </Label>
                              <p className="text-xs text-muted-foreground">
                                Session reminders and system updates
                              </p>
                            </div>
                            <Switch
                              checked={notificationsEnabled}
                              onCheckedChange={setNotificationsEnabled}
                            />
                          </div>

                          <div className="flex items-center justify-between">
                            <div className="space-y-1">
                              <Label className="text-sm font-medium">
                                Sound Alerts
                              </Label>
                              <p className="text-xs text-muted-foreground">
                                Audio notifications for important alerts
                              </p>
                            </div>
                            <Switch
                              checked={soundEnabled}
                              onCheckedChange={setSoundEnabled}
                            />
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Footer */}
                    <div className="border-t pt-6">
                      <div className="flex items-center justify-between">
                        <p className="text-xs text-muted-foreground">
                          Settings are automatically saved
                        </p>
                        <Button
                          onClick={() => setIsOpen(false)}
                          className="bg-primary hover:bg-primary/90 text-primary-foreground"
                        >
                          Done
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            </AnimatePresence>
          </div>,
          document.body
        )}
    </>
  );
}
