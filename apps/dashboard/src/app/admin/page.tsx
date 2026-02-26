"use client";

import React, { useState, useEffect } from "react";
import DashboardLayout from "@/components/layout";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import {
    Key,
    Database,
    Shield,
    Server,
    Save,
    EyeOff,
    Eye,
    CheckCircle2,
    Loader2,
    Layout,
    CreditCard,
    Wand2,
    Bot,
    Workflow,
    Code,
    ShoppingCart,
    TrendingUp,
    Lock,
    AlertTriangle
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";

// Admin-only system configuration
export default function AdminSettingsPage() {
    const { user, isLoading: authLoading } = useAuth();
    const router = useRouter();
    const [showKey, setShowKey] = useState<Record<string, boolean>>({});
    const [settings, setSettings] = useState<Record<string, string>>({
        // OAuth Credentials (System-wide)
        google_client_id: "",
        google_client_secret: "",
        tiktok_client_key: "",
        tiktok_client_secret: "",
        // API Keys (System-wide)
        groq_api_key: "",
        openai_api_key: "",
        elevenlabs_api_key: "",
        pexels_api_key: "",
        // Cloud Storage
        aws_access_key_id: "",
        aws_secret_access_key: "",
        aws_region: "us-east-1",
        aws_storage_bucket_name: "",
        storage_provider: "OCI",
        storage_access_key: "",
        storage_secret_key: "",
        storage_bucket: "",
        storage_endpoint: "",
        storage_region: "eu-frankfurt-1",
        // Payment
        stripe_secret_key: "",
        stripe_webhook_secret: "",
        // Shopify
        shopify_shop_url: "",
        shopify_access_token: "",
        // Production
        production_domain: "http://localhost:8000",
        // Render Node
        render_node_url: "",
        // Twilio/WhatsApp
        twilio_account_sid: "",
        twilio_auth_token: "",
        twilio_whatsapp_number: "",
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
    const [activeTab, setActiveTab] = useState("OAuth");

    // Redirect if not admin
    useEffect(() => {
        if (!authLoading && (!user || user.role !== "admin")) {
            router.push("/");
        }
    }, [authLoading, user, router]);

    const toggleKey = (id: string) => {
        setShowKey(prev => ({ ...prev, [id]: !prev[id] }));
    };

    const fetchSettings = async () => {
        setIsLoading(true);
        try {
            const token = localStorage.getItem("token");
            const response = await fetch(`${API_BASE}/settings/system`, {
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                }
            });
            if (response.ok) {
                const data = await response.json();
                setSettings(prev => ({ ...prev, ...data }));
            }
        } catch (error) {
            console.error("Failed to fetch settings:", error);
        } finally {
            setIsLoading(false);
        }
    };

    const saveSettings = async () => {
        setIsSaving(true);
        setSaveStatus("idle");
        try {
            const token = localStorage.getItem("token");
            const response = await fetch(`${API_BASE}/settings/system`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(settings)
            });
            if (response.ok) {
                setSaveStatus("success");
                setTimeout(() => setSaveStatus("idle"), 3000);
            } else {
                setSaveStatus("error");
            }
        } catch (error) {
            console.error("Failed to save settings:", error);
            setSaveStatus("error");
        } finally {
            setIsSaving(false);
        }
    };

    const updateSetting = (key: string, value: string) => {
        setSettings(prev => ({ ...prev, [key]: value }));
    };

    useEffect(() => {
        if (user && user.role === "admin") {
            fetchSettings();
        }
    }, [user]);

    if (authLoading || !user || user.role !== "admin") {
        return (
            <DashboardLayout>
                <div className="flex items-center justify-center h-[60vh]">
                    <div className="text-center space-y-4">
                        <AlertTriangle className="h-16 w-16 text-amber-500 mx-auto" />
                        <h2 className="text-2xl font-bold text-white">Access Denied</h2>
                        <p className="text-zinc-400">You must be an administrator to access this page.</p>
                    </div>
                </div>
            </DashboardLayout>
        );
    }

    const tabs = [
        { id: "OAuth", label: "OAuth & Auth", icon: Key },
        { id: "API", label: "API Keys", icon: Bot },
        { id: "Storage", label: "Storage", icon: Database },
        { id: "Engine", label: "Engine Parameters", icon: Wand2 },
        { id: "Payment", label: "Payment", icon: CreditCard },
        { id: "Commerce", label: "Commerce", icon: ShoppingCart },
        { id: "Infrastructure", label: "Infrastructure", icon: Server },
        { id: "WhatsApp", label: "WhatsApp", icon: Bot },
    ];

    return (
        <DashboardLayout>
            <div className="section-container relative pb-20">
                <div className="flex items-center justify-between mb-10">
                    <div>
                        <div className="flex items-center gap-4 mb-2">
                            <h1 className="text-5xl md:text-6xl font-black italic uppercase tracking-tighter text-white">
                                System <span className="text-transparent bg-clip-text bg-gradient-to-r from-red-400 to-white text-hollow">Master</span>
                            </h1>
                            <div className="px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-widest bg-red-500/10 text-red-500 border border-red-500/20 shadow-[0_0_15px_rgba(239,68,68,0.2)]">
                                Admin Protocol
                            </div>
                        </div>
                        <p className="text-zinc-500 max-w-xl">Configure system-wide API integrations, infrastructure, and autonomous engine parameters for all viral nodes.</p>
                    </div>
                    <button
                        onClick={saveSettings}
                        disabled={isSaving}
                        className={cn(
                            "bg-primary hover:bg-primary/90 text-white font-black py-4 px-8 rounded-2xl transition-all flex items-center gap-3 uppercase tracking-widest text-[10px] shadow-[0_0_30px_rgba(var(--primary-rgb),0.3)]",
                            isSaving && "opacity-50 cursor-not-allowed",
                            saveStatus === "success" && "bg-emerald-500 hover:bg-emerald-600 shadow-[0_0_30px_rgba(16,185,129,0.3)]"
                        )}
                    >
                        {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : saveStatus === "success" ? <CheckCircle2 className="h-4 w-4" /> : <Save className="h-4 w-4" />}
                        {isSaving ? "Synchronizing..." : saveStatus === "success" ? "Protocol Saved" : "Commit Changes"}
                    </button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-5 gap-10">
                    {/* Navigation Tabs */}
                    <div className="space-y-1">
                        {tabs.map(tab => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={cn(
                                    "w-full flex items-center gap-3 px-5 py-4 rounded-xl transition-all duration-300 font-black text-[10px] uppercase tracking-widest group",
                                    activeTab === tab.id
                                        ? "bg-red-500/15 text-red-500 border border-red-500/20 shadow-[0_0_20px_rgba(239,68,68,0.1)]"
                                        : "text-zinc-500 hover:bg-white/5 hover:text-zinc-200"
                                )}
                            >
                                <tab.icon className={cn("h-4 w-4 transition-transform", activeTab === tab.id ? "scale-110" : "group-hover:scale-110")} />
                                {tab.label}
                            </button>
                        ))}
                    </div>

                    {/* Main Content Area */}
                    <div className="lg:col-span-4 space-y-8">
                        {isLoading ? (
                            <div className="h-64 flex items-center justify-center">
                                <Loader2 className="h-8 w-8 text-primary animate-spin" />
                            </div>
                        ) : activeTab === "OAuth" && (
                            <section className="card-gradient border border-white/5 rounded-3xl p-10 space-y-10 shadow-2xl">
                                <div className="flex items-center gap-6">
                                    <div className="h-16 w-16 rounded-2xl bg-red-500/10 flex items-center justify-center border border-red-500/20 shadow-[0_0_20px_rgba(239,68,68,0.15)]">
                                        <Key className="h-8 w-8 text-red-500" />
                                    </div>
                                    <div>
                                        <h3 className="text-3xl font-black text-white italic uppercase tracking-tighter">OAuth <span className="text-hollow">Credentials</span></h3>
                                        <p className="text-zinc-500 text-sm">System-wide OAuth configuration for global integrations.</p>
                                    </div>
                                </div>

                                <div className="space-y-4 pt-4 border-t border-zinc-800">
                                    <h4 className="text-sm font-bold text-zinc-400 uppercase tracking-wider">Google / YouTube</h4>
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

                                <div className="space-y-4 pt-4 border-t border-zinc-800">
                                    <h4 className="text-sm font-bold text-zinc-400 uppercase tracking-wider">TikTok</h4>
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
                            </section>
                        )}

                        {activeTab === "API" && (
                            <section className="card-gradient border border-white/5 rounded-3xl p-10 space-y-10 shadow-2xl">
                                <div className="flex items-center gap-6">
                                    <div className="h-16 w-16 rounded-2xl bg-red-500/10 flex items-center justify-center border border-red-500/20 shadow-[0_0_20px_rgba(239,68,68,0.15)]">
                                        <Bot className="h-8 w-8 text-red-500" />
                                    </div>
                                    <div>
                                        <h3 className="text-3xl font-black text-white italic uppercase tracking-tighter">API <span className="text-hollow">Master Keys</span></h3>
                                        <p className="text-zinc-500 text-sm">System-wide API keys for background scanning and core intelligence.</p>
                                    </div>
                                </div>

                                <div className="space-y-6 pt-6 border-t border-white/5">
                                    <KeyInput
                                        label="Groq API Key"
                                        id="groq_api_key"
                                        value={settings.groq_api_key}
                                        onChange={(val) => updateSetting("groq_api_key", val)}
                                        isVisible={showKey["groq_api_key"]}
                                        onToggle={() => toggleKey("groq_api_key")}
                                    />
                                    <KeyInput
                                        label="OpenAI API Key"
                                        id="openai_api_key"
                                        value={settings.openai_api_key}
                                        onChange={(val) => updateSetting("openai_api_key", val)}
                                        isVisible={showKey["openai_api_key"]}
                                        onToggle={() => toggleKey("openai_api_key")}
                                    />
                                    <KeyInput
                                        label="ElevenLabs API Key"
                                        id="elevenlabs_api_key"
                                        value={settings.elevenlabs_api_key}
                                        onChange={(val) => updateSetting("elevenlabs_api_key", val)}
                                        isVisible={showKey["elevenlabs_api_key"]}
                                        onToggle={() => toggleKey("elevenlabs_api_key")}
                                    />
                                    <KeyInput
                                        label="Pexels API Key"
                                        id="pexels_api_key"
                                        value={settings.pexels_api_key}
                                        onChange={(val) => updateSetting("pexels_api_key", val)}
                                        isVisible={showKey["pexels_api_key"]}
                                        onToggle={() => toggleKey("pexels_api_key")}
                                    />
                                </div>
                            </section>
                        )}

                        {activeTab === "Storage" && (
                            <section className="card-gradient border border-white/5 rounded-3xl p-10 space-y-10 shadow-2xl">
                                <div className="flex items-center gap-6">
                                    <div className="h-16 w-16 rounded-2xl bg-red-500/10 flex items-center justify-center border border-red-500/20 shadow-[0_0_20px_rgba(239,68,68,0.15)]">
                                        <Database className="h-8 w-8 text-red-500" />
                                    </div>
                                    <div>
                                        <h3 className="text-3xl font-black text-white italic uppercase tracking-tighter">Cloud <span className="text-hollow">Vault</span></h3>
                                        <p className="text-zinc-500 text-sm">AWS S3 and OCI storage configuration for global asset delivery.</p>
                                    </div>
                                </div>

                                <div className="space-y-6 pt-6 border-t border-white/5">
                                    <div>
                                        <label className="text-[10px] font-bold text-zinc-400 mb-2 block uppercase tracking-widest">Storage Provider</label>
                                        <select
                                            value={settings.storage_provider}
                                            onChange={(e) => updateSetting("storage_provider", e.target.value)}
                                            className="w-full bg-zinc-950/50 border border-white/10 rounded-xl py-4 px-6 text-white font-bold"
                                        >
                                            <option value="LOCAL">Local Storage</option>
                                            <option value="AWS">AWS S3</option>
                                            <option value="OCI">Oracle Cloud Infrastructure</option>
                                            <option value="GCP">Google Cloud Platform</option>
                                            <option value="AZURE">Azure Blob Storage</option>
                                        </select>
                                    </div>
                                    <KeyInput
                                        label="AWS Access Key ID"
                                        id="aws_access_key_id"
                                        value={settings.aws_access_key_id}
                                        onChange={(val) => updateSetting("aws_access_key_id", val)}
                                        isVisible={showKey["aws_access_key_id"]}
                                        onToggle={() => toggleKey("aws_access_key_id")}
                                    />
                                    <KeyInput
                                        label="AWS Secret Access Key"
                                        id="aws_secret_access_key"
                                        value={settings.aws_secret_access_key}
                                        onChange={(val) => updateSetting("aws_secret_access_key", val)}
                                        isVisible={showKey["aws_secret_access_key"]}
                                        onToggle={() => toggleKey("aws_secret_access_key")}
                                    />
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div>
                                            <label className="text-[10px] font-bold text-zinc-400 mb-2 block uppercase tracking-widest">Region</label>
                                            <input
                                                type="text"
                                                value={settings.aws_region}
                                                onChange={(e) => updateSetting("aws_region", e.target.value)}
                                                className="w-full bg-zinc-950/50 border border-white/10 rounded-xl py-4 px-6 text-white"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-[10px] font-bold text-zinc-400 mb-2 block uppercase tracking-widest">Bucket Name</label>
                                            <input
                                                type="text"
                                                value={settings.aws_storage_bucket_name}
                                                onChange={(e) => updateSetting("aws_storage_bucket_name", e.target.value)}
                                                className="w-full bg-zinc-950/50 border border-white/10 rounded-xl py-4 px-6 text-white"
                                                placeholder="my-bucket"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </section>
                        )}

                        {activeTab === "Payment" && (
                            <section className="card-gradient border border-white/5 rounded-3xl p-10 space-y-10 shadow-2xl">
                                <div className="flex items-center gap-6">
                                    <div className="h-16 w-16 rounded-2xl bg-red-500/10 flex items-center justify-center border border-red-500/20 shadow-[0_0_20px_rgba(239,68,68,0.15)]">
                                        <CreditCard className="h-8 w-8 text-red-500" />
                                    </div>
                                    <div>
                                        <h3 className="text-3xl font-black text-white italic uppercase tracking-tighter">Payment <span className="text-hollow">Gateway</span></h3>
                                        <p className="text-zinc-500 text-sm">Stripe configuration for system-wide subscription processing.</p>
                                    </div>
                                </div>

                                <div className="space-y-6 pt-6 border-t border-white/5">
                                    <KeyInput
                                        label="Stripe Secret Key"
                                        id="stripe_secret_key"
                                        value={settings.stripe_secret_key}
                                        onChange={(val) => updateSetting("stripe_secret_key", val)}
                                        isVisible={showKey["stripe_secret_key"]}
                                        onToggle={() => toggleKey("stripe_secret_key")}
                                    />
                                    <KeyInput
                                        label="Stripe Webhook Secret"
                                        id="stripe_webhook_secret"
                                        value={settings.stripe_webhook_secret}
                                        onChange={(val) => updateSetting("stripe_webhook_secret", val)}
                                        isVisible={showKey["stripe_webhook_secret"]}
                                        onToggle={() => toggleKey("stripe_webhook_secret")}
                                    />
                                </div>
                            </section>
                        )}

                        {activeTab === "Commerce" && (
                            <section className="card-gradient border border-white/5 rounded-3xl p-10 space-y-10 shadow-2xl">
                                <div className="flex items-center gap-6">
                                    <div className="h-16 w-16 rounded-2xl bg-red-500/10 flex items-center justify-center border border-red-500/20 shadow-[0_0_20px_rgba(239,68,68,0.15)]">
                                        <ShoppingCart className="h-8 w-8 text-red-500" />
                                    </div>
                                    <div>
                                        <h3 className="text-3xl font-black text-white italic uppercase tracking-tighter">Commerce <span className="text-hollow">Core</span></h3>
                                        <p className="text-zinc-500 text-sm">Global Shopify and affiliate infrastructure settings.</p>
                                    </div>
                                </div>

                                <div className="space-y-6 pt-6 border-t border-white/5">
                                    <div>
                                        <label className="text-[10px] font-bold text-zinc-400 mb-2 block uppercase tracking-widest">Shopify Store URL</label>
                                        <input
                                            type="text"
                                            value={settings.shopify_shop_url}
                                            onChange={(e) => updateSetting("shopify_shop_url", e.target.value)}
                                            className="w-full bg-zinc-950/50 border border-white/10 rounded-xl py-4 px-6 text-white font-bold"
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
                            </section>
                        )}

                        {activeTab === "Infrastructure" && (
                            <section className="card-gradient border border-white/5 rounded-3xl p-10 space-y-10 shadow-2xl">
                                <div className="flex items-center gap-6">
                                    <div className="h-16 w-16 rounded-2xl bg-red-500/10 flex items-center justify-center border border-red-500/20 shadow-[0_0_20px_rgba(239,68,68,0.15)]">
                                        <Server className="h-8 w-8 text-red-500" />
                                    </div>
                                    <div>
                                        <h3 className="text-3xl font-black text-white italic uppercase tracking-tighter">System <span className="text-hollow">Node</span></h3>
                                        <p className="text-zinc-500 text-sm">Production domain and render cluster configuration.</p>
                                    </div>
                                </div>

                                <div className="space-y-6 pt-6 border-t border-white/5">
                                    <div>
                                        <label className="text-[10px] font-bold text-zinc-400 mb-2 block uppercase tracking-widest">Production Domain</label>
                                        <input
                                            type="text"
                                            value={settings.production_domain}
                                            onChange={(e) => updateSetting("production_domain", e.target.value)}
                                            className="w-full bg-zinc-950/50 border border-white/10 rounded-xl py-4 px-6 text-white font-bold"
                                            placeholder="https://api.yourdomain.com"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-[10px] font-bold text-zinc-400 mb-2 block uppercase tracking-widest">Render Node URL (LTX)</label>
                                        <input
                                            type="text"
                                            value={settings.render_node_url}
                                            onChange={(e) => updateSetting("render_node_url", e.target.value)}
                                            className="w-full bg-zinc-950/50 border border-white/10 rounded-xl py-4 px-6 text-white font-bold"
                                            placeholder="https://your-render-node.ngrok.io"
                                        />
                                    </div>
                                </div>
                            </section>
                        )}

                        {activeTab === "WhatsApp" && (
                            <section className="card-gradient border border-white/5 rounded-3xl p-10 space-y-10 shadow-2xl">
                                <div className="flex items-center gap-6">
                                    <div className="h-16 w-16 rounded-2xl bg-red-500/10 flex items-center justify-center border border-red-500/20 shadow-[0_0_20px_rgba(239,68,68,0.15)]">
                                        <Bot className="h-8 w-8 text-red-500" />
                                    </div>
                                    <div>
                                        <h3 className="text-3xl font-black text-white italic uppercase tracking-tighter">Nexus <span className="text-hollow">Comms</span></h3>
                                        <p className="text-zinc-500 text-sm">Twilio WhatsApp gateway for system-wide notifications.</p>
                                    </div>
                                </div>

                                <div className="space-y-6 pt-6 border-t border-white/5">
                                    <KeyInput
                                        label="Twilio Account SID"
                                        id="twilio_account_sid"
                                        value={settings.twilio_account_sid}
                                        onChange={(val) => updateSetting("twilio_account_sid", val)}
                                        isVisible={showKey["twilio_account_sid"]}
                                        onToggle={() => toggleKey("twilio_account_sid")}
                                    />
                                    <KeyInput
                                        label="Twilio Auth Token"
                                        id="twilio_auth_token"
                                        value={settings.twilio_auth_token}
                                        onChange={(val) => updateSetting("twilio_auth_token", val)}
                                        isVisible={showKey["twilio_auth_token"]}
                                        onToggle={() => toggleKey("twilio_auth_token")}
                                    />
                                    <div>
                                        <label className="text-[10px] font-bold text-zinc-400 mb-2 block uppercase tracking-widest">WhatsApp Sender Number</label>
                                        <input
                                            type="text"
                                            value={settings.twilio_whatsapp_number}
                                            onChange={(e) => updateSetting("twilio_whatsapp_number", e.target.value)}
                                            className="w-full bg-zinc-950/50 border border-white/10 rounded-xl py-4 px-6 text-white font-bold"
                                            placeholder="+1234567890"
                                        />
                                    </div>
                                </div>
                            </section>
                        )}

                        {activeTab === "Engine" && (
                            <section className="card-gradient border border-white/5 rounded-3xl p-10 space-y-10 shadow-2xl">
                                <div className="flex items-center gap-6">
                                    <div className="h-16 w-16 rounded-2xl bg-red-500/10 flex items-center justify-center border border-red-500/20 shadow-[0_0_20px_rgba(239,68,68,0.15)]">
                                        <Wand2 className="h-8 w-8 text-red-500" />
                                    </div>
                                    <div>
                                        <h3 className="text-3xl font-black text-white italic uppercase tracking-tighter">Viral <span className="text-hollow">Engine</span></h3>
                                        <p className="text-zinc-500 text-sm">Autonomous parameters and feature clusters for the production pipeline.</p>
                                    </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-6 border-t border-white/5">
                                    <div className="space-y-6">
                                        <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">Autonomous Parameters</h4>
                                        <div className="space-y-4">
                                            <div>
                                                <label className="text-[10px] font-bold text-zinc-400 mb-2 block uppercase tracking-widest">Scan Frequency</label>
                                                <select
                                                    value={settings.scan_frequency}
                                                    onChange={(e) => updateSetting("scan_frequency", e.target.value)}
                                                    className="w-full bg-zinc-950/50 border border-white/10 rounded-xl py-4 px-6 text-white font-bold"
                                                >
                                                    <option value="Every 15 minutes">Every 15 minutes</option>
                                                    <option value="Every 1 hour">Every 1 hour</option>
                                                    <option value="Every 6 hours">Every 6 hours</option>
                                                    <option value="Daily">Daily</option>
                                                </select>
                                            </div>
                                            <ToggleSwitch
                                                label="Viral Autonomy"
                                                description="Engine follows the zero-loop without approval"
                                                checked={settings.auto_pilot === "true"}
                                                onChange={(val) => updateSetting("auto_pilot", val ? "true" : "false")}
                                            />
                                            <ToggleSwitch
                                                label="Force Originality"
                                                description="Always prioritize un-indexed content"
                                                checked={settings.force_originality === "true"}
                                                onChange={(val) => updateSetting("force_originality", val ? "true" : "false")}
                                            />
                                        </div>
                                    </div>

                                    <div className="space-y-6">
                                        <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-zinc-500">Video Quality Protocol</h4>
                                        <div className="grid grid-cols-1 gap-4">
                                            <ToggleSwitch
                                                label="Sound Design"
                                                description="Neural audio layering"
                                                checked={settings.enable_sound_design === "true"}
                                                onChange={(val) => updateSetting("enable_sound_design", val ? "true" : "false")}
                                            />
                                            <ToggleSwitch
                                                label="Motion Graphics"
                                                description="High-fidelity visual overrides"
                                                checked={settings.enable_motion_graphics === "true"}
                                                onChange={(val) => updateSetting("enable_motion_graphics", val ? "true" : "false")}
                                            />
                                            <div className="pt-2">
                                                <label className="text-[10px] font-bold text-zinc-400 mb-2 block uppercase tracking-widest">AI Video Provider</label>
                                                <select
                                                    value={settings.ai_video_provider}
                                                    onChange={(e) => updateSetting("ai_video_provider", e.target.value)}
                                                    className="w-full bg-zinc-950/50 border border-white/10 rounded-xl py-4 px-6 text-white font-bold"
                                                >
                                                    <option value="none">Disabled</option>
                                                    <option value="runway">Runway ML</option>
                                                    <option value="pika">Pika Labs</option>
                                                </select>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </section>
                        )}
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}

function KeyInput({ label, id, value, onChange, isVisible, onToggle }: {
    label: string;
    id: string;
    value: string;
    onChange: (value: string) => void;
    isVisible: boolean;
    onToggle: () => void;
}) {
    return (
        <div>
            <label htmlFor={id} className="text-sm font-bold text-zinc-400 mb-2 block">{label}</label>
            <div className="relative">
                <input
                    id={id}
                    type={isVisible ? "text" : "password"}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    className="w-full bg-zinc-950/50 border border-white/10 rounded-xl py-3 px-4 pr-12 text-white font-mono text-sm"
                    placeholder="••••••••••••••••"
                />
                <button
                    type="button"
                    onClick={onToggle}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-white transition-colors"
                >
                    {isVisible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
            </div>
        </div>
    );
}

function ToggleSwitch({ label, description, checked, onChange }: {
    label: string;
    description: string;
    checked: boolean;
    onChange: (value: boolean) => void;
}) {
    return (
        <button
            onClick={() => onChange(!checked)}
            className={cn(
                "p-4 rounded-2xl border text-left transition-all",
                checked
                    ? "bg-primary/10 border-primary"
                    : "bg-zinc-950/30 border-zinc-800 hover:border-zinc-700"
            )}
        >
            <div className="flex items-center justify-between">
                <div>
                    <span className={cn("block font-bold text-sm", checked ? "text-white" : "text-zinc-400")}>{label}</span>
                    <span className="text-xs text-zinc-500">{description}</span>
                </div>
                <div className={cn(
                    "h-6 w-12 rounded-full transition-colors relative",
                    checked ? "bg-primary" : "bg-zinc-700"
                )}>
                    <div className={cn(
                        "absolute top-1 h-4 w-4 rounded-full bg-white transition-all",
                        checked ? "left-7" : "left-1"
                    )} />
                </div>
            </div>
        </button>
    );
}
