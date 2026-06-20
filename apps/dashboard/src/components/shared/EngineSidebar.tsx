"use client";

import React from "react";
import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

/** Module-internal — do not consume from outside. */
interface SidebarItem {
    id: string;
    label: string;
    icon: LucideIcon;
}

/** Module-internal — do not consume from outside. */
interface EngineSidebarProps {
    readonly items: readonly SidebarItem[];
    readonly activeId: string;
    readonly onSelect: (id: string) => void;
    readonly accentColor?: string;
}

const ACCENT_STYLES: Record<string, { active: string; dot: string }> = {
    cyan: {
        active: "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20",
        dot: "bg-cyan-400 shadow-[0_0_8px_rgba(6,182,212,0.5)]",
    },
    violet: {
        active: "bg-violet-500/10 text-violet-400 border border-violet-500/20",
        dot: "bg-violet-400 shadow-[0_0_8px_rgba(139,92,246,0.5)]",
    },
    rose: {
        active: "bg-rose-500/10 text-rose-400 border border-rose-500/20",
        dot: "bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.5)]",
    },
    emerald: {
        active: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20",
        dot: "bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.5)]",
    },
};

/**
 * Shared sidebar navigation for CommandCenterLayout-based pages.
 * Replaces the identical nav-item mapping pattern in 6+ dashboard pages.
 */
export function EngineSidebar({ items, activeId, onSelect, accentColor = "cyan" }: EngineSidebarProps) {
    const accent = ACCENT_STYLES[accentColor] ?? ACCENT_STYLES.cyan;
    return (
        <div className="space-y-1">
            {items.map((item) => (
                <button
                    key={item.id}
                    onClick={() => onSelect(item.id)}
                    className={cn(
                        "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group",
                        activeId === item.id ? accent.active : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
                    )}
                >
                    <item.icon className="h-4 w-4" />
                    <span className="text-xs font-bold uppercase tracking-tight">{item.label}</span>
                    {activeId === item.id && (
                        <div className={cn("ml-auto h-1.5 w-1.5 rounded-full", accent.dot)} />
                    )}
                </button>
            ))}
        </div>
    );
}
