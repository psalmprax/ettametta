const getApiBase = () => {
    let base = process.env.NEXT_PUBLIC_API_URL;
    
    if (!base && typeof window !== "undefined") {
        const host = window.location.host.includes(":7202") ? window.location.host.replace(":7202", ":7200") : window.location.host;
        base = `${window.location.protocol}//${host}/api/v1`;
    }
    
    if (!base) base = "http://api:8000/api/v1";

    // Ensure /v1 suffix exists and is not duplicated
    let cleanBase = base.replace(/\/+$/, ""); // Remove trailing slashes
    if (!cleanBase.includes("/v1")) {
        if (cleanBase.endsWith("/api")) {
            cleanBase += "/v1";
        } else {
            cleanBase += "/api/v1";
        }
    }
    
    if (typeof window !== "undefined") {
        console.log("[Ettametta] Resolved API_BASE:", cleanBase);
    }
    
    return cleanBase;
};

export const API_BASE = getApiBase();

const getWsBase = () => {
    if (process.env.NEXT_PUBLIC_WS_URL) {
        return process.env.NEXT_PUBLIC_WS_URL;
    }
    if (typeof window !== "undefined") {
        const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
        // If we are on port 7202 (direct dashboard), we likely need port 7200 for WS (Nginx)
        const host = window.location.host.includes(":7202") ? window.location.host.replace(":7202", ":7200") : window.location.host;
        return `${proto}//${host}/ws`;
    }
    return "ws://localhost:8000/ws";
};

export const WS_BASE = getWsBase();

// AI Gateway should point to the Nginx proxy path by default
export const AI_GATEWAY_URL = process.env.NEXT_PUBLIC_AI_GATEWAY_URL || 
    (typeof window !== "undefined" ? `${window.location.protocol}//${window.location.host}/ai-gateway` : "http://ai-gateway:8133");

export const INTERNAL_API_TOKEN = process.env.NEXT_PUBLIC_INTERNAL_API_TOKEN || "";
