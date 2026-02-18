import { useState, useEffect, useCallback, useRef } from 'react';

export function useWebSocket<T>(url: string) {
    const [data, setData] = useState<T | null>(null);
    const [status, setStatus] = useState<'connecting' | 'open' | 'closed'>('connecting');
    const ws = useRef<WebSocket | null>(null);

    const connect = useCallback(() => {
        try {
            const socket = new WebSocket(url);

            socket.onopen = () => {
                console.log(`[WS] Connected to ${url}`);
                setStatus('open');
            };

            socket.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    setData(message);
                } catch (e) {
                    console.error("[WS] Failed to parse message", e);
                }
            };

            socket.onclose = () => {
                console.log(`[WS] Disconnected from ${url}`);
                setStatus('closed');
                // Reconnect after 3 seconds
                setTimeout(connect, 3000);
            };

            socket.onerror = (error) => {
                console.error(`[WS] Error:`, error);
                socket.close();
            };

            ws.current = socket;
        } catch (e) {
            console.error("[WS] Connection failed", e);
            setStatus('closed');
            setTimeout(connect, 3000);
        }
    }, [url]);

    useEffect(() => {
        connect();
        return () => {
            if (ws.current) {
                ws.current.close();
            }
        };
    }, [connect]);

    return { data, status };
}
