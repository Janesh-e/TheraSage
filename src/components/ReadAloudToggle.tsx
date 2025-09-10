
import { useState, useEffect } from 'react';
import { Switch } from '@/components/ui/switch';
import { Volume2, VolumeX } from 'lucide-react';

interface ReadAloudToggleProps {
  onToggle: (enabled: boolean) => void;
  enabled: boolean;
}

const ReadAloudToggle = ({ onToggle, enabled }: ReadAloudToggleProps) => {
  const [isSupported, setIsSupported] = useState(false);

  useEffect(() => {
    // Check if SpeechSynthesis is supported
    setIsSupported('speechSynthesis' in window);
  }, []);

  if (!isSupported) {
    return null; // Don't show toggle if not supported
  }

  return (
    <div className="flex items-center space-x-3 bg-card rounded-lg p-2 shadow-sm border border-border">
      {enabled ? (
        <Volume2 size={16} className="text-green-500" />
      ) : (
        <VolumeX size={16} className="text-muted-foreground" />
      )}
      <Switch
        checked={enabled}
        onCheckedChange={onToggle}
        className={enabled ? "data-[state=checked]:bg-green-500" : "data-[state=unchecked]:bg-muted"}
      />
      <span className={`text-xs font-medium px-2 py-1 rounded-md transition-colors ${
        enabled ? "bg-green-500 text-white" : "text-muted-foreground"
      }`}>
        Read Aloud
      </span>
    </div>
  );
};

export default ReadAloudToggle;
