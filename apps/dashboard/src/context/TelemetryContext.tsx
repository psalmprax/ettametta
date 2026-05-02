"use client";

import React, { createContext, useContext, useState, useEffect, useRef, useCallback } from "react";
import { WS_BASE } from "@/lib/config";
import { 
    Cpu, 
    Globe, 
    Zap, 
    Activity, 
    Terminal, 
    ShieldAlert, 
    Radar,
    Server,
    Network,
    HardDrive,
    Bot
} from "lucide-react";

interface TelemetryPulse {
    status: string;
    cluster_node: string;
    hostname: string;
    active_jobs: number;
    nexus_active: number;
    video_active: number;
    latency_ms: number;
    timestamp: number;
    load_avg: number;
    memory_usage?: number;
    uptime?: string;
    signals: Array<{
        id: string;
        status: string;
        offset: string;
        details?: string;
    }>;
    metrics?: {
        bitrate: number;
        latency: number;
        signal_strength: number;
        active_nodes: number;
        global_velocity: number;
    };
    active_segments?: Array<{ label: string; load: number }>;
    geo_activity?: Array<{ lat: number; lng: number; intensity: number }>;
    real_stats?: {
        active_jobs: number;
        completed_jobs: number;
        total_published: number;
        total_discovered: number;
        total_views: number;
        total_likes: number;
        oracle_mae: number;
        oracle_status: string;
    };
}

interface LogEntry {
    type: string;
    level: string;
    module: string;
    message: string;
    timestamp: number;
}

interface TelemetryContextType {
    pulse: TelemetryPulse | null;
    logs: LogEntry[];
    lastJobUpdate: any | null;
    status: "connecting" | "open" | "closed";
    agents: any[];
}

const TelemetryContext = createContext<TelemetryContextType | undefined>(undefined);

export function TelemetryProvider({ children }: { children: React.ReactNode }) {
    const [pulse, setPulse] = useState<TelemetryPulse | null>(null);
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [lastJobUpdate, setLastJobUpdate] = useState<any | null>(null);
    const [status, setStatus] = useState<"connecting" | "open" | "closed">("connecting");
    const ws = useRef<WebSocket | null>(null);
    const reconnectAttempts = useRef(0);

    const connect = useCallback(() => {
        if (ws.current?.readyState === WebSocket.OPEN) return;

        try {
            const socket = new WebSocket(`${WS_BASE}/telemetry`);
            
            socket.onopen = () => {
                setStatus("open");
                reconnectAttempts.current = 0;
                console.log("[Telemetry] Secure Stream Established");
            };

            socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === "telemetry_pulse") {
                        setPulse(data);
                    } else if (data.type === "log") {
                        setLogs(prev => [data, ...prev].slice(0, 100));
                    } else if (data.type === "job_update" || data.type === "nexus_job_update") {
                        setLastJobUpdate(data);
                    }
                } catch (e) {
                    console.error("[Telemetry] Parse Error:", e);
                }
            };

            socket.onclose = () => {
                setStatus("closed");
                const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
                reconnectAttempts.current++;
                setTimeout(connect, delay);
            };

            ws.current = socket;
        } catch (e) {
            console.error("[Telemetry] Connection Failed:", e);
            setStatus("closed");
        }
    }, []);

    useEffect(() => {
        connect();
        return () => ws.current?.close();
    }, [connect]);

    // Map pulse signals to AgentMatrix format
    const agents = (pulse?.signals || []).map((s, i) => {
        const icons = {
            GPU_Cluster: HardDrive,
            Neural: Bot,
            Radar: Radar,
            Sentinel: Globe,
            Cluster: Server,
            Network: Network,
            Discovery: Activity
        };

        const iconKey = Object.keys(icons).find(k => s.id.includes(k)) as keyof typeof icons;
        const Icon = icons[iconKey] || Cpu;

        return {
            id: s.id,
            name: s.id.replace(/_/g, " "),
            icon: Icon,
            status: (s.status === "OPEN" || s.status === "HEALTHY" || s.status === "OK") ? "ACTIVE" : "DEGRADED",
            latency: parseInt(s.offset) || 0,
            load: pulse?.load_avg ? Math.min(100, Math.max(5, Math.round(pulse.load_avg * 20 + (i * 5)))) : 0,
            details: s.details || "Telemetry Active"
        };
    });

    // If no signals yet, provide skeleton/initial agents
    const finalAgents = agents.length > 0 ? agents : [
        { id: "SYS_CORE", name: "System Core", icon: Cpu, status: "QUEUED", latency: 0, load: 0, details: "Awaiting Sync" },
        { id: "NEURAL_01", name: "Neural Engine", icon: Bot, status: "QUEUED", latency: 0, load: 0, details: "Initializing" }
    ];

    return (
        <TelemetryContext.Provider value={{ pulse, logs, lastJobUpdate, status, agents: finalAgents }}>
            {children}
        </TelemetryContext.Provider>
    );
}

export function useTelemetry() {
    const context = useContext(TelemetryContext);
    if (context === undefined) {
        throw new Error("useTelemetry must be used within a TelemetryProvider");
    }
    return context;
}
