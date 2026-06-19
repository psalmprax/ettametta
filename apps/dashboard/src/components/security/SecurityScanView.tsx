"use client";

import React from "react";
import { Shield, ScanLine, AlertTriangle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/Button";

interface Props {
    scanResults: string[];
    isScanning: boolean;
    onScan: () => void;
}

/**
 * Vulnerability-Scan tab — full-system integrity check trigger + results.
 */
export default function SecurityScanView({ scanResults, isScanning, onScan }: Props) {
    return (
        <div className="space-y-8 overflow-y-auto custom-scrollbar flex-1 p-1">
            <div className="p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-8">
                <div className="flex items-center justify-between">
                    <div className="space-y-2">
                        <h3 className="text-xl font-bold text-white uppercase tracking-tight">Vulnerability Scanner</h3>
                        <p className="text-xs text-zinc-500">Performs comprehensive system integrity checks including secret scanning, port analysis, and configuration validation.</p>
                    </div>
                    <Button onClick={onScan} disabled={isScanning}
                        className="bg-emerald-500 hover:bg-emerald-400 text-black font-bold h-14 px-10 rounded-2xl gap-3 text-lg">
                        {isScanning ? <Loader2 className="h-5 w-5 animate-spin" /> : <ScanLine className="h-5 w-5" />}
                        {isScanning ? "Scanning..." : "Execute Scan"}
                    </Button>
                </div>

                {scanResults.length > 0 && (
                    <div className="space-y-4">
                        <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Findings ({scanResults.length})</h4>
                        {scanResults.map((finding, i) => (
                            <div key={i} className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-start gap-3">
                                <AlertTriangle className="h-4 w-4 text-rose-500 shrink-0 mt-0.5" />
                                <span className="text-xs text-zinc-300">{finding}</span>
                            </div>
                        ))}
                    </div>
                )}

                {scanResults.length === 0 && !isScanning && (
                    <div className="flex flex-col items-center justify-center py-16 opacity-20">
                        <Shield className="h-16 w-16 mb-4" />
                        <span className="text-[10px] font-bold uppercase tracking-[0.5em]">No scan results yet — run a scan to check for vulnerabilities</span>
                    </div>
                )}
            </div>
        </div>
    );
}
