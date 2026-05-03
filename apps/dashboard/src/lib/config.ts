const getApiBase = () => {
    // If NEXT_PUBLIC_API_URL is set (e.g. in .env), use it
    let base = process.env.NEXT_PUBLIC_API_URL;
    
    if (!base && typeof window !== "undefined") {
        // If we are on port 7202 (direct dashboard), we likely need port 7200 for API (Nginx)
        const host = window.location.host.includes(":7202") ? window.location.host.replace(":7202", ":7200") : window.location.host;
        // The API is served under /api/v1 via Nginx
        base = `${window.location.protocol}//${host}/api/v1`;
    }
    
    if (!base) base = "http://api:8000/api/v1";

    // Production Hardening: Ensure /v1 is always present to avoid 404s on auth/login
    if (base.endsWith("/api")) {
        base += "/v1";
    } else if (!base.includes("/v1")) {
        if (base.endsWith("/")) base += "v1";
        else base += "/v1";
    }
    
    return base;
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
