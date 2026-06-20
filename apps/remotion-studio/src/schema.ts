import { z } from 'zod';

export const viralClipSchema = z.object({
    title: z.string(),
    subtitle: z.string().optional(),
    video_url: z.string().optional(),
    audio_url: z.string().optional(),
    show_cta_overlay: z.boolean().optional(),
    cta_type: z.enum(['engagement', 'cta']).optional(),
    cta_text: z.string().optional(),
    video_duration_frames: z.number().optional(),
    timeline: z.array(z.object({
        text: z.string(),
        role: z.string(),
        start: z.number(),
        duration: z.number(),
        style: z.string().optional()
    })).optional(),
    words: z.array(z.object({
        word: z.string(),
        start: z.number(),
        end: z.number(),
        confidence: z.number().optional()
    })).optional(),
    clips: z.array(z.object({
        url: z.string(),
        duration_in_frames: z.number(),
    })).optional(),
    trademark_url: z.string().optional(),
    brand_name: z.string().optional(),
    primary_color: z.string().optional(),
    vignette_intensity: z.number().optional(),
    grain_opacity: z.number().optional(),
    style: z.string().optional(),
    intro_style: z.enum(['brand_reveal', 'cyberpunk', 'iridescent', 'portal', 'astrolabe', 'liquid_metal']).optional(),
    job_metadata: z.record(z.string(), z.any()).optional()
});
