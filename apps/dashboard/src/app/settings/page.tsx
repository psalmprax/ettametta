"use client";

import React, { useState, useEffect, useCallback } from "react";
import { withRealFallback } from "@/lib/real_first_utils";
import { useTelemetry } from "@/context/TelemetryContext";
import { useForm, useFormContext, FormProvider } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";import {
    Server,
    EyeOff,
    Eye,
    Terminal,
    Fingerprint,
    Lock,
    Settings,
    Crown,
    Sparkles,
    Clock,
    ArrowUpRight,
    Zap,
    AlertCircle,
    ChevronDown,
    Globe,
    Sliders,
    Key,
    Database,
    Video,
    MessageSquare,
    ShoppingCart,
    Mail,
    Link,
    Trash2
} from "lucide-react";
import { cn } from "@/lib/utils";
import { API_BASE } from "@/lib/config";
import { getAuthToken } from "@/lib/auth_utils";
import { toast } from "sonner";
import { motion, AnimatePresence } from "framer-motion";
import CommandCenterLayout from "@/components/CommandCenterLayout";
import { AgentMatrix } from "@/components/ui/CommandCenterComponents";
import { ThemeSwitcher } from "@/components/theme-toggle";
import { Button } from "@/components/ui/Button";
import { ConfirmModal } from "@/components/ui/ConfirmModal";

// ─── Setting Field Definitions ───────────────────────────────────────────────
// Each setting is defined here once, then used to drive the Zod schema, the UI,
// and the save payload. Single source of truth.

interface SettingField {
    key: string;
    label: string;
    description?: string;
    type: "password" | "text" | "select" | "toggle" | "number";
    tab: "security" | "infrastructure" | "operations";
    section: string;
    sectionLabel: string;
    category: string;
    sectionIcon?: React.ComponentType<{ className?: string }>;
    options?: { label: string; value: string }[];
    placeholder?: string;
}

