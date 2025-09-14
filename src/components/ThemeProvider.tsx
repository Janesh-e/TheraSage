import { createContext, useEffect, useState } from "react";

// Define the color schemes with their HSL values
export const colorSchemes = {
  orange: {
    primary: "24.6 95% 53.1%",
    "primary-foreground": "210 40% 98%",
    secondary: "32.1 95% 44.6%",
    "secondary-foreground": "210 40% 98%",
    accent: "24.6 95% 53.1%",
    "accent-foreground": "210 40% 98%",
    ring: "24.6 95% 53.1%",
  },
  green: {
    primary: "142.1 76.2% 36.3%",
    "primary-foreground": "210 40% 98%",
    secondary: "142.1 70.6% 45.3%",
    "secondary-foreground": "210 40% 98%",
    accent: "142.1 76.2% 36.3%",
    "accent-foreground": "210 40% 98%",
    ring: "142.1 76.2% 36.3%",
  },
  blue: {
    primary: "221.2 83.2% 53.3%",
    "primary-foreground": "210 40% 98%",
    secondary: "213.3 93.9% 67.8%",
    "secondary-foreground": "210 40% 98%",
    accent: "221.2 83.2% 53.3%",
    "accent-foreground": "210 40% 98%",
    ring: "221.2 83.2% 53.3%",
  },
  red: {
    primary: "0 84.2% 60.2%",
    "primary-foreground": "210 40% 98%",
    secondary: "0 93.5% 81.8%",
    "secondary-foreground": "210 40% 98%",
    accent: "0 84.2% 60.2%",
    "accent-foreground": "210 40% 98%",
    ring: "0 84.2% 60.2%",
  },
  pink: {
    primary: "330 84.2% 60.2%",
    "primary-foreground": "210 40% 98%",
    secondary: "330 85.5% 78.4%",
    "secondary-foreground": "210 40% 98%",
    accent: "330 84.2% 60.2%",
    "accent-foreground": "210 40% 98%",
    ring: "330 84.2% 60.2%",
  },
};

export type Theme = "dark" | "light" | "system";
export type ColorScheme = keyof typeof colorSchemes;

export interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  colorScheme: ColorScheme;
  setColorScheme: (color: ColorScheme) => void;
}

export const ThemeContext = createContext<ThemeContextType | undefined>(
  undefined
);

export function ThemeProvider({
  children,
  defaultTheme = "light",
  defaultColor = "orange",
  storageKey = "therasage-ui-theme",
}: {
  children: React.ReactNode;
  defaultTheme?: Theme;
  defaultColor?: ColorScheme;
  storageKey?: string;
}) {
  // Initialize with stored values or defaults immediately
  const [theme, setTheme] = useState<Theme>(() => {
    const stored = localStorage.getItem(storageKey) as Theme;
    return stored || defaultTheme;
  });

  const [colorScheme, setColorScheme] = useState<ColorScheme>(() => {
    const stored = localStorage.getItem(`${storageKey}-color`) as ColorScheme;
    return stored || defaultColor;
  });

  // Apply theme and color changes immediately when they change
  const applyTheme = (newTheme: Theme, newColorScheme: ColorScheme) => {
    const root = window.document.documentElement;

    // Remove existing theme classes immediately
    root.classList.remove("light", "dark");

    let effectiveTheme = newTheme;
    if (newTheme === "system") {
      const systemTheme = window.matchMedia("(prefers-color-scheme: dark)")
        .matches
        ? "dark"
        : "light";
      effectiveTheme = systemTheme;
    }

    // Apply theme class immediately
    root.classList.add(effectiveTheme);

    // Apply color scheme variables immediately
    const selectedScheme = colorSchemes[newColorScheme];
    for (const [key, value] of Object.entries(selectedScheme)) {
      root.style.setProperty(`--${key}`, value);
    }

    // Save to localStorage
    localStorage.setItem(storageKey, newTheme);
    localStorage.setItem(`${storageKey}-color`, newColorScheme);
  };

  // Apply theme immediately on mount and when dependencies change
  useEffect(() => {
    applyTheme(theme, colorScheme);
  }, [theme, colorScheme, storageKey]);

  // Apply theme immediately on first render
  useEffect(() => {
    applyTheme(theme, colorScheme);
  }, []);

  const handleSetTheme = (newTheme: Theme) => {
    setTheme(newTheme);
    // Apply immediately, don't wait for useEffect
    applyTheme(newTheme, colorScheme);
  };

  const handleSetColorScheme = (newColorScheme: ColorScheme) => {
    setColorScheme(newColorScheme);
    // Apply immediately, don't wait for useEffect
    applyTheme(theme, newColorScheme);
  };

  const value = {
    theme,
    setTheme: handleSetTheme,
    colorScheme,
    setColorScheme: handleSetColorScheme,
  };
  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
}
