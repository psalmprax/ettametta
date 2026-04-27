"use client";

import React, { useState, useEffect, Suspense } from "react";
import { withRealFallback } from "@/lib/real_first_utils";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import DashboardLayout from "@/components/layout";
import { useUI } from "@/context/UIContext";
import { ThemeSwitcher } from "@/components/theme-toggle";
import {
    Key,
    Database,
    Shield,
    Bell,
    Server,
    Save,
    EyeOff,
    Eye,
    CheckCircle2,
    Cpu,
    Loader2,
    Layout,
    User,
    CreditCard,
    Sparkles,
    Wand2,
    Film,
    Bot,
    Workflow,
    Code,
    ShoppingCart,
    TrendingUp,
    Globe,
    Link2,
    Unlink,
    RefreshCw,
    Phone,
    Send,
    Terminal,
    Activity,
    Radio,
    ChevronRight
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import { Canvas } from "@react-three/fiber";
import { Float, Sphere, MeshDistortMaterial } from "@react-three/drei";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

function SettingsBackground() {
    return (
        <div className="absolute inset-0 z-0 pointer-events-none opacity-20">
            <Canvas camera={{ position: [0, 0, 5] }}>
                <Suspense fallback={null}>
                    <ambientLight intensity={0.4} />
                    <pointLight position={[10, 10, 10]} intensity={1} color="#6366f1" />
                    <Float speed={1} rotationIntensity={0.5} floatIntensity={0.5}>
                        <Sphere args={[1.4, 64, 64]} scale={2.5}>
                            <MeshDistortMaterial
                                color="#6366f1"
                                speed={2}
                                distort={0.2}
                                radius={1}
                                wireframe
                                transparent
                                opacity={0.1}
                            />
                        </Sphere>
                    </Float>
                </Suspense>
            </Canvas>
        </div>
    );
}


const SettingsSchema = z.object({
    groq_api_key: z.string().optional(),
    youtube_api_key: z.string().optional(),
    scan_frequency: z.string(),
    force_originality: z.string(),
    auto_pilot: z.string(),
    shopify_access_token: z.string().optional(),
    shopify_shop_url: z.string().url().optional().or(z.string().length(0)),
    elevenlabs_api_key: z.string().optional(),
    fish_speech_endpoint: z.string().url().optional().or(z.string().length(0)),
    voice_engine: z.string(),
    pexels_api_key: z.string().optional(),
    aws_access_key_id: z.string().optional(),
    aws_secret_access_key: z.string().optional(),
    aws_region: z.string(),
    aws_storage_bucket_name: z.string().optional(),
    active_monetization_strategy: z.string(),
    monetization_mode: z.string(),
    monetization_aggression: z.string(),
    membership_platform_url: z.string().url().optional().or(z.string().length(0)),
    course_platform_url: z.string().url().optional().or(z.string().length(0)),
    lead_gen_url: z.string().url().optional().or(z.string().length(0)),
    digital_product_url: z.string().url().optional().or(z.string().length(0)),
    sponsorship_contact: z.string().optional(),
    brand_partners: z.string().optional(),
    crypto_wallets: z.string().optional(),
    donation_link: z.string().url().optional().or(z.string().length(0)),
    ai_matching_enabled: z.string(),
    auto_promo_enabled: z.string(),
    storage_provider: z.string(),
    storage_access_key: z.string().optional(),
    storage_secret_key: z.string().optional(),
    storage_bucket: z.string().optional(),
    storage_endpoint: z.string().url().optional().or(z.string().length(0)),
    storage_region: z.string().optional(),
    google_client_id: z.string().optional(),
    google_client_secret: z.string().optional(),
    tiktok_client_key: z.string().optional(),
    tiktok_client_secret: z.string().optional(),
    enable_sound_design: z.string(),
    enable_motion_graphics: z.string(),
    ai_video_provider: z.string(),
    default_quality_tier: z.string()
});

type SettingsValues = z.infer<typeof SettingsSchema>;

export default function SettingsPage() {
    const { isProMode, toggleProMode } = useUI();
    const [showKey, setShowKey] = useState<Record<string, boolean>>({});
    const { register, handleSubmit, reset, setValue, watch, formState: { errors, isDirty } } = useForm<SettingsValues>({
        resolver: zodResolver(SettingsSchema),
        defaultValues: {
            groq_api_key: "",
            youtube_api_key: "",
            scan_frequency: "Every 1 hour",
            force_originality: "true",
            auto_pilot: "false",
            shopify_access_token: "",
            shopify_shop_url: "",
            elevenlabs_api_key: "",
            fish_speech_endpoint: (typeof window !== "undefined" ? `${window.location.protocol}//${window.location.host}/ai-gateway/voice` : "http://ai-gateway:8133/voice"),
            voice_engine: "fish_speech",
            pexels_api_key: "",
            aws_access_key_id: "",
            aws_secret_access_key: "",
            aws_region: "us-east-1",
            aws_storage_bucket_name: "",
            active_monetization_strategy: "commerce",
            monetization_mode: "selective",
            monetization_aggression: "80",
            membership_platform_url: "",
            course_platform_url: "",
            lead_gen_url: "",
            digital_product_url: "",
            sponsorship_contact: "",
            brand_partners: "",
            crypto_wallets: "",
            donation_link: "",
            ai_matching_enabled: "true",
            auto_promo_enabled: "true",
            storage_provider: "OCI",
            storage_access_key: "",
            storage_secret_key: "",
            storage_bucket: "",
            storage_endpoint: "",
            storage_region: "",
            google_client_id: "",
            google_client_secret: "",
            tiktok_client_key: "",
            tiktok_client_secret: "",
            enable_sound_design: "false",
            enable_motion_graphics: "false",
            ai_video_provider: "none",
            default_quality_tier: "standard"
        }
    });

    const settings = watch();
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [saveStatus, setSaveStatus] = useState<"idle" | "success" | "error">("idle");
    const [activeTab, setActiveTab] = useState("Identity");
    const [userProfile, setUserProfile] = useState<{ telegram_chat_id: string, telegram_token: string, whatsapp_number: string, role: string, subscription: string }>({
        telegram_chat_id: "",
        telegram_token: "",
        whatsapp_number: "",
        role: "user",
        subscription: "free"
    });

    const toggleKey = (id: string) => {
        setShowKey(prev => ({ ...prev, [id]: !prev[id] }));
    };

    const fetchSettings = async () => {
        setIsLoading(true);
        await withRealFallback(
            async () => {
                const token = getAuthToken();
                if (!token) return;
                const headers = { Authorization: `Bearer ${token}` };
                return fetch(`${API_BASE}/v1/settings/`, { headers });
            },
            {
                fallback: null,
                onSuccess: (data: any) => {
                    if (Object.keys(data).length > 0) {
                        reset(data);
                    }
                }
            }
        );
        setIsLoading(false);
    };

    const fetchProfile = async () => {
        await withRealFallback(
            async () => {
                const token = getAuthToken();
                if (!token) return;
                return fetch(`${API_BASE}/v1/auth/me`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
            },
            {
                fallback: userProfile,
                onSuccess: (data: any) => {
                    setUserProfile({
                        telegram_chat_id: data.telegram_chat_id || "",
                        telegram_token: data.telegram_token || "",
                        whatsapp_number: data.whatsapp_number || "",
                        role: data.role || "user",
                        subscription: data.subscription || "free"
                    });
                    if (data.role === "admin") {
                        fetchSettings();
                    }
                }
            }
        );
    };

    useEffect(() => {
        fetchProfile();
    }, []);

    const handleSave = handleSubmit(async (data) => {
        setIsSaving(true);
        setSaveStatus("idle");
        const token = getAuthToken();
        if (!token) return;

        const payload = Object.entries(data).map(([key, value]) => ({
            key,
            value: String(value ?? ""),
            category: key.includes("key") || key.includes("id") ? "api_key" : "engine"
        }));

        await withRealFallback(
            () => fetch(`${API_BASE}/v1/settings/bulk`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            }),
            {
                fallback: null,
                onSuccess: () => {
                    setSaveStatus("success");
                    toast.success("Settings Synchronized");
                    reset(data);
                }
            }
        );
        setIsSaving(false);
    });

    return (
        <DashboardLayout>
            <div className="min-h-screen bg-bg-base relative flex flex-col font-sans overflow-hidden">
                <div className="noise-overlay" />
                <SettingsBackground />
                <div className="absolute inset-0 cyber-grid opacity-10 pointer-events-none" />
                <div className="absolute inset-0 scanline opacity-10 pointer-events-none z-50" />

                <div className="flex-1 section-container relative py-16 px-8 lg:px-24 max-w-screen-2xl mx-auto w-full z-10">
                    
                    {/* SETTINGS HEADER */}
                    <header className="mb-20 flex flex-col xl:flex-row xl:items-end justify-between gap-12">
                        <div className="space-y-6">
                            <motion.div 
                                initial={{ width: 0 }}
                                animate={{ width: 140 }}
                                className="h-1 bg-indigo-500 shadow-[0_0_20px_#6366f1]"
                            />
                            <div className="space-y-2">
                                <h1 className="text-4xl md:text-5xl font-bold text-white uppercase tracking-tighter leading-none  " data-text="CORE_CONFIG">
                                    Core Config
                                </h1>
                                <p className="font-data-mono text-zinc-500 text-[10px] flex items-center gap-3">
                                    <Terminal className="h-3 w-3 text-indigo-400" />
                                    OVERRIDE_AUTHORITY: {userProfile.role.toUpperCase()}
                                    <span className="w-1 h-1 bg-zinc-800 rounded-full" />
                                    ENCRYPTION: AES_X_QUANTUM
                                </p>
                            </div>
                        </div>

                        <div className="flex items-center gap-6">
                            <div className="surface-glass rim-light p-6 flex flex-col items-end">
                                <span className="font-data-mono text-[8px] text-zinc-600 mb-1">REVISION_ID</span>
                                <span className="text-xl font-bold text-white tabular-nums tracking-tighter">
                                    v3.2.0-STABLE
                                </span>
                            </div>
                            <button 
                                onClick={handleSave}
                                disabled={isSaving}
                                className="action-primary h-20 px-12  text-xs tracking-tighter flex items-center gap-4"
                            >
                                {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                                COMMIT_OVERRIDES
                            </button>
                        </div>
                    </header>

                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
                        
                        {/* NAV SIDEBAR */}
                        <div className="lg:col-span-3 space-y-4">
                            {[
                                { id: "Identity", icon: User },
                                { id: "Security", icon: Shield },
                                { id: "Network", icon: Globe },
                                { id: "Billing", icon: CreditCard },
                                { id: "Monetization", icon: TrendingUp },
                                { id: "Advanced", icon: Cpu },
                            ].map((tab) => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id)}
                                    className={cn(
                                        "w-full p-6 flex items-center justify-between border transition-all relative overflow-hidden group",
                                        activeTab === tab.id 
                                            ? "surface-glass rim-light-indigo bg-indigo-500/5 text-indigo-400" 
                                            : "bg-transparent border-white/5 text-zinc-600 hover:bg-white/2"
                                    )}
                                >
                                    <div className="flex items-center gap-4 relative z-10">
                                        <tab.icon className={cn("h-4 w-4", activeTab === tab.id ? "text-indigo-400" : "text-zinc-700")} />
                                        <span className="font-label-caps text-[9px] tracking-widest uppercase">{tab.id}</span>
                                    </div>
                                    <ChevronRight className={cn("h-3 w-3 transition-transform", activeTab === tab.id ? "translate-x-0 opacity-100" : "-translate-x-2 opacity-0")} />
                                </button>
                            ))}
                        </div>

                        {/* CONTENT TERMINAL */}
                        <div className="lg:col-span-9">
                            <AnimatePresence mode="wait">
                                <motion.div
                                    key={activeTab}
                                    initial={{ opacity: 0, x: 20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    exit={{ opacity: 0, x: -20 }}
                                    className="surface-glass rim-light p-12 min-h-[600px] relative overflow-hidden"
                                >
                                    <div className="absolute inset-0 scanline opacity-5" />
                                    
                                    <header className="mb-12 border-b border-white/5 pb-8 flex items-center justify-between">
                                        <div className="space-y-1">
                                            <h2 className="text-3xl font-bold text-white  tracking-tighter uppercase">{activeTab} Terminal</h2>
                                            <p className="font-data-mono text-[8px] text-zinc-600 uppercase tracking-widest">Protocol_Identity_Handoff</p>
                                        </div>
                                        <div className="h-2 w-2 rounded-full bg-indigo-500 shadow-[0_0_10px_#6366f1]" />
                                    </header>

                                    {activeTab === "Identity" && (
                                        <div className="space-y-12">
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                                <div className="p-8 bg-white/2 border border-white/5 space-y-4 group hover:border-indigo-500/20 transition-all">
                                                    <label className="font-label-caps text-[9px] text-zinc-600 uppercase tracking-widest">Network_Alias</label>
                                                    <p className="text-2xl font-bold text-white ">Administrator</p>
                                                </div>
                                                <div className="p-8 bg-white/2 border border-white/5 space-y-4 group hover:border-indigo-500/20 transition-all">
                                                    <label className="font-label-caps text-[9px] text-zinc-600 uppercase tracking-widest">Subscription_Tier</label>
                                                    <p className="text-2xl font-bold text-indigo-400 ">SOVEREIGN</p>
                                                </div>
                                            </div>

                                            <div className="space-y-6">
                                                <h3 className="font-label-caps text-[10px] text-zinc-400 flex items-center gap-3">
                                                    <ThemeSwitcher /> Appearance Mode
                                                </h3>
                                            </div>
                                        </div>
                                    )}

                                    {activeTab === "Security" && (
                                        <div className="space-y-12">
                                            <div className="p-8 bg-indigo-500/5 border border-indigo-500/20 space-y-6">
                                                <div className="flex items-center gap-4">
                                                    <Shield className="h-6 w-6 text-indigo-400" />
                                                    <h3 className="text-xl font-bold text-white  tracking-tighter uppercase">API Overrides</h3>
                                                </div>
                                                <div className="grid grid-cols-1 gap-8 pt-6 border-t border-white/5">
                                                    {[
                                                        { label: "GROQ_SECRET", id: "groq_api_key" },
                                                        { label: "ELEVEN_LABS_KEY", id: "elevenlabs_api_key" },
                                                        { label: "PEXELS_ACCESS", id: "pexels_api_key" },
                                                    ].map((key) => (
                                                        <div key={key.id} className="space-y-2">
                                                            <label className="font-data-mono text-[9px] text-zinc-600 uppercase tracking-widest">{key.label}</label>
                                                            <div className="relative">
                                                                <input
                                                                    type={showKey[key.id] ? "text" : "password"}
                                                                    {...register(key.id as any)}
                                                                    className="w-full bg-zinc-950 border border-white/5 p-4 text-white font-bold text-sm focus:border-indigo-500/50 outline-none pr-12 transition-all"
                                                                />
                                                                <button
                                                                    type="button"
                                                                    onClick={() => toggleKey(key.id)}
                                                                    className="absolute right-4 top-1/2 -translate-y-1/2 text-zinc-700 hover:text-white"
                                                                >
                                                                    {showKey[key.id] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                                                </button>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {activeTab === "Billing" && (
                                        <div className="space-y-12">
                                            <div className="surface-glass rim-light p-10 bg-indigo-500/5 border-indigo-500/20 text-center space-y-6">
                                                <div className="h-16 w-16 bg-indigo-500/10 rounded-full flex items-center justify-center mx-auto border border-indigo-500/20">
                                                    <CreditCard className="h-8 w-8 text-indigo-400" />
                                                </div>
                                                <div className="space-y-1">
                                                    <h3 className="text-2xl font-bold text-white  tracking-tighter uppercase">Empire Access</h3>
                                                    <p className="font-data-mono text-[8px] text-zinc-600 uppercase tracking-widest">Active_Subscription_Found</p>
                                                </div>
                                                <div className="pt-6 border-t border-white/5">
                                                    <button className="action-primary py-4 px-10  text-[10px] tracking-tighter">
                                                        MANAGE_PAYMENT_NODES
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {/* DEFAULT FALLBACK FOR OTHER TABS */}
                                    {["Network", "Monetization", "Advanced"].includes(activeTab) && (
                                        <div className="h-full flex flex-col items-center justify-center opacity-30 space-y-6 grayscale">
                                            <Activity className="h-16 w-16 text-zinc-700" />
                                            <p className="font-data-mono text-[9px] uppercase tracking-[0.5em] font-bold">Segment_Locked_v3.2</p>
                                        </div>
                                    )}
                                </motion.div>
                            </AnimatePresence>
                        </div>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
