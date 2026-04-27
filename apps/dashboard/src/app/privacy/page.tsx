"use client";

import React from "react";
import DashboardLayout from "@/components/layout";
import { Lock, Eye, CheckCircle2 } from "lucide-react";

export default function PrivacyPage() {
    return (
        <DashboardLayout>
            <div className="max-w-4xl mx-auto py-20 px-6 space-y-12">
                <div className="space-y-4">
                    <div className="flex items-center gap-3">
                        <div className="h-1 w-8 bg-primary rounded-full shadow-sm" />
                        <span className="text-[10px] font-bold uppercase tracking-[0.4em] text-primary">Data Protection</span>
                    </div>
                    <h1 className="text-5xl font-bold tracking-tighter uppercase text-white leading-none">
                        Privacy <span className="text-transparent bg-clip-text bg-linear-to-r from-primary to-emerald-400">Policy</span>
                    </h1>
                </div>

                <div className="glass-card p-10 rounded-[3rem] space-y-8 text-zinc-400 leading-relaxed font-medium border-white/5 bg-zinc-950/30">
                    <section className="space-y-4">
                        <h2 className="text-xl font-bold text-white uppercase tracking-tight flex items-center gap-3">
                            <Lock className="h-6 w-6 text-primary" />
                            1. Data Collection
                        </h2>
                        <p>
                            Ettametta collects minimal data necessary to provide its services, including account information and social media tokens for authorized platforms.
                        </p>
                    </section>

                    <section className="space-y-4">
                        <h2 className="text-xl font-bold text-white uppercase tracking-tight flex items-center gap-3">
                            <Eye className="h-6 w-6 text-primary" />
                            2. Use of Information
                        </h2>
                        <p>
                            Your data is used solely to facilitate content discovery and publishing as requested through the Ettametta dashboard.
                        </p>
                    </section>

                    <section className="space-y-4">
                        <h2 className="text-xl font-bold text-white uppercase tracking-tight flex items-center gap-3">
                            <CheckCircle2 className="h-6 w-6 text-primary" />
                            3. Security Measures
                        </h2>
                        <p>
                            We implement robust security measures to protect your tokens and configuration data within our secure production clusters.
                        </p>
                    </section>
                </div>
            </div>
        </DashboardLayout>
    );
}
