"use client";

import React, { useState, useCallback, memo } from "react";
import { Play, Loader2, Globe, BarChart3, Clock, CheckCircle2, X, Sparkles, Flame, BookOpen, Calendar, MessageSquare, Newspaper } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { VideoPreviewModal } from "@/components/ui/VideoPreviewModal";

// Types
interface ContentCandidate {
    id: string;
    platform: string;
    category: string;
    description: string;
    thumbnail_url: string;
    view_count: number;
    engagement_score: number;
    viral_score: number;
    published_at: string;
    creator_name: string;
    source_url: string;
    duration_seconds: number;
    title: string;
}

interface CandidateListProps {
    candidates: ContentCandidate[];
    isLoading: boolean;
    onSelectCandidate: (candidate: ContentCandidate) => void;
    onRefresh: () => void;
}

export const CandidateList = memo<CandidateListProps>(function CandidateList({
    candidates,
    isLoading,
    onSelectCandidate,
    onRefresh
}) {
    const [selectedCandidate, setSelectedCandidate] = useState<ContentCandidate | null>(null);
    const [showPreview, setShowPreview] = useState(false);

    const handlePreview = useCallback((candidate: ContentCandidate) => {
        setSelectedCandidate(candidate);
        setShowPreview(true);
    }, []);

    const getCategoryIcon = (category: string) => {
        switch (category) {
            case "video": return <Play className="h-4 w-4" />;
            case "blog": return <BookOpen className="h-4 w-4" />;
            case "social": return <MessageSquare className="h-4 w-4" />;
            case "news": return <Newspaper className="h-4 w-4" />;
            default: return <Globe className="h-4 w-4" />;
        }
    };

    const formatDuration = (seconds: number) => {
        if (seconds < 60) return `${seconds}s`;
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    };

    const getViralBadge = (score: number) => {
        if (score >= 90) return { icon: Flame, color: "text-red-500", bg: "bg-red-500/10", label: "🔥 VIRAL" };
        if (score >= 75) return { icon: Sparkles, color: "text-yellow-500", bg: "bg-yellow-500/10", label: "✨ HOT" };
        if (score >= 50) return { icon: BarChart3, color: "text-green-500", bg: "bg-green-500/10", label: "📈 TRENDING" };
        return { icon: Clock, color: "text-zinc-500", bg: "bg-zinc-500/10", label: "⏰ EMERGING" };
    };

    if (isLoading) {
        return (
            <div className="space-y-4">
                {[...Array(6)].map((_, i) => (
                    <motion.div
                        key={i}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className="glass-card p-4 animate-pulse"
                    >
                        <div className="flex items-start space-x-4">
                            <div className="w-24 h-16 bg-zinc-800 rounded-lg"></div>
                            <div className="flex-1 space-y-2">
                                <div className="h-4 bg-zinc-800 rounded w-3/4"></div>
                                <div className="h-3 bg-zinc-800 rounded w-1/2"></div>
                                <div className="flex space-x-2">
                                    <div className="h-6 bg-zinc-800 rounded w-16"></div>
                                    <div className="h-6 bg-zinc-800 rounded w-12"></div>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                ))}
            </div>
        );
    }

    return (
        <>
            <div className="space-y-4">
                <AnimatePresence>
                    {candidates.map((candidate, index) => {
                        const viralBadge = getViralBadge(candidate.viral_score);
                        const ViralIcon = viralBadge.icon;

                        return (
                            <motion.div
                                key={candidate.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                transition={{ delay: index * 0.05 }}
                                className="glass-card p-4 hover:bg-zinc-900/50 transition-all duration-300 group cursor-pointer"
                                onClick={() => onSelectCandidate(candidate)}
                            >
                                <div className="flex items-start space-x-4">
                                    <div className="relative">
                                        <div 
                                            className="w-24 h-16 bg-cover bg-center rounded-lg group-hover:scale-105 transition-transform"
                                            style={{ backgroundImage: `url(${candidate.thumbnail_url})` }}
                                            role="img"
                                            aria-label={candidate.title}
                                        />
                                        <div className="absolute inset-0 bg-black/50 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                            <Play className="h-6 w-6 text-white" />
                                        </div>
                                        <div className="absolute bottom-1 right-1 bg-black/80 text-white text-xs px-1 py-0.5 rounded">
                                            {formatDuration(candidate.duration_seconds)}
                                        </div>
                                    </div>

                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-start justify-between">
                                            <div className="flex-1 min-w-0">
                                                <h3 className="text-white font-semibold text-sm truncate group-hover:text-primary transition-colors">
                                                    {candidate.title}
                                                </h3>
                                                <p className="text-zinc-400 text-xs mt-1 line-clamp-2">
                                                    {candidate.description}
                                                </p>
                                            </div>
                                            <div className="flex items-center space-x-2 ml-4">
                                                <div className={cn(
                                                    "px-2 py-1 rounded-full text-xs font-bold flex items-center gap-1",
                                                    viralBadge.bg,
                                                    viralBadge.color
                                                )}>
                                                    <ViralIcon className="h-3 w-3" />
                                                    {viralBadge.label}
                                                </div>
                                            </div>
                                        </div>

                                        <div className="flex items-center justify-between mt-3">
                                            <div className="flex items-center space-x-4 text-xs text-zinc-500">
                                                <div className="flex items-center space-x-1">
                                                    {getCategoryIcon(candidate.category)}
                                                    <span className="capitalize">{candidate.category}</span>
                                                </div>
                                                <div className="flex items-center space-x-1">
                                                    <Globe className="h-3 w-3" />
                                                    <span className="capitalize">{candidate.platform}</span>
                                                </div>
                                                <div className="flex items-center space-x-1">
                                                    <BarChart3 className="h-3 w-3" />
                                                    <span>{candidate.view_count.toLocaleString()}</span>
                                                </div>
                                                <div className="flex items-center space-x-1">
                                                    <Clock className="h-3 w-3" />
                                                    <span>{new Date(candidate.published_at).toLocaleDateString()}</span>
                                                </div>
                                            </div>

                                            <div className="flex items-center space-x-2">
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handlePreview(candidate);
                                                    }}
                                                    className="p-2 rounded-lg bg-primary/10 hover:bg-primary/20 text-primary transition-colors"
                                                    title="Preview"
                                                >
                                                    <Play className="h-4 w-4" />
                                                </button>
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        onSelectCandidate(candidate);
                                                    }}
                                                    className="px-3 py-1 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-500 transition-colors text-xs font-medium"
                                                >
                                                    Select
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </motion.div>
                        );
                    })}
                </AnimatePresence>
            </div>

            <VideoPreviewModal
                isOpen={showPreview}
                onClose={() => setShowPreview(false)}
                videoUrl={selectedCandidate?.source_url || ""}
                title={selectedCandidate?.title || ""}
            />
        </>
    );
});