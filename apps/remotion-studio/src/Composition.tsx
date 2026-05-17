import React from 'react';
import { AbsoluteFill, Video, Audio, interpolate, useCurrentFrame, useVideoConfig, Sequence, staticFile } from 'remotion';
import { z } from 'zod';
import { CTAOverlay } from './components/CTAOverlay';
import { CinematicOverlay } from './components/CinematicOverlay';
import { RedditHook } from './components/RedditHook';
import { NewsTicker } from './components/NewsTicker';
import { VFXShader } from './components/VFXShader';
import { WordCaptions } from './components/WordCaptions';
import { ColorGrade, GradeType } from './components/ColorGrade';
import { KenBurns } from './components/KenBurns';
import { ProgressTracker } from './components/ProgressTracker';
import { ChapterOverlay } from './components/ChapterOverlay';
import { SceneTransition, TransitionType } from './components/SceneTransition';
import { BrandReveal } from './components/BrandReveal';

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
    job_metadata: z.record(z.string(), z.any()).optional()
});

export const ViralClip: React.FC<z.infer<typeof viralClipSchema>> = ({ 
    title, video_url, audio_url, clips, words,
    show_cta_overlay, cta_type, cta_text,
    trademark_url, brand_name, primary_color, 
    vignette_intensity, grain_opacity,
    style, job_metadata
}) => {
    const frame = useCurrentFrame();
    const { fps, durationInFrames } = useVideoConfig();

    const isReddit = style === 'REDDIT_STORY';
    const isNews = style === 'BROADCAST_NEWS';
    const isTutorial = style === 'ULTIMATE_TUTORIAL';
    const isHeartfelt = style === 'HEARTFELT_NARRATIVE';
    const isListicle = style === 'TOP_LISTICLE';
    const isCinematic = style === 'CINEMATIC_DOC';
    
    // --- 1. Beat-Sync Logic (Rhythmic Pulse) ---
    const bpm = isListicle ? 128 : (isHeartfelt ? 75 : 100);
    const safeFps = fps || 30;
    const framesPerBeat = (60 / bpm) * safeFps;
    const beatProgress = framesPerBeat > 0 ? (frame % framesPerBeat) / framesPerBeat : 0;
    
    // Impact scale on every beat
    const beatScale = isNaN(beatProgress) ? 1 : interpolate(beatProgress, [0, 0.1, 0.4], [1, 1.02, 1], { extrapolateRight: 'clamp' });
    
    // --- 2. Color Grade Resolution ---
    const colorGrade: GradeType = isHeartfelt ? 'warm_narrative' : (isListicle ? 'electric_listicle' : 'default');

    // Path resolution
    const resolvePath = (url?: string) => {
        if (!url) return undefined;
        if (url.startsWith('http')) return url;
        let cleanUrl = url;
        if (cleanUrl.startsWith('./')) cleanUrl = cleanUrl.substring(2);
        if (cleanUrl.startsWith('/')) cleanUrl = cleanUrl.substring(1);
        return staticFile(cleanUrl);
    };

    const resolvedVideoUrl = resolvePath(video_url);
    const resolvedClips = clips?.map(c => ({...c, url: resolvePath(c.url) || ''}));
    const resolvedAudioUrl = resolvePath(audio_url);
    const resolvedTrademarkUrl = resolvePath(trademark_url);

    // Calculate actual video length from clips
    const totalClipDuration = resolvedClips?.reduce((acc, c) => acc + c.duration_in_frames, 0) || 0;
    const effectiveDuration = totalClipDuration > 0 ? totalClipDuration : durationInFrames;

    // Transition Logic Table
    const getTransitionType = (index: number) => {
        if (isCinematic) {
            const cinemaTypes: TransitionType[] = ['blur', 'zoom', 'fade'];
            return cinemaTypes[index % cinemaTypes.length];
        }
        if (isListicle) return 'slide';
        const types: TransitionType[] = ['zoom', 'blur', 'slide'];
        return types[index % types.length];
    };

    return (
        <AbsoluteFill style={{ 
            backgroundColor: 'black', 
            fontFamily: 'Inter, system-ui, sans-serif',
            transform: `scale(${beatScale})` // Global beat pulse
        }}>
            {/* --- FEATURE: Shader-based Color Grading --- */}
            <ColorGrade type={colorGrade} intensity={0.8} />
            <VFXShader type={(job_metadata?.vfx as string) || 'default'} />

            {!isReddit && !isNews && (
                <CinematicOverlay 
                    vignetteIntensity={vignette_intensity ?? 0.6} 
                    grainOpacity={grain_opacity ?? 0.08}
                    showLetterbox={isCinematic}
                    chromaticAberration={isCinematic ? 4 : 2}
                />
            )}

            {/* --- FEATURE: Brand Reveal Hook (First 2 Seconds) --- */}
            <Sequence from={0} durationInFrames={fps * 2.5}>
                <BrandReveal 
                    brandName={brand_name} 
                    logoUrl={resolvedTrademarkUrl} 
                    primaryColor={primary_color} 
                />
            </Sequence>

            {/* --- FEATURE: Ken Burns Background Engine with SceneTransitions --- */}
            {resolvedClips && resolvedClips.length > 0 ? (
                resolvedClips.reduce((acc, clip, index) => {
                    const startFrame = acc.totalFrames;
                    acc.totalFrames += clip.duration_in_frames;
                    
                    const isActive = frame >= startFrame && frame < startFrame + clip.duration_in_frames;

                    if (isActive) {
                        acc.elements.push(
                            <Sequence key={index} from={startFrame} durationInFrames={clip.duration_in_frames}>
                                <SceneTransition 
                                    type={getTransitionType(index)} 
                                    durationInFrames={clip.duration_in_frames}
                                >
                                    <KenBurns durationInFrames={clip.duration_in_frames} index={index}>
                                         <Video src={clip.url} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                                    </KenBurns>
                                </SceneTransition>
                            </Sequence>
                        );
                    }
                    return acc;
                }, { elements: [] as React.JSX.Element[], totalFrames: 0 }).elements
            ) : resolvedVideoUrl ? (
                <Video src={resolvedVideoUrl} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            ) : null}

            {/* --- AUDIO LAYERS --- */}
            {resolvedAudioUrl && <Audio src={resolvedAudioUrl} />}

            {/* --- FEATURE: Automated SFX Sync --- */}
            {(() => {
                const clips = resolvedClips || [];
                return clips.map((_, index) => {
                    const startFrame = clips.slice(0, index).reduce((acc, c) => acc + c.duration_in_frames, 0);
                    return (
                        <React.Fragment key={`sfx-${index}`}>
                            {index > 0 && <Sequence from={startFrame - 5} durationInFrames={15}><Audio src={staticFile('sfx/whoosh.mp3')} volume={0.4} /></Sequence>}
                            {isListicle && <Sequence from={startFrame} durationInFrames={20}><Audio src={staticFile('sfx/impact.mp3')} volume={0.3} /></Sequence>}
                        </React.Fragment>
                    );
                });
            })()}

            {/* --- FEATURE: Chapter & Progress Overlays --- */}
            {!isReddit && <ProgressTracker primaryColor={primary_color} />}
            <ChapterOverlay title={isListicle ? "Top 5 Rankings" : title} primaryColor={primary_color} />

            {/* --- FEATURE: Kinetic Captions --- */}
            {words && words.length > 0 && (
                <WordCaptions words={words} primaryColor={primary_color} style={style} />
            )}

            {/* --- FEATURE: News Ticker for BROADCAST_NEWS style --- */}
            {isNews && (
                <NewsTicker 
                    headline={title || 'Breaking News'} 
                    breaking={true}
                />
            )}

            {/* Style-Specific Components */}
            {isReddit && job_metadata?.reddit_data && (
                <Sequence from={0} durationInFrames={fps * 3}>
                    <RedditHook {...(job_metadata.reddit_data as any)} />
                </Sequence>
            )}

            {/* --- FEATURE: High-Fidelity Outro --- */}
            {show_cta_overlay && frame > effectiveDuration - (fps * 3.5) && (
                <Sequence from={effectiveDuration - (fps * 3.5)} durationInFrames={fps * 3.5}>
                    <CTAOverlay type={cta_type || 'engagement'} text={cta_text || ''} />
                </Sequence>
            )}
        </AbsoluteFill>
    );
};
