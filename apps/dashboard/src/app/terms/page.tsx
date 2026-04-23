"use client";

import React from "react";
import DashboardLayout from "@/components/layout";
import { ShieldCheck, FileText, ChevronRight } from "lucide-react";
import { motion } from "framer-motion";

export default function TermsPage() {
    return (
        <DashboardLayout>
            <div className="max-w-4xl mx-auto py-20 px-6 space-y-12">
                <div className="space-y-4">
                    <div className="flex items-center gap-3">
                        <div className="h-1 w-8 bg-primary rounded-full shadow-sm" />
                        <span className="text-[10px] font-black uppercase tracking-[0.4em] text-primary">Legal Framework</span>
                    </div>
                    <h1 className="text-5xl font-black tracking-tighter uppercase text-white leading-none">
                        Terms of <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-emerald-400">Service</span>
                    </h1>
                </div>

                <div className="glass-card p-10 rounded-[3rem] space-y-8 text-zinc-400 leading-relaxed font-medium border-white/5 bg-zinc-950/30">
                    <section className="space-y-4">
                        <h2 className="text-xl font-black text-white uppercase tracking-tight flex items-center gap-3">
                            <ShieldCheck className="h-6 w-6 text-primary" />
                            1. Acceptance of Terms
                        </h2>
                        <p>
                            By accessing or using Ettametta, you agree to be bound by these Terms of Service. If you do not agree to all of these terms, do not use the service.
                        </p>
                    </section>

                    <section className="space-y-4">
                        <h2 className="text-xl font-black text-white uppercase tracking-tight flex items-center gap-3">
                            <FileText className="h-6 w-6 text-primary" />
                            2. Service Description
                        </h2>
                        <p>
                            Ettametta provides tools for content discovery, analysis, and social media publishing across various platforms including YouTube and TikTok.
                        </p>
                    </section>

                    <section className="space-y-4">
                        <h2 className="text-xl font-black text-white uppercase tracking-tight flex items-center gap-3">
                            <ChevronRight className="h-6 w-6 text-primary" />
                            3. User Obligations
                        </h2>
                        <p>
                            You are responsible for maintaining the security of your account and for all activities that occur under the account. You must comply with the terms of service of all connected social media platforms.
                        </p>
                    </section>
                </div>
            </div>
        </DashboardLayout>
    );
}
