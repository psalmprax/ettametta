"use client";

import React, { useState } from "react";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import { Button } from "@/components/ui/Button";

export function VoiceForgePanel() {
    const [text, setText] = useState("");
    const [voice, setVoice] = useState("alloy");
    const [isGenerating, setIsGenerating] = useState(false);
    const [audioUrl, setAudioUrl] = useState<string | null>(null);

    const handleGenerate = async () => {
        if (!text) {
            toast.error("Text input required");
            return;
        }
        setIsGenerating(true);
        const token = getAuthToken();
        if (!token) {
            setIsGenerating(false);
            return;
        }

        try {
            const response = await fetch(`${API_BASE}/tools/prompt/template`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ text, voice })
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.url) setAudioUrl(data.url);
                toast.success("Voice template generated");
            } else {
                toast.error("Failed to generate voice");
            }
        } catch (error) {
            console.error("Voice generation error:", error);
            toast.error("Voice generation error");
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <div className="h-full min-h-[400px] flex flex-col border border-white/5 bg-[#0F0F11]/60 rounded-[40px] p-8 space-y-6">
            <div className="flex items-center justify-between border-b border-white/5 pb-4">
                <h3 className="text-[10px] font-bold text-violet-400 tracking-[0.2em] uppercase">Voice Forge Core</h3>
                <span className="text-[8px] font-mono text-zinc-600">NEURAL_AUDIO_SYNTHESIS_HUB_ACTIVE</span>
            </div>

            <div className="space-y-4">
                <div>
                    <label htmlFor="inputText" className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-2 block">Input Text</label>
                    <textarea
                        id="inputText"
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        placeholder="Enter text to synthesize..."
                        className="w-full h-32 bg-black/20 border border-white/10 rounded-xl p-4 text-sm text-white placeholder:text-zinc-600 focus:outline-none focus:border-violet-500/50 resize-none"
                    />
                </div>

                <div>
                    <label htmlFor="voiceModel" className="text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-2 block">Voice Model</label>
                    <select
                        id="voiceModel"
                        value={voice}
                        onChange={(e) => setVoice(e.target.value)}
                        className="w-full bg-black/20 border border-white/10 rounded-xl p-3 text-sm text-white focus:outline-none focus:border-violet-500/50"
                    >
                        <option value="alloy">Alloy</option>
                        <option value="echo">Echo</option>
                        <option value="fable">Fable</option>
                        <option value="onyx">Onyx</option>
                        <option value="nova">Nova</option>
                        <option value="shimmer">Shimmer</option>
                    </select>
                </div>

                <Button
                    onClick={handleGenerate}
                    disabled={isGenerating || !text}
                    className="w-full h-14 bg-violet-500 hover:bg-violet-400 text-white font-bold text-sm rounded-xl transition-all uppercase tracking-widest"
                >
                    {isGenerating ? "Synthesizing..." : "Generate Voice"}
                </Button>

                {audioUrl && (
                    <div className="mt-4 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
                        <audio controls src={audioUrl} className="w-full">
                            <track kind="captions" />
                        </audio>
                    </div>
                )}
            </div>
        </div>
    );
}
