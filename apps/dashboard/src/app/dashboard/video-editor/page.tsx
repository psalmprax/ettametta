"use client";

import React, { useState } from "react";
import { 
    Video, 
    Upload, 
    ChevronDown, 
    Sparkles, 
    Play, 
    Plus,
    ChevronLeft,
    ChevronRight,
    Image as ImageIcon
} from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/Button";

const thumbnails = [
    { id: 1, src: "https://api.dicebear.com/7.x/avataaars/svg?seed=1" },
    { id: 2, src: "https://api.dicebear.com/7.x/avataaars/svg?seed=2" },
    { id: 3, src: "https://api.dicebear.com/7.x/avataaars/svg?seed=3", active: true },
    { id: 4, src: "https://api.dicebear.com/7.x/avataaars/svg?seed=4" },
    { id: 5, src: "https://api.dicebear.com/7.x/avataaars/svg?seed=5" },
];

import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import { useRouter } from "next/navigation";

export default function VideoEditorPage() {
    const router = useRouter();
    const [model, setModel] = useState("V2.0");
    const [resolution, setResolution] = useState("720P");
    const [prompt, setPrompt] = useState("");
    const [isGenerating, setIsGenerating] = useState(false);

    const handleCreate = async () => {
        if (!prompt) {
            toast.error("Please enter a prompt first");
            return;
        }
        setIsGenerating(true);
        try {
            const token = await getAuthToken();
            const res = await fetch(`${API_BASE}/video/launch-cinema`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ 
                    topic: prompt,
                    style: "story", // Default for now
                    duration_seconds: 60,
                    niche: "Motivation"
                })
            });
            
            if (!res.ok) throw new Error("Synthesis failure");
            
            toast.success("Cinema Sequence Initiated");
            router.push("/transformation"); // Redirect to jobs view
        } catch (err) {
            console.error(err);
            toast.error("Neural Link Failed");
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <div className="flex flex-col lg:flex-row gap-8 h-full animate-fade-in">
            {/* Editor Column */}
            <div className="flex-1 flex flex-col gap-6">
                <div className="flex items-center gap-3">
                    <h1 className="text-2xl font-bold text-white">Ettametta Video Editor</h1>
                </div>

                <div className="flex-1 flex flex-col gap-4 bg-slate-900/40 border border-white/5 rounded-3xl p-6">
                    {/* Upload Area */}
                    <div className="relative group cursor-pointer h-72 border-2 border-dashed border-white/10 hover:border-blue-500/50 rounded-2xl flex flex-col items-center justify-center gap-4 transition-all bg-black/20">
                        <div className="h-12 w-12 rounded-full bg-white/5 flex items-center justify-center group-hover:scale-110 transition-transform">
                            <Video className="h-6 w-6 text-slate-400 group-hover:text-blue-500" />
                        </div>
                        <div className="text-center">
                            <p className="text-sm font-semibold text-white">Upload a video you want to edit</p>
                            <p className="text-[10px] text-slate-500 mt-1 uppercase tracking-wider">(&lt;30M, 18s duration, &le;10s)</p>
                        </div>
                        <input type="file" className="absolute inset-0 opacity-0 cursor-pointer" />
                    </div>

                    {/* Description Area */}
                    <div className="flex-1 flex flex-col gap-2">
                        <textarea 
                            value={prompt}
                            onChange={(e) => setPrompt(e.target.value)}
                            className="flex-1 bg-black/40 border border-white/10 rounded-xl p-4 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-blue-500/50 transition-all resize-none"
                            placeholder="Describe your edits (add, remove, replace). Use the brush to mark areas or upload a reference image to specify changes."
                        />
                    </div>

                    {/* Settings & Create */}
                    <div className="flex flex-col gap-4">
                        <div className="flex gap-4">
                            <div className="flex-1 relative group">
                                <select 
                                    value={model} 
                                    onChange={(e) => setModel(e.target.value)}
                                    className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-xs font-bold text-white appearance-none focus:outline-none focus:border-blue-500/50"
                                >
                                    <option>V2.0</option>
                                    <option>V1.5</option>
                                </select>
                                <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500 pointer-events-none" />
                            </div>
                            <div className="flex-1 relative group">
                                <select 
                                    value={resolution} 
                                    onChange={(e) => setResolution(e.target.value)}
                                    className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-xs font-bold text-white appearance-none focus:outline-none focus:border-blue-500/50"
                                >
                                    <option>720P</option>
                                    <option>1080P</option>
                                    <option>4K</option>
                                </select>
                                <ChevronDown className="absolute right-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500 pointer-events-none" />
                            </div>
                        </div>

                        <Button 
                            onClick={handleCreate}
                            disabled={isGenerating || !prompt}
                            className={cn(
                                "w-full py-4 font-bold rounded-xl flex items-center justify-center gap-2 border border-white/5 transition-all",
                                isGenerating || !prompt ? "bg-slate-800 text-slate-500" : "bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/20"
                            )}
                        >
                            {isGenerating ? "Processing..." : "Create"}
                            {!isGenerating && (
                                <div className="flex items-center gap-1.5 ml-2">
                                    <Sparkles className="h-3.5 w-3.5 fill-current" />
                                    <span>0</span>
                                </div>
                            )}
                        </Button>
                    </div>
                </div>
            </div>

            {/* Preview Column */}
            <div className="flex-1 flex flex-col gap-6">
                <div className="flex items-center gap-3">
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">Sample Video</span>
                </div>

                <div className="flex-1 flex flex-col bg-slate-900/40 border border-white/5 rounded-3xl overflow-hidden p-2">
                    {/* Video Player */}
                    <div className="relative flex-1 bg-black rounded-2xl overflow-hidden flex items-center justify-center group">
                        <img 
                            src="https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=800&auto=format&fit=crop" 
                            alt="Preview" 
                            className="w-full h-full object-cover opacity-80"
                        />
                        
                        {/* Caption Overlay */}
                        <div className="absolute bottom-12 left-0 w-full text-center px-8">
                            <p className="text-lg font-medium text-white drop-shadow-lg">
                                Let the man in the picture walk to the left of this woman
                            </p>
                        </div>

                        {/* Floating Image Overlay */}
                        <div className="absolute right-8 top-1/2 -translate-y-1/2 w-24 h-32 rounded-lg border-2 border-rose-500/50 overflow-hidden rotate-12 shadow-2xl shadow-black/50">
                             <img 
                                src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&auto=format&fit=crop" 
                                alt="Ref" 
                                className="w-full h-full object-cover"
                            />
                        </div>

                        {/* Play Overlay */}
                        <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/20">
                            <div className="h-16 w-16 rounded-full bg-white/20 backdrop-blur-md flex items-center justify-center border border-white/30">
                                <Play className="h-8 w-8 text-white fill-current" />
                            </div>
                        </div>
                    </div>

                    {/* Thumbnails Section */}
                    <div className="p-4 flex items-center gap-4">
                        <button className="text-slate-500 hover:text-white transition-colors">
                            <ChevronLeft className="h-6 w-6" />
                        </button>
                        
                        <div className="flex-1 flex gap-3 overflow-x-hidden">
                            {thumbnails.map((thumb) => (
                                <div 
                                    key={thumb.id}
                                    className={cn(
                                        "relative shrink-0 w-24 h-24 rounded-xl overflow-hidden border-2 transition-all cursor-pointer",
                                        thumb.active ? "border-blue-500 scale-105 shadow-lg shadow-blue-500/20" : "border-transparent opacity-60 hover:opacity-100"
                                    )}
                                >
                                    <img src={thumb.src} alt="thumb" className="w-full h-full object-cover" />
                                    {thumb.active && (
                                        <div className="absolute inset-0 bg-blue-600/20 flex items-center justify-center">
                                            <div className="bg-blue-600 px-3 py-1 rounded-full flex items-center gap-2">
                                                <Play className="h-3 w-3 text-white fill-current" />
                                                <span className="text-[10px] font-bold text-white uppercase">Create</span>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>

                        <button className="text-slate-500 hover:text-white transition-colors">
                            <ChevronRight className="h-6 w-6" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
