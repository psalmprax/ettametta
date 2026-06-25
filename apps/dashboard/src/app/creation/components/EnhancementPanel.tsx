"use client";

import React, { useState, useRef, useEffect } from "react";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { withRealFallback } from "@/lib/real_first_utils";
import { toast } from "sonner";
import { Button } from "@/components/ui/Button";
import {
    Eraser,
    Music,
    Droplets,
    ImagePlus,
    Sparkles,
    Loader2,
    ChevronDown,
    Eye,
} from "lucide-react";
import { cn } from "@/lib/utils";

/** Enhancement modes */
/** Module-internal — do not consume from outside. */
const ENHANCEMENT_MODES = [
    {
        id: "background",
        label: "Background Removal",
        icon: Eraser,
        color: "rose",
        description: "Remove or replace video background using AI",
    },
    {
        id: "sound",
        label: "Sound Design",
        icon: Music,
        color: "emerald",
        description: "Add background music or ambient soundscape",
    },
    {
        id: "watermark",
        label: "Watermark",
        icon: Droplets,
        color: "sky",
        description: "Add text, image, or animated watermark",
    },
    {
        id: "branding",
        label: "Full Branding",
        icon: ImagePlus,
        color: "amber",
        description: "Burn brand logo + name + tagline into video",
    },
] as const;

/** Module-internal — do not consume from outside. */
type Mode = (typeof ENHANCEMENT_MODES)[number]["id"];

const POSITION_OPTIONS = [
    { value: "bottom_right", label: "Bottom Right" },
    { value: "bottom_left", label: "Bottom Left" },
    { value: "top_right", label: "Top Right" },
    { value: "top_left", label: "Top Left" },
    { value: "center", label: "Center" },
];

/** Module-internal — do not consume from outside. */
const AMBIENT_STYLES = [
    { value: "ambient", label: "🌌 Ambient" },
    { value: "rain", label: "🌧️ Rain" },
    { value: "wind", label: "💨 Wind" },
    { value: "ocean", label: "🌊 Ocean" },
    { value: "fire", label: "🔥 Fireplace" },
    { value: "city", label: "🏙️ City" },
];

/** Module-internal — do not consume from outside. */
const BG_METHODS = [
    { value: "auto", label: "Auto (ML + fallback)" },
    { value: "rembg", label: "ML (rembg — best quality)" },
    { value: "chromakey", label: "Chromakey (green/blue screen)" },
    { value: "colorkey", label: "Colorkey (any solid color)" },
];

const ANIMATION_TYPES = [
    { value: "pulse", label: "Pulse" },
    { value: "fade_loop", label: "Fade Loop" },
    { value: "slide_in", label: "Slide In" },
];

/** Module-internal — do not consume from outside. */
const COLOR_HEX: Record<string, string> = {
    rose: "#f43f5e",
    emerald: "#10b981",
    sky: "#0ea5e9",
    amber: "#f59e0b",
};

const COLOR_STYLES: Record<string, { bg: string; border: string; text: string; ring: string }> = {
    rose: { bg: "bg-rose-500/10", border: "border-rose-500/20", text: "text-rose-400", ring: "focus:border-rose-500/50" },
    emerald: { bg: "bg-emerald-500/10", border: "border-emerald-500/20", text: "text-emerald-400", ring: "focus:border-emerald-500/50" },
    sky: { bg: "bg-sky-500/10", border: "border-sky-500/20", text: "text-sky-400", ring: "focus:border-sky-500/50" },
    amber: { bg: "bg-amber-500/10", border: "border-amber-500/20", text: "text-amber-400", ring: "focus:border-amber-500/50" },
};

