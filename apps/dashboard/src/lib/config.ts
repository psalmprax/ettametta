const getApiBase = () => {
    if (typeof window !== "undefined") {
        return `${window.location.protocol}//${window.location.host}/api/v1`;
    }
    return (process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/v1` : "http://localhost:8000/api/v1");
};

export const API_BASE = getApiBase();

const getWsBase = () => {
    if (process.env.NEXT_PUBLIC_WS_URL) {
        return process.env.NEXT_PUBLIC_WS_URL;
    }
    if (typeof window !== "undefined") {
        const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
        const apiHost = process.env.NEXT_PUBLIC_API_HOST || window.location.hostname;
        const apiPort = process.env.NEXT_PUBLIC_API_PORT || "7201";
        return `${proto}//${apiHost}:${apiPort}/ws`;
    }
    return "ws://localhost:8000/ws";
};

export const WS_BASE = getWsBase();
