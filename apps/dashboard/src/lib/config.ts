const getApiBase = () => {
    if (typeof window !== "undefined") {
        return `${window.location.protocol}//${window.location.host}/api`;
    }
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
};

export const API_BASE = getApiBase();
export const WS_BASE = API_BASE.replace(/^http/, "ws");
