import { Button } from "@/components/ui/button";
import { useTheme } from "@/hooks/use-theme";
import { ColorScheme, colorSchemes } from "@/components/ThemeProvider";

const colorOptions: { name: ColorScheme; label: string; color: string }[] = [
  { name: "orange", label: "Orange", color: "#F97316" },
  { name: "green", label: "Green", color: "#10B981" },
  { name: "blue", label: "Blue", color: "#3B82F6" },
  { name: "red", label: "Red", color: "#EF4444" },
  { name: "pink", label: "Pink", color: "#EC4899" },
];

export function ColorSchemeSelector() {
  const { colorScheme, setColorScheme } = useTheme();

  return (
    <div className="flex flex-wrap gap-2">
      {colorOptions.map((option) => (
        <Button
          key={option.name}
          variant="ghost"
          size="sm"
          className={`w-8 h-8 p-0 rounded-full border-2 transition-all ${
            colorScheme === option.name
              ? "border-primary shadow-md scale-110"
              : "border-border hover:border-muted-foreground hover:scale-105"
          }`}
          style={{ backgroundColor: option.color }}
          onClick={() => setColorScheme(option.name)}
          title={option.label}
        >
          <span className="sr-only">{option.label}</span>
        </Button>
      ))}
    </div>
  );
}
