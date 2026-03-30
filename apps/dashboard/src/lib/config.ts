const getApiBase = () => {
    if (typeof window !== "undefined") {
        return `${window.location.protocol}//${window.location.host}/api/v1`;
    }
    return (process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/v1` : "http://localhost:8000/api/v1");
};

export const API_BASE = getApiBase();
// WebSocket base should point to /ws, so we strip /api/v1 and replace with /ws
export const WS_BASE = API_BASE.replace(/\/api\/v1$/, "/ws").replace(/^http/, "ws");
