"use client";

import React, { Component, ErrorInfo, ReactNode } from "react";
import { AlertTriangle, Home, RefreshCcw } from "lucide-react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

// Dynamic Sentry loader
const captureError = (error: Error, extra?: Record<string, unknown>) => {
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const Sentry = require("@sentry/react");
    Sentry.captureException(error, { extra });
  } catch {
    // Sentry not available
  }
};

export default class GlobalErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught error:", error, errorInfo);
    captureError(error, { componentStack: errorInfo.componentStack });
    this.reportErrorToAPI(error, errorInfo);
  }

  private reportErrorToAPI = async (error: Error, errorInfo: ErrorInfo) => {
    try {
      await fetch("/api/v1/errors", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: error.message,
          stack: error.stack,
          component_stack: errorInfo.componentStack,
          timestamp: new Date().toISOString(),
        }),
      });
    } catch (e) {
      console.error("Failed to report error to API:", e);
    }
  };

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.href = "/";
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-zinc-950 flex items-center justify-center p-6 font-sans">
          <div className="max-w-2xl w-full card-gradient border border-red-500/20 rounded-[2.5rem] p-12 text-center space-y-8 shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 p-8 opacity-5">
              <AlertTriangle className="h-40 w-140 text-red-500" />
            </div>

            <div className="flex justify-center flex-col items-center gap-6 relative z-10">
              <div className="h-24 w-24 rounded-3xl bg-red-500/10 flex items-center justify-center border border-red-500/20 shadow-[0_0_40px_rgba(239,68,68,0.2)]">
                <AlertTriangle className="h-12 w-12 text-red-500" />
              </div>
              <div>
                <h1 className="text-4xl md:text-5xl font-bold text-white uppercase tracking-tighter">
                  Nexus <span className="text-hollow text-red-500">Critical Error</span>
                </h1>
                <p className="text-zinc-500 text-sm mt-3 uppercase tracking-widest font-bold opacity-60">
                  The dashboard encountered an unhandled exception.
                </p>
              </div>
            </div>

            <div className="p-6 bg-zinc-900/50 border border-white/5 rounded-2xl text-left relative z-10">
              <p className="text-red-400 font-mono text-xs break-all">
                {this.state.error?.message || "An unknown error occurred."}
              </p>
            </div>

            <div className="flex flex-col md:flex-row items-center justify-center gap-4 relative z-10">
              <button
                onClick={() => window.location.reload()}
                className="w-full md:w-auto bg-zinc-800 hover:bg-zinc-700 text-white font-bold py-4 px-8 rounded-2xl transition-all flex items-center justify-center gap-2 uppercase tracking-widest text-[10px] border border-white/5"
              >
                <RefreshCcw className="h-4 w-4" />
                Retry Connection
              </button>
              <button
                onClick={this.handleReset}
                className="w-full md:w-auto bg-red-500 hover:bg-red-600 text-white font-bold py-4 px-10 rounded-2xl transition-all shadow-[0_0_30px_rgba(239,68,68,0.3)] flex items-center justify-center gap-2 uppercase tracking-widest text-[10px]"
              >
                <Home className="h-4 w-4" />
                Return to Nexus Home
              </button>
            </div>

            <p className="text-[10px] text-zinc-600 uppercase font-bold tracking-widest">
              Engine Status: <span className="text-red-500/50">Compromised</span>
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