export function EnhancementPanel() {
    const [mode, setMode] = useState<Mode>("background");
    const [videoPath, setVideoPath] = useState("");
    const [isProcessing, setIsProcessing] = useState(false);
    const [result, setResult] = useState<string | null>(null);

    // Background removal state
    const [bgMethod, setBgMethod] = useState("auto");
    const [bgColor, setBgColor] = useState("green");
    const [replaceColor, setReplaceColor] = useState("");

    // Sound design state
    const [musicPath, setMusicPath] = useState("");
    const [volume, setVolume] = useState(0.3);
    const [ambientStyle, setAmbientStyle] = useState("ambient");

    // Watermark state
    const [wmType, setWmType] = useState("text");
    const [wmText, setWmText] = useState("Created with ettametta");
    const [wmImagePath, setWmImagePath] = useState("");
    const [wmOpacity, setWmOpacity] = useState(0.3);
    const [wmPosition, setWmPosition] = useState("bottom_right");
    const [wmAnimation, setWmAnimation] = useState("pulse");

    // Branding state
    const [brandName, setBrandName] = useState("ettametta");
    const [logoPath, setLogoPath] = useState("");
    const [tagline, setTagline] = useState("");
    const [website, setWebsite] = useState("");

    // Preview state
    const [previewVisible, setPreviewVisible] = useState(false);

    const currentMode = ENHANCEMENT_MODES.find((m) => m.id === mode)!;
    const colors = COLOR_STYLES[currentMode.color];

    const handleSubmit = async () => {
        if (!videoPath) {
            toast.error("Video path required");
            return;
        }
        setIsProcessing(true);
        setResult(null);
        const token = getAuthToken();
        if (!token) {
            setIsProcessing(false);
            return;
        }

        let endpoint = "";
        let payload: Record<string, unknown> = { video_path: videoPath };

        switch (mode) {
            case "background":
                endpoint = `${API_BASE}/video/enhance/background`;
                payload = {
                    ...payload,
                    method: bgMethod,
                    color: bgColor,
                    replace_color: replaceColor || null,
                };
                break;
            case "sound":
                endpoint = `${API_BASE}/video/enhance/sound`;
                payload = {
                    ...payload,
                    music_path: musicPath || null,
                    volume,
                    ambient_style: musicPath ? null : ambientStyle,
                };
                break;
            case "watermark":
                endpoint = `${API_BASE}/video/enhance/watermark`;
                payload = {
                    ...payload,
                    type: wmType,
                    text: wmText,
                    image_path: wmImagePath || null,
                    opacity: wmOpacity,
                    position: wmPosition,
                    animation: wmType === "animated" ? wmAnimation : null,
                };
                break;
            case "branding":
                endpoint = `${API_BASE}/video/enhance/branding`;
                payload = {
                    ...payload,
                    brand_name: brandName,
                    logo_path: logoPath || null,
                    tagline: tagline || null,
                    website: website || null,
                    position: wmPosition,
                    opacity: wmOpacity,
                };
                break;
        }

        await withRealFallback<{ output_path: string } | null>(
            (signal) =>
                fetch(endpoint, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify(payload),
                    signal,
                }),
            {
                fallback: null,
                onSuccess: (data) => {
                    const outputPath = data?.output_path;
                    setResult(outputPath ?? null);
                    toast.success(`${currentMode.label} applied successfully!`);
                },
                onFallback: (err) => {
                    toast.error(`Enhancement failed: ${err.message}`);
                },
            }
        );
        setIsProcessing(false);
    };

    const inputClass = cn(
        "w-full bg-black/20 border border-white/10 rounded-xl p-3 text-sm text-white placeholder:text-zinc-600 focus:outline-none",
        colors.ring
    );
    const labelClass = "text-[10px] font-bold text-zinc-400 uppercase tracking-wider mb-2 block";

    return (
        <div className="h-full min-h-[400px] flex flex-col border border-white/5 bg-[#0F0F11]/60 rounded-[40px] p-8 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-white/5 pb-4">
                <h3
                    className={cn(
                        "text-[10px] font-bold tracking-[0.2em] uppercase",
                        colors.text
                    )}
                >
                    Video Enhancement Studio
                </h3>
                <span className="text-[8px] font-mono text-zinc-600">
                    ENHANCEMENT_PIPELINE_ACTIVE
                </span>
            </div>

            {/* Mode selector */}
            <div className="grid grid-cols-4 gap-2">
                {ENHANCEMENT_MODES.map((m) => {
                    const mColors = COLOR_STYLES[m.color];
                    return (
                        <button
                            key={m.id}
                            onClick={() => setMode(m.id)}
                            className={cn(
                                "flex flex-col items-center gap-1.5 p-3 rounded-xl border transition-all",
                                mode === m.id
                                    ? `${mColors.bg} ${mColors.border} ${mColors.text}`
                                    : "text-zinc-500 border-transparent hover:text-zinc-300 hover:bg-white/5"
                            )}
                        >
                            <m.icon className="h-4 w-4" />
                            <span className="text-[8px] font-bold uppercase tracking-wider">
                                {m.label.split(" ")[0]}
                            </span>
                        </button>
                    );
                })}
            </div>

            {/* Common: video path */}
            <div className="space-y-4">
                <div>
                    <label className={labelClass}>
                        Video Path
                        <span className="text-zinc-600 font-normal ml-1">
                            — server path or URL
                        </span>
                    </label>
                    <input
                        value={videoPath}
                        onChange={(e) => setVideoPath(e.target.value)}
                        placeholder="/data/storage/outputs/video.mp4"
                        className={inputClass}
                    />
                </div>

                {/* Mode-specific controls */}
                {mode === "background" && (
                    <>
                        <div>
                            <label className={labelClass}>Method</label>
                            <select
                                value={bgMethod}
                                onChange={(e) => setBgMethod(e.target.value)}
                                className={inputClass}
                            >
                                {BG_METHODS.map((m) => (
                                    <option key={m.value} value={m.value}>
                                        {m.label}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <label className={labelClass}>Key Color</label>
                                <select
                                    value={bgColor}
                                    onChange={(e) => setBgColor(e.target.value)}
                                    className={inputClass}
                                >
                                    <option value="green">Green Screen</option>
                                    <option value="blue">Blue Screen</option>
                                    <option value="red">Red</option>
                                    <option value="white">White</option>
                                    <option value="black">Black</option>
                                </select>
                            </div>
                            <div>
                                <label className={labelClass}>
                                    Replace Color{" "}
                                    <span className="text-zinc-600">(hex)</span>
                                </label>
                                <input
                                    value={replaceColor}
                                    onChange={(e) => setReplaceColor(e.target.value)}
                                    placeholder="#FF0000 or empty"
                                    className={inputClass}
                                />
                            </div>
                        </div>
                    </>
                )}

                {mode === "sound" && (
                    <>
                        <div>
                            <label className={labelClass}>
                                Music File Path{" "}
                                <span className="text-zinc-600">(optional)</span>
                            </label>
                            <input
                                value={musicPath}
                                onChange={(e) => setMusicPath(e.target.value)}
                                placeholder="/path/to/music.mp3 (or use ambient style)"
                                className={inputClass}
                            />
                        </div>
                        {!musicPath && (
                            <div>
                                <label className={labelClass}>Ambient Style</label>
                                <div className="grid grid-cols-3 gap-2">
                                    {AMBIENT_STYLES.map((s) => (
                                        <button
                                            key={s.value}
                                            onClick={() => setAmbientStyle(s.value)}
                                            className={cn(
                                                "p-2 rounded-xl border text-xs transition-all text-center",
                                                ambientStyle === s.value
                                                    ? `${colors.bg} ${colors.border} ${colors.text}`
                                                    : "border-white/5 text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
                                            )}
                                        >
                                            {s.label}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}
                        <div>
                            <label className={labelClass}>
                                Volume{" "}
                                <span className="text-zinc-600 font-mono">
                                    {Math.round(volume * 100)}%
                                </span>
                            </label>
                            <input
                                type="range"
                                min={0}
                                max={1}
                                step={0.05}
                                value={volume}
                                onChange={(e) => setVolume(parseFloat(e.target.value))}
                                className="w-full accent-emerald-500"
                            />
                        </div>
                    </>
                )}

                {mode === "watermark" && (
                    <>
                        <div>
                            <label className={labelClass}>Watermark Type</label>
                            <div className="grid grid-cols-3 gap-2">
                                {["text", "image", "animated"].map((t) => (
                                    <button
                                        key={t}
                                        onClick={() => setWmType(t)}
                                        className={cn(
                                            "p-2 rounded-xl border text-xs uppercase transition-all",
                                            wmType === t
                                                ? `${colors.bg} ${colors.border} ${colors.text}`
                                                : "border-white/5 text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
                                        )}
                                    >
                                        {t}
                                    </button>
                                ))}
                            </div>
                        </div>
                        {wmType === "text" && (
                            <div>
                                <label className={labelClass}>Watermark Text</label>
                                <input
                                    value={wmText}
                                    onChange={(e) => setWmText(e.target.value)}
                                    className={inputClass}
                                />
                            </div>
                        )}
                        {wmType === "image" && (
                            <div>
                                <label className={labelClass}>Image Path (PNG)</label>
                                <input
                                    value={wmImagePath}
                                    onChange={(e) => setWmImagePath(e.target.value)}
                                    placeholder="/path/to/logo.png"
                                    className={inputClass}
                                />
                            </div>
                        )}
                        {wmType === "animated" && (
                            <>
                                <div>
                                    <label className={labelClass}>Text</label>
                                    <input
                                        value={wmText}
                                        onChange={(e) => setWmText(e.target.value)}
                                        className={inputClass}
                                    />
                                </div>
                                <div>
                                    <label className={labelClass}>Animation</label>
                                    <select
                                        value={wmAnimation}
                                        onChange={(e) => setWmAnimation(e.target.value)}
                                        className={inputClass}
                                    >
                                        {ANIMATION_TYPES.map((a) => (
                                            <option key={a.value} value={a.value}>
                                                {a.label}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            </>
                        )}
                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <label className={labelClass}>Position</label>
                                <select
                                    value={wmPosition}
                                    onChange={(e) => setWmPosition(e.target.value)}
                                    className={inputClass}
                                >
                                    {POSITION_OPTIONS.map((p) => (
                                        <option key={p.value} value={p.value}>
                                            {p.label}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className={labelClass}>
                                    Opacity{" "}
                                    <span className="text-zinc-600 font-mono">
                                        {Math.round(wmOpacity * 100)}%
                                    </span>
                                </label>
                                <input
                                    type="range"
                                    min={0.1}
                                    max={1}
                                    step={0.05}
                                    value={wmOpacity}
                                    onChange={(e) =>
                                        setWmOpacity(parseFloat(e.target.value))
                                    }
                                    className="w-full accent-sky-500"
                                />
                            </div>
                        </div>
                    </>
                )}

                {mode === "branding" && (
                    <>
                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <label className={labelClass}>Brand Name</label>
                                <input
                                    value={brandName}
                                    onChange={(e) => setBrandName(e.target.value)}
                                    className={inputClass}
                                />
                            </div>
                            <div>
                                <label className={labelClass}>
                                    Logo Path{" "}
                                    <span className="text-zinc-600">(optional)</span>
                                </label>
                                <input
                                    value={logoPath}
                                    onChange={(e) => setLogoPath(e.target.value)}
                                    placeholder="/path/to/logo.png"
                                    className={inputClass}
                                />
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <label className={labelClass}>
                                    Tagline <span className="text-zinc-600">(optional)</span>
                                </label>
                                <input
                                    value={tagline}
                                    onChange={(e) => setTagline(e.target.value)}
                                    placeholder="Your brand tagline"
                                    className={inputClass}
                                />
                            </div>
                            <div>
                                <label className={labelClass}>
                                    Website <span className="text-zinc-600">(optional)</span>
                                </label>
                                <input
                                    value={website}
                                    onChange={(e) => setWebsite(e.target.value)}
                                    placeholder="https://example.com"
                                    className={inputClass}
                                />
                            </div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <label className={labelClass}>Position</label>
                                <select
                                    value={wmPosition}
                                    onChange={(e) => setWmPosition(e.target.value)}
                                    className={inputClass}
                                >
                                    {POSITION_OPTIONS.map((p) => (
                                        <option key={p.value} value={p.value}>
                                            {p.label}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className={labelClass}>
                                    Opacity{" "}
                                    <span className="text-zinc-600 font-mono">
                                        {Math.round(wmOpacity * 100)}%
                                    </span>
                                </label>
                                <input
                                    type="range"
                                    min={0.1}
                                    max={1}
                                    step={0.05}
                                    value={wmOpacity}
                                    onChange={(e) =>
                                        setWmOpacity(parseFloat(e.target.value))
                                    }
                                    className="w-full accent-amber-500"
                                />
                            </div>
                        </div>
                    </>
                )}

                {/* Submit */}
                <Button
                    onClick={handleSubmit}
                    disabled={isProcessing || !videoPath}
                    className={"w-full h-14 text-white font-bold text-sm rounded-xl transition-all uppercase tracking-widest disabled:opacity-40 disabled:cursor-not-allowed"}
                    style={{
                        backgroundColor: COLOR_HEX[currentMode.color],
                    }}
                >
                    {isProcessing ? (
                        <span className="flex items-center justify-center gap-2">
                            <Loader2 className="h-4 w-4 animate-spin" />
                            Processing...
                        </span>
                    ) : (
                        <span className="flex items-center justify-center gap-2">
                            <Sparkles className="h-4 w-4" />
                            Apply {currentMode.label}
                        </span>
                    )}
                </Button>
            </div>

            {/* Result */}
            {result && (
                <div
                    className={cn(
                        "p-4 rounded-xl border",
                        colors.bg,
                        colors.border
                    )}
                >
                    <div className="flex items-center justify-between">
                        <div>
                            <p
                                className={cn(
                                    "text-[9px] font-bold uppercase tracking-wider",
                                    colors.text
                                )}
                            >
                                Enhancement Complete
                            </p>
                            <p className="text-[10px] text-zinc-400 font-mono mt-1 break-all">
                                {result}
                            </p>
                        </div>
                        <button
                            onClick={() => setPreviewVisible(!previewVisible)}
                            className={cn(
                                "p-2 rounded-lg border transition-all",
                                colors.border,
                                "hover:bg-white/5"
                            )}
                            title="Toggle preview"
                        >
                            <Eye className={cn("h-4 w-4", colors.text)} />
                        </button>
                    </div>
                    {previewVisible && result && (
                        <video
                            src={result.startsWith("http") ? result : `${API_BASE}/static/${result.split("/").pop()}`}
                            controls
                            className="w-full mt-3 rounded-lg border border-white/10"
                            style={{ maxHeight: 300 }}
                        />
                    )}
                </div>
            )}
        </div>
    );
}
