"use client";

import { Sun, Moon, Monitor } from "lucide-react";
import { useTheme } from "@/components/theme-provider";
import { cn } from "@/lib/utils";

const themeOrder: Array<"light" | "dark" | "system"> = ["light", "dark", "system"];

const themeConfig = {
  light: { icon: Sun, label: "Light" },
  dark: { icon: Moon, label: "Dark" },
  system: { icon: Monitor, label: "System" },
} as const;

export function ThemeToggle({ className }: { className?: string }) {
  const { theme, setTheme } = useTheme();

  const cycle = () => {
    const idx = themeOrder.indexOf(theme);
    const next = themeOrder[(idx + 1) % themeOrder.length];
    setTheme(next);
  };

  const { icon: Icon, label } = themeConfig[theme];

  return (
    <button
      onClick={cycle}
      className={cn(
        "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors",
        className
      )}
      title={`Theme: ${label}`}
    >
      <Icon className="h-4 w-4 transition-transform duration-200" />
      {label} mode
    </button>
  );
}
