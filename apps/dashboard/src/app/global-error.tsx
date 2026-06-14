"use client";

import React, { useEffect } from "react";

interface GlobalErrorProps {
    readonly error: Error & { digest?: string };
    readonly reset: () => void;
}

export default function GlobalError({ error, reset }: GlobalErrorProps) {
    useEffect(() => {
        console.error("[GlobalErrorBoundary] Fatal error:", error);
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
                    fatal: true,
                }),
            });
        } catch {
            // Silent fail
        }
    }, [error]);

    return (
        <html lang="en">
            <body className="bg-[#050505] text-white">
                <div className="h-screen w-full flex items-center justify-center p-6">
                    <div className="max-w-md w-full p-12 space-y-10 text-center">
                        <div className="flex justify-center">
                            <div className="h-24 w-24 rounded-[32px] bg-rose-500/10 border border-rose-500/20 flex items-center justify-center">
                                <svg className="h-12 w-12 text-rose-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                                </svg>
                            </div>
                        </div>

                        <div className="space-y-3">
                            <h1 className="text-4xl font-black text-white uppercase tracking-tighter">
                                Critical Failure
                            </h1>
                            <p className="text-zinc-500 text-sm leading-relaxed">
                                A critical system error occurred. The application cannot recover automatically.
                            </p>
                        </div>

                        <div className="p-4 rounded-2xl bg-white/5 border border-white/5">
                            <p className="text-[10px] font-mono text-zinc-600 break-all leading-relaxed text-left">
                                {error.message.slice(0, 200)}
                            </p>
                        </div>

                        <div className="flex flex-col gap-4">
                            <button
                                onClick={reset}
                                className="w-full h-14 bg-rose-500 hover:bg-rose-400 text-black font-bold uppercase tracking-widest text-xs rounded-2xl transition-all hover:shadow-[0_0_30px_rgba(239,68,68,0.3)]"
                            >
                                Attempt Recovery
                            </button>
                            <button
                                onClick={() => {
                                    if (typeof window !== "undefined") {
                                        window.location.href = "/";
                                    }
                                }}
                                className="w-full h-14 border border-white/10 hover:bg-white/5 text-white font-bold uppercase tracking-widest text-xs rounded-2xl transition-all"
                            >
                                Return to Home
                            </button>
                        </div>
                    </div>
                </div>
            </body>
        </html>
    );
}
