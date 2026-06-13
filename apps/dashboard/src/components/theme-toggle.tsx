"use client";

import { useUITheme } from "@/context/UIThemeContext";
import { cn } from "@/lib/utils";

interface ThemeToggleProps {
    readonly className?: string;
    readonly showLabel?: boolean;
}

export function ThemeToggle({ className, showLabel = false }: ThemeToggleProps) {
    const { theme, toggleTheme } = useUITheme();

    return (
        <button
            onClick={toggleTheme}
            className={cn(
                "flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors",
                "bg-zinc-800 hover:bg-zinc-700 border border-zinc-700",
                className
            )}
            aria-label={`Switch to ${theme === "legacy" ? "modern" : "legacy"} design`}
            title={`Switch to ${theme === "legacy" ? "modern" : "legacy"} design`}
        >
            <span className="text-sm">{theme === "legacy" ? "🕐" : "✨"}</span>
            {showLabel && (
                <span className="text-xs text-zinc-400">
                    {theme === "legacy" ? "Legacy" : "Modern"}
                </span>
            )}
        </button>
    );
}

export function ThemeSwitcher() {
    const { theme, setTheme } = useUITheme();

    return (
        <div className="flex items-center gap-2 p-1 bg-zinc-900 rounded-lg">
            <button
                onClick={() => setTheme("legacy")}
                className={cn(
                    "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                    theme === "legacy"
                        ? "bg-zinc-800 text-white"
                        : "text-zinc-500 hover:text-zinc-300"
                )}
            >
                Legacy
            </button>
            <button
                onClick={() => setTheme("modern")}
                className={cn(
                    "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                    theme === "modern"
                        ? "bg-violet-600 text-white"
                        : "text-zinc-500 hover:text-zinc-300"
                )}
            >
                Modern
            </button>
        </div>
    );
}
