"use client";

import React, { useState, useEffect, useCallback, useRef, useMemo, Suspense } from "react";
import { withRealFallback } from "@/lib/real_first_utils";
import {
    Bot,
    Send,
    Terminal,
    Cpu,
    User,
    Loader2,
    Sparkles,
    Zap,
    Brain,
    Code,
    MessageSquare,
    ChevronRight,
    Activity,
    ShieldCheck,
    Globe,
    Database,
    Layers,
    Video,
    FileText,
    Search,
    BarChart3
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { AgentMatrix } from "@/components/ui/CommandCenterComponents";
import { Button } from "@/components/ui/Button";
import { useTelemetry } from "@/context/TelemetryContext";

interface ChatMessage {
    id: string;
    role: "user" | "assistant";
    content: string;
    agent?: string;
    timestamp: Date;
}

interface AgentCapability {
    id: string;
    name: string;
    category: string;
    stability: string;
    description: string;
}

function AgentContent() {
    const { agents, logs: systemLogs, status, pulse } = useTelemetry();
    const [activeEngine, setActiveEngine] = useState("chat");
    const [messages, setMessages] = useState<ChatMessage[]>([
        {
            id: "welcome",
            role: "assistant",
            content: "I'm your AI Agent interface. I can help with video generation, content analysis, code review, brand creation, and more. What would you like to do?",
            agent: "openclaw-master",
            timestamp: new Date()
        }
    ]);
    const [input, setInput] = useState("");
    const [isSending, setIsSending] = useState(false);
    const [capabilities, setCapabilities] = useState<AgentCapability[]>([]);
    const [workers, setWorkers] = useState<any>({});
    const [actionLogs, setActionLogs] = useState<string[]>(["AGENT_INTERFACE_INITIALIZED"]);
    const chatEndRef = useRef<HTMLDivElement>(null);

    const fetchCapabilities = useCallback(async () => {
        const token = await getAuthToken();
        if (!token) return;
        await withRealFallback<any>(
            () => fetch(`${API_BASE}/agent/capabilities`, {
                headers: { Authorization: `Bearer ${token}` }
            }),
            {
                fallback: null,
                onSuccess: (data) => {
                    const caps = data?.data || data;
                    setCapabilities(caps?.workers || []);
                    setWorkers(caps?.workforce || []);
                    setActionLogs((prev: string[]) => ["[INFO] Loaded agent capabilities", ...prev]);
                }
            }
        );
    }, []);

    useEffect(() => {
        fetchCapabilities();
    }, [fetchCapabilities]);

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    const handleSend = async () => {
        const message = input.trim();
        if (!message || isSending) return;
        setInput("");
        setIsSending(true);

        const userMsg: ChatMessage = {
            id: `user-${Date.now()}`,
            role: "user",
            content: message,
            timestamp: new Date()
        };
        setMessages((prev) => [...prev, userMsg]);
        setActionLogs((prev: string[]) => [`[USER] ${message.slice(0, 60)}...`, ...prev]);

        const token = await getAuthToken();
        if (!token) { setIsSending(false); return; }

        const placeholderId = `assistant-${Date.now()}`;
        const placeholder: ChatMessage = {
            id: placeholderId,
            role: "assistant",
            content: "",
            agent: "openclaw-master",
            timestamp: new Date()
        };
        setMessages((prev) => [...prev, placeholder]);

        await withRealFallback<any>(
            () => fetch(`${API_BASE}/agent/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                body: JSON.stringify({ message, context: { source: "dashboard" } })
            }),
            {
                fallback: null,
                onSuccess: (data) => {
                    const response = data?.data?.response || data?.response || "I processed your request.";
                    setMessages((prev) =>
                        prev.map((m) =>
                            m.id === placeholderId ? { ...m, content: response, agent: data?.data?.agent || "openclaw-master" } : m
                        )
                    );
                    setActionLogs((prev: string[]) => [`[AGENT] Response received`, ...prev]);
                },
                onFallback: (err) => {
                    setMessages((prev) =>
                        prev.map((m) =>
                            m.id === placeholderId ? { ...m, content: `Error: ${err.message}` } : m
                        )
                    );
                    toast.error(`Agent request failed: ${err.message}`);
                }
            }
        );
        setIsSending(false);
    };

    // Group capabilities by category
    const categorizedCapabilities = useMemo(() => {
        const grouped: Record<string, AgentCapability[]> = {};
        for (const cap of capabilities) {
            const cat = cap.category || "General";
            if (!grouped[cat]) grouped[cat] = [];
            grouped[cat].push(cap);
        }
        return grouped;
    }, [capabilities]);

    return (
        <CommandCenterLayout
            title="AGENT INTERFACE"
            subtitle="OPENCLAW_V3.0"
            leftPanel={
                <div className="space-y-1">
                    {[
                        { id: "chat", label: "Agent Chat", icon: MessageSquare },
                        { id: "capabilities", label: "Capabilities", icon: Cpu },
                        { id: "logs", label: "Engine Logs", icon: Terminal },
                    ].map((item) => (
                        <button
                            key={item.id}
                            onClick={() => setActiveEngine(item.id)}
                            className={cn(
                                "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group",
                                activeEngine === item.id ? "bg-violet-500/10 text-violet-400 border border-violet-500/20" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
                            )}
                        >
                            <item.icon className="h-4 w-4" />
                            <span className="text-xs font-bold uppercase tracking-tight">{item.label}</span>
                            {activeEngine === item.id && <div className="ml-auto h-1.5 w-1.5 rounded-full bg-violet-500 shadow-[0_0_8px_rgba(139,92,246,0.5)]" />}
                        </button>
                    ))}
                </div>
            }
            rightPanel={
                <>
                    <AgentMatrix agents={agents} />
                    <div className="p-6 rounded-2xl border border-white/5 bg-white/5 space-y-4">
                        <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Workforce Status</h4>
                        <div className="flex flex-col">
                            <span className={cn(
                                "text-sm font-bold",
                                workers?.status === "healthy" ? "text-emerald-500" : "text-amber-500"
                            )}>{workers?.description || "Agent System"}</span>
                            <span className="text-[8px] text-zinc-600 font-bold uppercase tracking-widest">
                                Circuit: {workers?.circuit_breaker || "closed"}
                            </span>
                        </div>
                    </div>
                    <div className="p-6 rounded-2xl border border-white/5 bg-white/5 space-y-4">
                        <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Quick Actions</h4>
                        <div className="space-y-2">
                            <Button variant="outline" className="w-full border-violet-500/20 text-violet-400 hover:bg-violet-500/10 text-[8px] h-8"
                                onClick={() => {
                                    setInput("Generate a video about motivation");
                                    setActiveEngine("chat");
                                }}>
                                <Video className="h-3 w-3 mr-1" /> Generate Video
                            </Button>
                            <Button variant="outline" className="w-full border-violet-500/20 text-violet-400 hover:bg-violet-500/10 text-[8px] h-8"
                                onClick={() => {
                                    setInput("Analyze this niche for trends: AI Technology");
                                    setActiveEngine("chat");
                                }}>
                                <Search className="h-3 w-3 mr-1" /> Analyze Niche
                            </Button>
                            <Button variant="outline" className="w-full border-violet-500/20 text-violet-400 hover:bg-violet-500/10 text-[8px] h-8"
                                onClick={() => {
                                    setInput("Create a brand identity for: Motivation niche");
                                    setActiveEngine("chat");
                                }}>
                                <Sparkles className="h-3 w-3 mr-1" /> Build Brand
                            </Button>
                        </div>
                    </div>
                </>
            }
        >
            <div className="p-10 space-y-10 relative h-full flex flex-col">
                <AnimatePresence mode="wait">
                    <motion.div
                        key={activeEngine}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                        className="flex-1 flex flex-col min-h-0"
                    >
                        {activeEngine === "chat" && (
                            <div className="flex-1 flex flex-col min-h-0 bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden">
                                {/* Chat Header */}
                                <div className="p-6 border-b border-white/5 flex items-center justify-between bg-black/20 shrink-0">
                                    <div className="flex items-center gap-4">
                                        <div className="h-10 w-10 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center">
                                            <Bot className="h-5 w-5 text-violet-500" />
                                        </div>
                                        <div>
                                            <h3 className="text-sm font-bold text-white uppercase tracking-tight">OpenClaw Master Agent</h3>
                                            <span className="text-[9px] text-zinc-600 font-bold uppercase tracking-widest">Online • Multi-Skill</span>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                                        <span className="text-[9px] font-bold text-emerald-500 uppercase">Active</span>
                                    </div>
                                </div>

                                {/* Messages */}
                                <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-4">
                                    {messages.map((msg) => (
                                        <div key={msg.id} className={cn(
                                            "flex gap-4 items-start",
                                            msg.role === "user" ? "flex-row-reverse" : "flex-row"
                                        )}>
                                            <div className={cn(
                                                "h-10 w-10 rounded-xl flex items-center justify-center shrink-0",
                                                msg.role === "user" ? "bg-cyan-500/10 border border-cyan-500/20" : "bg-violet-500/10 border border-violet-500/20"
                                            )}>
                                                {msg.role === "user" ? <User className="h-5 w-5 text-cyan-400" /> : <Bot className="h-5 w-5 text-violet-500" />}
                                            </div>
                                            <div className={cn(
                                                "max-w-[70%] rounded-2xl p-4",
                                                msg.role === "user" ? "bg-cyan-500/10 border border-cyan-500/20" : "bg-white/5 border border-white/5"
                                            )}>
                                                {msg.content ? (
                                                    <p className="text-sm text-zinc-200 leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                                                ) : (
                                                    <div className="flex items-center gap-2">
                                                        <Loader2 className="h-4 w-4 text-violet-500 animate-spin" />
                                                        <span className="text-xs text-zinc-500 italic">Thinking...</span>
                                                    </div>
                                                )}
                                                {msg.agent && msg.role === "assistant" && msg.content && (
                                                    <div className="mt-2 flex items-center gap-2">
                                                        <span className="text-[8px] font-bold text-violet-500/60 uppercase tracking-widest">{msg.agent}</span>
                                                        <span className="text-[8px] text-zinc-700">{msg.timestamp.toLocaleTimeString()}</span>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                    <div ref={chatEndRef} />
                                </div>

                                {/* Input */}
                                <div className="p-4 border-t border-white/5 bg-black/20 shrink-0">
                                    <div className="flex gap-4">
                                        <input
                                            type="text"
                                            value={input}
                                            onChange={(e) => setInput(e.target.value)}
                                            onKeyDown={(e) => e.key === "Enter" && handleSend()}
                                            placeholder="Type a message or ask the agent to do something..."
                                            className="flex-1 bg-white/5 border border-white/10 rounded-2xl px-6 py-4 text-white text-sm font-mono focus:outline-none focus:border-violet-500/30 transition-all"
                                            disabled={isSending}
                                        />
                                        <Button
                                            onClick={handleSend}
                                            disabled={!input.trim() || isSending}
                                            className="h-full aspect-square rounded-2xl bg-violet-500 hover:bg-violet-400 text-black"
                                        >
                                            {isSending ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
                                        </Button>
                                    </div>
                                </div>
                            </div>
                        )}

                        {activeEngine === "capabilities" && (
                            <div className="overflow-y-auto custom-scrollbar flex-1 p-1 space-y-8">
                                {Object.entries(categorizedCapabilities).map(([category, caps]) => (
                                    <div key={category} className="space-y-4">
                                        <h3 className="text-xs font-bold text-violet-400 uppercase tracking-widest">{category}</h3>
                                        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                                            {caps.map((cap) => (
                                                <div key={cap.id} className="p-6 rounded-2xl bg-white/5 border border-white/5 space-y-3 group hover:border-violet-500/20 transition-all">
                                                    <div className="flex items-center justify-between">
                                                        <span className="text-xs font-bold text-white uppercase tracking-tight">{cap.name}</span>
                                                        <span className={cn(
                                                            "px-2 py-0.5 rounded text-[8px] font-bold uppercase",
                                                            cap.stability === "Stable" ? "bg-emerald-500/20 text-emerald-400" :
                                                            cap.stability === "Beta" ? "bg-amber-500/20 text-amber-400" :
                                                            "bg-zinc-500/20 text-zinc-400"
                                                        )}>{cap.stability}</span>
                                                    </div>
                                                    <p className="text-[10px] text-zinc-500 leading-relaxed">{cap.description}</p>
                                                    <span className="block text-[8px] font-mono text-zinc-700">{cap.id}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                ))}
                                {capabilities.length === 0 && (
                                    <div className="flex flex-col items-center justify-center py-32 opacity-20">
                                        <Cpu className="h-16 w-16 mb-4" />
                                        <span className="text-[10px] font-bold uppercase tracking-[0.5em]">Loading capabilities...</span>
                                    </div>
                                )}
                            </div>
                        )}

                        {activeEngine === "logs" && (
                            <div className="flex-1 flex flex-col min-h-0 bg-[#0F0F11]/60 border border-white/5 rounded-[32px] overflow-hidden">
                                <div className="p-6 border-b border-white/5 flex items-center justify-between bg-black/20">
                                    <div className="flex items-center gap-4">
                                        <Terminal className="h-4 w-4 text-zinc-500" />
                                        <h3 className="text-xs font-bold text-white uppercase tracking-widest">Agent Interface Logs</h3>
                                    </div>
                                    <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-violet-500/10 border border-violet-500/20">
                                        <div className="h-1.5 w-1.5 rounded-full bg-violet-500 animate-pulse" />
                                        <span className="text-[9px] font-bold text-violet-500 uppercase">Agent_Active</span>
                                    </div>
                                </div>
                                <div className="flex-1 overflow-y-auto custom-scrollbar p-8 font-mono text-xs space-y-3">
                                    {actionLogs.map((log, i) => (
                                        <div key={i} className="flex gap-6 group hover:bg-white/5 p-2 rounded-lg transition-all">
                                            <span className="text-zinc-700 shrink-0 select-none">{new Date().toLocaleTimeString()}</span>
                                            <span className="text-zinc-800 shrink-0 select-none">|</span>
                                            <span className={cn(
                                                log.startsWith("[AGENT]") ? "text-violet-400" :
                                                log.startsWith("[USER]") ? "text-cyan-400" :
                                                log.startsWith("[ERROR]") ? "text-rose-500" :
                                                "text-zinc-400"
                                            )}>{log}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </motion.div>
                </AnimatePresence>
            </div>
        </CommandCenterLayout>
    );
}

export default function AgentPage() {
    return (
        <Suspense fallback={null}>
            <AgentContent />
        </Suspense>
    );
}
