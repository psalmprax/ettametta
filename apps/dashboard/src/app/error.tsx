"use client";

import React, { useEffect } from "react";
import { AlertTriangle, RefreshCw, Home, Terminal } from "lucide-react";
import { Button } from "@/components/ui/Button";

/** Module-internal — do not consume from outside. */
interface ErrorPageProps {
    readonly error: Error & { digest?: string };
    readonly reset: () => void;
}

export default function ErrorPage({ error, reset }: ErrorPageProps) {
    useEffect(() => {
        // Log the error to the console and optionally to the backend
        console.error("[ErrorBoundary] Unhandled error:", error);
        
        // Attempt to report to backend error endpoint
        try {
            fetch("/api/v1/security/errors", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: error.message,
                    stack: error.stack?.slice(0, 2000),
                    digest: error.digest,
                    url: typeof window !== "undefined" ? window.location.href : "",
                    timestamp: new Date().toISOString(),
                }),
            });
        } catch {
            // Silently fail if error reporting itself fails
        }
    }, [error]);

    return (
        <div className="h-screen w-full flex items-center justify-center bg-[#050505]">
            <div className="max-w-md w-full p-12 space-y-10 text-center">
                {/* Icon */}
                <div className="flex justify-center">
                    <div className="h-24 w-24 rounded-[32px] bg-rose-500/10 border border-rose-500/20 flex items-center justify-center">
                        <AlertTriangle className="h-12 w-12 text-rose-500" />
                    </div>
                </div>

                {/* Error info */}
                <div className="space-y-3">
                    <h1 className="text-4xl font-black text-white uppercase tracking-tighter">
                        System Error
                    </h1>
                    <p className="text-zinc-500 text-sm leading-relaxed">
                        The neural network encountered an unexpected fault. 
                        This has been logged for diagnostic analysis.
                    </p>
                </div>

                {/* Error detail (collapsed) */}
                <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
                    <div className="flex items-center gap-2 mb-2">
                        <Terminal className="h-3 w-3 text-rose-500" />
                        <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">
                            Error Signature
                        </span>
                    </div>
                    <p className="text-[10px] font-mono text-zinc-600 break-all leading-relaxed text-left">
                        {error.digest 
                            ? `DIGEST: ${error.digest}\n${error.message.slice(0, 200)}`
                            : error.message.slice(0, 200)
                        }
                    </p>
                </div>

                {/* Actions */}
                <div className="flex flex-col sm:flex-row gap-4">
                    <Button
                        onClick={reset}
                        variant="primary"
                        className="flex-1 h-14 bg-rose-500 hover:bg-rose-400 text-white font-bold uppercase tracking-widest text-xs"
                        icon={<RefreshCw className="h-4 w-4" />}
                    >
                        Retry
                    </Button>
                    <Button
                        onClick={() => {
                            if (typeof window !== "undefined") {
                                window.location.href = "/";
                            }
                        }}
                        variant="outline"
                        className="flex-1 h-14 border-white/10 text-white font-bold uppercase tracking-widest text-xs"
                        icon={<Home className="h-4 w-4" />}
                    >
                        Return Home
                    </Button>
                </div>
            </div>
        </div>
    );
}
