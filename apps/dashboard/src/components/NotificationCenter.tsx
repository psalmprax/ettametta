"use client";

import React, { useState, useEffect } from "react";
import { Bell, DollarSign, Shield, Video, Zap, CheckCircle2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { withRealFallback } from "@/lib/real_first_utils";

interface Notification {
    id: string;
    type: string;
    title: string;
    message?: string;
    timestamp: string;
    read: boolean;
    link?: string;
}

export function NotificationCenter() {
    const [isOpen, setIsOpen] = useState(false);
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [hasUnread, setHasUnread] = useState(false);

    const fetchNotifications = async () => {
        const token = getAuthToken();
        if (!token) return;

        await withRealFallback<any[]>(
            (signal) => fetch(`${API_BASE}/notifications/`, {
                headers: { Authorization: `Bearer ${token}` },
                signal,
            }),
            {
                fallback: [],
                onSuccess: (notes) => {
                    const parsed = notes.map((n: any) => ({
                        id: n.id,
                        type: n.type || "system",
                        title: n.title || n.message,
                        message: n.message,
                        timestamp: n.timestamp || new Date().toISOString(),
                        read: n.read ?? false,
                        link: n.link,
                    }));
                    setNotifications(parsed);
                    setHasUnread(parsed.some(n => !n.read));
                }
            }
        );
    };

    useEffect(() => {
        fetchNotifications();
        const interval = setInterval(fetchNotifications, 30000);
        return () => clearInterval(interval);
    }, []);

    const markAllRead = async () => {
        const token = getAuthToken();
        if (token) {
            await fetch(`${API_BASE}/notifications/read-all`, {
                method: "PUT",
                headers: { Authorization: `Bearer ${token}` },
            }).catch(() => {});
        }
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

function NotificationItem({ note }: { readonly note: Notification }) {
    const icons: Record<string, React.ComponentType<{ className?: string }>> = {
        security: Shield,
        job: Video,
        billing: DollarSign,
        compliance: CheckCircle2,
        system: Zap
    };
    const colors: Record<string, string> = {
        security: "text-rose-500 bg-rose-100",
        job: "text-indigo-500 bg-indigo-100",
        billing: "text-blue-500 bg-blue-100",
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
                <p className="text-sm font-medium text-slate-800 leading-tight">{note.title}</p>
                {note.message && (
                    <p className="text-xs text-slate-500 leading-tight">{note.message}</p>
                )}
                <p className="text-[10px] text-slate-400">{new Date(note.timestamp).toLocaleTimeString()}</p>
            </div>
        </div>
    );
}
