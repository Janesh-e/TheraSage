
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
    <div className="flex items-center space-x-2">
      {enabled ? (
        <Volume2 size={16} className="text-purple-500" />
      ) : (
        <VolumeX size={16} className="text-gray-400" />
      )}
      <Switch
        checked={enabled}
        onCheckedChange={onToggle}
        className="data-[state=checked]:bg-purple-500"
      />
      <span className="text-sm text-gray-600">Read Aloud</span>
    </div>
  );
};

export default ReadAloudToggle;
