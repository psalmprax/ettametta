"use client";

import React, { useState, useEffect } from "react";
import { Bell, Shield, Video, Zap, CheckCircle2, AlertCircle, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { withRealFallback } from "@/lib/real_first_utils";

interface Notification {
    id: string;
    type: "compliance" | "job" | "system" | "security";
    message: string;
    timestamp: string;
    read: boolean;
    link?: string;
}

export function NotificationCenter() {
    const [isOpen, setIsOpen] = useState(false);
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [hasUnread, setHasUnread] = useState(false);

    useEffect(() => {
        // Poll for events every 30s
        fetchNotifications();
        const interval = setInterval(fetchNotifications, 30000);
        return () => clearInterval(interval);
    }, []);

    const fetchNotifications = async () => {
        const token = getAuthToken();
        if (!token) return;

        // In a real system, we'd have an /api/notifications endpoint.
        // For now, we'll derive some from /publish/history and /security/events
        await withRealFallback<any[]>(
            () => fetch(`${API_BASE}/security/events`, {
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: [],
                onSuccess: (events) => {
                    const newNotes = events.slice(0, 5).map((e: any, i: number) => ({
                        id: `sec-${i}`,
                        type: "security" as const,
                        message: typeof e === 'string' ? e : e.message,
                        timestamp: new Date().toISOString(),
                        read: false
                    }));
                    setNotifications(prev => {
                        const merged = [...newNotes, ...prev].slice(0, 10);
                        setHasUnread(merged.some(n => !n.read));
                        return merged;
                    });
                }
            }
        );
    };

    const markAllRead = () => {
        setNotifications(prev => prev.map(n => ({ ...n, read: true })));
        setHasUnread(false);
    };

    return (
        <div className="relative">
            <button
                onClick={() => { setIsOpen(!isOpen); if (!isOpen) markAllRead(); }}
                className="relative h-10 w-10 flex items-center justify-center rounded-xl bg-white border border-slate-200 hover:bg-slate-50 hover:border-slate-300 transition-all shadow-sm group"
            >
                <Bell className={cn("h-5 w-5 transition-all", hasUnread ? "text-amber-500" : "text-slate-400 group-hover:text-slate-600")} />
                {hasUnread && (
                    <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-amber-500 shadow-[0_0_6px_rgba(245,158,11,0.6)]" />
                )}
            </button>

            <AnimatePresence>
                {isOpen && (
                    <>
                        <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
                        <motion.div
                            initial={{ opacity: 0, y: 10, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 10, scale: 0.95 }}
                            className="absolute right-0 mt-3 w-80 rounded-2xl overflow-hidden z-50 shadow-xl border border-slate-200 bg-white"
                        >
                            <div className="p-5 border-b border-slate-100 flex items-center justify-between">
                                <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">Notifications</span>
                                <button onClick={() => setNotifications([])} className="text-[10px] font-semibold text-slate-400 hover:text-slate-600">Clear All</button>
                            </div>

                            <div className="max-h-80 overflow-y-auto">
                                {notifications.length === 0 ? (
                                    <div className="py-12 flex flex-col items-center gap-3 opacity-40">
                                        <Bell className="h-8 w-8 text-slate-400" />
                                        <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide">No new notifications</p>
                                    </div>
                                ) : (
                                    notifications.map((note) => (
                                        <NotificationItem key={note.id} note={note} />
                                    ))
                                )}
                            </div>

                            {notifications.length > 0 && (
                                <div className="p-4 border-t border-slate-100 bg-slate-50 text-center">
                                    <button className="text-[10px] font-semibold text-slate-500 hover:text-slate-700">View All</button>
                                </div>
                            )}
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </div>
    );
}

function NotificationItem({ note }: { note: Notification }) {
    const icons = {
        security: Shield,
        job: Video,
        compliance: CheckCircle2,
        system: Zap
    };
    const colors = {
        security: "text-rose-500 bg-rose-100",
        job: "text-indigo-500 bg-indigo-100",
        compliance: "text-emerald-500 bg-emerald-100",
        system: "text-amber-500 bg-amber-100"
    };
    const Icon = icons[note.type] || Zap;

    return (
        <div className={cn(
            "p-4 flex gap-3 hover:bg-slate-50 transition-colors border-b border-slate-50 cursor-pointer",
            !note.read && "bg-indigo-50/30"
        )}>
            <div className={cn("h-8 w-8 rounded-lg flex items-center justify-center shrink-0", colors[note.type])}>
                <Icon className="h-4 w-4" />
            </div>
            <div className="space-y-1 flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-800 leading-tight">{note.message}</p>
                <p className="text-[10px] text-slate-400">{new Date(note.timestamp).toLocaleTimeString()}</p>
            </div>
        </div>
    );
}
