"use client";

import { useState, useEffect, useCallback, useRef } from 'react';

// fallow-ignore-next-line unused-export
export function useWebSocket<T>(url: string) {
    const [data, setData] = useState<T | null>(null);
    const [status, setStatus] = useState<'connecting' | 'open' | 'closed'>('connecting');
    const [reconnectCount, setReconnectCount] = useState(0);
    const ws = useRef<WebSocket | null>(null);
    const isMounted = useRef(true);
    const reconnectTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
    const reconnectAttempts = useRef(0);
    const maxReconnectAttempts = 10;
    const connectionTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
    const connectRef = useRef<(() => void) | null>(null);

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
                setStatus('open');
                reconnectAttempts.current = 0;
                setReconnectCount(0);
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

            socket.onclose = () => {
                if (connectionTimeout.current) {
                    clearTimeout(connectionTimeout.current);
                }
                if (!isMounted.current) return;
                setStatus('closed');

                // Retry with exponential backoff
                if (reconnectAttempts.current < maxReconnectAttempts) {
                    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
                    reconnectAttempts.current++;
                    setReconnectCount(reconnectAttempts.current);
                    if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
                    reconnectTimeout.current = setTimeout(() => {
                        if (isMounted.current) connectRef.current?.();
                    }, delay);
                }
            };

            socket.onerror = (error) => {
                if (!isMounted.current) return;
                // Log more diagnostic information
                console.error(`[WS] Error for ${url}:`, error);
                console.error(`[WS] ReadyState: ${socket.readyState} (0=CONNECTING, 1=OPEN, 2=CLOSING, 3=CLOSED)`);
                console.error(`[WS] URL: ${socket.url}`);

                // Log additional details if available
                if (error && typeof error === 'object' && 'target' in error) {
                    const target = error.target as WebSocket | null;
                    if (target) {
                        console.error(`[WS] Target readyState: ${target.readyState}`);
                    }
                }
            };

            ws.current = socket;
        } catch (e) {
            console.error("[WS] Connection failed", e);
            if (isMounted.current) {
                setStatus('closed');
                setReconnectCount(reconnectAttempts.current);
            }
        }
    }, [url]);

    useEffect(() => {
        connectRef.current = connect;
    }, [connect]);

    useEffect(() => {
        isMounted.current = true;

        // Longer delay to ensure component is fully mounted and network is ready
        const initTimeout = setTimeout(() => {
            connect();
        }, 500);

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

    return { data, status, reconnectAttempts: reconnectCount };
}
