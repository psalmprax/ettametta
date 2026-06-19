"use client";

import React from "react";
import { cn } from "@/lib/utils";

export interface SidenavItem {
    id: string;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
}

export interface CommandCenterSidenavProps {
    items: SidenavItem[];
    active: string;
    onSelect: (id: string) => void;
    /** Tailwind classes applied when an item is active. */
    activeClass?: string;
    /** Tailwind class for the active-item dot indicator. */
    dotClass?: string;
}

/**
 * Sidebar nav shared across all "Command Center" sub-pages.
 *
 * Each page previously inlined the same `<div className="space-y-1"> … active
 * button … </div>` block with a page-specific accent colour. Behaviour and
 * styling are identical except for the accent — pass `activeClass` + `dotClass`
 * to theme per-page.
 *
 * Sensible default is emerald (matches the `<CommandCenterLayout>` shell).
 */
export function CommandCenterSidenav({
    items,
    active,
    onSelect,
    activeClass = "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20",
    dotClass = "bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.5)]",
}: CommandCenterSidenavProps) {
    return (
        <div className="space-y-1">
            {items.map((item) => (
                <button
                    key={item.id}
                    onClick={() => onSelect(item.id)}
                    className={cn(
                        "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group",
                        active === item.id
                            ? activeClass
                            : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
                    )}
                >
                    <item.icon className="h-4 w-4" />
                    <span className="text-xs font-bold uppercase tracking-tight">
                        {item.label}
                    </span>
                    {active === item.id && (
                        <div className={cn("ml-auto h-1.5 w-1.5 rounded-full", dotClass)} />
                    )}
                </button>
            ))}
        </div>
    );
}
