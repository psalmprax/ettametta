import { useState, useEffect, useCallback, useRef } from 'react';

export function useWebSocket<T>(url: string) {
    const [data, setData] = useState<T | null>(null);
    const [status, setStatus] = useState<'connecting' | 'open' | 'closed'>('connecting');
    const ws = useRef<WebSocket | null>(null);
    const isMounted = useRef(true);
    const reconnectTimeout = useRef<any>(null);
    const reconnectAttempts = useRef(0);
    const maxReconnectAttempts = 10;
    const connectionTimeout = useRef<any>(null);

    const connect = useCallback(() => {
        if (!isMounted.current) return;

        if (reconnectAttempts.current >= maxReconnectAttempts) {
            console.warn(`[WS] Max reconnect attempts (${maxReconnectAttempts}) reached for ${url}`);
            setStatus('closed');
            return;
        }

        // Clear any existing connection
        if (ws.current) {
            ws.current.close();
        }

        try {
            const socket = new WebSocket(url);

            // Set connection timeout
            connectionTimeout.current = setTimeout(() => {
                if (socket.readyState !== WebSocket.OPEN) {
                    console.warn(`[WS] Connection timeout for ${url}, closing...`);
                    socket.close();
                }
            }, 10000);

            socket.onopen = () => {
                if (connectionTimeout.current) {
                    clearTimeout(connectionTimeout.current);
                }
                if (!isMounted.current) {
                    socket.close();
                    return;
                }
                console.log(`[WS] Connected to ${url}`);
                setStatus('open');
                reconnectAttempts.current = 0;
            };

            socket.onmessage = (event) => {
                if (!isMounted.current) return;
                try {
                    const message = JSON.parse(event.data);
                    setData(message);
                } catch (e) {
                    console.error("[WS] Failed to parse message", e);
                }
            };

            socket.onclose = (event) => {
                if (connectionTimeout.current) {
                    clearTimeout(connectionTimeout.current);
                }
                if (!isMounted.current) return;
                console.log(`[WS] Disconnected from ${url} (code: ${event.code})`);
                setStatus('closed');

                // Retry with exponential backoff
                if (reconnectAttempts.current < maxReconnectAttempts) {
                    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
                    reconnectAttempts.current++;
                    console.log(`[WS] Reconnecting to ${url} in ${delay}ms (attempt ${reconnectAttempts.current})`);
                    if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
                    reconnectTimeout.current = setTimeout(() => {
                        if (isMounted.current) connect();
                    }, delay);
                }
            };

            socket.onerror = (error) => {
                if (!isMounted.current) return;
                console.error(`[WS] Error for ${url}:`, error);
            };

            ws.current = socket;
        } catch (e) {
            console.error("[WS] Connection failed", e);
            if (isMounted.current) {
                setStatus('closed');
            }
        }
    }, [url]);

    useEffect(() => {
        isMounted.current = true;
        
        // Small delay to ensure component is fully mounted
        const initTimeout = setTimeout(() => {
            connect();
        }, 100);

        return () => {
            isMounted.current = false;
            if (initTimeout) clearTimeout(initTimeout);
            if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
            if (connectionTimeout.current) clearTimeout(connectionTimeout.current);
            if (ws.current) {
                ws.current.close();
            }
        };
    }, [connect]);

    return { data, status };
}
