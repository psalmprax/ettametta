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

    // Style detection
    const isReddit = style === 'REDDIT_STORY';
    const isNews = style === 'BROADCAST_NEWS';
    const isTutorial = style === 'ULTIMATE_TUTORIAL';
    const isHeartfelt = style === 'HEARTFELT_NARRATIVE';
    const isListicle = style === 'TOP_LISTICLE';
    const isCinematic = style === 'CINEMATIC_DOC';
    const isVox = style === 'VOX_EXPLAINER';
    const isDeepDive = style === 'DEEP_DIVE';
    const isPersona = style === 'PERSONA_MONTAGE';
    const isFastHype = style === 'FAST_HYPE';
    const isNoir = style === 'NOIR_MYSTERY';
    const isInvestigation = style === 'INVESTIGATION';
    const isRetro = style === 'RETRO_ARCHIVE';
    const isMotivational = style === 'MOTIVATIONAL';
    const isProduct = style === 'PRODUCT_SHOWCASE';
    const isReaction = style === 'REACTION_COMMENTARY';
    const isHorror = style === 'HORROR_CREEPY';
    const isLofi = style === 'LOFI_CHILL';
    const isPodcast = style === 'PODCAST_SIM';
    const isCulinary = style === 'CULINARY_MASTERCLASS';
    const isStoic = style === 'STOIC_WISDOM';
    const isRelationship = style === 'RELATIONSHIP_DRAMA';
    const isTravel = style === 'TRAVEL_VLOG';
    const isFitness = style === 'FITNESS_MOTIVATION';
    const isGaming = style === 'GAMING_LORE';
    const isEsports = style === 'ESPORTS_HYPE';

    // --- 1. Beat-Sync Logic (Rhythmic Pulse) ---
    const bpm = isListicle ? 128 : (isEsports ? 140 : (isFastHype ? 130 : (isFitness ? 135 : (isHeartfelt ? 75 : (isLofi ? 85 : (isStoic ? 80 : 100))))));
    const safeFps = fps || 30;
    const framesPerBeat = (60 / bpm) * safeFps;
    const beatProgress = framesPerBeat > 0 ? (frame % framesPerBeat) / framesPerBeat : 0;

    // Impact scale on every beat
    const beatScale = isNaN(beatProgress) ? 1 : interpolate(beatProgress, [0, 0.1, 0.4], [1, 1.02, 1], { extrapolateRight: 'clamp' });

    // --- 2. Color Grade Resolution ---
    const colorGrade: GradeType =
        isHeartfelt ? 'warm_narrative' :
        isListicle ? 'electric_listicle' :
        isNoir || isHorror ? 'dark_mystery' :
        isCinematic ? 'default' :
        isRetro ? 'retro_vhs' :
        isCulinary || isTravel ? 'vibrant_bloom' :
        isRelationship ? 'melancholic' :
        isStoic ? 'monochrome_high_contrast' :
        isMotivational ? 'gold_luxury' :
        isFastHype || isEsports ? 'neon_hype' :
        'default';

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

    // Calculate actual video length from clips — loop clips if they don't cover full duration
    const totalClipDuration = resolvedClips?.reduce((acc, c) => acc + c.duration_in_frames, 0) || 0;
    const effectiveDuration = durationInFrames; // Always use the full video duration

    // Build a looping clip list that covers the full video duration
    const loopingClips: typeof resolvedClips = resolvedClips ? (() => {
        const out: typeof resolvedClips = [];
        let covered = 0;
        while (covered < durationInFrames && resolvedClips.length > 0) {
            for (const clip of resolvedClips) {
                if (covered >= durationInFrames) break;
                out.push(clip);
                covered += clip.duration_in_frames;
            }
        }
        return out;
    })() : [];

    // Transition Logic Table
    const getTransitionType = (index: number): TransitionType => {
        if (isCinematic || isDeepDive || isStoic) {
            const cinemaTypes: TransitionType[] = ['blur', 'zoom', 'fade'];
            return cinemaTypes[index % cinemaTypes.length];
        }
        if (isListicle || isFastHype || isEsports) return 'slide';
        if (isNoir || isHorror || isInvestigation) {
            const darkTypes: TransitionType[] = ['blur', 'fade'];
            return darkTypes[index % darkTypes.length];
        }
        if (isHeartfelt || isRelationship || isLofi) {
            const softTypes: TransitionType[] = ['fade', 'blur'];
            return softTypes[index % softTypes.length];
        }
        if (isProduct || isCulinary) {
            const cleanTypes: TransitionType[] = ['zoom', 'fade'];
            return cleanTypes[index % cleanTypes.length];
        }
        if (isRetro) {
            const retroTypes: TransitionType[] = ['fade', 'slide'];
            return retroTypes[index % retroTypes.length];
        }
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
                    vignetteIntensity={isNoir || isHorror ? 0.8 : (isCinematic ? 0.7 : 0.6)}
                    grainOpacity={isNoir || isRetro ? 0.15 : (isCinematic ? 0.1 : 0.08)}
                    showLetterbox={isCinematic || isDeepDive || isStoic || isNoir}
                    chromaticAberration={isCinematic ? 4 : (isNoir ? 3 : 2)}
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
            {loopingClips && loopingClips.length > 0 ? (
                loopingClips.reduce((acc, clip, index) => {
                    const startFrame = acc.totalFrames;
                    acc.totalFrames += clip.duration_in_frames;

                    // Stop accumulating once we've covered the full video
                    if (startFrame >= durationInFrames) return acc;

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
                const clips = loopingClips || [];
                return clips.map((_, index) => {
                    const startFrame = clips.slice(0, index).reduce((acc, c) => acc + c.duration_in_frames, 0);
                    if (startFrame >= durationInFrames) return null;
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

            {/* Investigation: magnifier overlay */}
            {isInvestigation && (
                <div style={{
                    position: 'absolute', top: '10px', left: '10px',
                    padding: '6px 12px', backgroundColor: 'rgba(0,255,0,0.15)',
                    border: '1px solid rgba(0,255,0,0.4)', borderRadius: '4px',
                    color: '#0f0', fontSize: '14px', fontFamily: 'monospace',
                    zIndex: 50
                }}>
                    INVESTIGATION: {title || 'CLASSIFIED'}
                </div>
            )}

            {/* Retro: timestamp overlay */}
            {isRetro && (
                <div style={{
                    position: 'absolute', bottom: '60px', right: '20px',
                    padding: '4px 8px', backgroundColor: 'rgba(0,0,0,0.5)',
                    color: '#0f0', fontSize: '16px', fontFamily: 'monospace',
                    zIndex: 50
                }}>
                    REC {new Date().toLocaleDateString()}
                </div>
            )}

            {/* Podcast: show mic icon */}
            {isPodcast && (
                <div style={{
                    position: 'absolute', top: '20px', right: '20px',
                    padding: '8px 16px', backgroundColor: 'rgba(0,0,0,0.6)',
                    borderRadius: '20px', color: 'white', fontSize: '14px',
                    zIndex: 50
                }}>
                    PODCAST
                </div>
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
