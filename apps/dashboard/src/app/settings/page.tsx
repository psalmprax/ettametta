"use client";

import React, { useState, useEffect } from "react";
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
    Send
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { toast } from "sonner";

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
            fish_speech_endpoint: "http://voiceover:8080",
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

    // We still need a way to watch all values for the bulk save if we don't use handleSubmit immediately
    const settings = watch();
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [saveStatus, setSaveStatus] = useState<"idle" | "success" | "error">("idle");
    const [activeTab, setActiveTab] = useState("Profile");
    const [userProfile, setUserProfile] = useState<{ telegram_chat_id: string, telegram_token: string, whatsapp_number: string, role: string, subscription: string }>({
        telegram_chat_id: "",
        telegram_token: "",
        whatsapp_number: "",
        role: "user",
        subscription: "free"
    });
    const [subscriptionData, setSubscriptionData] = useState<any>(null);
    const [isCancelling, setIsCancelling] = useState(false);
    const [passwordFields, setPasswordFields] = useState({ current_password: "", new_password: "", confirm_password: "" });
    const [isChangingPassword, setIsChangingPassword] = useState(false);
    const [passwordStatus, setPasswordStatus] = useState<"idle" | "success" | "error">("idle");

    const toggleKey = (id: string) => {
        setShowKey(prev => ({ ...prev, [id]: !prev[id] }));
    };

    const fetchSettings = async () => {
        setIsLoading(true);
        await withRealFallback(
            async () => {
                const token = localStorage.getItem("et_token");
                const headers = { Authorization: `Bearer ${token}` };
                return fetch(`${API_BASE}/settings/`, { headers });
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
                const token = localStorage.getItem("et_token");
                return fetch(`${API_BASE}/auth/me`, {
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
                        setActiveTab("Keys");
                        fetchSettings();
                    } else {
                        setActiveTab("Profile");
                        setIsLoading(false);
                    }
                }
            }
        );
    };

    const handleSave = handleSubmit(async (data) => {
        setIsSaving(true);
        setSaveStatus("idle");
        
        const token = localStorage.getItem("et_token");
        const payload = Object.entries(data).map(([key, value]) => ({
            key,
            value: String(value ?? ""),
            category: key.includes("key") || key.includes("id") ? "api_key" : "engine"
        }));

        const settingsEndpoint = userProfile.role === "admin"
            ? `${API_BASE}/settings/bulk`
            : `${API_BASE}/settings/user`;

        await withRealFallback(
            async () => {
                const sres = await fetch(settingsEndpoint, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },
                    body: JSON.stringify(payload)
                });
                
                if (!sres.ok) throw new Error("Settings synchronization failed");

                return fetch(`${API_BASE}/auth/me`, {
                    method: "PATCH",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        telegram_chat_id: userProfile.telegram_chat_id || null,
                        telegram_token: userProfile.telegram_token || null,
                        whatsapp_number: userProfile.whatsapp_number || null
                    })
                });
            },
            {
                fallback: null,
                onSuccess: () => {
                    setSaveStatus("success");
                    toast.success("Settings Synchronized", { description: "Identity and engine parameters updated." });
                    reset(data);
                },
                onFallback: (err: any) => {
                    setSaveStatus("error");
                    toast.error("Sync Failed", { description: err.message });
                }
            }
        );
        setIsSaving(false);
    });

    const fetchSubscription = async () => {
        await withRealFallback(
            async () => {
                const token = localStorage.getItem("et_token");
                return fetch(`${API_BASE}/billing/subscription`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
            },
            {
                fallback: subscriptionData,
                onSuccess: (data: any) => setSubscriptionData(data)
            }
        );
    };

    const handleCancelSubscription = async () => {
        setIsCancelling(true);
        await withRealFallback(
            async () => {
                const token = localStorage.getItem("et_token");
                return fetch(`${API_BASE}/billing/cancel`, {
                    method: "POST",
                    headers: { Authorization: `Bearer ${token}` }
                });
            },
            {
                fallback: null,
                onSuccess: () => {
                    setSaveStatus("success");
                    toast.success("Subscription Cancelled", { description: "Resource de-allocation initiated." });
                    fetchSubscription();
                    fetchProfile();
                },
                onFallback: (err: any) => {
                    setSaveStatus("error");
                    toast.error("Cancel Failed", { description: err.message });
                }
            }
        );
        setIsCancelling(false);
    };

    const [isVerifying, setIsVerifying] = useState<Record<string, boolean>>({});
    const [verifyStatus, setVerifyStatus] = useState<Record<string, "success" | "error" | "idle">>({});

    const handleVerifyComms = async (platform: "telegram" | "whatsapp") => {
        setIsVerifying(prev => ({ ...prev, [platform]: true }));
        setVerifyStatus(prev => ({ ...prev, [platform]: "idle" }));
        await withRealFallback(
            async () => {
                const token = localStorage.getItem("et_token");
                return fetch(`${API_BASE}/auth/verify-comms?platform=${platform}`, {
                    method: "POST",
                    headers: { Authorization: `Bearer ${token}` }
                });
            },
            {
                fallback: null,
                onSuccess: () => {
                    setVerifyStatus(prev => ({ ...prev, [platform]: "success" }));
                    toast.success("Signal Sent", { description: `Verification ping dispatched to ${platform}.` });
                },
                onFallback: (err: any) => {
                    setVerifyStatus(prev => ({ ...prev, [platform]: "error" }));
                    toast.error("Signal Failed", { description: err.message });
                }
            }
        );
        setIsVerifying(prev => ({ ...prev, [platform]: false }));
    };

    const handleChangePassword = async () => {
        if (passwordFields.new_password !== passwordFields.confirm_password) {
            setPasswordStatus("error");
            toast.error("Mismatch", { description: "New passwords do not match." });
            return;
        }
        if (passwordFields.new_password.length < 6) {
            setPasswordStatus("error");
            toast.error("Weak Password", { description: "Minimum 6 characters required." });
            return;
        }
        setIsChangingPassword(true);
        setPasswordStatus("idle");
        await withRealFallback(
            async () => {
                const token = localStorage.getItem("et_token");
                return fetch(`${API_BASE}/auth/me/change-password`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        current_password: passwordFields.current_password,
                        new_password: passwordFields.new_password
                    })
                });
            },
            {
                fallback: null,
                onSuccess: () => {
                    setPasswordStatus("success");
                    toast.success("Security Hardened", { description: "Password rotated successfully." });
                    setPasswordFields({ current_password: "", new_password: "", confirm_password: "" });
                },
                onFallback: (err: any) => {
                    setPasswordStatus("error");
                    toast.error("Auth Error", { description: err.message });
                }
            }
        );
        setIsChangingPassword(false);
    };

    useEffect(() => {
        fetchProfile();
        fetchSubscription();
    }, []);

    const updateSetting = (key: keyof SettingsValues, value: string) => {
        setValue(key, value, { shouldDirty: true });
    };

    return (
        <DashboardLayout>
            <div className="section-container relative pb-20">
                <div className="flex items-center justify-between mb-10">
                    <div>
                        <div className="flex items-center gap-3 mb-1">
                            <h1 className="text-5xl md:text-6xl font-black uppercase tracking-tighter text-white">My <span className="text-transparent bg-clip-text bg-gradient-to-r from-zinc-400 to-white text-hollow">Settings</span></h1>
                            <div className={cn(
                                "px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest border",
                                userProfile.subscription === "studio" ? "bg-purple-500/10 text-purple-500 border-purple-500/20 shadow-[0_0_10px_rgba(168,85,247,0.2)]" :
                                    userProfile.subscription === "sovereign" ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20 shadow-[0_0_10px_rgba(16,185,129,0.2)]" :
                                        userProfile.subscription === "premium" ? "bg-amber-500/10 text-amber-500 border-amber-500/20 shadow-[0_0_10px_rgba(245,158,11,0.2)]" :
                                            userProfile.subscription === "basic" ? "bg-blue-500/10 text-blue-500 border-blue-500/20" :
                                                "bg-zinc-500/10 text-zinc-500 border-zinc-500/20"
                            )}>
                                {userProfile.subscription === "basic" ? "Creator" : userProfile.subscription === "premium" ? "Empire" : userProfile.subscription}
                            </div>
                        </div>
                        <p className="text-zinc-500 text-sm font-bold tracking-tight">Configure personal overrides and manage your identity.</p>
                    </div>
                    <button
                        onClick={handleSave}
                        disabled={isSaving}
                        className={cn(
                            "bg-primary hover:bg-primary/90 text-white font-black py-4 px-8 rounded-2xl transition-all flex items-center gap-2 uppercase tracking-widest text-[10px] shadow-[0_0_30px_rgba(var(--primary-rgb),0.3)] border border-primary/20",
                            isSaving && "opacity-50 cursor-not-allowed",
                            saveStatus === "success" && "bg-emerald-500 hover:bg-emerald-600 shadow-emerald-500/20"
                        )}
                    >
                        {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : saveStatus === "success" ? <CheckCircle2 className="h-4 w-4" /> : <Save className="h-4 w-4" />}
                        {isSaving ? "Saving..." : saveStatus === "success" ? "Saved!" : "Synchronize"}
                    </button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-4 gap-12">
                    <div className="space-y-2">
                        <TabItem icon={<User className="h-4 w-4" />} label="Identity" active={activeTab === "Profile"} onClick={() => setActiveTab("Profile")} />
                        <TabItem icon={<Key className="h-4 w-4" />} label="Private Keys" active={activeTab === "Keys"} onClick={() => setActiveTab("Keys")} />
                        <TabItem icon={<Bell className="h-4 w-4" />} label="Comms" active={activeTab === "Notifications"} onClick={() => setActiveTab("Notifications")} />
                        <TabItem icon={<CreditCard className="h-4 w-4" />} label="Billing" active={activeTab === "Billing"} onClick={() => setActiveTab("Billing")} />
                        <TabItem icon={<TrendingUp className="h-4 w-4" />} label="Monetization" active={activeTab === "Monetization"} onClick={() => setActiveTab("Monetization")} />
                        <TabItem icon={<Wand2 className="h-4 w-4" />} label="Engine" active={activeTab === "Engine"} onClick={() => setActiveTab("Engine")} />
                        <TabItem icon={<Globe className="h-4 w-4" />} label="Browser Bridge" active={activeTab === "opencli"} onClick={() => setActiveTab("opencli")} />
                    </div>

                    <div className="lg:col-span-3 space-y-12">
                        {isLoading ? (
                            <div className="h-96 flex items-center justify-center">
                                <Loader2 className="h-12 w-12 text-primary animate-spin" />
                            </div>
                        ) : activeTab === "Keys" ? (
                            <section className="card-gradient border border-white/5 rounded-[2.5rem] p-12 space-y-12 shadow-2xl relative overflow-hidden">
                                <div className="absolute top-0 right-0 p-8 opacity-5">
                                    <Key className="h-32 w-32 text-white" />
                                </div>
                                <div className="flex items-center gap-6 relative z-10">
                                    <div className="h-20 w-20 rounded-3xl bg-primary/10 flex items-center justify-center border border-primary/20 shadow-[0_0_30px_rgba(var(--primary-rgb),0.15)]">
                                        <Key className="h-10 w-10 text-primary" />
                                    </div>
                                    <div>
                                        <h3 className="text-4xl font-black text-white uppercase tracking-tighter">Private <span className="text-hollow">Overrides</span></h3>
                                        <p className="text-zinc-500 text-sm mt-1 uppercase tracking-widest font-black opacity-60">Personal vault for high-priority secrets</p>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-10 pt-10 border-t border-white/5 relative z-10">
                                    <KeyInput
                                        label="Groq API Key"
                                        id="groq_api_key"
                                        value={settings.groq_api_key || ""}
                                        onChange={(val) => updateSetting("groq_api_key", val)}
                                        isVisible={showKey["groq_api_key"]}
                                        onToggle={() => toggleKey("groq_api_key")}
                                        error={errors.groq_api_key?.message}
                                    />
                                    <KeyInput
                                        label="YouTube Data API v3"
                                        id="youtube_api_key"
                                        value={settings.youtube_api_key || ""}
                                        onChange={(val) => updateSetting("youtube_api_key", val)}
                                        isVisible={showKey["youtube_api_key"]}
                                        onToggle={() => toggleKey("youtube_api_key")}
                                        error={errors.youtube_api_key?.message}
                                    />
                                    <KeyInput
                                        label="ElevenLabs Key"
                                        id="elevenlabs_api_key"
                                        value={settings.elevenlabs_api_key || ""}
                                        onChange={(val) => updateSetting("elevenlabs_api_key", val)}
                                        isVisible={showKey["elevenlabs_api_key"]}
                                        onToggle={() => toggleKey("elevenlabs_api_key")}
                                        error={errors.elevenlabs_api_key?.message}
                                    />
                                    <KeyInput
                                        label="Pexels/Pixabay API"
                                        id="pexels_api_key"
                                        value={settings.pexels_api_key || ""}
                                        onChange={(val) => updateSetting("pexels_api_key", val)}
                                        isVisible={showKey["pexels_api_key"]}
                                        onToggle={() => toggleKey("pexels_api_key")}
                                        error={errors.pexels_api_key?.message}
                                    />
                                </div>
                            </section>
                        ) : activeTab === "Notifications" ? (
                            <section className="card-gradient border border-white/5 rounded-[2.5rem] p-12 space-y-12 shadow-2xl relative overflow-hidden">
                                <div className="flex items-center gap-6">
                                    <div className="h-20 w-20 rounded-3xl bg-blue-500/10 flex items-center justify-center border border-blue-500/20 shadow-[0_0_30px_rgba(59,130,246,0.15)]">
                                        <Bell className="h-10 w-10 text-blue-500" />
                                    </div>
                                    <div>
                                        <h3 className="text-4xl font-black text-white uppercase tracking-tighter">Nexus <span className="text-hollow">Comms</span></h3>
                                        <p className="text-zinc-500 text-sm mt-1 uppercase tracking-widest font-black opacity-60">Inbound alerts and autonomous status updates</p>
                                    </div>
                                </div>

                                <div className="space-y-8 pt-10 border-t border-white/5">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                                        <div className="space-y-4">
                                            <div className="space-y-2">
                                                <label className="text-[10px] font-black text-zinc-500 uppercase tracking-[0.2em] mb-3 block">Telegram Identity</label>
                                                <div className="relative">
                                                    <input
                                                        type="text"
                                                        value={userProfile.telegram_chat_id}
                                                        onChange={(e) => setUserProfile({ ...userProfile, telegram_chat_id: e.target.value })}
                                                        className="w-full bg-zinc-950/50 border border-white/5 rounded-2xl py-4 px-6 text-white font-black text-sm focus:ring-2 ring-primary/50 outline-none transition-all pr-32"
                                                        placeholder="Chat ID (e.g. 12345678)"
                                                    />
                                                    <button
                                                        onClick={() => handleVerifyComms("telegram")}
                                                        disabled={isVerifying["telegram"] || !userProfile.telegram_chat_id}
                                                        className={cn(
                                                            "absolute right-2 top-2 bottom-2 px-4 rounded-xl text-[8px] font-black uppercase tracking-widest transition-all flex items-center gap-2",
                                                            verifyStatus["telegram"] === "success" ? "bg-emerald-500/20 text-emerald-500 border border-emerald-500/30" :
                                                                verifyStatus["telegram"] === "error" ? "bg-red-500/20 text-red-500 border border-red-500/30" :
                                                                    "bg-white/5 text-zinc-400 hover:bg-white/10"
                                                        )}
                                                    >
                                                        {isVerifying["telegram"] ? <Loader2 className="h-3 w-3 animate-spin" /> : <Send className="h-3 w-3" />}
                                                        {verifyStatus["telegram"] === "success" ? "Sent!" : "Verify"}
                                                    </button>
                                                </div>
                                                <p className="text-[10px] text-zinc-600 uppercase font-bold pl-2">Get your ID via @userinfobot</p>
                                            </div>

                                            <div className="space-y-2 pt-4">
                                                <label className="text-[10px] font-black text-zinc-500 uppercase tracking-[0.2em] mb-3 block">WhatsApp Number</label>
                                                <div className="relative">
                                                    <input
                                                        type="text"
                                                        value={userProfile.whatsapp_number}
                                                        onChange={(e) => setUserProfile({ ...userProfile, whatsapp_number: e.target.value })}
                                                        className="w-full bg-zinc-950/50 border border-white/5 rounded-2xl py-4 px-6 text-white font-black text-sm focus:ring-2 ring-emerald-500/50 outline-none transition-all pr-32"
                                                        placeholder="+1234567890"
                                                    />
                                                    <button
                                                        onClick={() => handleVerifyComms("whatsapp")}
                                                        disabled={isVerifying["whatsapp"] || !userProfile.whatsapp_number}
                                                        className={cn(
                                                            "absolute right-2 top-2 bottom-2 px-4 rounded-xl text-[8px] font-black uppercase tracking-widest transition-all flex items-center gap-2",
                                                            verifyStatus["whatsapp"] === "success" ? "bg-emerald-500/20 text-emerald-500 border border-emerald-500/30" :
                                                                verifyStatus["whatsapp"] === "error" ? "bg-red-500/20 text-red-500 border border-red-500/30" :
                                                                    "bg-white/5 text-zinc-400 hover:bg-white/10"
                                                        )}
                                                    >
                                                        {isVerifying["whatsapp"] ? <Loader2 className="h-3 w-3 animate-spin" /> : <Send className="h-3 w-3" />}
                                                        {verifyStatus["whatsapp"] === "success" ? "Sent!" : "Verify"}
                                                    </button>
                                                </div>
                                                <p className="text-[10px] text-zinc-600 uppercase font-bold pl-2">E.164 Format: +[Country][Number]</p>
                                            </div>
                                        </div>
                                        <div className="space-y-6">
                                            <KeyInput
                                                label="Bot Token Override"
                                                id="telegram_token"
                                                value={userProfile.telegram_token}
                                                onChange={(val) => setUserProfile({ ...userProfile, telegram_token: val })}
                                                isVisible={showKey["tg_token"]}
                                                onToggle={() => toggleKey("tg_token")}
                                                placeholder="XXXX:YYYYYYYYY"
                                            />
                                            <div className="p-6 rounded-[2rem] bg-zinc-950/30 border border-white/5 space-y-3">
                                                <h5 className="text-[10px] font-black text-white uppercase tracking-widest flex items-center gap-2">
                                                    <Phone className="h-3 w-3 text-emerald-500" /> WhatsApp Sandbox
                                                </h5>
                                                <p className="text-[10px] text-zinc-500 font-medium leading-relaxed">
                                                    To receive messages via Twilio Sandbox, send <span className="text-emerald-500 font-black">join [sandbox-code]</span> to the system number first.
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </section>
                        ) : activeTab === "Profile" ? (
                            <section className="card-gradient border border-white/5 rounded-[2.5rem] p-12 space-y-12 shadow-2xl relative overflow-hidden">
                                <div className="flex items-center gap-6">
                                    <div className="h-20 w-20 rounded-3xl bg-zinc-500/10 flex items-center justify-center border border-white/10 shadow-[0_0_30px_rgba(255,255,255,0.05)]">
                                        <User className="h-10 w-10 text-white" />
                                    </div>
                                    <div>
                                        <h3 className="text-4xl font-black text-white uppercase tracking-tighter">User <span className="text-hollow">Identity</span></h3>
                                        <p className="text-zinc-500 text-sm mt-1 uppercase tracking-widest font-black opacity-60">Authentication and authorization parameters</p>
                                    </div>
                                </div>

                                {/* Theme Switcher - User Preference */}
                                <div className="pt-8 border-t border-white/5">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <h4 className="text-lg font-bold text-white">UI Theme</h4>
                                            <p className="text-sm text-zinc-500">Choose your preferred interface design</p>
                                        </div>
                                        <ThemeSwitcher />
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-10 pt-10 border-t border-white/5">
                                    <div className="space-y-6">
                                        <div className="p-6 bg-zinc-950/50 border border-white/5 rounded-2xl">
                                            <label className="text-[10px] font-black text-zinc-500 uppercase tracking-[0.2em] mb-4 block">Global Rank</label>
                                            <div className="flex items-center gap-4">
                                                <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center border border-primary/20">
                                                    <Shield className="h-6 w-6 text-primary" />
                                                </div>
                                                <div className="text-2xl font-black text-white uppercase">{userProfile.role}</div>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="space-y-6">
                                        <div className="p-6 bg-zinc-950/50 border border-white/5 rounded-2xl">
                                            <label className="text-[10px] font-black text-zinc-500 uppercase tracking-[0.2em] mb-4 block">Asset Tier</label>
                                            <div className="flex items-center gap-4">
                                                <div className="h-12 w-12 rounded-xl bg-amber-500/10 flex items-center justify-center border border-amber-500/20">
                                                    <Sparkles className="h-6 w-6 text-amber-500" />
                                                </div>
                                                <div className="text-2xl font-black text-white uppercase">{userProfile.subscription}</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Change Password */}
                                <div className="pt-10 border-t border-white/5 space-y-6">
                                    <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-500">Security Override</h4>
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                        <div className="space-y-2">
                                            <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest pl-2">Current Password</label>
                                            <input
                                                type="password"
                                                value={passwordFields.current_password}
                                                onChange={(e) => setPasswordFields({ ...passwordFields, current_password: e.target.value })}
                                                className="w-full bg-zinc-950/50 border border-white/5 rounded-2xl py-4 px-6 text-white text-sm focus:ring-2 ring-primary/50 outline-none transition-all"
                                                placeholder="Enter current password"
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest pl-2">New Password</label>
                                            <input
                                                type="password"
                                                value={passwordFields.new_password}
                                                onChange={(e) => setPasswordFields({ ...passwordFields, new_password: e.target.value })}
                                                className="w-full bg-zinc-950/50 border border-white/5 rounded-2xl py-4 px-6 text-white text-sm focus:ring-2 ring-primary/50 outline-none transition-all"
                                                placeholder="Min 6 characters"
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest pl-2">Confirm Password</label>
                                            <input
                                                type="password"
                                                value={passwordFields.confirm_password}
                                                onChange={(e) => setPasswordFields({ ...passwordFields, confirm_password: e.target.value })}
                                                className="w-full bg-zinc-950/50 border border-white/5 rounded-2xl py-4 px-6 text-white text-sm focus:ring-2 ring-primary/50 outline-none transition-all"
                                                placeholder="Confirm new password"
                                            />
                                        </div>
                                    </div>
                                    <button
                                        onClick={handleChangePassword}
                                        disabled={isChangingPassword || !passwordFields.current_password || !passwordFields.new_password || !passwordFields.confirm_password}
                                        className={cn(
                                            "bg-primary hover:bg-primary/90 text-white font-black py-4 px-8 rounded-2xl transition-all flex items-center gap-2 uppercase tracking-widest text-[10px] shadow-[0_0_30px_rgba(var(--primary-rgb),0.3)]",
                                            (isChangingPassword || !passwordFields.current_password) && "opacity-50 cursor-not-allowed",
                                            passwordStatus === "success" && "bg-emerald-500 hover:bg-emerald-600",
                                            passwordStatus === "error" && "bg-red-500 hover:bg-red-600"
                                        )}
                                    >
                                        {isChangingPassword ? <Loader2 className="h-4 w-4 animate-spin" /> : passwordStatus === "success" ? <CheckCircle2 className="h-4 w-4" /> : <Shield className="h-4 w-4" />}
                                        {isChangingPassword ? "Updating..." : passwordStatus === "success" ? "Password Updated" : passwordStatus === "error" ? "Update Failed" : "Change Password"}
                                    </button>
                                </div>
                            </section>
                        ) : activeTab === "Billing" ? (
                            <section className="card-gradient border border-white/5 rounded-[2.5rem] p-12 space-y-12 shadow-2xl relative overflow-hidden">
                                <div className="flex items-center gap-6">
                                    <div className="h-20 w-20 rounded-3xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20 shadow-[0_0_30px_rgba(16,185,129,0.15)]">
                                        <CreditCard className="h-10 w-10 text-emerald-500" />
                                    </div>
                                    <div>
                                        <h3 className="text-4xl font-black text-white uppercase tracking-tighter">Empire <span className="text-hollow">Credits</span></h3>
                                        <p className="text-zinc-500 text-sm mt-1 uppercase tracking-widest font-black opacity-60">Subscription and resource allocation</p>
                                    </div>
                                </div>

                                {/* Subscription Status */}
                                <div className="pt-10 border-t border-white/5 space-y-8">
                                    <div className="bg-zinc-950/50 border border-white/5 rounded-[2rem] p-10 space-y-6">
                                        <div className="flex items-center justify-between">
                                            <div className="space-y-1">
                                                <p className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-500">Current Plan</p>
                                                <h4 className="text-3xl font-black text-white uppercase">{userProfile.subscription === "basic" ? "Creator" : userProfile.subscription === "premium" ? "Empire" : userProfile.subscription}</h4>
                                            </div>
                                            <div className={cn(
                                                "px-4 py-2 rounded-xl border text-[10px] font-black uppercase tracking-widest",
                                                subscriptionData?.status === "active" ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-500" : "bg-zinc-500/10 border-zinc-500/30 text-zinc-500"
                                            )}>
                                                {subscriptionData?.status || "Free Tier"}
                                            </div>
                                        </div>
                                        {subscriptionData?.current_period_end && (
                                            <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">
                                                Renews: {new Date(subscriptionData.current_period_end * 1000).toLocaleDateString()}
                                            </p>
                                        )}
                                        {subscriptionData?.status === "active" && userProfile.subscription !== "free" && (
                                            <button
                                                onClick={handleCancelSubscription}
                                                disabled={isCancelling}
                                                className="bg-red-500/10 hover:bg-red-500/20 text-red-500 font-black py-3 px-6 rounded-xl transition-all uppercase tracking-widest text-[10px] border border-red-500/20"
                                            >
                                                {isCancelling ? "Cancelling..." : "Cancel Subscription"}
                                            </button>
                                        )}
                                    </div>

                                    {/* Upgrade Options */}
                                    <div className="bg-zinc-950/50 border border-emerald-500/20 rounded-[2rem] p-10 text-center space-y-6">
                                        <h4 className="text-[10px] font-black uppercase text-emerald-500 tracking-[0.3em]">Status: Transmission Optimized</h4>
                                        <p className="text-zinc-400 max-w-md mx-auto text-sm font-bold">Your current {userProfile.subscription} tier handles up to 300 autonomous distributions.</p>
                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                            {[
                                                { tier: "creator", label: "Creator", price: "$29/mo" },
                                                { tier: "empire", label: "Empire", price: "$99/mo" },
                                                { tier: "sovereign", label: "Sovereign", price: "$149/mo" }
                                            ].map((plan) => (
                                                <button
                                                    key={plan.tier}
                                                    onClick={async () => {
                                                        try {
                                                            const token = localStorage.getItem("et_token");
                                                            const res = await fetch(`${API_BASE}/billing/create-checkout-session`, {
                                                                method: "POST",
                                                                headers: {
                                                                    "Content-Type": "application/json",
                                                                    Authorization: `Bearer ${token}`
                                                                },
                                                                body: JSON.stringify({ tier: plan.tier })
                                                            });
                                                            if (res.ok) {
                                                                const data = await res.json();
                                                                if (data.url) window.location.href = data.url;
                                                            }
                                                        } catch (err) {
                                                            console.error("Checkout error:", err);
                                                        }
                                                    }}
                                                    className={cn(
                                                        "py-4 px-6 rounded-xl border font-black uppercase text-[10px] tracking-widest transition-all",
                                                        userProfile.subscription === plan.tier
                                                            ? "bg-emerald-500/20 border-emerald-500 text-emerald-500"
                                                            : "bg-zinc-950/50 border-white/5 text-zinc-400 hover:text-white hover:border-primary/50"
                                                    )}
                                                >
                                                    {plan.label} - {plan.price}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </section>
                        ) : activeTab === "Monetization" ? (
                            <section className="card-gradient border border-white/5 rounded-[2.5rem] p-12 space-y-12 shadow-2xl relative overflow-hidden">
                                <div className="flex items-center gap-6">
                                    <div className="h-20 w-20 rounded-3xl bg-amber-500/10 flex items-center justify-center border border-amber-500/20 shadow-[0_0_30px_rgba(245,158,11,0.15)]">
                                        <TrendingUp className="h-10 w-10 text-amber-500" />
                                    </div>
                                    <div>
                                        <h3 className="text-4xl font-black text-white uppercase tracking-tighter">Growth <span className="text-hollow">Monetization</span></h3>
                                        <p className="text-zinc-500 text-sm mt-1 uppercase tracking-widest font-black opacity-60">Revenue streams and audience support vectors</p>
                                    </div>
                                </div>

                                <div className="space-y-12 pt-10 border-t border-white/5">
                                    {/* Precision Distribution Control */}
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                                        <div className="space-y-6">
                                            <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-500 mb-6">Precision Control</h4>
                                            <div className="space-y-8">
                                                <div className="p-6 bg-zinc-950/50 border border-white/5 rounded-2xl space-y-4">
                                                    <div className="flex justify-between items-center">
                                                        <label className="text-[10px] font-black text-zinc-400 uppercase tracking-widest">Aggression Level</label>
                                                        <span className="text-primary font-black text-sm">{settings.monetization_aggression}%</span>
                                                    </div>
                                                    <input
                                                        type="range"
                                                        min="0"
                                                        max="100"
                                                        value={settings.monetization_aggression}
                                                        onChange={(e) => updateSetting("monetization_aggression", e.target.value)}
                                                        className="w-full h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-primary"
                                                    />
                                                    <p className="text-[9px] text-zinc-600 uppercase font-bold text-center tracking-tighter">Controls frequency of monetization pitch injection</p>
                                                </div>

                                                <div className="space-y-3">
                                                    <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest pl-2">Distribution Mode</label>
                                                    <div className="grid grid-cols-2 gap-4">
                                                        {['selective', 'aggressive'].map((m) => (
                                                            <button
                                                                key={m}
                                                                onClick={() => updateSetting("monetization_mode", m)}
                                                                className={cn(
                                                                    "py-3 px-4 rounded-xl border font-black uppercase text-[10px] tracking-widest transition-all",
                                                                    settings.monetization_mode === m ? "bg-amber-500/20 border-amber-500 text-amber-500 shadow-[0_0_20px_rgba(245,158,11,0.2)]" : "bg-zinc-950/50 border-white/5 text-zinc-600 hover:text-white"
                                                                )}
                                                            >
                                                                {m}
                                                            </button>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="space-y-6">
                                            <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-500 mb-6">Active Strategy</h4>
                                            <div className="grid grid-cols-2 gap-3">
                                                {[
                                                    { id: 'commerce', label: 'E-Commerce' },
                                                    { id: 'affiliate', label: 'Affiliate' },
                                                    { id: 'lead_gen', label: 'Lead Gen' },
                                                    { id: 'membership', label: 'Patreon' },
                                                    { id: 'course', label: 'Academy' },
                                                    { id: 'digital_product', label: 'Digital' },
                                                    { id: 'sponsorship', label: 'Sponsor' },
                                                    { id: 'crypto', label: 'Crypto' }
                                                ].map((s) => (
                                                    <button
                                                        key={s.id}
                                                        onClick={() => updateSetting("active_monetization_strategy", s.id)}
                                                        className={cn(
                                                            "py-3 px-3 rounded-xl border font-black uppercase text-[9px] tracking-widest transition-all text-center",
                                                            settings.active_monetization_strategy === s.id ? "bg-primary border-primary text-white shadow-[0_0_20px_rgba(var(--primary-rgb),0.3)]" : "bg-zinc-950/50 border-white/5 text-zinc-500 hover:text-white hover:border-white/10"
                                                        )}
                                                    >
                                                        {s.label}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    </div>

                                    {/* Primary Vectors */}
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-10 pt-10 border-t border-white/5">
                                        <div className="space-y-6">
                                            <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-500 mb-6">Passive Vectors</h4>
                                            <div className="space-y-4">
                                                <div className="space-y-2">
                                                    <div className="flex justify-between items-center px-2">
                                                        <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest transition-colors">Membership Platform (Patreon/Substack)</label>
                                                        {errors.membership_platform_url && <span className="text-[9px] font-bold text-red-500 uppercase tracking-tighter">{errors.membership_platform_url.message}</span>}
                                                    </div>
                                                    <input
                                                        type="text"
                                                        value={settings.membership_platform_url || ""}
                                                        onChange={(e) => updateSetting("membership_platform_url", e.target.value)}
                                                        className={cn(
                                                            "w-full bg-zinc-950/50 border rounded-2xl py-4 px-6 text-white text-sm focus:ring-2 outline-none transition-all",
                                                            errors.membership_platform_url ? "border-red-500/50 ring-red-500/20" : "border-white/5 ring-primary/50"
                                                        )}
                                                        placeholder="https://patreon.com/your-name"
                                                    />
                                                </div>
                                                <div className="space-y-2">
                                                    <div className="flex justify-between items-center px-2">
                                                        <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest transition-colors">Lead Magnet / Lead Gen URL</label>
                                                        {errors.lead_gen_url && <span className="text-[9px] font-bold text-red-500 uppercase tracking-tighter">{errors.lead_gen_url.message}</span>}
                                                    </div>
                                                    <input
                                                        type="text"
                                                        value={settings.lead_gen_url || ""}
                                                        onChange={(e) => updateSetting("lead_gen_url", e.target.value)}
                                                        className={cn(
                                                            "w-full bg-zinc-950/50 border rounded-2xl py-4 px-6 text-white text-sm focus:ring-2 outline-none transition-all",
                                                            errors.lead_gen_url ? "border-red-500/50 ring-red-500/20" : "border-white/5 ring-emerald-500/50"
                                                        )}
                                                        placeholder="https://your-site.com/free-guide"
                                                    />
                                                </div>
                                            </div>
                                        </div>

                                        <div className="space-y-6">
                                            <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-500 mb-6">Product Vectors</h4>
                                            <div className="space-y-4">
                                                <div className="space-y-2">
                                                    <div className="flex justify-between items-center px-2">
                                                        <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest transition-colors">Online Academy / Course URL</label>
                                                        {errors.course_platform_url && <span className="text-[9px] font-bold text-red-500 uppercase tracking-tighter">{errors.course_platform_url.message}</span>}
                                                    </div>
                                                    <input
                                                        type="text"
                                                        value={settings.course_platform_url || ""}
                                                        onChange={(e) => updateSetting("course_platform_url", e.target.value)}
                                                        className={cn(
                                                            "w-full bg-zinc-950/50 border rounded-2xl py-4 px-6 text-white text-sm focus:ring-2 outline-none transition-all",
                                                            errors.course_platform_url ? "border-red-500/50 ring-red-500/20" : "border-white/5 ring-primary/50"
                                                        )}
                                                        placeholder="https://your-academy.com/course"
                                                    />
                                                </div>
                                                <div className="space-y-2">
                                                    <div className="flex justify-between items-center px-2">
                                                        <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest transition-colors">Digital Downloads Store</label>
                                                        {errors.digital_product_url && <span className="text-[9px] font-bold text-red-500 uppercase tracking-tighter">{errors.digital_product_url.message}</span>}
                                                    </div>
                                                    <input
                                                        type="text"
                                                        value={settings.digital_product_url || ""}
                                                        onChange={(e) => updateSetting("digital_product_url", e.target.value)}
                                                        className={cn(
                                                            "w-full bg-zinc-950/50 border rounded-2xl py-4 px-6 text-white text-sm focus:ring-2 outline-none transition-all",
                                                            errors.digital_product_url ? "border-red-500/50 ring-red-500/20" : "border-white/5 ring-amber-500/50"
                                                        )}
                                                        placeholder="https://gumroad.com/your-store"
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Support & AI Autonomy */}
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-10 pt-10 border-t border-white/5">
                                        <div className="space-y-6">
                                            <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-500 mb-6">Support & Capital</h4>
                                            <div className="space-y-4">
                                                <div className="space-y-2">
                                                    <div className="flex justify-between items-center px-2">
                                                        <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest transition-colors">Donation/Tip Link</label>
                                                        {errors.donation_link && <span className="text-[9px] font-bold text-red-500 uppercase tracking-tighter">{errors.donation_link.message}</span>}
                                                    </div>
                                                    <input
                                                        type="text"
                                                        value={settings.donation_link || ""}
                                                        onChange={(e) => updateSetting("donation_link", e.target.value)}
                                                        className={cn(
                                                            "w-full bg-zinc-950/50 border rounded-2xl py-4 px-6 text-white text-sm focus:ring-2 outline-none transition-all",
                                                            errors.donation_link ? "border-red-500/50 ring-red-500/20" : "border-white/5 ring-primary/50"
                                                        )}
                                                        placeholder="https://buymeacoffee.com/name"
                                                    />
                                                </div>
                                                <div className="space-y-2">
                                                    <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest pl-2">Crypto Node Addresses</label>
                                                    <input
                                                        type="text"
                                                        value={settings.crypto_wallets || ""}
                                                        onChange={(e) => updateSetting("crypto_wallets", e.target.value)}
                                                        className="w-full bg-zinc-950/50 border border-white/5 rounded-2xl py-4 px-6 text-white text-sm focus:ring-2 ring-primary/50 outline-none transition-all"
                                                        placeholder="BTC: 0x..., ETH: 0x..."
                                                    />
                                                </div>
                                            </div>
                                        </div>

                                        <div className="space-y-6">
                                            <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-500 mb-6">AI Autonomy</h4>
                                            <div className="space-y-4">
                                                <ToggleSwitch
                                                    label="AI Product Matching"
                                                    description="Auto-match viral trends to assets"
                                                    checked={settings.ai_matching_enabled === "true"}
                                                    onChange={(val) => updateSetting("ai_matching_enabled", val ? "true" : "false")}
                                                />
                                                <ToggleSwitch
                                                    label="Auto-Promo Generation"
                                                    description="LLM-driven sales script injection"
                                                    checked={settings.auto_promo_enabled === "true"}
                                                    onChange={(val) => updateSetting("auto_promo_enabled", val ? "true" : "false")}
                                                />
                                            </div>
                                        </div>
                                    </div>

                                    {/* Brands */}
                                    <div className="space-y-6 pt-10 border-t border-white/5">
                                        <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-500 mb-6">Brand Partnerships</h4>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                                            <div className="space-y-2">
                                                <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest pl-2">Sponsorship Protocol (Email/URL)</label>
                                                <input
                                                    type="text"
                                                    value={settings.sponsorship_contact || ""}
                                                    onChange={(e) => updateSetting("sponsorship_contact", e.target.value)}
                                                    className="w-full bg-zinc-950/50 border border-white/5 rounded-2xl py-4 px-6 text-white text-sm focus:ring-2 ring-primary/50 outline-none transition-all"
                                                    placeholder="sponsorships@yourdomain.com"
                                                />
                                            </div>
                                            <div className="space-y-2">
                                                <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest pl-2">Active Node Partners</label>
                                                <input
                                                    type="text"
                                                    value={settings.brand_partners || ""}
                                                    onChange={(e) => updateSetting("brand_partners", e.target.value)}
                                                    className="w-full bg-zinc-950/50 border border-white/5 rounded-2xl py-4 px-6 text-white text-sm focus:ring-2 ring-primary/50 outline-none transition-all"
                                                    placeholder="Stripe, AWS, DigitalOcean"
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </section>
                        ) : activeTab === "Engine" ? (
                            <section className="card-gradient border border-white/5 rounded-[2.5rem] p-12 space-y-12 shadow-2xl relative overflow-hidden">
                                <div className="flex items-center gap-6">
                                    <div className="h-20 w-20 rounded-3xl bg-orange-500/10 flex items-center justify-center border border-orange-500/20 shadow-[0_0_30px_rgba(249,115,22,0.15)]">
                                        <Sparkles className="h-10 w-10 text-orange-500" />
                                    </div>
                                    <div>
                                        <h3 className="text-4xl font-black text-white uppercase tracking-tighter">Personal <span className="text-hollow">Engine</span></h3>
                                        <p className="text-zinc-500 text-sm mt-1 uppercase tracking-widest font-black opacity-60">Aesthetic and performance quality overrides</p>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-12 pt-10 border-t border-white/5">
                                    <div className="space-y-10">
                                        <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-500">Feature Injectors</h4>
                                        <div className="space-y-6">
                                            <ToggleSwitch
                                                label="Neural Audio"
                                                description="High-fidelity sound design"
                                                checked={settings.enable_sound_design === "true"}
                                                onChange={(val) => updateSetting("enable_sound_design", val ? "true" : "false")}
                                            />
                                            <ToggleSwitch
                                                label="Motion Graphics"
                                                description="Procedural visual enhancement"
                                                checked={settings.enable_motion_graphics === "true"}
                                                onChange={(val) => updateSetting("enable_motion_graphics", val ? "true" : "false")}
                                            />
                                        </div>
                                    </div>
                                    <div className="space-y-10">
                                        <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-500">Quality Vectors</h4>
                                        <div className="space-y-8">
                                            <div className="space-y-3">
                                                <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest pl-2">Inference Provider</label>
                                                <div className="grid grid-cols-2 gap-4">
                                                    {['runway', 'pika'].map((p) => (
                                                        <button
                                                            key={p}
                                                            onClick={() => updateSetting("ai_video_provider", p)}
                                                            className={cn(
                                                                "py-3 px-4 rounded-xl border font-black uppercase text-[10px] tracking-widest transition-all",
                                                                settings.ai_video_provider === p ? "bg-primary/20 border-primary text-primary" : "bg-zinc-950/50 border-white/5 text-zinc-600 hover:text-white"
                                                            )}
                                                        >
                                                            {p}
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                            <div className="space-y-3">
                                                <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest pl-2">Processing Tier</label>
                                                <div className="grid grid-cols-3 gap-3">
                                                    {['standard', 'enhanced', 'premium'].map((t) => (
                                                        <button
                                                            key={t}
                                                            onClick={() => updateSetting("default_quality_tier", t)}
                                                            className={cn(
                                                                "py-3 px-2 rounded-xl border font-black uppercase text-[8px] tracking-[0.2em] transition-all",
                                                                settings.default_quality_tier === t ? "bg-emerald-500/20 border-emerald-500 text-emerald-500 shadow-[0_0_20px_rgba(16,185,129,0.2)]" : "bg-zinc-950/50 border-white/5 text-zinc-600 hover:text-white"
                                                            )}
                                                        >
                                                            {t}
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </section>
                        ) : activeTab === "opencli" ? (
                            <OpenCLITab />
                        ) : null}
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}

function OpenCLITab() {
    const [sessions, setSessions] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [available, setAvailable] = useState(false);
    const [connectModal, setConnectModal] = useState<{ open: boolean; platform: string }>({ open: false, platform: "" });
    const [cookies, setCookies] = useState("");
    const [connecting, setConnecting] = useState(false);
    const [statusMsg, setStatusMsg] = useState("");

    const fetchSessions = async () => {
        await withRealFallback(
            async () => {
                const token = localStorage.getItem("et_token");
                return fetch(`${API_BASE}/opencli/sessions`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
            },
            {
                fallback: { sessions: [], available: false },
                onSuccess: (data: any) => {
                    setSessions(data.sessions || []);
                    setAvailable(data.available || false);
                },
                onFallback: (err: any) => {
                    if (err.status === 404) setAvailable(false);
                }
            }
        );
        setLoading(false);
    };

    useEffect(() => { fetchSessions(); }, []);

    const connectPlatform = async () => {
        if (!cookies.trim() || !connectModal.platform) return;
        setConnecting(true);
        setStatusMsg("");
        await withRealFallback(
            async () => {
                const token = localStorage.getItem("et_token");
                return fetch(`${API_BASE}/opencli/sessions/connect`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                    body: JSON.stringify({ platform: connectModal.platform, cookies })
                });
            },
            {
                fallback: null,
                onSuccess: (data: any) => {
                    setStatusMsg(data.status === "connected" ? "Connected successfully!" : `Status: ${data.status} — ${data.message}`);
                    setCookies("");
                    toast.success("Bridge Established", { description: `${connectModal.platform} linked.` });
                    fetchSessions();
                },
                onFallback: (err: any) => {
                    setStatusMsg(`Error: ${err.message || "Connection failed"}`);
                    toast.error("Bridge Failed", { description: err.message });
                }
            }
        );
        setConnecting(false);
    };

    const disconnectPlatform = async (platform: string) => {
        await withRealFallback(
            async () => {
                const token = localStorage.getItem("et_token");
                return fetch(`${API_BASE}/opencli/sessions/disconnect/${platform}`, {
                    method: "POST",
                    headers: { Authorization: `Bearer ${token}` }
                });
            },
            {
                fallback: null,
                onSuccess: () => {
                    toast.info("Bridge Terminated", { description: `${platform} session purged.` });
                    fetchSessions();
                },
                onFallback: (err: any) => {
                    toast.error("Disconnect Failed", { description: err.message });
                }
            }
        );
    };

    const verifyPlatform = async (platform: string) => {
        await withRealFallback(
            async () => {
                const token = localStorage.getItem("et_token");
                return fetch(`${API_BASE}/opencli/sessions/verify/${platform}`, {
                    method: "POST",
                    headers: { Authorization: `Bearer ${token}` }
                });
            },
            {
                fallback: null,
                onSuccess: (data: any) => {
                    setStatusMsg(`${platform}: ${data.status} — ${data.message}`);
                    toast.success("Session Verified", { description: `${platform} is operational.` });
                    fetchSessions();
                },
                onFallback: (err: any) => {
                    toast.error("Verification Error", { description: err.message });
                }
            }
        );
    };

    if (loading) {
        return <div className="h-96 flex items-center justify-center"><Loader2 className="h-12 w-12 text-primary animate-spin" /></div>;
    }

    if (!available) {
        return (
            <section className="card-gradient border border-white/5 rounded-[2.5rem] p-12 space-y-8 shadow-2xl">
                <div className="flex items-center gap-6">
                    <div className="h-20 w-20 rounded-3xl bg-red-500/10 flex items-center justify-center border border-red-500/20">
                        <Globe className="h-10 w-10 text-red-500" />
                    </div>
                    <div>
                        <h3 className="text-4xl font-black text-white uppercase tracking-tighter">Browser <span className="text-hollow">Bridge</span></h3>
                        <p className="text-zinc-500 text-sm mt-1 uppercase tracking-widest font-black opacity-60">opencli-rs not available</p>
                    </div>
                </div>
                <div className="pt-10 border-t border-white/5 space-y-4">
                    <p className="text-zinc-400">The opencli-rs binary is not installed or the feature is disabled.</p>
                    <div className="bg-zinc-900/50 rounded-xl p-6 font-mono text-sm text-zinc-300 space-y-2">
                        <p className="text-zinc-500"># Install opencli-rs</p>
                        <p>cargo install opencli-rs</p>
                        <p className="text-zinc-500 mt-4"># Enable in .env</p>
                        <p>ENABLE_OPENCLI=true</p>
                    </div>
                </div>
            </section>
        );
    }

    const connected = sessions.filter(s => s.status === "connected");
    const disconnected = sessions.filter(s => s.status === "disconnected");
    const expired = sessions.filter(s => s.status === "expired" || s.status === "error");

    return (
        <section className="card-gradient border border-white/5 rounded-[2.5rem] p-12 space-y-12 shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 p-8 opacity-5">
                <Globe className="h-32 w-32 text-white" />
            </div>
            <div className="flex items-center gap-6 relative z-10">
                <div className="h-20 w-20 rounded-3xl bg-cyan-500/10 flex items-center justify-center border border-cyan-500/20 shadow-[0_0_30px_rgba(6,182,212,0.15)]">
                    <Globe className="h-10 w-10 text-cyan-500" />
                </div>
                <div>
                    <h3 className="text-4xl font-black text-white uppercase tracking-tighter">Browser <span className="text-hollow">Bridge</span></h3>
                    <p className="text-zinc-500 text-sm mt-1 uppercase tracking-widest font-black opacity-60">Connect your Chrome sessions — no API keys needed</p>
                </div>
                <button onClick={fetchSessions} className="ml-auto p-3 rounded-xl bg-zinc-900/50 border border-white/5 hover:border-primary/20 transition-all">
                    <RefreshCw className="h-5 w-5 text-zinc-400" />
                </button>
            </div>

            {statusMsg && (
                <div className={`rounded-xl p-4 text-sm ${statusMsg.startsWith("Error") ? "bg-red-500/10 text-red-400 border border-red-500/20" : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"}`}>
                    {statusMsg}
                </div>
            )}

            {/* Connected Platforms */}
            {connected.length > 0 && (
                <div className="space-y-4 relative z-10">
                    <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-emerald-500">Connected ({connected.length})</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {connected.map(s => (
                            <div key={s.platform} className="bg-emerald-500/5 border border-emerald-500/20 rounded-2xl p-6 space-y-3">
                                <div className="flex items-center justify-between">
                                    <span className="font-black uppercase text-sm text-white">{s.platform}</span>
                                    <span className="text-[8px] uppercase tracking-widest text-emerald-500 font-bold">Live</span>
                                </div>
                                <div className="flex flex-wrap gap-1">
                                    {(s.capabilities || []).slice(0, 4).map((c: string) => (
                                        <span key={c} className="text-[8px] uppercase tracking-wider bg-zinc-800/50 px-2 py-1 rounded text-zinc-400">{c}</span>
                                    ))}
                                </div>
                                <div className="flex gap-2">
                                    <button onClick={() => verifyPlatform(s.platform)} className="text-[10px] uppercase tracking-wider text-zinc-500 hover:text-white transition-colors">Verify</button>
                                    <button onClick={() => disconnectPlatform(s.platform)} className="text-[10px] uppercase tracking-wider text-red-500/60 hover:text-red-400 transition-colors flex items-center gap-1">
                                        <Unlink className="h-3 w-3" /> Disconnect
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Expired/Error Platforms */}
            {expired.length > 0 && (
                <div className="space-y-4 relative z-10">
                    <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-amber-500">Needs Attention ({expired.length})</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {expired.map(s => (
                            <div key={s.platform} className="bg-amber-500/5 border border-amber-500/20 rounded-2xl p-6 space-y-3">
                                <div className="flex items-center justify-between">
                                    <span className="font-black uppercase text-sm text-white">{s.platform}</span>
                                    <span className="text-[8px] uppercase tracking-widest text-amber-500 font-bold">{s.status}</span>
                                </div>
                                <p className="text-[10px] text-zinc-500">{s.message}</p>
                                <button
                                    onClick={() => { setConnectModal({ open: true, platform: s.platform }); setCookies(""); setStatusMsg(""); }}
                                    className="text-[10px] uppercase tracking-wider text-amber-500 hover:text-amber-400 transition-colors flex items-center gap-1"
                                >
                                    <RefreshCw className="h-3 w-3" /> Reconnect
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Available Platforms to Connect */}
            <div className="space-y-4 relative z-10 pt-10 border-t border-white/5">
                <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-500">Available Platforms</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                    {disconnected.map(s => (
                        <button
                            key={s.platform}
                            onClick={() => { setConnectModal({ open: true, platform: s.platform }); setCookies(""); setStatusMsg(""); }}
                            className="bg-zinc-900/50 border border-white/5 rounded-xl p-4 text-center hover:border-primary/20 hover:bg-primary/5 transition-all group"
                        >
                            <Link2 className="h-5 w-5 text-zinc-600 group-hover:text-primary mx-auto mb-2" />
                            <span className="text-[10px] font-black uppercase tracking-wider text-zinc-500 group-hover:text-white">{s.platform}</span>
                        </button>
                    ))}
                </div>
            </div>

            {/* Connect Modal */}
            {connectModal.open && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={() => setConnectModal({ open: false, platform: "" })}>
                    <div className="bg-zinc-950 border border-white/10 rounded-3xl p-10 max-w-lg w-full mx-4 space-y-6" onClick={e => e.stopPropagation()}>
                        <h3 className="text-2xl font-black text-white uppercase tracking-tight">
                            Connect <span className="text-primary">{connectModal.platform}</span>
                        </h3>
                        <p className="text-zinc-500 text-sm">
                            Paste your Chrome session cookies from the opencli extension.
                            Log into {connectModal.platform} in Chrome first, then use the extension to export cookies.
                        </p>
                        <textarea
                            value={cookies}
                            onChange={e => setCookies(e.target.value)}
                            placeholder="# Netscape HTTP Cookie File&#10;# Exported from opencli Chrome extension&#10;.youtube.com  TRUE  /  TRUE  0  SID  xxxxxxx"
                            className="w-full h-40 bg-zinc-900/50 border border-white/10 rounded-xl p-4 text-sm font-mono text-zinc-300 placeholder:text-zinc-700 focus:outline-none focus:border-primary/30 resize-none"
                        />
                        <div className="flex gap-3">
                            <button
                                onClick={connectPlatform}
                                disabled={connecting || !cookies.trim()}
                                className="flex-1 py-3 rounded-xl bg-primary/20 border border-primary/30 text-primary font-black uppercase text-[10px] tracking-widest hover:bg-primary/30 transition-all disabled:opacity-30"
                            >
                                {connecting ? "Connecting..." : "Connect"}
                            </button>
                            <button
                                onClick={() => setConnectModal({ open: false, platform: "" })}
                                className="py-3 px-6 rounded-xl bg-zinc-900/50 border border-white/10 text-zinc-500 font-black uppercase text-[10px] tracking-widest hover:text-white transition-all"
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </section>
    );
}

function TabItem({ icon, label, active, onClick }: { icon: React.ReactNode, label: string, active: boolean, onClick: () => void }) {
    return (
        <button
            onClick={onClick}
            className={cn(
                "w-full flex items-center gap-4 px-8 py-5 rounded-2xl transition-all group relative overflow-hidden",
                active
                    ? "bg-primary/10 text-primary border border-primary/20 shadow-[0_10px_30px_rgba(var(--primary-rgb),0.1)]"
                    : "text-zinc-500 hover:text-white hover:bg-white/5 border border-transparent"
            )}
        >
            <div className={cn(
                "transition-all duration-300",
                active ? "scale-110" : "group-hover:scale-110 grayscale opacity-50 group-hover:grayscale-0 group-hover:opacity-100"
            )}>
                {icon}
            </div>
            <span className="font-black text-xs uppercase tracking-[0.2em]">{label}</span>
            {active && (
                <div className="absolute right-4 w-1.5 h-1.5 rounded-full bg-primary shadow-[0_0_10px_rgba(var(--primary-rgb),0.5)]" />
            )}
        </button>
    );
}

function KeyInput({ label, id, value, onChange, isVisible, onToggle, placeholder, error }: { label: string, id: string, value: string, onChange: (val: string) => void, isVisible: boolean, onToggle: () => void, placeholder?: string, error?: string }) {
    return (
        <div className="space-y-3 group">
            <div className="flex justify-between items-center px-2">
                <label htmlFor={id} className={cn("text-[10px] font-black uppercase tracking-[0.2em] transition-colors", error ? "text-red-500" : "text-zinc-500 group-focus-within:text-primary")}>{label}</label>
                {error && <span className="text-[9px] font-bold text-red-500 uppercase tracking-tighter">{error}</span>}
            </div>
            <div className="relative">
                <input
                    id={id}
                    type={isVisible ? "text" : "password"}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    placeholder={placeholder || "••••••••••••••••"}
                    className={cn(
                        "w-full bg-zinc-950/50 border rounded-2xl py-5 pl-8 pr-16 text-white font-mono text-sm focus:ring-2 outline-none transition-all",
                        error ? "border-red-500/50 ring-red-500/20" : "border-white/5 focus:ring-primary/30 border-white/10"
                    )}
                />
                <button
                    onClick={onToggle}
                    className="absolute right-6 top-1/2 -translate-y-1/2 text-zinc-600 hover:text-white transition-colors p-2"
                >
                    {isVisible ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
            </div>
        </div>
    );
}

function ToggleSwitch({ label, description, checked, onChange }: { label: string, description: string, checked: boolean, onChange: (val: boolean) => void }) {
    return (
        <div className="p-6 bg-zinc-950/50 border border-white/5 rounded-[1.5rem] flex items-center justify-between group hover:border-white/10 transition-all shadow-lg">
            <div className="space-y-1">
                <span className="text-sm font-black text-white block uppercase tracking-tight group-hover:text-primary transition-colors">{label}</span>
                <p className="text-[10px] text-zinc-500 uppercase font-black tracking-widest opacity-60">{description}</p>
            </div>
            <button
                onClick={() => onChange(!checked)}
                className={cn(
                    "w-14 h-7 rounded-full relative transition-all duration-500 p-1",
                    checked ? "bg-primary shadow-[0_0_25px_rgba(var(--primary-rgb),0.4)]" : "bg-zinc-800"
                )}
            >
                <div className={cn(
                    "w-5 h-5 bg-white rounded-full transition-all duration-500 shadow-xl",
                    checked ? "translate-x-7" : "translate-x-0"
                )} />
            </button>
        </div>
    );
}