const SETTING_FIELDS: SettingField[] = [
    // ── Security Hub / LLM Providers ──────────────────────────────────────
    { key: "groq_api_key", label: "GROQ", description: "Fast inference, 30 RPM free tier", type: "password", tab: "security", section: "llm", sectionLabel: "LLM Providers", category: "llm", sectionIcon: Key },
    { key: "openai_api_key", label: "OpenAI", description: "GPT-4o, GPT-4, GPT-3.5", type: "password", tab: "security", section: "llm", sectionLabel: "LLM Providers", category: "llm" },
    { key: "anthropic_api_key", label: "Anthropic", description: "Claude 3.5 Sonnet, Haiku", type: "password", tab: "security", section: "llm", sectionLabel: "LLM Providers", category: "llm" },
    { key: "xai_api_key", label: "xAI (Grok)", description: "Grok models via xAI", type: "password", tab: "security", section: "llm", sectionLabel: "LLM Providers", category: "llm" },
    { key: "deepseek_api_key", label: "DeepSeek", description: "DeepSeek V2/V3", type: "password", tab: "security", section: "llm", sectionLabel: "LLM Providers", category: "llm" },
    { key: "google_api_key", label: "Google AI", description: "Gemini models (gemin-1.5-flash, pro)", type: "password", tab: "security", section: "llm", sectionLabel: "LLM Providers", category: "llm" },
    { key: "cohere_api_key", label: "Cohere", description: "20 RPM, 1K tokens/mo free", type: "password", tab: "security", section: "llm", sectionLabel: "LLM Providers", category: "llm" },
    { key: "mistral_api_key", label: "Mistral AI", description: "1 req/s, 1B tokens/mo free", type: "password", tab: "security", section: "llm", sectionLabel: "LLM Providers", category: "llm" },
    { key: "cerebras_api_key", label: "Cerebras", description: "30 RPM, 14K RPD free", type: "password", tab: "security", section: "llm", sectionLabel: "LLM Providers", category: "llm" },
    { key: "cloudflare_api_key", label: "Cloudflare Workers AI", type: "password", tab: "security", section: "llm", sectionLabel: "LLM Providers", category: "llm" },
    { key: "cloudflare_account_id", label: "Cloudflare Account ID", type: "text", tab: "security", section: "llm", sectionLabel: "LLM Providers", category: "llm" },
    { key: "hugging_face_api_key", label: "Hugging Face", description: "$0.10/mo free credits", type: "password", tab: "security", section: "llm", sectionLabel: "LLM Providers", category: "llm" },
    { key: "openrouter_api_key", label: "OpenRouter", description: "50 RPD free", type: "password", tab: "security", section: "llm", sectionLabel: "LLM Providers", category: "llm" },
    { key: "nvidia_api_key", label: "NVIDIA NIM", description: "40 RPM free", type: "password", tab: "security", section: "llm", sectionLabel: "LLM Providers", category: "llm" },
    { key: "ollama_cloud_api_key", label: "Ollama Cloud", type: "password", tab: "security", section: "llm", sectionLabel: "LLM Providers", category: "llm" },
    { key: "siliconflow_api_key", label: "SiliconFlow", description: "1K RPM, 50K TPM free", type: "password", tab: "security", section: "llm", sectionLabel: "LLM Providers", category: "llm" },
    { key: "ollama_url", label: "Ollama URL", description: "Local Ollama server endpoint", type: "text", tab: "security", section: "llm", sectionLabel: "LLM Providers", category: "llm", placeholder: "http://ettametta-ollama:11434" },
    { key: "lm_studio_url", label: "LM Studio URL", description: "Local LM Studio endpoint", type: "text", tab: "security", section: "llm", sectionLabel: "LLM Providers", category: "llm", placeholder: "http://localhost:1234" },

    // ── Security Hub / Social Media & OAuth ───────────────────────────────
    { key: "youtube_api_key", label: "YouTube API Key", type: "password", tab: "security", section: "social", sectionLabel: "Social Media & OAuth", category: "social", sectionIcon: Globe },
    { key: "tiktok_api_key", label: "TikTok API Key", type: "password", tab: "security", section: "social", sectionLabel: "Social Media & OAuth", category: "social" },
    { key: "tiktok_client_key", label: "TikTok Client Key", type: "password", tab: "security", section: "social", sectionLabel: "Social Media & OAuth", category: "social" },
    { key: "tiktok_client_secret", label: "TikTok Client Secret", type: "password", tab: "security", section: "social", sectionLabel: "Social Media & OAuth", category: "social" },
    { key: "google_client_id", label: "Google Client ID", description: "Used for OAuth + YouTube publishing", type: "password", tab: "security", section: "social", sectionLabel: "Social Media & OAuth", category: "social" },
    { key: "google_client_secret", label: "Google Client Secret", type: "password", tab: "security", section: "social", sectionLabel: "Social Media & OAuth", category: "social" },

    // ── Security Hub / Video & Voice ──────────────────────────────────────
    { key: "elevenlabs_api_key", label: "ElevenLabs", description: "Voice cloning & TTS", type: "password", tab: "security", section: "video-engine", sectionLabel: "Video & Voice Engines", category: "video", sectionIcon: Video },
    { key: "fish_speech_endpoint", label: "Fish Speech Endpoint", type: "text", tab: "security", section: "video-engine", sectionLabel: "Video & Voice Engines", category: "video", placeholder: "http://voiceover:8080" },
    { key: "pexels_api_key", label: "Pexels", description: "Stock video library", type: "password", tab: "security", section: "video-engine", sectionLabel: "Video & Voice Engines", category: "video" },
    { key: "google_search_cx", label: "Google Search CX", description: "Custom Search Engine ID", type: "text", tab: "security", section: "video-engine", sectionLabel: "Video & Voice Engines", category: "video" },
    { key: "runway_api_key", label: "Runway ML", description: "Text/video-to-video generation", type: "password", tab: "security", section: "video-engine", sectionLabel: "Video & Voice Engines", category: "video" },
    { key: "pika_api_key", label: "Pika Labs", description: "Video generation", type: "password", tab: "security", section: "video-engine", sectionLabel: "Video & Voice Engines", category: "video" },
    { key: "zsky_api_key", label: "ZSky", description: "~50 credits/day", type: "password", tab: "security", section: "video-engine", sectionLabel: "Video & Voice Engines", category: "video" },
    { key: "kling_api_key", label: "Kling", description: "~100 credits/day", type: "password", tab: "security", section: "video-engine", sectionLabel: "Video & Voice Engines", category: "video" },
    { key: "pixverse_api_key", label: "PixVerse", description: "~20 credits/day", type: "password", tab: "security", section: "video-engine", sectionLabel: "Video & Voice Engines", category: "video" },
    { key: "replicate_api_key", label: "Replicate", description: "Free trial credits", type: "password", tab: "security", section: "video-engine", sectionLabel: "Video & Voice Engines", category: "video" },
    { key: "stability_api_key", label: "Stability AI", description: "~25 credits/day", type: "password", tab: "security", section: "video-engine", sectionLabel: "Video & Voice Engines", category: "video" },

    // ── Security Hub / Payment & E-commerce ───────────────────────────────
    { key: "stripe_secret_key", label: "Stripe Secret Key", type: "password", tab: "security", section: "payment", sectionLabel: "Payment & E-commerce", category: "payment", sectionIcon: ShoppingCart },
    { key: "shopify_shop_url", label: "Shopify Shop URL", description: "Your myshopify.com domain", type: "text", tab: "security", section: "payment", sectionLabel: "Payment & E-commerce", category: "payment", placeholder: "https://your-store.myshopify.com" },
    { key: "shopify_access_token", label: "Shopify Access Token", type: "password", tab: "security", section: "payment", sectionLabel: "Payment & E-commerce", category: "payment" },
    { key: "printful_api_key", label: "Printful API Key", description: "Print-on-demand fulfillment", type: "password", tab: "security", section: "payment", sectionLabel: "Payment & E-commerce", category: "payment" },

    // ── Security Hub / Communication ──────────────────────────────────────
    { key: "telegram_bot_token", label: "Telegram Bot Token", type: "password", tab: "security", section: "communication", sectionLabel: "Communication", category: "communication", sectionIcon: MessageSquare },
    { key: "telegram_admin_id", label: "Telegram Admin ID", type: "text", tab: "security", section: "communication", sectionLabel: "Communication", category: "communication" },
    { key: "twilio_account_sid", label: "Twilio Account SID", type: "password", tab: "security", section: "communication", sectionLabel: "Communication", category: "communication" },
    { key: "twilio_auth_token", label: "Twilio Auth Token", type: "password", tab: "security", section: "communication", sectionLabel: "Communication", category: "communication" },
    { key: "twilio_whatsapp_number", label: "Twilio WhatsApp Number", type: "text", tab: "security", section: "communication", sectionLabel: "Communication", category: "communication", placeholder: "+1234567890" },

    // ── Security Hub / Email Marketing ────────────────────────────────────
    { key: "mailchimp_api_key", label: "Mailchimp API Key", type: "password", tab: "security", section: "email", sectionLabel: "Email Marketing", category: "email", sectionIcon: Mail },
    { key: "mailchimp_list_id", label: "Mailchimp List ID", type: "text", tab: "security", section: "email", sectionLabel: "Email Marketing", category: "email" },
    { key: "convertkit_api_key", label: "ConvertKit API Key", type: "password", tab: "security", section: "email", sectionLabel: "Email Marketing", category: "email" },

    // ── Security Hub / Affiliate Programs ─────────────────────────────────
    { key: "amazon_associates_tag", label: "Amazon Associates Tag", type: "text", tab: "security", section: "affiliate", sectionLabel: "Affiliate Programs", category: "affiliate", sectionIcon: Link },
    { key: "amazon_paapi_key", label: "Amazon PA-API Key", type: "password", tab: "security", section: "affiliate", sectionLabel: "Affiliate Programs", category: "affiliate" },
    { key: "amazon_paapi_tag", label: "Amazon PA-API Tag", type: "text", tab: "security", section: "affiliate", sectionLabel: "Affiliate Programs", category: "affiliate" },
    { key: "impact_radius_api_key", label: "Impact Radius API Key", type: "password", tab: "security", section: "affiliate", sectionLabel: "Affiliate Programs", category: "affiliate" },
    { key: "shareasale_api_key", label: "ShareASale API Key", type: "password", tab: "security", section: "affiliate", sectionLabel: "Affiliate Programs", category: "affiliate" },

    // ── Infrastructure / Domain & Endpoints ───────────────────────────────
    { key: "production_domain", label: "Production Domain", description: "Public-facing domain URL", type: "text", tab: "infrastructure", section: "domain", sectionLabel: "Domain & Endpoints", category: "infrastructure", sectionIcon: Globe, placeholder: "http://localhost:8000" },
    { key: "cors_origins", label: "CORS Origins", description: "Comma-separated allowed origins", type: "text", tab: "infrastructure", section: "domain", sectionLabel: "Domain & Endpoints", category: "infrastructure", placeholder: "http://localhost:3000,http://localhost:8080" },
    { key: "comfyui_url", label: "ComfyUI URL", type: "text", tab: "infrastructure", section: "domain", sectionLabel: "Domain & Endpoints", category: "infrastructure", placeholder: "http://localhost:8188" },
    { key: "render_node_url", label: "Render Node URL", description: "Colab/Remote GPU node", type: "text", tab: "infrastructure", section: "domain", sectionLabel: "Domain & Endpoints", category: "infrastructure" },
    { key: "dify_api_url", label: "Dify API URL", type: "text", tab: "infrastructure", section: "domain", sectionLabel: "Domain & Endpoints", category: "infrastructure" },

    // ── Infrastructure / Storage ──────────────────────────────────────────────
    { key: "storage_provider", label: "Storage Provider", description: "Local, AWS S3, OCI, GCP, Azure", type: "select", tab: "infrastructure", section: "storage", sectionLabel: "Storage Configuration", category: "infrastructure", sectionIcon: Database, options: [
        { label: "Local", value: "LOCAL" },
        { label: "AWS S3", value: "AWS" },
        { label: "OCI", value: "OCI" },
        { label: "GCP", value: "GCP" },
        { label: "Azure", value: "AZURE" },
        { label: "Custom S3", value: "CUSTOM" },
    ]},
    { key: "storage_endpoint", label: "Storage Endpoint URL", type: "text", tab: "infrastructure", section: "storage", sectionLabel: "Storage Configuration", category: "infrastructure" },
    { key: "storage_bucket", label: "Storage Bucket Name", type: "text", tab: "infrastructure", section: "storage", sectionLabel: "Storage Configuration", category: "infrastructure" },
    { key: "storage_access_key", label: "Storage Access Key", type: "password", tab: "infrastructure", section: "storage", sectionLabel: "Storage Configuration", category: "infrastructure" },
    { key: "storage_secret_key", label: "Storage Secret Key", type: "password", tab: "infrastructure", section: "storage", sectionLabel: "Storage Configuration", category: "infrastructure" },
    { key: "storage_region", label: "Storage Region", type: "text", tab: "infrastructure", section: "storage", sectionLabel: "Storage Configuration", category: "infrastructure", placeholder: "us-east-1" },

    // ── Operations / Feature Toggles ──────────────────────────────────────
    { key: "enable_sound_design", label: "Sound Design Engine", description: "Auto background music & SFX", type: "toggle", tab: "operations", section: "toggles", sectionLabel: "Feature Toggles", category: "features", sectionIcon: Sliders },
    { key: "enable_motion_graphics", label: "Motion Graphics Engine", description: "Animated text overlays & titles", type: "toggle", tab: "operations", section: "toggles", sectionLabel: "Feature Toggles", category: "features" },
    { key: "enable_langchain", label: "LangChain Integration", description: "LangChain agent framework", type: "toggle", tab: "operations", section: "toggles", sectionLabel: "Feature Toggles", category: "features" },
    { key: "enable_crewai", label: "CrewAI Integration", description: "Multi-agent orchestration", type: "toggle", tab: "operations", section: "toggles", sectionLabel: "Feature Toggles", category: "features" },
    { key: "enable_interpreter", label: "Code Interpreter", description: "Sandboxed Python execution", type: "toggle", tab: "operations", section: "toggles", sectionLabel: "Feature Toggles", category: "features" },
    { key: "enable_affiliate_api", label: "Affiliate API", description: "Auto-affiliate link insertion", type: "toggle", tab: "operations", section: "toggles", sectionLabel: "Feature Toggles", category: "features" },
    { key: "enable_opencli", label: "OpenCLI Bridge", description: "Per-user Chrome session bridge", type: "toggle", tab: "operations", section: "toggles", sectionLabel: "Feature Toggles", category: "features" },
    { key: "use_os_models", label: "Use OS Models", description: "Prefer open-source models over API", type: "toggle", tab: "operations", section: "toggles", sectionLabel: "Feature Toggles", category: "features" },
    { key: "enable_monetization", label: "Monetization Engine", description: "Enable monetization features", type: "toggle", tab: "operations", section: "toggles", sectionLabel: "Feature Toggles", category: "features" },

    // ── Operations / AI & Video Defaults ──────────────────────────────────
    { key: "default_llm_provider", label: "Default LLM Provider", description: "Primary AI provider for inference", type: "select", tab: "operations", section: "ai-defaults", sectionLabel: "AI & Video Defaults", category: "features", sectionIcon: Zap, options: [
        { label: "Groq", value: "groq" },
        { label: "OpenAI", value: "openai" },
        { label: "Anthropic", value: "anthropic" },
        { label: "DeepSeek", value: "deepseek" },
        { label: "Google Gemini", value: "google" },
        { label: "xAI (Grok)", value: "xai" },
        { label: "Cohere", value: "cohere" },
        { label: "Mistral", value: "mistral" },
        { label: "Cerebras", value: "cerebras" },
        { label: "Cloudflare", value: "cloudflare" },
        { label: "Hugging Face", value: "huggingface" },
        { label: "OpenRouter", value: "openrouter" },
        { label: "NVIDIA NIM", value: "nvidia" },
        { label: "Ollama Cloud", value: "ollama_cloud" },
        { label: "SiliconFlow", value: "siliconflow" },
        { label: "Local Ollama", value: "ollama" },
        { label: "Local LM Studio", value: "lm_studio" },
    ]},
    { key: "default_vlm_model", label: "Default VLM Model", description: "Vision-language model for video understanding", type: "text", tab: "operations", section: "ai-defaults", sectionLabel: "AI & Video Defaults", category: "features", placeholder: "gemini-1.5-flash" },
    { key: "ai_video_provider", label: "AI Video Provider", description: "Primary video generation engine", type: "select", tab: "operations", section: "ai-defaults", sectionLabel: "AI & Video Defaults", category: "features", options: [
        { label: "None", value: "none" },
        { label: "Runway ML", value: "runway" },
        { label: "Pika Labs", value: "pika" },
        { label: "Luma Ray", value: "luma" },
        { label: "ZSky", value: "zsky" },
        { label: "Kling", value: "kling" },
        { label: "PixVerse", value: "pixverse" },
        { label: "Replicate", value: "replicate" },
        { label: "Stability AI", value: "stability" },
    ]},
    { key: "ai_video_fallbacks", label: "AI Video Fallbacks", description: "Comma-separated fallback providers", type: "text", tab: "operations", section: "ai-defaults", sectionLabel: "AI & Video Defaults", category: "features", placeholder: "runway,pika,replicate" },
    { key: "default_quality_tier", label: "Default Quality Tier", description: "Default video processing level", type: "select", tab: "operations", section: "ai-defaults", sectionLabel: "AI & Video Defaults", category: "features", options: [
        { label: "Standard", value: "standard" },
        { label: "Enhanced", value: "enhanced" },
        { label: "Premium", value: "premium" },
    ]},
    { key: "voice_engine", label: "Voice Engine", description: "Default TTS provider", type: "select", tab: "operations", section: "ai-defaults", sectionLabel: "AI & Video Defaults", category: "features", options: [
        { label: "gTTS (No API key)", value: "gtts" },
        { label: "ElevenLabs", value: "elevenlabs" },
        { label: "Fish Speech", value: "fish_speech" },
    ]},
    { key: "monetization_mode", label: "Monetization Mode", description: "Content monetization strategy", type: "select", tab: "operations", section: "ai-defaults", sectionLabel: "AI & Video Defaults", category: "features", options: [
        { label: "Selective", value: "selective" },
        { label: "All Content", value: "all" },
    ]},

    // ── Operations / Business Logic Limits ────────────────────────────────
    { key: "limit_free", label: "Free Tier Limit", description: "Daily requests for free users", type: "number", tab: "operations", section: "limits", sectionLabel: "Business Logic Limits", category: "limits", sectionIcon: Sliders },
    { key: "limit_pro", label: "Pro Tier Limit", description: "Daily requests for pro users", type: "number", tab: "operations", section: "limits", sectionLabel: "Business Logic Limits", category: "limits" },
    { key: "limit_sovereign", label: "Sovereign Tier Limit", description: "Daily requests for sovereign users", type: "number", tab: "operations", section: "limits", sectionLabel: "Business Logic Limits", category: "limits" },
    { key: "music_volume", label: "Music Volume", description: "Background music volume (0.0 - 1.0)", type: "number", tab: "operations", section: "limits", sectionLabel: "Business Logic Limits", category: "limits" },
    { key: "sfx_volume", label: "SFX Volume", description: "Sound effects volume (0.0 - 1.0)", type: "number", tab: "operations", section: "limits", sectionLabel: "Business Logic Limits", category: "limits" },
    { key: "gpu_queue_slots", label: "GPU Queue Slots", description: "Max concurrent GPU generations", type: "number", tab: "operations", section: "limits", sectionLabel: "Business Logic Limits", category: "limits" },
    { key: "gpu_queue_timeout", label: "GPU Queue Timeout (s)", description: "Max wait for a GPU slot", type: "number", tab: "operations", section: "limits", sectionLabel: "Business Logic Limits", category: "limits" },

    // ── Operations / Monetization & Legacy ────────────────────────────────
    { key: "active_monetization_strategy", label: "Monetization Strategy", description: "Revenue generation approach", type: "select", tab: "operations", section: "monetization", sectionLabel: "Monetization & Legacy Config", category: "monetization", sectionIcon: Sparkles, options: [
        { label: "E-Commerce", value: "commerce" },
        { label: "Affiliate Marketing", value: "affiliate" },
        { label: "Lead Generation", value: "lead_gen" },
        { label: "Digital Products", value: "digital_product" },
        { label: "Membership", value: "membership" },
        { label: "Online Courses", value: "course" },
        { label: "Sponsorships", value: "sponsorship" },
        { label: "Crypto/Donations", value: "crypto" },
    ]},
    { key: "scan_frequency", label: "Scan Frequency", description: "How often to scan for trends", type: "select", tab: "operations", section: "monetization", sectionLabel: "Monetization & Legacy Config", category: "monetization", options: [
        { label: "Every 30 min", value: "Every 30 minutes" },
        { label: "Every 1 hour", value: "Every 1 hour" },
        { label: "Every 2 hours", value: "Every 2 hours" },
        { label: "Every 6 hours", value: "Every 6 hours" },
        { label: "Every 12 hours", value: "Every 12 hours" },
        { label: "Daily", value: "Every 24 hours" },
    ]},
    { key: "monetization_aggression", label: "Monetization Aggression", description: "How aggressively to monetize (0-100)", type: "select", tab: "operations", section: "monetization", sectionLabel: "Monetization & Legacy Config", category: "monetization", options: [
        { label: "Conservative (20)", value: "20" },
        { label: "Moderate (50)", value: "50" },
        { label: "Aggressive (80)", value: "80" },
        { label: "Maximum (100)", value: "100" },
    ]},
    { key: "lead_gen_url", label: "Lead Gen URL", description: "URL for lead capture funnel", type: "text", tab: "operations", section: "monetization", sectionLabel: "Monetization & Legacy Config", category: "monetization" },
    { key: "digital_product_url", label: "Digital Product URL", description: "URL for digital product sales", type: "text", tab: "operations", section: "monetization", sectionLabel: "Monetization & Legacy Config", category: "monetization" },
    { key: "force_originality", label: "Force Originality", description: "Enforce unique content generation", type: "toggle", tab: "operations", section: "monetization", sectionLabel: "Monetization & Legacy Config", category: "monetization" },
    { key: "auto_pilot", label: "Auto-Pilot Mode", description: "Fully autonomous content pipeline", type: "toggle", tab: "operations", section: "monetization", sectionLabel: "Monetization & Legacy Config", category: "monetization" },
    { key: "ai_matching_enabled", label: "AI Content Matching", description: "Auto-match content to trends", type: "toggle", tab: "operations", section: "monetization", sectionLabel: "Monetization & Legacy Config", category: "monetization" },
    { key: "auto_promo_enabled", label: "Auto-Promotion", description: "Auto-promote content across platforms", type: "toggle", tab: "operations", section: "monetization", sectionLabel: "Monetization & Legacy Config", category: "monetization" },
    { key: "auto_merch_enabled", label: "Auto-Merchandising", description: "Auto-generate merchandise from content", type: "toggle", tab: "operations", section: "monetization", sectionLabel: "Monetization & Legacy Config", category: "monetization" },
];

