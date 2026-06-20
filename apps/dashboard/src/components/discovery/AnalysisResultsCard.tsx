"use client";

import React, { memo, useState } from "react";
import {
    Brain,
    Flame,
    Gauge,
    Smile,
    FileText,
    ChevronDown,
    ChevronUp,
    Play,
    Sparkles,
    TrendingUp,
    Zap,
    Target,
    Palette,
    Waves,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

// ── AnalysisReport types (mirrors backend schemas.py) ──────────────────────

/** Module-internal — do not consume from outside. */
interface HookInsights {
    first_3_seconds: string;
    emotional_angle: string;
    scroll_stopper: boolean;
}

/** Module-internal — do not consume from outside. */
interface PacingInsights {
    bpm: number;
    cuts_per_minute: number;
    recommended_duration_s: number;
}

/** Module-internal — do not consume from outside. */
interface StructureInsights {
    arc: string[];
    act_breaks: string[];
    retention_curve: number[];
}

/** Module-internal — do not consume from outside. */
interface StyleInsights {
    recommended_style: string;
    motion_graphics: string[];
    color_palette?: string[];
    typography?: string;
}

/** Module-internal — do not consume from outside. */
interface SentimentInsights {
    overall: string;
    emotional_triggers: string[];
    target_audience: string;
}

export interface AnalysisReportData {
    candidate_id: string;
    hook: HookInsights;
    pacing: PacingInsights;
    structure: StructureInsights;
    style: StyleInsights;
    sentiment: SentimentInsights;
    summary: string;
    viral_score: number;
    confidence: number;
}

// ── Props ──────────────────────────────────────────────────────────────────

/** Module-internal — do not consume from outside. */
interface AnalysisResultsCardProps {
    report: AnalysisReportData;
    isLoading?: boolean;
    onClose?: () => void;
    onCreateVideo?: (contentId: string) => void;
}

// ── Sub-components ─────────────────────────────────────────────────────────

/** Module-internal — do not consume from outside. */
const SectionHeader = memo(function SectionHeader({
    icon: Icon,
    label,
}: {
    readonly icon: any;
    readonly label: string;
}) {
    return (
        <div className="flex items-center gap-2 mb-3">
            <Icon className="h-4 w-4 text-primary" />
            <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest">
                {label}
            </span>
        </div>
    );
});

/** Module-internal — do not consume from outside. */
const ScoreRing = memo(function ScoreRing({
    score,
    label,
    color,
    max = 100,
}: {
    readonly score: number;
    readonly label: string;
    readonly color: string;
    readonly max?: number;
}) {
    const pct = max > 0 ? Math.min(100, Math.max(0, (score / max) * 100)) : 0;
    const circumference = 2 * Math.PI * 28;
    const offset = circumference - (pct / 100) * circumference;

    return (
        <div className="flex flex-col items-center gap-1">
            <div className="relative w-[72px] h-[72px] flex items-center justify-center">
                <svg className="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 64 64">
                    <circle
                        cx="32"
                        cy="32"
                        r="28"
                        fill="none"
                        stroke="rgba(255,255,255,0.05)"
                        strokeWidth="4"
                    />
                    <circle
                        cx="32"
                        cy="32"
                        r="28"
                        fill="none"
                        stroke={color}
                        strokeWidth="4"
                        strokeLinecap="round"
                        strokeDasharray={circumference}
                        strokeDashoffset={offset}
                        className="transition-all duration-1000 ease-out"
                    />
                </svg>
                <span className={cn("text-xl font-bold z-10", color.replace("stroke", "text"))}>
                    {Math.round(score)}
                </span>
            </div>
            <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-wider">
                {label}
            </span>
        </div>
    );
});

// ── Main Component ─────────────────────────────────────────────────────────

export const AnalysisResultsCard = memo<AnalysisResultsCardProps>(
    function AnalysisResultsCard({ report, isLoading, onClose, onCreateVideo }) {
        const [expanded, setExpanded] = useState(false);
        const [showFullSummary, setShowFullSummary] = useState(false);

        if (isLoading) {
            return (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="glass-card p-6 space-y-4 animate-pulse"
                >
                    <div className="h-6 bg-zinc-800 rounded w-2/3" />
                    <div className="grid grid-cols-2 gap-4">
                        <div className="h-20 bg-zinc-800 rounded-xl" />
                        <div className="h-20 bg-zinc-800 rounded-xl" />
                    </div>
                    <div className="space-y-2">
                        <div className="h-3 bg-zinc-800 rounded w-full" />
                        <div className="h-3 bg-zinc-800 rounded w-3/4" />
                    </div>
                </motion.div>
            );
        }

        const viralColor =
            report.viral_score >= 80
                ? "stroke-red-500"
                : report.viral_score >= 60
                  ? "stroke-yellow-500"
                  : "stroke-green-500";

        const viralTextColor =
            report.viral_score >= 80
                ? "text-red-500"
                : report.viral_score >= 60
                  ? "text-yellow-500"
                  : "text-green-500";

        const viralBg =
            report.viral_score >= 80
                ? "bg-red-500/10 border-red-500/20"
                : report.viral_score >= 60
                  ? "bg-yellow-500/10 border-yellow-500/20"
                  : "bg-green-500/10 border-green-500/20";

        const ViralIcon =
            report.viral_score >= 80
                ? Flame
                : report.viral_score >= 60
                  ? Sparkles
                  : TrendingUp;

        return (
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="glass-card overflow-hidden"
            >
                {/* ── Header ─────────────────────────────────────────────────── */}
                <div className="p-6 border-b border-white/5 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center">
                            <Brain className="h-5 w-5 text-violet-400" />
                        </div>
                        <div>
                            <h3 className="text-sm font-bold text-white uppercase tracking-tight">
                                AI Analysis Report
                            </h3>
                            <p className="text-[10px] text-zinc-500 font-mono">
                                {report.candidate_id?.slice(0, 16)}...
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <div
                            className={cn(
                                "flex items-center gap-1.5 px-3 py-1.5 rounded-full border",
                                viralBg
                            )}
                        >
                            <ViralIcon className={cn("h-3.5 w-3.5", viralTextColor)} />
                            <span
                                className={cn(
                                    "text-[10px] font-bold uppercase",
                                    viralTextColor
                                )}
                            >
                                {report.viral_score >= 80
                                    ? "VIRAL"
                                    : report.viral_score >= 60
                                      ? "HOT"
                                      : "TRENDING"}
                            </span>
                        </div>
                        {onClose && (
                            <button
                                onClick={onClose}
                                className="p-2 rounded-lg hover:bg-white/5 text-zinc-500 hover:text-zinc-300 transition-colors"
                            >
                                ✕
                            </button>
                        )}
                    </div>
                </div>

                {/* ── Scores Row ────────────────────────────────────────────── */}
                <div className="p-6 border-b border-white/5">
                    <div className="flex items-center justify-around">
                        <ScoreRing
                            score={report.viral_score}
                            label="Viral Score"
                            color={viralColor}
                        />
                        <div className="h-12 w-px bg-white/5" />
                        <ScoreRing
                            score={Math.round(report.confidence * 100)}
                            label="Confidence"
                            color="stroke-violet-500"
                            max={100}
                        />
                        <div className="h-12 w-px bg-white/5" />
                        <div className="flex flex-col items-center gap-1">
                            <div className="w-[72px] h-[72px] flex flex-col items-center justify-center">
                                <Gauge className="h-5 w-5 text-cyan-400 mb-1" />
                                <span className="text-lg font-bold text-cyan-400">
                                    {report.pacing.bpm}
                                </span>
                            </div>
                            <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-wider">
                                BPM
                            </span>
                        </div>
                    </div>
                </div>

                {/* ── Hook Section ─────────────────────────────────────────────── */}
                <div className="p-6 border-b border-white/5 space-y-4">
                    <SectionHeader icon={Zap} label="Hook (First 3 Seconds)" />
                    <div className="bg-white/[0.02] rounded-xl p-4 border border-white/5">
                        <p className="text-sm text-zinc-300 leading-relaxed italic">
                            &ldquo;{report.hook.first_3_seconds}&rdquo;
                        </p>
                    </div>
                    <div className="flex items-center gap-6 text-xs">
                        <div className="flex items-center gap-2">
                            <Smile className="h-3.5 w-3.5 text-amber-400" />
                            <span className="text-zinc-500">Angle:</span>
                            <span className="text-zinc-300 font-medium capitalize">
                                {report.hook.emotional_angle}
                            </span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-zinc-500">Scroll Stopper:</span>
                            <span
                                className={cn(
                                    "px-2 py-0.5 rounded text-[10px] font-bold uppercase",
                                    report.hook.scroll_stopper
                                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                        : "bg-zinc-500/10 text-zinc-400 border border-zinc-500/20"
                                )}
                            >
                                {report.hook.scroll_stopper ? "YES ✓" : "NO"}
                            </span>
                        </div>
                    </div>
                </div>

                {/* ── Pacing & Structure Row ─────────────────────────────────── */}
                <div className="p-6 border-b border-white/5">
                    <div className="grid grid-cols-2 gap-6">
                        <div className="space-y-3">
                            <SectionHeader icon={Gauge} label="Pacing" />
                            <div className="space-y-2">
                                <div className="flex justify-between text-xs">
                                    <span className="text-zinc-500">Cuts/min</span>
                                    <span className="text-zinc-300 font-mono">
                                        {report.pacing.cuts_per_minute}
                                    </span>
                                </div>
                                <div className="flex justify-between text-xs">
                                    <span className="text-zinc-500">
                                        Recommended Duration
                                    </span>
                                    <span className="text-zinc-300 font-mono">
                                        {report.pacing.recommended_duration_s}s
                                    </span>
                                </div>
                            </div>
                        </div>
                        <div className="space-y-3">
                            <SectionHeader icon={Waves} label="Structure" />
                            <div className="flex flex-wrap gap-1.5">
                                {report.structure.arc.map((step, i) => (
                                    <span
                                        key={i}
                                        className="px-2 py-0.5 rounded bg-primary/10 border border-primary/20 text-[10px] font-bold text-primary uppercase"
                                    >
                                        {step}
                                    </span>
                                ))}
                            </div>
                            {report.structure.retention_curve.length > 0 && (
                                <div className="flex items-end gap-0.5 h-8 mt-2">
                                    {report.structure.retention_curve.map(
                                        (v, i) => (
                                            <div
                                                key={i}
                                                className="flex-1 rounded-t-sm bg-primary/30"
                                                style={{
                                                    height: `${Math.round(v * 100)}%`,
                                                }}
                                                title={`${Math.round(v * 100)}%`}
                                            />
                                        )
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* ── Style & Sentiment Row ──────────────────────────────────── */}
                <div className="p-6 border-b border-white/5">
                    <div className="grid grid-cols-2 gap-6">
                        <div className="space-y-3">
                            <SectionHeader icon={Palette} label="Style" />
                            <div className="flex items-center gap-2">
                                <span className="text-xs text-zinc-500">Recommended:</span>
                                <span className="px-2 py-0.5 rounded bg-violet-500/10 border border-violet-500/20 text-[10px] font-bold text-violet-400 uppercase">
                                    {report.style.recommended_style}
                                </span>
                            </div>
                            {report.style.motion_graphics.length > 0 && (
                                <div className="flex flex-wrap gap-1">
                                    {report.style.motion_graphics.map((mg, i) => (
                                        <span
                                            key={i}
                                            className="px-1.5 py-0.5 rounded bg-white/5 text-[9px] text-zinc-400"
                                        >
                                            {mg}
                                        </span>
                                    ))}
                                </div>
                            )}
                        </div>
                        <div className="space-y-3">
                            <SectionHeader icon={Target} label="Sentiment & Audience" />
                            <div className="flex items-center gap-2 text-xs">
                                <span className="text-zinc-500">Overall:</span>
                                <span
                                    className={cn(
                                        "px-2 py-0.5 rounded text-[10px] font-bold uppercase",
                                        report.sentiment.overall === "positive"
                                            ? "bg-emerald-500/10 text-emerald-400"
                                            : report.sentiment.overall === "negative"
                                              ? "bg-rose-500/10 text-rose-400"
                                              : "bg-amber-500/10 text-amber-400"
                                    )}
                                >
                                    {report.sentiment.overall}
                                </span>
                            </div>
                            <div className="text-xs">
                                <span className="text-zinc-500">Audience: </span>
                                <span className="text-zinc-300">
                                    {report.sentiment.target_audience}
                                </span>
                            </div>
                            {report.sentiment.emotional_triggers.length > 0 && (
                                <div className="flex flex-wrap gap-1">
                                    {report.sentiment.emotional_triggers.map((t, i) => (
                                        <span
                                            key={i}
                                            className="px-1.5 py-0.5 rounded bg-amber-500/10 border border-amber-500/20 text-[9px] text-amber-400"
                                        >
                                            {t}
                                        </span>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* ── Summary ──────────────────────────────────────────────────── */}
                <div className="p-6 border-b border-white/5 space-y-3">
                    <button
                        onClick={() => setShowFullSummary(!showFullSummary)}
                        className="flex items-center gap-2 w-full"
                    >
                        <SectionHeader icon={FileText} label="AI Summary" />
                        <ChevronDown
                            className={cn(
                                "h-3.5 w-3.5 text-zinc-500 ml-auto transition-transform",
                                showFullSummary && "rotate-180"
                            )}
                        />
                    </button>
                    <p
                        className={cn(
                            "text-xs text-zinc-400 leading-relaxed",
                            !showFullSummary && "line-clamp-3"
                        )}
                    >
                        {report.summary}
                    </p>
                </div>

                {/* ── Expandable Details ──────────────────────────────────────── */}
                <div className="p-6">
                    <button
                        onClick={() => setExpanded(!expanded)}
                        className="flex items-center gap-2 text-[10px] font-bold text-zinc-500 uppercase tracking-wider hover:text-zinc-300 transition-colors w-full"
                    >
                        {expanded ? (
                            <ChevronUp className="h-3 w-3" />
                        ) : (
                            <ChevronDown className="h-3 w-3" />
                        )}
                        {expanded ? "Hide details" : "Show all details"}
                    </button>
                    <AnimatePresence>
                        {expanded && (
                            <motion.div
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: "auto", opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                className="overflow-hidden"
                            >
                                <div className="pt-4 grid grid-cols-2 gap-4 text-[10px]">
                                    {report.style.color_palette &&
                                        report.style.color_palette.length > 0 && (
                                            <div className="space-y-1.5">
                                                <span className="text-zinc-500 font-bold uppercase">
                                                    Color Palette
                                                </span>
                                                <div className="flex gap-1">
                                                    {report.style.color_palette.map(
                                                        (c, i) => (
                                                            <div
                                                                key={i}
                                                                className="w-5 h-5 rounded border border-white/10"
                                                                style={{
                                                                    backgroundColor: c,
                                                                }}
                                                                title={c}
                                                            />
                                                        )
                                                    )}
                                                </div>
                                            </div>
                                        )}
                                    {report.style.typography && (
                                        <div className="space-y-1.5">
                                            <span className="text-zinc-500 font-bold uppercase">
                                                Typography
                                            </span>
                                            <span className="text-zinc-300 font-mono">
                                                {report.style.typography}
                                            </span>
                                        </div>
                                    )}
                                    {report.structure.act_breaks.length > 0 && (
                                        <div className="col-span-2 space-y-1.5">
                                            <span className="text-zinc-500 font-bold uppercase">
                                                Act Breaks
                                            </span>
                                            <div className="flex gap-1.5">
                                                {report.structure.act_breaks.map(
                                                    (b, i) => (
                                                        <span
                                                            key={i}
                                                            className="px-2 py-0.5 rounded bg-white/5 text-zinc-400 font-mono"
                                                        >
                                                            {b}
                                                        </span>
                                                    )
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* ── Actions ──────────────────────────────────────────────────── */}
                {onCreateVideo && (
                    <div className="p-6 pt-0 flex gap-3">
                        <button
                            onClick={() => onCreateVideo(report.candidate_id)}
                            className="flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-violet-500 hover:bg-violet-400 text-black font-bold text-sm uppercase tracking-wider transition-all hover:shadow-[0_0_20px_rgba(139,92,246,0.3)]"
                        >
                            <Play className="h-4 w-4" />
                            Create Video
                        </button>
                    </div>
                )}
            </motion.div>
        );
    }
);


