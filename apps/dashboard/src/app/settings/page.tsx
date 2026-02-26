"use client";

import React, { useState, useEffect } from "react";
import DashboardLayout from "@/components/layout";
import { useUI } from "@/context/UIContext";
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
    TrendingUp
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";

export default function SettingsPage() {
    const { isProMode, toggleProMode } = useUI();
    const [showKey, setShowKey] = useState<Record<string, boolean>>({});
    const [settings, setSettings] = useState<Record<string, string>>({
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
    });
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [saveStatus, setSaveStatus] = useState<"idle" | "success" | "error">("idle");
    const [activeTab, setActiveTab] = useState("Profile");
    const [userProfile, setUserProfile] = useState<{ telegram_chat_id: string, telegram_token: string, role: string, subscription: string }>({
        telegram_chat_id: "",
        telegram_token: "",
        role: "user",
        subscription: "free"
    });

    const toggleKey = (id: string) => {
        setShowKey(prev => ({ ...prev, [id]: !prev[id] }));
    };

    const fetchSettings = async () => {
        setIsLoading(true);
        try {
            const token = localStorage.getItem("et_token");
            const headers = { Authorization: `Bearer ${token}` };
            const response = await fetch(`${API_BASE}/settings/`, { headers });
            const data = await response.json();
            if (Object.keys(data).length > 0) {
                setSettings(prev => ({ ...prev, ...data }));
            }
        } catch (error) {
            console.error("Failed to fetch settings", error);
        } finally {
            setIsLoading(false);
        }
    };

    const fetchProfile = async () => {
        try {
            const token = localStorage.getItem("et_token");
            const response = await fetch(`${API_BASE}/auth/me`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                setUserProfile({
                    telegram_chat_id: data.telegram_chat_id || "",
                    telegram_token: data.telegram_token || "",
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
        } catch (error) {
            console.error("Failed to fetch profile", error);
        }
    };

    const handleSave = async () => {
        setIsSaving(true);
        setSaveStatus("idle");
        try {
            const token = localStorage.getItem("et_token");

            if (userProfile.role === "admin") {
                const payload = Object.entries(settings).map(([key, value]) => ({
                    key,
                    value,
                    category: key.includes("key") || key.includes("id") ? "api_key" : "engine"
                }));

                const response = await fetch(`${API_BASE}/settings/bulk`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${token}`
                    },
                    body: JSON.stringify(payload)
                });

                if (!response.ok) {
                    setSaveStatus("error");
                    setIsSaving(false);
                    return;
                }
            }

            const profileRes = await fetch(`${API_BASE}/auth/me`, {
                method: "PATCH",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    telegram_chat_id: userProfile.telegram_chat_id || null,
                    telegram_token: userProfile.telegram_token || null
                })
            });

            if (profileRes.ok) {
                setSaveStatus("success");
                setTimeout(() => setSaveStatus("idle"), 3000);
            } else {
                setSaveStatus("error");
            }
        } catch (error) {
            setSaveStatus("error");
        } finally {
            setIsSaving(false);
        }
    };

    useEffect(() => {
        fetchProfile();
    }, []);

    const updateSetting = (key: string, value: string) => {
        setSettings(prev => ({ ...prev, [key]: value }));
    };

    return (
        <DashboardLayout>
            <div className="section-container relative pb-20">
                <div className="flex items-center justify-between mb-10">
                    <div>
                        <div className="flex items-center gap-3 mb-1">
                            <h1 className="text-5xl md:text-6xl font-black italic uppercase tracking-tighter text-white">My <span className="text-transparent bg-clip-text bg-gradient-to-r from-zinc-400 to-white text-hollow">Settings</span></h1>
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
                        <p className="text-zinc-500 text-sm italic font-bold tracking-tight">Configure personal overrides and manage your identity.</p>
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
                                        <h3 className="text-4xl font-black text-white italic uppercase tracking-tighter">Private <span className="text-hollow">Overrides</span></h3>
                                        <p className="text-zinc-500 text-sm mt-1 uppercase tracking-widest font-black opacity-60">Personal vault for high-priority secrets</p>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-10 pt-10 border-t border-white/5 relative z-10">
                                    <KeyInput
                                        label="Groq API Key"
                                        id="groq_api_key"
                                        value={settings.groq_api_key}
                                        onChange={(val) => updateSetting("groq_api_key", val)}
                                        isVisible={showKey["groq_api_key"]}
                                        onToggle={() => toggleKey("groq_api_key")}
                                    />
                                    <KeyInput
                                        label="YouTube Data API v3"
                                        id="youtube_api_key"
                                        value={settings.youtube_api_key}
                                        onChange={(val) => updateSetting("youtube_api_key", val)}
                                        isVisible={showKey["youtube_api_key"]}
                                        onToggle={() => toggleKey("youtube_api_key")}
                                    />
                                    <KeyInput
                                        label="ElevenLabs Key"
                                        id="elevenlabs_api_key"
                                        value={settings.elevenlabs_api_key}
                                        onChange={(val) => updateSetting("elevenlabs_api_key", val)}
                                        isVisible={showKey["elevenlabs_api_key"]}
                                        onToggle={() => toggleKey("elevenlabs_api_key")}
                                    />
                                    <KeyInput
                                        label="Pexels/Pixabay API"
                                        id="pexels_api_key"
                                        value={settings.pexels_api_key}
                                        onChange={(val) => updateSetting("pexels_api_key", val)}
                                        isVisible={showKey["pexels_api_key"]}
                                        onToggle={() => toggleKey("pexels_api_key")}
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
                                        <h3 className="text-4xl font-black text-white italic uppercase tracking-tighter">Nexus <span className="text-hollow">Comms</span></h3>
                                        <p className="text-zinc-500 text-sm mt-1 uppercase tracking-widest font-black opacity-60">Inbound alerts and autonomous status updates</p>
                                    </div>
                                </div>

                                <div className="space-y-8 pt-10 border-t border-white/5">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                                        <div className="space-y-2">
                                            <label className="text-[10px] font-black text-zinc-500 uppercase tracking-[0.2em] mb-3 block">Telegram Identity</label>
                                            <input
                                                type="text"
                                                value={userProfile.telegram_chat_id}
                                                onChange={(e) => setUserProfile({ ...userProfile, telegram_chat_id: e.target.value })}
                                                className="w-full bg-zinc-950/50 border border-white/5 rounded-2xl py-4 px-6 text-white font-black text-sm focus:ring-2 ring-primary/50 outline-none transition-all"
                                                placeholder="Chat ID (e.g. 12345678)"
                                            />
                                            <p className="text-[10px] text-zinc-600 uppercase font-bold pl-2">Get your ID via @userinfobot</p>
                                        </div>
                                        <KeyInput
                                            label="Bot Token Override"
                                            id="telegram_token"
                                            value={userProfile.telegram_token}
                                            onChange={(val) => setUserProfile({ ...userProfile, telegram_token: val })}
                                            isVisible={showKey["tg_token"]}
                                            onToggle={() => toggleKey("tg_token")}
                                            placeholder="XXXX:YYYYYYYYY"
                                        />
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
                                        <h3 className="text-4xl font-black text-white italic uppercase tracking-tighter">User <span className="text-hollow">Identity</span></h3>
                                        <p className="text-zinc-500 text-sm mt-1 uppercase tracking-widest font-black opacity-60">Authentication and authorization parameters</p>
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
                                                <div className="text-2xl font-black text-white uppercase italic">{userProfile.role}</div>
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
                                                <div className="text-2xl font-black text-white uppercase italic">{userProfile.subscription}</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </section>
                        ) : activeTab === "Billing" ? (
                            <section className="card-gradient border border-white/5 rounded-[2.5rem] p-12 space-y-12 shadow-2xl relative overflow-hidden">
                                <div className="flex items-center gap-6">
                                    <div className="h-20 w-20 rounded-3xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20 shadow-[0_0_30px_rgba(16,185,129,0.15)]">
                                        <CreditCard className="h-10 w-10 text-emerald-500" />
                                    </div>
                                    <div>
                                        <h3 className="text-4xl font-black text-white italic uppercase tracking-tighter">Empire <span className="text-hollow">Credits</span></h3>
                                        <p className="text-zinc-500 text-sm mt-1 uppercase tracking-widest font-black opacity-60">Monetization limits and resource allocation</p>
                                    </div>
                                </div>

                                <div className="pt-10 border-t border-white/5">
                                    <div className="bg-zinc-950/50 border border-emerald-500/20 rounded-[2rem] p-10 text-center space-y-6">
                                        <h4 className="text-[10px] font-black uppercase text-emerald-500 tracking-[0.3em]">Status: Transmission Optimized</h4>
                                        <p className="text-zinc-400 max-w-md mx-auto text-sm font-bold">Your current {userProfile.subscription} tier handles up to 300 autonomous distributions.</p>
                                        <button className="bg-emerald-500 hover:bg-emerald-600 text-white font-black py-5 px-12 rounded-2xl transition-all shadow-[0_0_40px_rgba(16,185,129,0.3)] uppercase tracking-[0.2em] text-[10px]">
                                            Expand Empire
                                        </button>
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
                                        <h3 className="text-4xl font-black text-white italic uppercase tracking-tighter">Growth <span className="text-hollow">Monetization</span></h3>
                                        <p className="text-zinc-500 text-sm mt-1 uppercase tracking-widest font-black opacity-60">Revenue streams and audience support vectors</p>
                                    </div>
                                </div>

                                <div className="space-y-12 pt-10 border-t border-white/5">
                                    {/* Precision Distribution Control */}
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                                        <div className="space-y-6">
                                            <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-500 mb-6 italic">Precision Control</h4>
                                            <div className="space-y-8">
                                                <div className="p-6 bg-zinc-950/50 border border-white/5 rounded-2xl space-y-4">
                                                    <div className="flex justify-between items-center">
                                                        <label className="text-[10px] font-black text-zinc-400 uppercase tracking-widest">Aggression Level</label>
                                                        <span className="text-primary font-black text-sm italic">{settings.monetization_aggression}%</span>
                                                    </div>
                                                    <input
                                                        type="range"
                                                        min="0"
                                                        max="100"
                                                        value={settings.monetization_aggression}
                                                        onChange={(e) => updateSetting("monetization_aggression", e.target.value)}
                                                        className="w-full h-1 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-primary"
                                                    />
                                                    <p className="text-[9px] text-zinc-600 uppercase font-bold text-center tracking-tighter italic">Controls frequency of monetization pitch injection</p>
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
                                            <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-500 mb-6 italic">Active Strategy</h4>
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
                                                    <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest pl-2">Membership Platform (Patreon/Substack)</label>
                                                    <input
                                                        type="text"
                                                        value={settings.membership_platform_url}
                                                        onChange={(e) => updateSetting("membership_platform_url", e.target.value)}
                                                        className="w-full bg-zinc-950/50 border border-white/5 rounded-2xl py-4 px-6 text-white text-sm focus:ring-2 ring-primary/50 outline-none transition-all"
                                                        placeholder="https://patreon.com/your-name"
                                                    />
                                                </div>
                                                <div className="space-y-2">
                                                    <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest pl-2">Lead Magnet / Lead Gen URL</label>
                                                    <input
                                                        type="text"
                                                        value={settings.lead_gen_url || ""}
                                                        onChange={(e) => updateSetting("lead_gen_url", e.target.value)}
                                                        className="w-full bg-zinc-950/50 border border-white/5 rounded-2xl py-4 px-6 text-white text-sm focus:ring-2 ring-emerald-500/50 outline-none transition-all"
                                                        placeholder="https://your-site.com/free-guide"
                                                    />
                                                </div>
                                            </div>
                                        </div>

                                        <div className="space-y-6">
                                            <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-500 mb-6">Product Vectors</h4>
                                            <div className="space-y-4">
                                                <div className="space-y-2">
                                                    <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest pl-2">Online Academy / Course URL</label>
                                                    <input
                                                        type="text"
                                                        value={settings.course_platform_url}
                                                        onChange={(e) => updateSetting("course_platform_url", e.target.value)}
                                                        className="w-full bg-zinc-950/50 border border-white/5 rounded-2xl py-4 px-6 text-white text-sm focus:ring-2 ring-primary/50 outline-none transition-all"
                                                        placeholder="https://your-academy.com/course"
                                                    />
                                                </div>
                                                <div className="space-y-2">
                                                    <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest pl-2">Digital Downloads Store</label>
                                                    <input
                                                        type="text"
                                                        value={settings.digital_product_url || ""}
                                                        onChange={(e) => updateSetting("digital_product_url", e.target.value)}
                                                        className="w-full bg-zinc-950/50 border border-white/5 rounded-2xl py-4 px-6 text-white text-sm focus:ring-2 ring-amber-500/50 outline-none transition-all"
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
                                                    <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest pl-2">Donation/Tip Link</label>
                                                    <input
                                                        type="text"
                                                        value={settings.donation_link}
                                                        onChange={(e) => updateSetting("donation_link", e.target.value)}
                                                        className="w-full bg-zinc-950/50 border border-white/5 rounded-2xl py-4 px-6 text-white text-sm focus:ring-2 ring-primary/50 outline-none transition-all"
                                                        placeholder="https://buymeacoffee.com/name"
                                                    />
                                                </div>
                                                <div className="space-y-2">
                                                    <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest pl-2">Crypto Node Addresses</label>
                                                    <input
                                                        type="text"
                                                        value={settings.crypto_wallets}
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
                                        <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-500 mb-6 italic">Brand Partnerships</h4>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                                            <div className="space-y-2">
                                                <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest pl-2">Sponsorship Protocol (Email/URL)</label>
                                                <input
                                                    type="text"
                                                    value={settings.sponsorship_contact}
                                                    onChange={(e) => updateSetting("sponsorship_contact", e.target.value)}
                                                    className="w-full bg-zinc-950/50 border border-white/5 rounded-2xl py-4 px-6 text-white text-sm focus:ring-2 ring-primary/50 outline-none transition-all"
                                                    placeholder="sponsorships@yourdomain.com"
                                                />
                                            </div>
                                            <div className="space-y-2">
                                                <label className="text-[10px] font-black text-zinc-500 uppercase tracking-widest pl-2">Active Node Partners</label>
                                                <input
                                                    type="text"
                                                    value={settings.brand_partners}
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
                                        <h3 className="text-4xl font-black text-white italic uppercase tracking-tighter">Personal <span className="text-hollow">Engine</span></h3>
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
                        ) : null}
                    </div>
                </div>
            </div>
        </DashboardLayout>
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

function KeyInput({ label, id, value, onChange, isVisible, onToggle, placeholder }: { label: string, id: string, value: string, onChange: (val: string) => void, isVisible: boolean, onToggle: () => void, placeholder?: string }) {
    return (
        <div className="space-y-3 group">
            <label htmlFor={id} className="text-[10px] font-black text-zinc-500 uppercase tracking-[0.2em] pl-2 transition-colors group-focus-within:text-primary">{label}</label>
            <div className="relative">
                <input
                    id={id}
                    type={isVisible ? "text" : "password"}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    placeholder={placeholder || "••••••••••••••••"}
                    className="w-full bg-zinc-950/50 border border-white/5 rounded-2xl py-5 pl-8 pr-16 text-white font-mono text-sm focus:ring-2 ring-primary/30 outline-none transition-all border-white/10"
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
                <span className="text-sm font-black text-white block uppercase italic tracking-tight group-hover:text-primary transition-colors">{label}</span>
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
