"use client";

import React, { useState } from "react";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { withRealFallback } from "@/lib/real_first_utils";
import { ScriptOutput } from "@/lib/types";
import { toast } from "sonner";
import { Button } from "@/components/ui/Button";

export const NEXUS_STYLE_OPTIONS = [
    { id: "CINEMATIC_DOC", label: "Cinematic Doc" },
    { id: "FAST_HYPE", label: "Fast Hype" },
    { id: "REDDIT_STORY", label: "Reddit Story" },
    { id: "ULTIMATE_TUTORIAL", label: "Tutorial" },
    { id: "VOX_EXPLAINER", label: "Vox Explainer" },
    { id: "NOIR_MYSTERY", label: "Noir Mystery" },
    { id: "BROADCAST_NEWS", label: "Broadcast News" },
    { id: "MOTIVATIONAL", label: "Motivational" },
    { id: "FITNESS_MOTIVATION", label: "Fitness" },
    { id: "GAMING_LORE", label: "Gaming Lore" },
    { id: "RELATIONSHIP_DRAMA", label: "Relationship Drama" },
    { id: "STOIC_WISDOM", label: "Stoic Wisdom" },
];

export function ScriptEnginePanel() {
    const [topic, setTopic] = useState("");
    const [niche, setNiche] = useState("Auto-Detect");
    const [style, setStyle] = useState("CINEMATIC_DOC");
    const [duration, setDuration] = useState(60);
    const [isGenerating, setIsGenerating] = useState(false);
    const [script, setScript] = useState<ScriptOutput | null>(null);

    const handleGenerate = async () => {
        if (!topic) {
            toast.error("Topic required");
            return;
        }
        setIsGenerating(true);
        const token = getAuthToken();
        if (!token) {
            setIsGenerating(false);
            return;
        }

        // Send null for niche to trigger auto-detection
        const nichePayload = niche === "Auto-Detect" ? null : niche;

        await withRealFallback<ScriptOutput>((signal) => fetch(`${API_BASE}/no-face/script`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ topic, niche: nichePayload, style, duration_seconds: duration })
            }),
            {
                fallback: {} as ScriptOutput,
                onSuccess: (data) => {
                    setScript(data);
                    toast.success("Script generated successfully");
                },
                onFallback: (err) => {
                    toast.error(`Script generation failed: ${err.message}`);
                }
            }
        );
        setIsGenerating(false);
    };

    return (
        <div className="h-full min-h-[400px] flex flex-col border border-white/5 bg-[#0F0F11]/60 rounded-[40px] p-8 space-y-6">
            <div className="flex items-center justify-between border-b border-white/5 pb-4">
                <h3 className="text-[10px] font-bold text-violet-400 tracking-[0.2em] uppercase">Script Synthesis Engine</h3>
                <span className="text-[8px] font-mono text-zinc-600">LLM_ORCHESTRATION_LAYER_READY</span>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                    <label htmlFor="scriptTopic" className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-2 block">Topic</label>
                    <input
                        id="scriptTopic"
                        type="text"
                        value={topic}
                        onChange={(e) => setTopic(e.target.value)}
                        placeholder="Enter video topic..."
                        className="w-full bg-black/20 border border-white/10 rounded-xl p-3 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-violet-500/50"
                    />
                </div>

                <div>
                    <label htmlFor="scriptNiche" className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-2 block">Niche</label>
                    <select
                        id="scriptNiche"
                        value={niche}
                        onChange={(e) => setNiche(e.target.value)}
                        className="w-full bg-black/20 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-violet-500/50"
                    >
                        <option value="Auto-Detect">✨ Auto-Detect (Recommended)</option>
                        <option value="Motivation">Motivation</option>
                        <option value="Tech">Tech</option>
                        <option value="Finance">Finance</option>
                        <option value="Health">Health</option>
                        <option value="Gaming">Gaming</option>
                        <option value="Education">Education</option>
                        <option value="Social Commentary">Social Commentary</option>
                        <option value="Entertainment">Entertainment</option>
                        <option value="Lifestyle">Lifestyle</option>
                        <option value="Spirituality">Spirituality</option>
                    </select>
                </div>

                <div>
                    <label htmlFor="scriptDuration" className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-2 block">Duration (seconds)</label>
                    <input
                        id="scriptDuration"
                        type="number"
                        value={duration}
                        onChange={(e) => setDuration(Number(e.target.value))}
                        min={15}
                        max={300}
                        className="w-full bg-black/20 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-violet-500/50"
                    />
                </div>

                <div className="col-span-2">
                    <label htmlFor="scriptStyle" className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-2 block">Nexus Style</label>
                    <select
                        id="scriptStyle"
                        value={style}
                        onChange={(e) => setStyle(e.target.value)}
                        className="w-full bg-black/20 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-violet-500/50"
                    >
                        {NEXUS_STYLE_OPTIONS.map(option => (
                            <option key={option.id} value={option.id}>{option.label}</option>
                        ))}
                    </select>
                </div>
            </div>

            <Button
                onClick={handleGenerate}
                disabled={isGenerating || !topic}
                className="w-full h-14 bg-violet-500 hover:bg-violet-400 text-white font-bold text-sm rounded-xl transition-all uppercase tracking-widest"
            >
                {isGenerating ? "Synthesizing..." : "Generate Script"}
            </Button>

            {script && (
                <div className="flex-1 overflow-y-auto custom-scrollbar p-4 bg-black/20 rounded-xl border border-white/5">
                    <h4 className="text-sm font-bold text-white mb-2">{script.title}</h4>
                    <div className="space-y-2">
                        {script.segments?.map((segment, i) => (
                            <div key={i} className="p-3 bg-white/5 rounded-lg">
                                <p className="text-xs text-zinc-300">{segment.text}</p>
                                <span className="text-[8px] text-zinc-500 mt-1 block">{segment.duration}s</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
