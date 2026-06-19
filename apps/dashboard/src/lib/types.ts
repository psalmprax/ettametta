/**
 * Shared TypeScript interfaces for Ettametta API
 * These mirror the backend Pydantic models for type safety.
 */

export interface User {
    id: string;
    username: string;
    email: string;
    role: 'admin' | 'super_admin' | 'user';
    subscription: 'free' | 'basic' | 'premium' | 'sovereign' | 'studio';
    telegram_chat_id?: string;
    telegram_token?: string;
    whatsapp_number?: string;
}

export interface ScriptSegment {
    type: string;
    text: string;
    visual_cue: string;
    visual_style?: string;
    tone?: string;
    pattern_interrupt?: string;
    duration: number;
}

export interface ScriptOutput {
    title: string;
    emotional_arc?: string;
    segments: ScriptSegment[];
    hashtags: string[];
}

interface HookAnalysis {
    status: 'VALID' | 'KILL' | string;
    score: number;
    analysis: string;
    alternatives?: string[];
}

export interface BlueprintNode {
    id: string;
    type: 'ingress' | 'cognition' | 'synthesis' | 'egress';
    label: string;
    desc: string;
}

export interface Blueprint {
    id: string;
    name: string;
    description: string;
    composition_id: string;
    nodes: BlueprintNode[];
}

interface NexusComposeRequest {
    niche: string;
    topic?: string;
    style?: string;
    cta_text?: string | null;
    cta_type?: string;
    cta_template?: string | null;
    visual_paths?: string[];
    voiceover_paths?: string[];
    music_path?: string | null;
    script_segments?: any[] | null;
    generate_thumbnail?: boolean;
    cinema_mode?: boolean;
    blueprint_id?: string;
    job_metadata?: Record<string, any> | null;
}

export interface NexusJob {
    id: string;
    niche: string;
    status: string;
    progress: number;
    output_path?: string;
    error_log?: string;
    created_at: string;
    user_id: string;
    job_metadata?: Record<string, any>;
    node_status?: Record<string, string>;
    blueprint_id?: string;
    current_node?: string;
}

interface CreditBalance {
    balance: number;
    user_id: string;
}

interface ProcessingStep {
    id: string;
    label: string;
    description: string;
    status: 'pending' | 'processing' | 'complete' | 'error';
    progress?: number;
}

interface StockVideo {
    preview: string;
    url?: string;
    id?: string;
    duration?: number;
}

export interface Persona {
    id?: string;
    _id?: string;
    name: string;
    reference_image_uri: string;
}