// Generate the Zod schema from the field definitions
const schemaShape: Record<string, z.ZodTypeAny> = {};
for (const field of SETTING_FIELDS) {
    schemaShape[field.key] = z.string().optional();
}
const SettingsSchema = z.object(schemaShape);

type SettingsValues = z.infer<typeof SettingsSchema>;

// ─── Helper: get fields by tab and section ──────────────────────────────────

function getFieldsByTabAndSection(tab: string): Record<string, SettingField[]> {
    const sections: Record<string, SettingField[]> = {};
    for (const field of SETTING_FIELDS) {
        if (field.tab !== tab) continue;
        if (!sections[field.section]) sections[field.section] = [];
        sections[field.section].push(field);
    }
    return sections;
}

function getSectionLabel(section: string): string {
    const field = SETTING_FIELDS.find(f => f.section === section);
    return field?.sectionLabel ?? section;
}

function getSectionIcon(section: string): React.ComponentType<{ className?: string }> | undefined {
    const field = SETTING_FIELDS.find(f => f.section === section && f.sectionIcon);
    return field?.sectionIcon;
}

// ─── Reusable Field Components ─────────────────────────────────────────────

function PasswordField({ field, showKey, toggleShow }: {
    field: SettingField;
    showKey: Record<string, boolean>;
    toggleShow: (key: string) => void;
}) {
    const { register } = useFormContext<SettingsValues>();
    const isVisible = showKey[field.key];

    return (
        <div key={field.key} className="space-y-2">
            <div className="flex items-center justify-between">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">{field.label}</label>
                {field.description && (
                    <span className="text-[9px] text-zinc-600">{field.description}</span>
                )}
            </div>
            <div className="relative">
                <input
                    type={isVisible ? "text" : "password"}
                    {...register(field.key as any)}
                    placeholder={field.placeholder || "••••••••••••••••"}
                    className="w-full h-12 bg-black/60 border border-white/10 rounded-2xl px-5 pr-12 text-white font-mono text-xs tracking-widest focus:border-violet-500/50 outline-none transition-colors placeholder:text-zinc-700"
                />
                <button
                    type="button"
                    onClick={() => toggleShow(field.key)}
                    className="absolute right-5 top-1/2 -translate-y-1/2 text-zinc-600 hover:text-white transition-colors"
                >
                    {isVisible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
            </div>
        </div>
    );
}

function TextField({ field }: { field: SettingField }) {
    const { register } = useFormContext<SettingsValues>();
    return (
        <div key={field.key} className="space-y-2">
            <div className="flex items-center justify-between">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">{field.label}</label>
                {field.description && (
                    <span className="text-[9px] text-zinc-600">{field.description}</span>
                )}
            </div>
            <input
                type="text"
                {...register(field.key as any)}
                placeholder={field.placeholder || ""}
                className="w-full h-12 bg-black/60 border border-white/10 rounded-2xl px-5 text-white text-xs font-mono tracking-wider focus:border-violet-500/50 outline-none transition-colors placeholder:text-zinc-700"
            />
        </div>
    );
}

function NumberField({ field }: { field: SettingField }) {
    const { register } = useFormContext<SettingsValues>();
    return (
        <div key={field.key} className="space-y-2">
            <div className="flex items-center justify-between">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">{field.label}</label>
                {field.description && (
                    <span className="text-[9px] text-zinc-600">{field.description}</span>
                )}
            </div>
            <input
                type="number"
                step="any"
                {...register(field.key as any)}
                className="w-full h-12 bg-black/60 border border-white/10 rounded-2xl px-5 text-white text-xs font-mono tracking-wider focus:border-violet-500/50 outline-none transition-colors"
            />
        </div>
    );
}

function SelectField({ field }: { field: SettingField }) {
    const { register } = useFormContext<SettingsValues>();
    return (
        <div key={field.key} className="space-y-2">
            <div className="flex items-center justify-between">
                <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">{field.label}</label>
                {field.description && (
                    <span className="text-[9px] text-zinc-600">{field.description}</span>
                )}
            </div>
            <select
                {...register(field.key as any)}
                className="w-full h-12 bg-black/60 border border-white/10 rounded-2xl px-5 text-white text-xs font-mono tracking-wider focus:border-violet-500/50 outline-none transition-colors appearance-none cursor-pointer"
            >
                {(field.options || []).map(opt => (
                    <option key={opt.value} value={opt.value} className="bg-zinc-900 text-white">
                        {opt.label}
                    </option>
                ))}
            </select>
        </div>
    );
}

function ToggleField({ field }: { field: SettingField }) {
    const { setValue, getValues } = useFormContext<SettingsValues>();
    const currentValue = getValues(field.key as any);
    const isEnabled = currentValue === "true" || currentValue === true;

    return (
        <div key={field.key} className="flex items-center justify-between py-2">
            <div className="min-w-0 flex-1">
                <span className="text-xs font-bold text-zinc-300 uppercase tracking-wider block truncate">{field.label}</span>
                {field.description && (
                    <p className="text-[9px] text-zinc-600 mt-0.5">{field.description}</p>
                )}
            </div>
            <button
                type="button"
                onClick={() => setValue(field.key as any, isEnabled ? "false" : "true")}
                className={cn(
                    "relative h-6 w-11 rounded-full transition-colors shrink-0 ml-4",
                    isEnabled ? "bg-violet-500" : "bg-zinc-700"
                )}
            >
                <span
                    className={cn(
                        "block h-5 w-5 rounded-full bg-white shadow-sm transition-transform mt-0.5 ml-0.5",
                        isEnabled ? "translate-x-[22px]" : "translate-x-0"
                    )}
                />
            </button>
        </div>
    );
}

// ─── Settings Section (collapsible) ────────────────────────────────────────

function SettingsSection({ sectionKey, fields, showKey, toggleShow }: {
    sectionKey: string;
    fields: SettingField[];
    showKey: Record<string, boolean>;
    toggleShow: (key: string) => void;
}) {
    const [isOpen, setIsOpen] = useState(true);
    const Icon = getSectionIcon(sectionKey);

    // Count fields for badge
    const count = fields.length;

    return (
        <div className="rounded-2xl border border-white/5 bg-white/[0.02] overflow-hidden">
            <button
                type="button"
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center justify-between px-5 py-4 hover:bg-white/[0.02] transition-colors"
            >
                <div className="flex items-center gap-3">
                    {Icon && <Icon className="h-4 w-4 text-violet-500" />}
                    <span className="text-xs font-bold text-zinc-400 uppercase tracking-widest">
                        {getSectionLabel(sectionKey)}
                    </span>
                    <span className="text-[9px] font-bold text-zinc-600 bg-white/5 px-2 py-0.5 rounded-full">
                        {count}
                    </span>
                </div>
                <ChevronDown
                    className={cn(
                        "h-4 w-4 text-zinc-600 transition-transform duration-200",
                        isOpen && "rotate-180"
                    )}
                />
            </button>
            <AnimatePresence initial={false}>
                {isOpen && (
                    <motion.div
                        key="content"
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2, ease: "easeInOut" }}
                        className="overflow-hidden"
                    >
                        <div className="px-5 pb-5 space-y-4">
                            {fields.map(field => {
                                switch (field.type) {
                                    case "password": return <PasswordField key={field.key} field={field} showKey={showKey} toggleShow={toggleShow} />;
                                    case "text": return <TextField key={field.key} field={field} />;
                                    case "number": return <NumberField key={field.key} field={field} />;
                                    case "select": return <SelectField key={field.key} field={field} />;
                                    case "toggle": return <ToggleField key={field.key} field={field} />;
                                    default: return <TextField key={field.key} field={field} />;
                                }
                            })}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

// ─── Interfaces (unchanged) ─────────────────────────────────────────────────

interface TrialInfo {
    active: boolean;
    ends_at?: string;
    ended_at?: string;
    days_remaining: number;
}

interface SubscriptionData {
    tier: string;
    status: string;
    features: string[];
    stripe_subscription_id?: string;
    trial?: TrialInfo | null;
}

interface TierInfo {
    id: string;
    name: string;
    price_cents: number;
    price_formatted: string;
    features: string[];
    limit_videos: number;
    available: boolean;
    trial_available: boolean;
    trial_days: number;
}

interface TiersResponse {
    tiers: TierInfo[];
    count: number;
}

// ─── Main Page Component ────────────────────────────────────────────────────

export default function SettingsPage() {
    const [activeEngine, setActiveEngine] = useState("security");
    const [_isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [showKey, setShowKey] = useState<Record<string, boolean>>({});
    const [logs, setLogs] = useState<string[]>(["IDENTITY_INITIALIZED", "PROTOCOL_READY"]);
    const [subscription, setSubscription] = useState<SubscriptionData | null>(null);
    const [tiers, setTiers] = useState<TierInfo[]>([]);
    const [subLoading, setSubLoading] = useState(true);
    const [showCancelModal, setShowCancelModal] = useState(false);
    const [isCancelling, setIsCancelling] = useState(false);
    const { agents, logs: _systemLogs, status: _status, pulse: _pulse } = useTelemetry();

    const form = useForm<SettingsValues>({
        resolver: zodResolver(SettingsSchema),
        defaultValues: {},
    });

    const { register, handleSubmit, reset, setValue } = form;

    const fetchData = useCallback(async () => {
        setIsLoading(true);
        const token = await getAuthToken();
        if (!token) return;
        await withRealFallback((signal) => fetch(`${API_BASE}/settings/`, { headers: { Authorization: `Bearer ${token}` }, signal }),
            { fallback: null, onSuccess: (data: any) => reset(data) }
        );
        setIsLoading(false);
    }, [reset]);

    const fetchSubscription = useCallback(async () => {
        setSubLoading(true);
        const token = await getAuthToken();
        if (!token) return;
        await Promise.all([
            withRealFallback<SubscriptionData>(
                (signal) => fetch(`${API_BASE}/billing/subscription`, { headers: { Authorization: `Bearer ${token}` }, signal }),
                { fallback: null as unknown as SubscriptionData, onSuccess: (data) => setSubscription(data) }
            ),
            withRealFallback<TiersResponse>(
                (signal) => fetch(`${API_BASE}/billing/tiers`, { signal }),
                { fallback: { tiers: [], count: 0 }, onSuccess: (data) => setTiers(data.tiers) }
            ),
        ]);
        setSubLoading(false);
    }, []);

    const handleCancelSubscription = async () => {
        setIsCancelling(true);
        const token = await getAuthToken();
        if (!token) {
            setIsCancelling(false);
            return;
        }
        
        setLogs((prev: string[]) => [`[PROTOCOL] Initiating subscription cancellation...`, ...prev]);
        await withRealFallback<any>((signal) => fetch(`${API_BASE}/billing/cancel`, {
                method: "POST",
                headers: { Authorization: `Bearer ${token}` },
                signal
            }),
            {
                fallback: null,
                onSuccess: (data) => {
                    const cancelsAt = data?.data?.cancels_at || data?.cancels_at;
                    const msg = cancelsAt 
                        ? `Subscription will be cancelled at the end of the billing period (${new Date(cancelsAt).toLocaleDateString()})`
                        : "Subscription cancelled successfully";
                    toast.success(msg);
                    setLogs((prev: string[]) => [`[SUCCESS] ${msg}`, ...prev]);
                    setShowCancelModal(false);
                    // Refresh subscription data
                    fetchSubscription();
                },
                onFallback: (err) => {
                    toast.error(`Cancellation failed: ${err?.message || 'Unknown error'}`);
                    setLogs((prev: string[]) => [`[FAILURE] Cancellation failed: ${err?.message || 'Unknown error'}`, ...prev]);
                }
            }
        );
        setIsCancelling(false);
    };

    useEffect(() => {
        fetchData();
        fetchSubscription();
    }, [fetchData, fetchSubscription]);

    const handleSave = handleSubmit(async (data) => {
        setIsSaving(true);
        setLogs((prev: string[]) => [`[PROTOCOL] Committing configuration updates...`, ...prev]);
        const token = await getAuthToken();
        if (!token) return;

        const payload = Object.entries(data).map(([key, value]) => ({
            key,
            value: String(value ?? ""),
            category: SETTING_FIELDS.find(f => f.key === key)?.category || "general"
        }));

        const result = await withRealFallback((signal) => fetch(`${API_BASE}/settings/user`, {
                method: "POST",
                headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
                body: JSON.stringify(payload),
                signal
            }),
            {
                fallback: null,
                errorMessage: "Settings update failed — check connection and try again",
                onSuccess: () => {
                    toast.success("Protocol Updated");
                    setLogs((prev: string[]) => [`[SUCCESS] Configuration synchronized with neural vault.`, ...prev]);
                    reset(data);
                },
                onFallback: (err: any) => {
                    setLogs((prev: string[]) => [`[FAILURE] Sync failed: ${err?.message || 'Unknown error'}`, ...prev]);
                }
            }
        );
        if (!result) {
            setIsSaving(false);
            return;
        }
        setIsSaving(false);
    });

    const toggleShowKey = (key: string) => {
        setShowKey(prev => ({ ...prev, [key]: !prev[key] }));
    };

    // Compute sections for each tab
    const securitySections = getFieldsByTabAndSection("security");
    const infrastructureSections = getFieldsByTabAndSection("infrastructure");
    const operationsSections = getFieldsByTabAndSection("operations");

    return (
        <FormProvider {...form}>
            <CommandCenterLayout
              title="CORE CONFIG"
              subtitle="CENTRAL_COMMAND_V4.0"
              leftPanel={
                <div className="space-y-1">
                  {[
                    { id: "identity", label: "Neural Identity", icon: Fingerprint },
                    { id: "security", label: "Security Hub", icon: Lock },
                    { id: "billing", label: "Subscription", icon: Crown },
                    { id: "infrastructure", label: "Infrastructure", icon: Server },
                    { id: "operations", label: "Operations", icon: Settings },
                    { id: "logs", label: "Session Logs", icon: Terminal },
                  ].map((item) => (
                    <button
                      key={item.id}
                      onClick={() => setActiveEngine(item.id)}
                      className={cn(
                        "w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group",
                        activeEngine === item.id ? "bg-violet-500/10 text-violet-400 border border-violet-500/20" : "text-zinc-500 hover:text-zinc-300 hover:bg-white/5"
                      )}
                    >
                      <item.icon className="h-4 w-4" />
                      <span className="text-xs font-bold uppercase tracking-tight">{item.label}</span>
                      {activeEngine === item.id && <div className="ml-auto h-1.5 w-1.5 rounded-full bg-violet-400 shadow-[0_0_8px_rgba(139,92,246,0.5)]" />}
                    </button>
                  ))}
                </div>
              }
              rightPanel={
                <>
                  <AgentMatrix agents={agents} />
                  <div className="p-6 rounded-2xl border border-white/5 bg-white/5 space-y-4">
                    <h4 className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Aesthetic Mode</h4>
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-zinc-400 font-bold uppercase">Theme Engine</span>
                      <ThemeSwitcher />
                    </div>
                  </div>
                  <Button onClick={handleSave} disabled={isSaving} className="w-full bg-violet-500 hover:bg-violet-400 text-white font-bold h-14 rounded-2xl">
                    {isSaving ? "Synchronizing..." : "Commit Protocol"}
                  </Button>
                </>
              }
            >
              <div className="p-10 space-y-10 relative h-full flex flex-col">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={activeEngine}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    className="flex-1 flex flex-col min-h-0"
                  >
                    <div className="flex-1 overflow-y-auto custom-scrollbar pr-4 space-y-10">
                      {activeEngine === "identity" && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                           <div className="p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-4">
                             <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Administrator Alias</span>
                             <h3 className="text-2xl font-bold text-white uppercase tracking-tight">User_Sovereign</h3>
                           </div>
                           <div className="p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-4">
                             <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Clearance Level</span>
                             <h3 className="text-2xl font-bold text-violet-400 uppercase tracking-tight">Level 5 (Admin)</h3>
                           </div>
                        </div>
                      )}

                      {activeEngine === "security" && (
                        <div className="space-y-4">
                          {Object.entries(securitySections).map(([sectionKey, fields]) => (
                            <SettingsSection
                              key={sectionKey}
                              sectionKey={sectionKey}
                              fields={fields}
                              showKey={showKey}
                              toggleShow={toggleShowKey}
                            />
                          ))}
                        </div>
                      )}

                      {activeEngine === "infrastructure" && (
                        <div className="space-y-4">
                          {Object.entries(infrastructureSections).map(([sectionKey, fields]) => (
                            <SettingsSection
                              key={sectionKey}
                              sectionKey={sectionKey}
                              fields={fields}
                              showKey={showKey}
                              toggleShow={toggleShowKey}
                            />
                          ))}
                        </div>
                      )}

                      {activeEngine === "operations" && (
                        <div className="space-y-4">
                          {Object.entries(operationsSections).map(([sectionKey, fields]) => (
                            <SettingsSection
                              key={sectionKey}
                              sectionKey={sectionKey}
                              fields={fields}
                              showKey={showKey}
                              toggleShow={toggleShowKey}
                            />
                          ))}
                        </div>
                      )}

                      {activeEngine === "billing" && (
                        <div className="space-y-10">
                          <div className="flex items-center gap-4">
                            <h3 className="text-2xl font-bold text-white uppercase tracking-widest">Subscription</h3>
                            {subscription?.trial?.active && (
                              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[10px] font-bold text-emerald-400 uppercase tracking-wider">
                                <Sparkles className="h-3 w-3" />
                                Free Trial
                              </span>
                            )}
                          </div>

                          {subLoading ? (
                            <div className="flex items-center justify-center py-20">
                              <div className="h-8 w-8 border-2 border-violet-500/30 border-t-violet-400 rounded-full animate-spin" />
                            </div>
                          ) : (
                            <>
                              {/* Current Plan Card */}
                              <div className="p-8 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-6">
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-4">
                                    <div className="h-14 w-14 rounded-2xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center">
                                      <Crown className="h-7 w-7 text-violet-400" />
                                    </div>
                                    <div>
                                      <p className="text-xs font-bold text-zinc-500 uppercase tracking-widest">Current Plan</p>
                                      <h4 className="text-2xl font-bold text-white uppercase tracking-tight mt-1">
                                        {tiers.find(t => t.id === subscription?.tier)?.name || (subscription?.tier ?? "Free")}
                                      </h4>
                                    </div>
                                  </div>
                                  {!subLoading && (
                                    <span className={cn(
                                      "px-4 py-2 rounded-full text-[10px] font-bold uppercase tracking-wider border",
                                      subscription?.status === "active" || !subscription?.stripe_subscription_id
                                        ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                                        : "bg-amber-500/10 border-amber-500/20 text-amber-400"
                                    )}>
                                      {subscription?.stripe_subscription_id ? subscription?.status : "Active"}
                                    </span>
                                  )}
                                </div>

                                {subscription?.features && subscription.features.length > 0 && (
                                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                                    {subscription.features.map((feat, i) => (
                                      <div key={i} className="flex items-center gap-3 px-4 py-3 rounded-2xl bg-white/3 border border-white/5">
                                        <Zap className="h-3 w-3 text-violet-500 shrink-0" />
                                        <span className="text-xs text-zinc-300 font-medium">{feat}</span>
                                      </div>
                                    ))}
                                  </div>
                                )}

                                {(() => {
                                  const tierInfo = tiers.find(t => t.id === subscription?.tier);
                                  if (!tierInfo) return null;
                                  return (
                                    <div className="flex items-center justify-between px-4 py-3 rounded-2xl bg-white/3 border border-white/5">
                                      <span className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Daily Video Limit</span>
                                      <span className="text-sm font-bold text-white">{tierInfo.limit_videos}/day</span>
                                    </div>
                                  );
                                })()}
                              </div>

                              {subscription?.trial && (
                                <div className={cn(
                                  "p-8 rounded-[32px] border space-y-6 overflow-hidden relative",
                                  subscription.trial.active
                                    ? "bg-emerald-500/3 border-emerald-500/15"
                                    : "bg-amber-500/3 border-amber-500/15"
                                )}>
                                  {subscription.trial.active && (
                                    <div className="absolute top-0 right-0 w-48 h-48 bg-emerald-500/5 blur-[80px] -mr-24 -mt-24" />
                                  )}
                                  <div className="flex items-center justify-between relative z-10">
                                    <div className="flex items-center gap-4">
                                      <div className={cn(
                                        "h-14 w-14 rounded-2xl border flex items-center justify-center",
                                        subscription.trial.active
                                          ? "bg-emerald-500/10 border-emerald-500/20"
                                          : "bg-amber-500/10 border-amber-500/20"
                                      )}>
                                        {subscription.trial.active
                                          ? <Sparkles className="h-7 w-7 text-emerald-400" />
                                          : <AlertCircle className="h-7 w-7 text-amber-400" />
                                        }
                                      </div>
                                      <div>
                                        <p className="text-xs font-bold text-zinc-500 uppercase tracking-widest">
                                          {subscription.trial.active ? "Trial Period" : "Trial Expired"}
                                        </p>
                                        <h4 className="text-xl font-bold text-white mt-1">
                                          {subscription.trial.active
                                            ? `${subscription.trial.days_remaining} day${subscription.trial.days_remaining !== 1 ? 's' : ''} remaining`
                                            : "Your free trial has ended"}
                                        </h4>
                                      </div>
                                    </div>
                                    {subscription.trial.active && (
                                      <div className="hidden sm:flex items-center gap-2">
                                        <Clock className="h-4 w-4 text-emerald-500" />
                                        <span className="text-xs font-mono text-emerald-500 font-bold">
                                          Ends {new Date(subscription.trial.ends_at!).toLocaleDateString()}
                                        </span>
                                      </div>
                                    )}
                                  </div>

                                  {subscription.trial.active && subscription.trial.days_remaining <= 7 && (
                                    <div className="space-y-2 relative z-10">
                                      <div className="flex items-center justify-between text-[10px] font-bold text-zinc-500 uppercase tracking-wider">
                                        <span>Trial ends soon</span>
                                        <span>{subscription.trial.days_remaining} day{subscription.trial.days_remaining !== 1 ? 's' : ''}</span>
                                      </div>
                                      <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                                        <motion.div
                                          initial={{ width: "0%" }}
                                          animate={{
                                            width: `${Math.min(100, Math.max(5, (subscription.trial.days_remaining / 14) * 100))}%`,
                                          }}
                                          transition={{ duration: 1, ease: "easeOut" }}
                                          className={cn(
                                            "h-full rounded-full",
                                            subscription.trial.days_remaining <= 3
                                              ? "bg-amber-500"
                                              : "bg-emerald-500"
                                          )}
                                        />
                                      </div>
                                    </div>
                                  )}

                                  {subscription?.tier === "free" && (
                                    <div className="relative z-10 pt-2">
                                      <a
                                        href="/credits"
                                        className="inline-flex items-center gap-2 px-8 py-4 bg-violet-500 hover:bg-violet-400 text-white font-bold text-xs uppercase tracking-widest rounded-2xl transition-all hover:gap-4 hover:shadow-[0_0_30px_rgba(139,92,246,0.3)]"
                                      >
                                        <Crown className="h-4 w-4" />
                                        {subscription.trial.active
                                          ? "Upgrade Before Trial Ends"
                                          : "Subscribe Now"}
                                        <ArrowUpRight className="h-4 w-4" />
                                      </a>
                                      <p className="text-[9px] text-zinc-600 mt-3 font-bold uppercase tracking-wider">
                                        {subscription.trial.active
                                          ? "Keep your sovereign features after the trial"
                                          : "Choose a plan to unlock premium features"}
                                      </p>
                                    </div>
                                  )}
                                </div>
                              )}

                              {!subscription?.trial && subscription?.tier === "free" && (
                                <div className="p-8 rounded-[32px] bg-violet-500/3 border border-violet-500/15 space-y-6">
                                  <div className="flex items-center gap-4">
                                    <div className="h-14 w-14 rounded-2xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center">
                                      <Crown className="h-7 w-7 text-violet-400" />
                                    </div>
                                    <div>
                                      <p className="text-xs font-bold text-zinc-500 uppercase tracking-widest">Free Plan</p>
                                      <h4 className="text-xl font-bold text-white mt-1">Upgrade to unlock the full platform</h4>
                                    </div>
                                  </div>
                                  <a
                                    href="/credits"
                                    className="inline-flex items-center gap-2 px-8 py-4 bg-violet-500 hover:bg-violet-400 text-white font-bold text-xs uppercase tracking-widest rounded-2xl transition-all hover:gap-4"
                                  >
                                    <Sparkles className="h-4 w-4" />
                                    View Plans
                                    <ArrowUpRight className="h-4 w-4" />
                                  </a>
                                </div>
                              )}

                              {/* Cancel Subscription Section */}
                              {subscription?.tier && subscription.tier !== "free" && subscription.status === "active" && (
                                <div className="p-8 rounded-[32px] bg-rose-500/3 border border-rose-500/15 space-y-6">
                                  <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-4">
                                      <div className="h-14 w-14 rounded-2xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center">
                                        <Trash2 className="h-7 w-7 text-rose-400" />
                                      </div>
                                      <div>
                                        <p className="text-xs font-bold text-zinc-500 uppercase tracking-widest">Danger Zone</p>
                                        <h4 className="text-xl font-bold text-white mt-1">Cancel Subscription</h4>
                                      </div>
                                    </div>
                                    <Button
                                      onClick={() => setShowCancelModal(true)}
                                      variant="danger"
                                      rounded="xl"
                                      className="h-12 px-8 bg-rose-500/20 border border-rose-500/30 text-rose-400 hover:bg-rose-500/30 text-[10px] font-bold uppercase tracking-widest"
                                    >
                                      Cancel Plan
                                    </Button>
                                  </div>
                                  <p className="text-[10px] text-zinc-500 leading-relaxed">
                                    Your subscription will remain active until the end of the current billing period. 
                                    After cancellation, you'll be downgraded to the Free tier and lose access to premium features.
                                  </p>
                                </div>
                              )}

                              {tiers.length > 0 && (
                                <div className="space-y-6">
                                  <h4 className="text-xs font-bold text-zinc-500 uppercase tracking-widest">Available Plans</h4>
                                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                    {tiers.filter(t => t.available).map((tier) => {
                                      const isCurrent = tier.id === subscription?.tier;
                                      return (
                                        <div
                                          key={tier.id}
                                          className={cn(
                                            "p-6 rounded-2xl border transition-all relative overflow-hidden group",
                                            isCurrent
                                              ? "bg-violet-500/5 border-violet-500/20"
                                              : "bg-white/3 border-white/5 hover:border-white/20 hover:bg-white/5"
                                          )}
                                        >
                                          {tier.trial_available && !isCurrent && subscription?.tier === "free" && !subscription?.trial && (
                                            <span className="absolute top-3 right-3 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[8px] font-bold text-emerald-400 uppercase">
                                              Trial available
                                            </span>
                                          )}
                                          <div className="space-y-4">
                                            <h5 className="text-sm font-bold text-white uppercase tracking-wider">{tier.name}</h5>
                                            <p className="text-2xl font-bold text-white">
                                              {tier.price_cents > 0 ? tier.price_formatted : "Free"}
                                              {tier.price_cents > 0 && (
                                                <span className="text-xs font-medium text-zinc-500 ml-1">/mo</span>
                                              )}
                                            </p>
                                            <div className="space-y-2">
                                              {tier.features.map((feat, i) => (
                                                <div key={i} className="flex items-center gap-2">
                                                  <Zap className="h-2.5 w-2.5 text-violet-500 shrink-0" />
                                                  <span className="text-[10px] text-zinc-400">{feat}</span>
                                                </div>
                                              ))}
                                            </div>
                                            <p className="text-[9px] text-zinc-600 font-bold uppercase tracking-wider">
                                              {tier.limit_videos} video{tier.limit_videos !== 1 ? 's' : ''}/day
                                            </p>
                                          </div>
                                        </div>
                                      );
                                    })}
                                  </div>
                                </div>
                              )}
                            </>
                          )}
                        </div>
                      )}
                    </div>

                    <div className="mt-8 flex-1 min-h-0 flex flex-col bg-[#0F0F11]/40 rounded-[32px] border border-white/5 overflow-hidden shrink-0">
                      <div className="p-4 border-b border-white/5 flex items-center justify-between">
                        <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">Session Logs</span>
                        <span className="text-[8px] font-mono text-violet-500/50">IDENTITY_HUB_ACTIVE</span>
                      </div>
                      <div className="flex-1 overflow-y-auto custom-scrollbar p-6 font-mono text-[10px] space-y-1">
                        {logs.map((log, i) => (
                          <div key={i} className="flex gap-4">
                            <span className="text-zinc-800">[{new Date().toLocaleTimeString()}]</span>
                            <span className={cn(
                              log.includes("[PROTOCOL]") ? "text-cyan-400" :
                              log.includes("[SUCCESS]") ? "text-emerald-500" : "text-zinc-600"
                            )}>{log}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </motion.div>
                </AnimatePresence>
              </div>

              {/* Cancel Subscription Confirmation Modal */}
              <ConfirmModal
                isOpen={showCancelModal}
                onClose={() => setShowCancelModal(false)}
                onConfirm={handleCancelSubscription}
                title="Cancel Subscription?"
                description="Your subscription will remain active until the end of the current billing period. After that, your account will be downgraded to the Free tier. This action cannot be undone."
                confirmText="Confirm Cancellation"
                cancelText="Keep Subscription"
                variant="danger"
                isLoading={isCancelling}
              />
            </CommandCenterLayout>
        </FormProvider>
    );
}
