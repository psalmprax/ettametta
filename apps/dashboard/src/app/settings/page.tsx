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
        monetization_aggression: "80",
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
        membership_platform_url: "",
        course_platform_url: "",
        sponsorship_contact: "",
        brand_partners: "",
        crypto_wallets: "",
        donation_link: "",
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
        // Video Quality Tiers
        enable_sound_design: "false",
        enable_motion_graphics: "false",
        ai_video_provider: "none",
        default_quality_tier: "standard",
        // Agent Frameworks
        enable_langchain: "false",
        enable_crewai: "false",
        enable_interpreter: "false",
        enable_affiliate_api: "false",
        enable_trading: "false"
    });
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [saveStatus, setSaveStatus] = useState<"idle" | "success" | "error">("idle");
    const [activeTab, setActiveTab] = useState("Notifications");
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

                // Switch to API Keys if admin, otherwise Notifications is safe
                if (data.role === "admin") {
                    setActiveTab("API Keys");
                    fetchSettings(); // Only admins can fetch global settings
                } else {
                    setActiveTab("Notifications");
                    setIsLoading(false); // Done loading for common users
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

            // Only admins save global settings
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

            // All users save personal profile settings
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
                <div className="flex items-center justify-between">
                    <div>
                        <div className="flex items-center gap-3 mb-1">
                            <h1 className="text-5xl md:text-6xl font-black italic uppercase tracking-tighter text-white">System <span className="text-transparent bg-clip-text bg-gradient-to-r from-zinc-400 to-white text-hollow">Settings</span></h1>
                            <div className={cn(
                                "px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest border",
                                userProfile.subscription === "studio" ? "bg-purple-500/10 text-purple-500 border-purple-500/20 shadow-[0_0_10px_rgba(168,85,247,0.2)]" :
                                    userProfile.subscription === "sovereign" ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20 shadow-[0_0_10px_rgba(16,185,129,0.2)]" :
                                        userProfile.subscription === "premium" ? "bg-amber-500/10 text-amber-500 border-amber-500/20" :
                                            userProfile.subscription === "basic" ? "bg-blue-500/10 text-blue-500 border-blue-500/20" :
                                                "bg-zinc-500/10 text-zinc-500 border-zinc-500/20"
                            )}>
                                {userProfile.subscription === "basic" ? "Creator" : userProfile.subscription === "premium" ? "Empire" : userProfile.subscription}
                            </div>
                            {userProfile.role === "admin" && (
                                <div className="px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest bg-primary/10 text-primary border border-primary/20">
                                    Admin
                                </div>
                            )}
                        </div>
                        <p className="text-zinc-500">Configure your API integrations and autonomous engine parameters.</p>
                    </div>
                    <button
                        onClick={handleSave}
                        disabled={isSaving}
                        className={cn(
                            "bg-primary hover:bg-primary/90 text-white font-black py-3 px-6 rounded-xl transition-all flex items-center gap-2 uppercase tracking-widest text-[10px] shadow-[0_0_20px_rgba(var(--primary-rgb),0.3)]",
                            isSaving && "opacity-50 cursor-not-allowed",
                            saveStatus === "success" && "bg-emerald-500 hover:bg-emerald-600"
                        )}
                    >
                        {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : saveStatus === "success" ? <CheckCircle2 className="h-4 w-4" /> : <Save className="h-4 w-4" />}
                        {isSaving ? "Saving..." : saveStatus === "success" ? "Saved!" : "Save Changes"}
                    </button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-4 gap-10">
                    {/* Navigation Tabs */}
                    <div className="space-y-1">
                        {userProfile.role === "admin" && (
                            <>
                                <TabItem icon={<Key className="h-4 w-4" />} label="API Keys" active={activeTab === "API Keys"} onClick={() => setActiveTab("API Keys")} />
                                <TabItem icon={<Layout className="h-4 w-4" />} label="Interface" active={activeTab === "Interface"} onClick={() => setActiveTab("Interface")} />
                                <TabItem icon={<Server className="h-4 w-4" />} label="Infrastructure" active={activeTab === "Infrastructure"} onClick={() => setActiveTab("Infrastructure")} />
                                <TabItem icon={<Shield className="h-4 w-4" />} label="Security" active={activeTab === "Security"} onClick={() => setActiveTab("Security")} />
                            </>
                        )}
                        <TabItem icon={<Bell className="h-4 w-4" />} label="Notifications" active={activeTab === "Notifications"} onClick={() => setActiveTab("Notifications")} />
                        <TabItem icon={<User className="h-4 w-4" />} label="Profile" active={activeTab === "Profile"} onClick={() => setActiveTab("Profile")} />
                        <TabItem icon={<CreditCard className="h-4 w-4" />} label="Billing" active={activeTab === "Billing"} onClick={() => setActiveTab("Billing")} />
                    </div>

                    {/* Main Content Area */}
                    <div className="lg:col-span-3 space-y-8">
                        {isLoading ? (
                            <div className="h-64 flex items-center justify-center">
                                <Loader2 className="h-8 w-8 text-primary animate-spin" />
                            </div>
                        ) : activeTab === "API Keys" ? (
                            <>
                                {/* API Keys Section */}
                                <section className="space-y-6">
                                    <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-8 space-y-8">
                                        <div className="flex items-center gap-3">
                                            <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center">
                                                <Key className="h-5 w-5 text-primary" />
                                            </div>
                                            <div>
                                                <h3 className="text-xl font-bold">API Integrations</h3>
                                                <p className="text-zinc-500 text-sm">Manage keys for brain and discovery engines.</p>
                                            </div>
                                        </div>

                                        <div className="space-y-6">
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
                                                label="TikTok Video Kit Client ID"
                                                id="tiktok_client_id"
                                                value={settings.tiktok_client_id}
                                                onChange={(val) => updateSetting("tiktok_client_id", val)}
                                                isVisible={showKey["tiktok_client_id"]}
                                                onToggle={() => toggleKey("tiktok_client_id")}
                                            />
                                            <KeyInput
                                                label="TikTok Video Kit Client Secret"
                                                id="tiktok_client_secret"
                                                value={settings.tiktok_client_secret}
                                                onChange={(val) => updateSetting("tiktok_client_secret", val)}
                                                isVisible={showKey["tiktok_client_secret"]}
                                                onToggle={() => toggleKey("tiktok_client_secret")}
                                            />
                                            <div className="pt-4 border-t border-zinc-800/50">
                                                <label className="text-sm font-bold text-zinc-400 mb-4 block">Voice Synthesis Engine</label>
                                                <div className="grid grid-cols-2 gap-4 mb-6">
                                                    <button
                                                        onClick={() => updateSetting("voice_engine", "fish_speech")}
                                                        className={cn(
                                                            "p-4 rounded-2xl border transition-all text-left group",
                                                            settings.voice_engine === "fish_speech"
                                                                ? "bg-primary/10 border-primary shadow-[0_0_20px_rgba(var(--primary-rgb),0.2)]"
                                                                : "bg-zinc-950/30 border-zinc-800 hover:border-zinc-700"
                                                        )}
                                                    >
                                                        <div className="flex items-center justify-between mb-2">
                                                            <div className={cn("h-8 w-8 rounded-lg flex items-center justify-center", settings.voice_engine === "fish_speech" ? "bg-primary text-white" : "bg-zinc-800 text-zinc-400")}>
                                                                <Server className="h-4 w-4" />
                                                            </div>
                                                            {settings.voice_engine === "fish_speech" && <CheckCircle2 className="h-4 w-4 text-primary" />}
                                                        </div>
                                                        <span className={cn("block font-bold text-sm", settings.voice_engine === "fish_speech" ? "text-white" : "text-zinc-500")}>Fish Speech</span>
                                                        <span className="text-[10px] text-zinc-600 uppercase font-black">Local Infrastructure</span>
                                                    </button>

                                                    <button
                                                        onClick={() => updateSetting("voice_engine", "elevenlabs")}
                                                        className={cn(
                                                            "p-4 rounded-2xl border transition-all text-left",
                                                            settings.voice_engine === "elevenlabs"
                                                                ? "bg-blue-500/10 border-blue-500 shadow-[0_0_20px_rgba(59,130,246,0.2)]"
                                                                : "bg-zinc-950/30 border-zinc-800 hover:border-zinc-700"
                                                        )}
                                                    >
                                                        <div className="flex items-center justify-between mb-2">
                                                            <div className={cn("h-8 w-8 rounded-lg flex items-center justify-center", settings.voice_engine === "elevenlabs" ? "bg-blue-500 text-white" : "bg-zinc-800 text-zinc-400")}>
                                                                <Bell className="h-4 w-4" />
                                                            </div>
                                                            {settings.voice_engine === "elevenlabs" && <CheckCircle2 className="h-4 w-4 text-blue-500" />}
                                                        </div>
                                                        <span className={cn("block font-bold text-sm", settings.voice_engine === "elevenlabs" ? "text-white" : "text-zinc-500")}>ElevenLabs</span>
                                                        <span className="text-[10px] text-zinc-600 uppercase font-black">Cloud API</span>
                                                    </button>
                                                </div>

                                                {settings.voice_engine === "fish_speech" ? (
                                                    <div className="space-y-4 p-4 bg-primary/5 border border-primary/20 rounded-2xl">
                                                        <div className="flex items-center justify-between">
                                                            <span className="text-[10px] text-primary font-black uppercase tracking-widest">OCI Neural Engine Active</span>
                                                            <span className="text-[10px] text-zinc-500 font-bold bg-zinc-800 px-2 py-0.5 rounded-full">200GB Expanded</span>
                                                        </div>
                                                        <div className="space-y-2">
                                                            <label className="text-xs font-bold text-zinc-500 uppercase">Service Endpoint</label>
                                                            <input
                                                                type="text"
                                                                value={settings.fish_speech_endpoint}
                                                                onChange={(e) => updateSetting("fish_speech_endpoint", e.target.value)}
                                                                className="w-full bg-zinc-950/50 border border-white/5 rounded-xl py-2 px-3 text-sm font-mono text-zinc-400"
                                                            />
                                                        </div>
                                                    </div>
                                                ) : (
                                                    <KeyInput
                                                        label="ElevenLabs API Key"
                                                        id="elevenlabs_api_key"
                                                        value={settings.elevenlabs_api_key}
                                                        onChange={(val) => updateSetting("elevenlabs_api_key", val)}
                                                        isVisible={showKey["elevenlabs_api_key"]}
                                                        onToggle={() => toggleKey("elevenlabs_api_key")}
                                                    />
                                                )}
                                            </div>

                                            <KeyInput
                                                label="Pexels/Pixabay API Key"
                                                id="pexels_api_key"
                                                value={settings.pexels_api_key}
                                                onChange={(val) => updateSetting("pexels_api_key", val)}
                                                isVisible={showKey["pexels_api_key"]}
                                                onToggle={() => toggleKey("pexels_api_key")}
                                            />

                                            <div className="pt-4 border-t border-zinc-800/50">
                                                <label className="text-sm font-bold text-zinc-400 mb-4 block">YouTube OAuth (Google Cloud)</label>
                                                <div className="space-y-4">
                                                    <KeyInput
                                                        label="Google Client ID"
                                                        id="google_client_id"
                                                        value={settings.google_client_id}
                                                        onChange={(val) => updateSetting("google_client_id", val)}
                                                        isVisible={showKey["google_client_id"]}
                                                        onToggle={() => toggleKey("google_client_id")}
                                                    />
                                                    <KeyInput
                                                        label="Google Client Secret"
                                                        id="google_client_secret"
                                                        value={settings.google_client_secret}
                                                        onChange={(val) => updateSetting("google_client_secret", val)}
                                                        isVisible={showKey["google_client_secret"]}
                                                        onToggle={() => toggleKey("google_client_secret")}
                                                    />
                                                </div>
                                            </div>

                                            <div className="pt-4 border-t border-zinc-800/50">
                                                <label className="text-sm font-bold text-zinc-400 mb-4 block">TikTok Developer Tools</label>
                                                <div className="space-y-4">
                                                    <KeyInput
                                                        label="TikTok Client Key"
                                                        id="tiktok_client_key"
                                                        value={settings.tiktok_client_key}
                                                        onChange={(val) => updateSetting("tiktok_client_key", val)}
                                                        isVisible={showKey["tiktok_client_key"]}
                                                        onToggle={() => toggleKey("tiktok_client_key")}
                                                    />
                                                    <KeyInput
                                                        label="TikTok Client Secret"
                                                        id="tiktok_client_secret"
                                                        value={settings.tiktok_client_secret}
                                                        onChange={(val) => updateSetting("tiktok_client_secret", val)}
                                                        isVisible={showKey["tiktok_client_secret"]}
                                                        onToggle={() => toggleKey("tiktok_client_secret")}
                                                    />
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </section>

                                {/* Commerce Integration Section */}
                                <section className="space-y-6">
                                    <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-8 space-y-8">
                                        <div className="flex items-center gap-3">
                                            <div className="h-10 w-10 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                                                <Database className="h-5 w-5 text-emerald-500" />
                                            </div>
                                            <div>
                                                <h3 className="text-xl font-bold">Commerce Core</h3>
                                                <p className="text-zinc-500 text-sm">Connect Shopify or Printful for autonomous sales.</p>
                                            </div>
                                        </div>

                                        <div className="space-y-6">
                                            <div className="space-y-2">
                                                <label htmlFor="shopify-store-url" className="text-sm font-bold text-zinc-400">Shopify Store URL</label>
                                                <input
                                                    id="shopify-store-url"
                                                    name="shopify-store-url"
                                                    type="text"
                                                    value={settings.shopify_shop_url}
                                                    onChange={(e) => updateSetting("shopify_shop_url", e.target.value)}
                                                    className="w-full bg-zinc-950/50 border border-white/10 rounded-xl py-3 px-4 focus:ring-2 ring-primary/50 outline-none text-zinc-300 transition-all text-sm font-bold placeholder:text-zinc-700"
                                                    placeholder="your-store.myshopify.com"
                                                />
                                            </div>
                                            <KeyInput
                                                label="Shopify Admin API Access Token"
                                                id="shopify_access_token"
                                                value={settings.shopify_access_token}
                                                onChange={(val) => updateSetting("shopify_access_token", val)}
                                                isVisible={showKey["shopify_access_token"]}
                                                onToggle={() => toggleKey("shopify_access_token")}
                                            />
                                        </div>
                                    </div>
                                </section>

                                {/* Video Quality Tiers Section */}
                                <section className="space-y-6">
                                    <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-8 space-y-8">
                                        <div className="flex items-center gap-3">
                                            <div className="h-10 w-10 rounded-xl bg-purple-500/10 flex items-center justify-center">
                                                <Sparkles className="h-5 w-5 text-purple-500" />
                                            </div>
                                            <div>
                                                <h3 className="text-xl font-bold">Video Quality Tiers</h3>
                                                <p className="text-zinc-500 text-sm">Enhanced video processing capabilities.</p>
                                            </div>
                                        </div>

                                        <div className="space-y-6">
                                            {/* Sound Design Toggle */}
                                            <div className="p-4 bg-zinc-950/30 border border-zinc-800 rounded-2xl flex items-center justify-between">
                                                <div className="space-y-1">
                                                    <span className="text-sm font-bold text-white flex items-center gap-2">
                                                        <Wand2 className="h-4 w-4 text-purple-400" />
                                                        Sound Design
                                                    </span>
                                                    <p className="text-xs text-zinc-500">AI-powered music & SFX generation</p>
                                                </div>
                                                <button
                                                    onClick={() => updateSetting("enable_sound_design", settings.enable_sound_design === "true" ? "false" : "true")}
                                                    className={cn(
                                                        "w-12 h-6 rounded-full relative transition-colors",
                                                        settings.enable_sound_design === "true" ? "bg-purple-500" : "bg-zinc-700"
                                                    )}
                                                >
                                                    <div className={cn(
                                                        "absolute top-1 w-4 h-4 bg-white rounded-full transition-all",
                                                        settings.enable_sound_design === "true" ? "right-1" : "left-1"
                                                    )} />
                                                </button>
                                            </div>

                                            {/* Motion Graphics Toggle */}
                                            <div className="p-4 bg-zinc-950/30 border border-zinc-800 rounded-2xl flex items-center justify-between">
                                                <div className="space-y-1">
                                                    <span className="text-sm font-bold text-white flex items-center gap-2">
                                                        <Film className="h-4 w-4 text-orange-400" />
                                                        Motion Graphics
                                                    </span>
                                                    <p className="text-xs text-zinc-500">AI-generated animations & overlays</p>
                                                </div>
                                                <button
                                                    onClick={() => updateSetting("enable_motion_graphics", settings.enable_motion_graphics === "true" ? "false" : "true")}
                                                    className={cn(
                                                        "w-12 h-6 rounded-full relative transition-colors",
                                                        settings.enable_motion_graphics === "true" ? "bg-orange-500" : "bg-zinc-700"
                                                    )}
                                                >
                                                    <div className={cn(
                                                        "absolute top-1 w-4 h-4 bg-white rounded-full transition-all",
                                                        settings.enable_motion_graphics === "true" ? "right-1" : "left-1"
                                                    )} />
                                                </button>
                                            </div>

                                            {/* AI Video Provider */}
                                            <div className="space-y-3">
                                                <label className="text-sm font-bold text-zinc-400">AI Video Generation</label>
                                                <div className="grid grid-cols-3 gap-3">
                                                    {['none', 'runway', 'pika'].map((provider) => (
                                                        <button
                                                            key={provider}
                                                            onClick={() => updateSetting("ai_video_provider", provider)}
                                                            className={cn(
                                                                "p-3 rounded-xl border transition-all text-center",
                                                                settings.ai_video_provider === provider
                                                                    ? "bg-pink-500/10 border-pink-500 shadow-[0_0_15px_rgba(236,72,153,0.2)]"
                                                                    : "bg-zinc-950/30 border-zinc-800 hover:border-zinc-700"
                                                            )}
                                                        >
                                                            <span className={cn(
                                                                "block font-bold text-xs uppercase",
                                                                settings.ai_video_provider === provider ? "text-pink-400" : "text-zinc-500"
                                                            )}>
                                                                {provider}
                                                            </span>
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>

                                            {/* Default Quality Tier */}
                                            <div className="space-y-3">
                                                <label className="text-sm font-bold text-zinc-400">Default Processing Tier</label>
                                                <div className="grid grid-cols-3 gap-3">
                                                    {['standard', 'enhanced', 'premium'].map((tier) => (
                                                        <button
                                                            key={tier}
                                                            onClick={() => updateSetting("default_quality_tier", tier)}
                                                            className={cn(
                                                                "p-3 rounded-xl border transition-all text-center",
                                                                settings.default_quality_tier === tier
                                                                    ? "bg-emerald-500/10 border-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.2)]"
                                                                    : "bg-zinc-950/30 border-zinc-800 hover:border-zinc-700"
                                                            )}
                                                        >
                                                            <span className={cn(
                                                                "block font-bold text-xs uppercase",
                                                                settings.default_quality_tier === tier ? "text-emerald-400" : "text-zinc-500"
                                                            )}>
                                                                {tier}
                                                            </span>
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </section>

                                {/* Agent Frameworks Section */}
                                <section className="space-y-6">
                                    <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-8 space-y-8">
                                        <div className="flex items-center gap-3">
                                            <div className="h-10 w-10 rounded-xl bg-blue-500/10 flex items-center justify-center">
                                                <Bot className="h-5 w-5 text-blue-500" />
                                            </div>
                                            <div>
                                                <h3 className="text-xl font-bold">Agent Frameworks</h3>
                                                <p className="text-zinc-500 text-sm">Advanced AI agent orchestration.</p>
                                            </div>
                                        </div>

                                        <div className="space-y-4">
                                            {/* LangChain */}
                                            <div className="p-4 bg-zinc-950/30 border border-zinc-800 rounded-2xl flex items-center justify-between">
                                                <div className="space-y-1">
                                                    <span className="text-sm font-bold text-white flex items-center gap-2">
                                                        <Workflow className="h-4 w-4 text-cyan-400" />
                                                        LangChain
                                                    </span>
                                                    <p className="text-xs text-zinc-500">LLM chaining & prompt management</p>
                                                </div>
                                                <button
                                                    onClick={() => updateSetting("enable_langchain", settings.enable_langchain === "true" ? "false" : "true")}
                                                    className={cn(
                                                        "w-12 h-6 rounded-full relative transition-colors",
                                                        settings.enable_langchain === "true" ? "bg-cyan-500" : "bg-zinc-700"
                                                    )}
                                                >
                                                    <div className={cn(
                                                        "absolute top-1 w-4 h-4 bg-white rounded-full transition-all",
                                                        settings.enable_langchain === "true" ? "right-1" : "left-1"
                                                    )} />
                                                </button>
                                            </div>

                                            {/* CrewAI */}
                                            <div className="p-4 bg-zinc-950/30 border border-zinc-800 rounded-2xl flex items-center justify-between">
                                                <div className="space-y-1">
                                                    <span className="text-sm font-bold text-white flex items-center gap-2">
                                                        <Bot className="h-4 w-4 text-green-400" />
                                                        CrewAI
                                                    </span>
                                                    <p className="text-xs text-zinc-500">Multi-agent orchestration</p>
                                                </div>
                                                <button
                                                    onClick={() => updateSetting("enable_crewai", settings.enable_crewai === "true" ? "false" : "true")}
                                                    className={cn(
                                                        "w-12 h-6 rounded-full relative transition-colors",
                                                        settings.enable_crewai === "true" ? "bg-green-500" : "bg-zinc-700"
                                                    )}
                                                >
                                                    <div className={cn(
                                                        "absolute top-1 w-4 h-4 bg-white rounded-full transition-all",
                                                        settings.enable_crewai === "true" ? "right-1" : "left-1"
                                                    )} />
                                                </button>
                                            </div>

                                            {/* Open Interpreter */}
                                            <div className="p-4 bg-zinc-950/30 border border-zinc-800 rounded-2xl flex items-center justify-between">
                                                <div className="space-y-1">
                                                    <span className="text-sm font-bold text-white flex items-center gap-2">
                                                        <Code className="h-4 w-4 text-yellow-400" />
                                                        Open Interpreter
                                                    </span>
                                                    <p className="text-xs text-zinc-500">Code execution for dynamic effects</p>
                                                </div>
                                                <button
                                                    onClick={() => updateSetting("enable_interpreter", settings.enable_interpreter === "true" ? "false" : "true")}
                                                    className={cn(
                                                        "w-12 h-6 rounded-full relative transition-colors",
                                                        settings.enable_interpreter === "true" ? "bg-yellow-500" : "bg-zinc-700"
                                                    )}
                                                >
                                                    <div className={cn(
                                                        "absolute top-1 w-4 h-4 bg-white rounded-full transition-all",
                                                        settings.enable_interpreter === "true" ? "right-1" : "left-1"
                                                    )} />
                                                </button>
                                            </div>

                                            {/* Affiliate API */}
                                            <div className="p-4 bg-zinc-950/30 border border-zinc-800 rounded-2xl flex items-center justify-between">
                                                <div className="space-y-1">
                                                    <span className="text-sm font-bold text-white flex items-center gap-2">
                                                        <ShoppingCart className="h-4 w-4 text-amber-400" />
                                                        Affiliate API
                                                    </span>
                                                    <p className="text-xs text-zinc-500">Product recommendations integration</p>
                                                </div>
                                                <button
                                                    onClick={() => updateSetting("enable_affiliate_api", settings.enable_affiliate_api === "true" ? "false" : "true")}
                                                    className={cn(
                                                        "w-12 h-6 rounded-full relative transition-colors",
                                                        settings.enable_affiliate_api === "true" ? "bg-amber-500" : "bg-zinc-700"
                                                    )}
                                                >
                                                    <div className={cn(
                                                        "absolute top-1 w-4 h-4 bg-white rounded-full transition-all",
                                                        settings.enable_affiliate_api === "true" ? "right-1" : "left-1"
                                                    )} />
                                                </button>
                                            </div>

                                            {/* Trading API */}
                                            <div className="p-4 bg-zinc-950/30 border border-zinc-800 rounded-2xl flex items-center justify-between">
                                                <div className="space-y-1">
                                                    <span className="text-sm font-bold text-white flex items-center gap-2">
                                                        <TrendingUp className="h-4 w-4 text-red-400" />
                                                        Trading API
                                                    </span>
                                                    <p className="text-xs text-zinc-500">Market data & sentiment analysis</p>
                                                </div>
                                                <button
                                                    onClick={() => updateSetting("enable_trading", settings.enable_trading === "true" ? "false" : "true")}
                                                    className={cn(
                                                        "w-12 h-6 rounded-full relative transition-colors",
                                                        settings.enable_trading === "true" ? "bg-red-500" : "bg-zinc-700"
                                                    )}
                                                >
                                                    <div className={cn(
                                                        "absolute top-1 w-4 h-4 bg-white rounded-full transition-all",
                                                        settings.enable_trading === "true" ? "right-1" : "left-1"
                                                    )} />
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </section>

                                {/* Engine Config Section */}
                                <section className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 space-y-6">
                                    <h3 className="text-xl font-bold flex items-center gap-2">
                                        <Cpu className="h-5 w-5 text-zinc-400" />
                                        Autonomous Parameters
                                    </h3>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div className="space-y-2">
                                            <label className="text-sm font-bold text-zinc-400">Scan Frequency</label>
                                            <select
                                                value={settings.scan_frequency}
                                                onChange={(e) => updateSetting("scan_frequency", e.target.value)}
                                                className="w-full bg-zinc-950/50 border border-white/10 rounded-xl p-3 text-white focus:ring-2 ring-primary/50 outline-none text-xs font-bold uppercase tracking-wider cursor-pointer"
                                            >
                                                <option>Every 1 hour</option>
                                                <option>Every 6 hours</option>
                                                <option>Every 12 hours</option>
                                                <option>Daily</option>
                                            </select>
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-sm font-bold text-zinc-400">Force Originality</label>
                                            <div className="p-3 bg-zinc-950/50 border border-white/10 rounded-xl flex items-center justify-between">
                                                <span className="text-sm">Mandatory Mirror Transform</span>
                                                <button
                                                    onClick={() => updateSetting("force_originality", settings.force_originality === "true" ? "false" : "true")}
                                                    className={cn(
                                                        "w-10 h-5 rounded-full relative transition-colors",
                                                        settings.force_originality === "true" ? "bg-primary" : "bg-zinc-700"
                                                    )}
                                                >
                                                    <div className={cn(
                                                        "absolute top-1 w-3 h-3 bg-white rounded-full transition-all",
                                                        settings.force_originality === "true" ? "right-1" : "left-1"
                                                    )} />
                                                </button>
                                            </div>
                                        </div>
                                        <div className="space-y-2">
                                            <div className="flex justify-between items-center">
                                                <label className="text-sm font-bold text-zinc-400">Monetization Aggression</label>
                                                <span className="text-xs font-mono text-primary bg-primary/10 px-2 py-0.5 rounded-full">{settings.monetization_aggression}%</span>
                                            </div>
                                            <div className="p-4 bg-zinc-950/50 border border-white/10 rounded-xl space-y-4">
                                                <input
                                                    id="monetization-aggression"
                                                    name="monetization-aggression"
                                                    type="range"
                                                    min="0"
                                                    max="100"
                                                    step="5"
                                                    value={settings.monetization_aggression}
                                                    onChange={(e) => updateSetting("monetization_aggression", e.target.value)}
                                                    className="w-full h-1.5 bg-zinc-900 rounded-lg appearance-none cursor-pointer accent-primary"
                                                />
                                                <div className="flex justify-between text-[10px] text-zinc-500 uppercase font-bold">
                                                    <span>Passive</span>
                                                    <span>Optimal</span>
                                                    <span>Aggressive</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-sm font-bold text-zinc-400">Viral Autonomy</label>
                                            <div className="p-3 bg-primary/5 border border-primary/20 rounded-xl flex items-center justify-between">
                                                <div className="space-y-0.5">
                                                    <span className="text-sm font-bold text-primary">Zero-Touch Publishing</span>
                                                    <p className="text-[10px] text-zinc-500 uppercase tracking-widest font-black">AI-Driven Master Loop</p>
                                                </div>
                                                <button
                                                    onClick={() => updateSetting("auto_pilot", settings.auto_pilot === "true" ? "false" : "true")}
                                                    className={cn(
                                                        "w-10 h-5 rounded-full relative transition-colors",
                                                        settings.auto_pilot === "true" ? "bg-primary" : "bg-zinc-700"
                                                    )}
                                                >
                                                    <div className={cn(
                                                        "absolute top-1 w-3 h-3 bg-white rounded-full transition-all",
                                                        settings.auto_pilot === "true" ? "right-1" : "left-1"
                                                    )} />
                                                </button>
                                            </div>
                                        </div>
                                        <div className="space-y-6 col-span-1 md:col-span-2">
                                            <div className="p-6 bg-zinc-950/50 border border-zinc-800 rounded-2xl">
                                                <div className="flex items-center justify-between mb-4">
                                                    <div className="space-y-1">
                                                        <label className="text-sm font-bold text-white flex items-center gap-2">
                                                            Monetization Mode
                                                            <div className="group relative">
                                                                <Shield className="h-3 w-3 text-zinc-500 cursor-help" />
                                                                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-48 p-2 bg-zinc-900 border border-zinc-800 rounded-lg text-[10px] text-zinc-400 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 shadow-xl">
                                                                    Selective mode only monetizes videos that achieve a high predicted Viral Score.
                                                                </div>
                                                            </div>
                                                        </label>
                                                        <p className="text-[10px] text-zinc-600 uppercase font-black">Exposure Integrity Control</p>
                                                    </div>

                                                    <div className="flex bg-zinc-900 p-1 rounded-xl border border-zinc-800">
                                                        <button
                                                            onClick={() => updateSetting("monetization_mode", "selective")}
                                                            className={cn(
                                                                "px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all",
                                                                settings.monetization_mode === "selective" ? "bg-primary text-white shadow-lg shadow-primary/20" : "text-zinc-600 hover:text-zinc-400"
                                                            )}
                                                        >
                                                            Selective
                                                        </button>
                                                        <button
                                                            onClick={() => updateSetting("monetization_mode", "all")}
                                                            className={cn(
                                                                "px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all",
                                                                settings.monetization_mode === "all" ? "bg-red-500 text-white shadow-lg shadow-red-500/20" : "text-zinc-600 hover:text-zinc-400"
                                                            )}
                                                        >
                                                            All Content
                                                        </button>
                                                    </div>
                                                </div>
                                                <div className="h-1 w-full bg-zinc-900 rounded-full overflow-hidden">
                                                    <div className={cn("h-full transition-all duration-500", settings.monetization_mode === "selective" ? "w-1/2 bg-primary" : "w-full bg-red-500")} />
                                                </div>
                                            </div>

                                            <div className="space-y-4">
                                                <div className="flex justify-between items-center">
                                                    <label className="text-sm font-bold text-zinc-400">Monetization Strategy</label>
                                                    <span className="text-[10px] text-zinc-500 uppercase font-black px-2 py-0.5 bg-zinc-800 rounded-full">Decoupled Scaling Mode</span>
                                                </div>
                                                <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                                                    {["commerce", "affiliate", "lead_gen", "digital_product", "membership", "course", "sponsorship", "crypto"].map((strategy) => (
                                                        <button
                                                            key={strategy}
                                                            onClick={() => updateSetting("active_monetization_strategy", strategy)}
                                                            className={cn(
                                                                "p-3 rounded-xl border text-xs font-bold transition-all capitalize",
                                                                settings.active_monetization_strategy === strategy
                                                                    ? "bg-primary/20 border-primary text-primary shadow-[0_0_15px_rgba(var(--primary-rgb),0.2)]"
                                                                    : "bg-zinc-800 border-zinc-700 text-zinc-500 hover:border-zinc-600"
                                                            )}
                                                        >
                                                            {strategy.replace("_", " ")}
                                                        </button>
                                                    ))}
                                                </div>
                                                <p className="text-[10px] text-zinc-600 mt-1">
                                                    {settings.active_monetization_strategy === "commerce" && "Focuses on Shopify/Printful product integration."}
                                                    {settings.active_monetization_strategy === "affiliate" && "Prioritizes high-commission affiliate network links."}
                                                    {settings.active_monetization_strategy === "lead_gen" && "Builds lists via newsletter and lead magnet signups."}
                                                    {settings.active_monetization_strategy === "digital_product" && "Scales high-margin courses, SaaS, and digital downloads."}
                                                    {settings.active_monetization_strategy === "membership" && "Recurring revenue through Patreon/supporter tiers."}
                                                    {settings.active_monetization_strategy === "course" && "Sell online courses and educational content."}
                                                    {settings.active_monetization_strategy === "sponsorship" && "Brand deals and sponsored content partnerships."}
                                                    {settings.active_monetization_strategy === "crypto" && "Accept crypto tips and donations."}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </section>

                                {/* DB Status */}
                                <div className="flex items-center justify-between p-6 bg-emerald-500/5 border border-emerald-500/10 rounded-3xl">
                                    <div className="flex items-center gap-4">
                                        <Database className="h-6 w-6 text-emerald-500" />
                                        <div>
                                            <h4 className="font-bold">PostgreSQL Persistence</h4>
                                            <p className="text-xs text-zinc-500">Connected to db:5432 • Live Mode active</p>
                                        </div>
                                    </div>
                                    <CheckCircle2 className="h-6 w-6 text-emerald-500" />
                                </div>
                            </>
                        ) : activeTab === "Interface" ? (
                            <section className="space-y-6">
                                <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 space-y-8">
                                    <div className="flex items-center gap-3">
                                        <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center">
                                            <Layout className="h-5 w-5 text-primary" />
                                        </div>
                                        <div>
                                            <h3 className="text-xl font-bold">Workspace Appearance</h3>
                                            <p className="text-zinc-500 text-sm">Customize visual density and engine terminology.</p>
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                        {/* Pro Mode Toggle */}
                                        <div className="space-y-4">
                                            <div className="flex items-center justify-between">
                                                <div className="space-y-1">
                                                    <h4 className="font-bold">Pro Mode</h4>
                                                    <p className="text-xs text-zinc-500">Cleaner, high-density interface for enterprise workflows. Removes scanlines and heavy glows.</p>
                                                </div>
                                                <button
                                                    onClick={toggleProMode}
                                                    className={cn(
                                                        "w-12 h-6 rounded-full relative transition-all duration-300",
                                                        isProMode ? "bg-primary shadow-[0_0_15px_rgba(var(--primary-rgb),0.5)]" : "bg-zinc-800"
                                                    )}
                                                >
                                                    <div className={cn(
                                                        "absolute top-1 w-4 h-4 bg-white rounded-full transition-all duration-300",
                                                        isProMode ? "right-1" : "left-1"
                                                    )} />
                                                </button>
                                            </div>
                                        </div>

                                        {/* Accessibility / High Contrast */}
                                        <div className="space-y-4">
                                            <div className="flex items-center justify-between">
                                                <div className="space-y-1">
                                                    <h4 className="font-bold">High Contrast Borders</h4>
                                                    <p className="text-xs text-zinc-500">Sharper distinction between cards and background for better visibility.</p>
                                                </div>
                                                <button
                                                    disabled
                                                    className="w-12 h-6 rounded-full bg-zinc-800/50 cursor-not-allowed relative"
                                                >
                                                    <div className="absolute top-1 left-1 w-4 h-4 bg-zinc-600 rounded-full" />
                                                </button>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="p-6 bg-primary/5 border border-primary/20 rounded-2xl flex items-start gap-4">
                                        <div className="p-2 bg-primary/10 rounded-lg">
                                            <Shield className="h-4 w-4 text-primary" />
                                        </div>
                                        <div className="space-y-1">
                                            <p className="text-sm font-bold text-primary">Preview Engine Injected</p>
                                            <p className="text-xs text-zinc-400">Settings applied globally to all `glass-card` elements using standardized spacing variables.</p>
                                        </div>
                                    </div>
                                </div>
                            </section>
                        ) : activeTab === "Infrastructure" ? (
                            <section className="space-y-6">
                                <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 space-y-8">
                                    <div className="flex items-center gap-3">
                                        <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center">
                                            <Server className="h-5 w-5 text-primary" />
                                        </div>
                                        <div>
                                            <h3 className="text-xl font-bold">Cloud Infrastructure</h3>
                                            <p className="text-zinc-500 text-sm">Manage OCI Object Storage and archival parameters.</p>
                                        </div>
                                    </div>

                                    <div className="space-y-6">
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                            <div className="space-y-2">
                                                <label className="text-sm font-bold text-zinc-400">Storage Provider</label>
                                                <select
                                                    value={settings.storage_provider}
                                                    onChange={(e) => updateSetting("storage_provider", e.target.value)}
                                                    className="w-full bg-zinc-950/50 border border-white/10 rounded-xl p-3 text-white focus:ring-2 ring-primary/50 outline-none text-xs font-bold uppercase tracking-wider cursor-pointer"
                                                >
                                                    <option value="LOCAL">Local Disk (No Archival)</option>
                                                    <option value="OCI">Oracle Cloud Infrastructure (OCI)</option>
                                                    <option value="AWS">AWS S3</option>
                                                </select>
                                            </div>
                                            <div className="space-y-2">
                                                <label className="text-sm font-bold text-zinc-400">Region</label>
                                                <input
                                                    type="text"
                                                    value={settings.storage_region}
                                                    onChange={(e) => updateSetting("storage_region", e.target.value)}
                                                    className="w-full bg-zinc-950/50 border border-white/10 rounded-xl py-2 px-3 text-sm text-zinc-300"
                                                    placeholder="eu-frankfurt-1"
                                                />
                                            </div>
                                        </div>

                                        <div className="space-y-2">
                                            <label className="text-sm font-bold text-zinc-400">Storage Endpoint</label>
                                            <input
                                                type="text"
                                                value={settings.storage_endpoint}
                                                onChange={(e) => updateSetting("storage_endpoint", e.target.value)}
                                                className="w-full bg-zinc-950/50 border border-white/10 rounded-xl py-2 px-3 text-sm text-zinc-300 font-mono"
                                                placeholder="https://<namespace>.compat.objectstorage.eu-frankfurt-1.oraclecloud.com"
                                            />
                                        </div>

                                        <div className="space-y-2">
                                            <label className="text-sm font-bold text-zinc-400">Bucket Name</label>
                                            <input
                                                type="text"
                                                value={settings.storage_bucket}
                                                onChange={(e) => updateSetting("storage_bucket", e.target.value)}
                                                className="w-full bg-zinc-950/50 border border-white/10 rounded-xl py-2 px-3 text-sm text-zinc-300"
                                                placeholder="viral-forge-assets"
                                            />
                                        </div>

                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-zinc-800/50">
                                            <KeyInput
                                                label="Access Key ID"
                                                id="storage_access_key"
                                                value={settings.storage_access_key}
                                                onChange={(val) => updateSetting("storage_access_key", val)}
                                                isVisible={showKey["storage_access_key"]}
                                                onToggle={() => toggleKey("storage_access_key")}
                                            />
                                            <KeyInput
                                                label="Secret Access Key"
                                                id="storage_secret_key"
                                                value={settings.storage_secret_key}
                                                onChange={(val) => updateSetting("storage_secret_key", val)}
                                                isVisible={showKey["storage_secret_key"]}
                                                onToggle={() => toggleKey("storage_secret_key")}
                                            />
                                        </div>
                                    </div>
                                </div>
                            </section>
                        ) : activeTab === "Notifications" ? (
                            <section className="space-y-6">
                                <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 space-y-8">
                                    <div className="flex items-center gap-3">
                                        <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center">
                                            <Bell className="h-5 w-5 text-primary" />
                                        </div>
                                        <div>
                                            <h3 className="text-xl font-bold">Telegram Agent (OpenClaw)</h3>
                                            <p className="text-zinc-500 text-sm">Link your account to the autonomous Telegram bot.</p>
                                        </div>
                                    </div>

                                    <div className="space-y-6">
                                        <div className="space-y-2">
                                            <label className="text-sm font-bold text-zinc-400">Telegram Chat ID</label>
                                            <div className="relative group">
                                                <input
                                                    type="text"
                                                    value={userProfile.telegram_chat_id}
                                                    onChange={(e) => setUserProfile(prev => ({ ...prev, telegram_chat_id: e.target.value }))}
                                                    className="w-full bg-zinc-950/50 border border-white/10 rounded-xl py-3 px-4 focus:ring-2 ring-primary/50 outline-none text-zinc-300 transition-all font-mono text-sm font-bold"
                                                    placeholder="Enter your Telegram ID (e.g. 123456789)..."
                                                />
                                            </div>
                                            <p className="text-[10px] text-zinc-500 uppercase tracking-widest font-black flex items-center gap-2">
                                                <Shield className="h-3 w-3" />
                                                Found via @userinfobot or by messaging @OpenClawBot
                                            </p>
                                        </div>

                                        <div className="space-y-2">
                                            <div className="flex items-center justify-between">
                                                <label className="text-sm font-bold text-zinc-400">Telegram Bot Token (Private Agent)</label>
                                                <a href="https://t.me/BotFather" target="_blank" rel="noreferrer" className="text-[10px] text-primary hover:underline font-bold uppercase">Setup with @BotFather</a>
                                            </div>
                                            <div className="relative group">
                                                <input
                                                    type={showKey["tg_token"] ? "text" : "password"}
                                                    value={userProfile.telegram_token}
                                                    onChange={(e) => setUserProfile({ ...userProfile, telegram_token: e.target.value })}
                                                    className="w-full bg-zinc-950/50 border border-white/10 rounded-xl py-3 px-4 pr-12 focus:ring-2 ring-primary/50 outline-none text-zinc-300 transition-all font-mono text-sm font-bold placeholder:text-zinc-800"
                                                    placeholder="123456789:ABCDefGhIjKlMnOpQrStUvWxYz..."
                                                />
                                                <button
                                                    onClick={() => toggleKey("tg_token")}
                                                    className="absolute right-3 top-1/2 -translate-y-1/2 p-2 text-zinc-500 hover:text-white transition-colors"
                                                >
                                                    {showKey["tg_token"] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                                </button>
                                            </div>
                                            <p className="text-[10px] text-zinc-600 italic">
                                                Providing a private token spins up a dedicated OpenClaw instance for your account.
                                            </p>
                                        </div>

                                        <div className="p-6 bg-zinc-950/50 border border-zinc-800 rounded-2xl space-y-4">
                                            <div className="flex items-center justify-between">
                                                <div className="space-y-1">
                                                    <h4 className="font-bold">Activity Pulses</h4>
                                                    <p className="text-xs text-zinc-500">Receive real-time notifications on Telegram for successful transmissions.</p>
                                                </div>
                                                <button
                                                    disabled
                                                    className="w-10 h-5 bg-zinc-800 rounded-full relative cursor-not-allowed"
                                                >
                                                    <div className="absolute top-1 left-1 w-3 h-3 bg-zinc-600 rounded-full" />
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </section>
                        ) : activeTab === "Profile" ? (
                            <section className="space-y-6">
                                <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 space-y-6">
                                    <div className="flex items-center gap-3">
                                        <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center">
                                            <User className="h-5 w-5 text-primary" />
                                        </div>
                                        <div>
                                            <h3 className="text-lg font-bold text-white">Profile Settings</h3>
                                            <p className="text-xs text-zinc-500">Manage your account credentials</p>
                                        </div>
                                    </div>

                                    <div className="space-y-4">
                                        <div className="space-y-2">
                                            <label className="text-sm font-bold text-zinc-400">Current Password</label>
                                            <input
                                                type="password"
                                                id="currentPassword"
                                                className="w-full bg-zinc-950/50 border border-white/10 rounded-xl py-3 px-4 text-white focus:ring-2 ring-primary/50 outline-none"
                                                placeholder="Enter current password"
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-sm font-bold text-zinc-400">New Password</label>
                                            <input
                                                type="password"
                                                id="newPassword"
                                                className="w-full bg-zinc-950/50 border border-white/10 rounded-xl py-3 px-4 text-white focus:ring-2 ring-primary/50 outline-none"
                                                placeholder="Enter new password"
                                            />
                                        </div>
                                        <div className="space-y-2">
                                            <label className="text-sm font-bold text-zinc-400">Confirm New Password</label>
                                            <input
                                                type="password"
                                                id="confirmPassword"
                                                className="w-full bg-zinc-950/50 border border-white/10 rounded-xl py-3 px-4 text-white focus:ring-2 ring-primary/50 outline-none"
                                                placeholder="Confirm new password"
                                            />
                                        </div>
                                        <button
                                            onClick={async () => {
                                                const currentPassword = (document.getElementById('currentPassword') as HTMLInputElement).value;
                                                const newPassword = (document.getElementById('newPassword') as HTMLInputElement).value;
                                                const confirmPassword = (document.getElementById('confirmPassword') as HTMLInputElement).value;

                                                if (!currentPassword || !newPassword || !confirmPassword) {
                                                    alert('Please fill in all password fields');
                                                    return;
                                                }
                                                if (newPassword !== confirmPassword) {
                                                    alert('New passwords do not match');
                                                    return;
                                                }
                                                if (newPassword.length < 6) {
                                                    alert('Password must be at least 6 characters');
                                                    return;
                                                }

                                                try {
                                                    const token = localStorage.getItem('token');
                                                    const res = await fetch(`${API_BASE}/auth/me/change-password`, {
                                                        method: 'POST',
                                                        headers: {
                                                            'Content-Type': 'application/json',
                                                            'Authorization': `Bearer ${token}`
                                                        },
                                                        body: JSON.stringify({
                                                            current_password: currentPassword,
                                                            new_password: newPassword
                                                        })
                                                    });
                                                    if (res.ok) {
                                                        alert('Password changed successfully!');
                                                        (document.getElementById('currentPassword') as HTMLInputElement).value = '';
                                                        (document.getElementById('newPassword') as HTMLInputElement).value = '';
                                                        (document.getElementById('confirmPassword') as HTMLInputElement).value = '';
                                                    } else {
                                                        const err = await res.json();
                                                        alert(err.detail || 'Failed to change password');
                                                    }
                                                } catch (e) {
                                                    alert('Error changing password');
                                                }
                                            }}
                                            className="w-full bg-primary hover:bg-primary/90 text-white font-bold py-3 px-6 rounded-xl transition-all"
                                        >
                                            Change Password
                                        </button>
                                    </div>
                                </div>
                            </section>
                        ) : activeTab === "Billing" ? (
                            <section className="space-y-6">
                                <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 space-y-6">
                                    <div className="flex items-center gap-3">
                                        <div className="h-10 w-10 rounded-xl bg-amber-500/10 flex items-center justify-center">
                                            <CreditCard className="h-5 w-5 text-amber-500" />
                                        </div>
                                        <div>
                                            <h3 className="text-lg font-bold text-white">Subscription & Billing</h3>
                                            <p className="text-xs text-zinc-500">Manage your subscription tier</p>
                                        </div>
                                    </div>

                                    <div className="p-4 bg-zinc-950/50 border border-zinc-800 rounded-xl">
                                        <div className="flex items-center justify-between mb-4">
                                            <div>
                                                <p className="text-sm text-zinc-400">Current Plan</p>
                                                <p className="text-2xl font-black text-white uppercase">{userProfile.subscription}</p>
                                            </div>
                                            <div className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${userProfile.subscription === 'studio' ? 'bg-purple-500/10 text-purple-500' :
                                                userProfile.subscription === 'sovereign' ? 'bg-emerald-500/10 text-emerald-500' :
                                                    userProfile.subscription === 'premium' ? 'bg-amber-500/10 text-amber-500' :
                                                        userProfile.subscription === 'basic' ? 'bg-blue-500/10 text-blue-500' :
                                                            'bg-zinc-500/10 text-zinc-500'
                                                }`}>
                                                {userProfile.subscription === 'free' ? 'Free Tier' : 'Active'}
                                            </div>
                                        </div>

                                        <div className="space-y-3 pt-4 border-t border-zinc-800">
                                            <p className="text-sm font-bold text-zinc-400">Available Plans</p>

                                            <div className="grid gap-3">
                                                <div className={`p-4 rounded-xl border ${userProfile.subscription === 'free' ? 'border-primary bg-primary/5' : 'border-zinc-800'} transition-all`}>
                                                    <div className="flex items-center justify-between">
                                                        <div>
                                                            <p className="font-bold text-white uppercase">Free</p>
                                                            <p className="text-xs text-zinc-500">1 video/day • Basic discovery</p>
                                                        </div>
                                                        <span className="text-sm font-bold text-zinc-500">$0/mo</span>
                                                    </div>
                                                </div>

                                                <div className={`p-4 rounded-xl border ${userProfile.subscription === 'basic' ? 'border-primary bg-primary/5' : 'border-zinc-800'} transition-all`}>
                                                    <div className="flex items-center justify-between">
                                                        <div>
                                                            <p className="font-bold text-white uppercase">Creator</p>
                                                            <p className="text-xs text-zinc-500">3 videos/day • Transformation pipeline</p>
                                                        </div>
                                                        <span className="text-sm font-bold text-zinc-500">$29/mo</span>
                                                    </div>
                                                    {userProfile.subscription !== 'basic' && (
                                                        <button
                                                            onClick={() => alert("Redirecting to Stripe...")}
                                                            className="mt-2 text-xs bg-blue-500/10 text-blue-500 px-3 py-1 rounded-full font-bold"
                                                        >
                                                            Upgrade
                                                        </button>
                                                    )}
                                                </div>

                                                <div className={`p-4 rounded-xl border ${userProfile.subscription === 'premium' ? 'border-primary bg-primary/5' : 'border-amber-500/30'} transition-all`}>
                                                    <div className="flex items-center justify-between">
                                                        <div>
                                                            <p className="font-bold text-white uppercase">Empire</p>
                                                            <p className="text-xs text-zinc-500">90 videos/month • Lite4K Synthesis ONLY</p>
                                                        </div>
                                                        <span className="text-sm font-bold text-amber-500">$99/mo</span>
                                                    </div>
                                                    {userProfile.subscription !== 'premium' && (
                                                        <button
                                                            onClick={() => alert("Redirecting to Stripe...")}
                                                            className="mt-2 text-xs bg-amber-500/10 text-amber-500 px-3 py-1 rounded-full font-bold"
                                                        >
                                                            Upgrade
                                                        </button>
                                                    )}
                                                </div>

                                                <div className={`p-4 rounded-xl border ${userProfile.subscription === 'sovereign' ? 'border-primary bg-primary/5' : 'border-emerald-500/30'} transition-all`}>
                                                    <div className="flex items-center justify-between">
                                                        <div>
                                                            <p className="font-bold text-white uppercase">Sovereign</p>
                                                            <p className="text-xs text-zinc-500">120 videos/month • LTX-Video Access</p>
                                                        </div>
                                                        <span className="text-sm font-bold text-emerald-500">$149/mo</span>
                                                    </div>
                                                    {userProfile.subscription !== 'sovereign' && (
                                                        <button
                                                            onClick={() => alert("Redirecting to Stripe...")}
                                                            className="mt-2 text-xs bg-emerald-500/10 text-emerald-500 px-3 py-1 rounded-full font-bold"
                                                        >
                                                            Upgrade
                                                        </button>
                                                    )}
                                                </div>

                                                <div className={`p-4 rounded-xl border ${userProfile.subscription === 'studio' ? 'border-primary bg-primary/5' : 'border-purple-500/30'} transition-all`}>
                                                    <div className="flex items-center justify-between">
                                                        <div>
                                                            <p className="font-bold text-white uppercase">Studio</p>
                                                            <p className="text-xs text-zinc-500">200 videos/month • Runway/Pika/Veo3/Wan2.2</p>
                                                        </div>
                                                        <span className="text-sm font-bold text-purple-500">$299/mo</span>
                                                    </div>
                                                    {userProfile.subscription !== 'studio' && (
                                                        <button
                                                            onClick={() => alert("Redirecting to Stripe...")}
                                                            className="mt-2 text-xs bg-purple-500/10 text-purple-500 px-3 py-1 rounded-full font-bold"
                                                        >
                                                            Upgrade
                                                        </button>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </section>
                        ) : (
                            <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-12 text-center space-y-4">
                                <div className="h-16 w-16 rounded-2xl bg-zinc-800 flex items-center justify-center mx-auto">
                                    <Server className="h-8 w-8 text-zinc-600" />
                                </div>
                                <h3 className="text-xl font-bold text-zinc-400">{activeTab} Configuration</h3>
                                <p className="text-zinc-500 max-w-sm mx-auto">
                                    Direct access to {activeTab.toLowerCase()} parameters is coming soon. ettametta is currently using optimized default parameters for high-velocity distribution.
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </DashboardLayout >
    );
}

function TabItem({ icon, label, active = false, onClick }: { icon: React.ReactNode, label: string, active?: boolean, onClick: () => void }) {
    return (
        <button
            onClick={onClick}
            type="button"
            className={cn(
                "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 font-bold text-sm cursor-pointer group",
                active
                    ? "bg-primary/15 text-primary shadow-[0_0_20px_rgba(var(--primary-rgb),0.1)]"
                    : "text-zinc-500 hover:bg-zinc-900 hover:text-zinc-200"
            )}
        >
            <div className={cn(
                "transition-transform duration-200",
                active ? "scale-110" : "group-hover:scale-110"
            )}>
                {icon}
            </div>
            {label}
        </button>
    );
}

interface Settings {
    created_at: string;
}

interface MonetizationData {
    total_revenue: number;
    epm: number;
}

function KeyInput({ label, id, value, onChange, isVisible, onToggle }: { label: string, id: string, value: string, onChange: (val: string) => void, isVisible: boolean, onToggle: () => void }) {
    return (
        <div className="space-y-2">
            <label htmlFor={id} className="text-sm font-bold text-zinc-400">{label}</label>
            <div className="relative group">
                <input
                    id={id}
                    name={id}
                    type={isVisible ? "text" : "password"}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    className="w-full bg-zinc-950/50 border border-white/10 rounded-xl py-3 px-4 pr-12 focus:ring-2 ring-primary/50 outline-none text-zinc-300 transition-all font-mono text-sm font-bold placeholder:text-zinc-700"
                    placeholder={`Enter ${label}...`}
                />
                <button
                    onClick={onToggle}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-2 text-zinc-500 hover:text-white transition-colors"
                >
                    {isVisible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
            </div>
        </div>
    );
}
