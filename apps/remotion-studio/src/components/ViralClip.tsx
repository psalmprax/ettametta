import React from 'react';
import { AbsoluteFill, Video, Audio, interpolate, useCurrentFrame, useVideoConfig, Sequence, staticFile } from 'remotion';
import { z } from 'zod';
import { CTAOverlay } from './CTAOverlay';
import { CinematicOverlay } from './CinematicOverlay';
import { NewsTicker } from './NewsTicker';
import { VFXShader } from './VFXShader';
import { WordCaptions } from './WordCaptions';
import { ColorGrade, GradeType } from './ColorGrade';
import { KenBurns } from './KenBurns';
import { ProgressTracker } from './ProgressTracker';
import { ChapterOverlay } from './ChapterOverlay';
import { SceneTransition, TransitionType } from './SceneTransition';
import { viralClipSchema } from '../schema';
import { IntroScene } from './scenes/IntroScene';
import { RedditScene } from './scenes/RedditScene';
import { NewsScene } from './scenes/NewsScene';
import { InvestigationOverlay } from './overlays/InvestigationOverlay';
import { RetroOverlay } from './overlays/RetroOverlay';
import { PodcastOverlay } from './overlays/PodcastOverlay';

type ViralClipProps = z.infer<typeof viralClipSchema>;

const INTRO_STYLE_MAP: Record<string, string> = {
    'CINEMATIC_DOC': 'portal',
    'DEEP_DIVE': 'astrolabe',
    'NOIR_MYSTERY': 'astrolabe',
    'INVESTIGATION': 'astrolabe',
    'FAST_HYPE': 'cyberpunk',
    'ESPORTS_HYPE': 'cyberpunk',
    'GAMING_LORE': 'cyberpunk',
    'FITNESS_MOTIVATION': 'cyberpunk',
    'REDDIT_STORY': 'cyberpunk',
    'MOTIVATIONAL': 'particle_reveal',
    'STOIC_WISDOM': 'particle_reveal',
    'HEARTFELT_NARRATIVE': 'particle_reveal',
    'RELATIONSHIP_DRAMA': 'particle_reveal',
    'TECH': 'portal',
    'TRAVEL_VLOG': 'particle_reveal',
    'PERSONA_MONTAGE': 'brand_reveal',
    'TOP_LISTICLE': 'cyberpunk',
    'PRODUCT_SHOWCASE': 'brand_reveal',
    'SCIENCE': 'portal',
    'HISTORY': 'astrolabe',
    'SPIRITUALITY': 'astrolabe',
};

const resolvePath = (url?: string) => {
    if (!url) return undefined;
    if (url.startsWith('http')) return url;
    let cleanUrl = url;
    if (cleanUrl.startsWith('./')) cleanUrl = cleanUrl.substring(2);
    if (cleanUrl.startsWith('/')) cleanUrl = cleanUrl.substring(1);
    return staticFile(cleanUrl);
};

const COLOR_GRADE_MAP: Record<string, GradeType> = {
    'HEARTFELT_NARRATIVE': 'warm_narrative',
    'TOP_LISTICLE': 'electric_listicle',
    'NOIR_MYSTERY': 'dark_mystery',
    'HORROR_CREEPY': 'dark_mystery',
    'CINEMATIC_DOC': 'default',
    'RETRO_ARCHIVE': 'retro_vhs',
    'CULINARY_MASTERCLASS': 'vibrant_bloom',
    'TRAVEL_VLOG': 'vibrant_bloom',
    'RELATIONSHIP_DRAMA': 'melancholic',
    'STOIC_WISDOM': 'monochrome_high_contrast',
    'MOTIVATIONAL': 'gold_luxury',
    'FAST_HYPE': 'neon_hype',
    'ESPORTS_HYPE': 'neon_hype',
};

const TRANSITION_MAP: Record<string, TransitionType[]> = {
    'CINEMATIC_DOC': ['blur', 'zoom', 'fade'],
    'DEEP_DIVE': ['blur', 'zoom', 'fade'],
    'STOIC_WISDOM': ['blur', 'zoom', 'fade'],
    'TOP_LISTICLE': ['slide'],
    'FAST_HYPE': ['slide'],
    'ESPORTS_HYPE': ['slide'],
    'NOIR_MYSTERY': ['blur', 'fade'],
    'HORROR_CREEPY': ['blur', 'fade'],
    'INVESTIGATION': ['blur', 'fade'],
    'HEARTFELT_NARRATIVE': ['fade', 'blur'],
    'RELATIONSHIP_DRAMA': ['fade', 'blur'],
    'LOFI_CHILL': ['fade', 'blur'],
    'PRODUCT_SHOWCASE': ['zoom', 'fade'],
    'CULINARY_MASTERCLASS': ['zoom', 'fade'],
    'RETRO_ARCHIVE': ['fade', 'slide'],
};

const SPEED_PATTERN = [1.0, 0.85, -1.0, 1.12];

export const ViralClip: React.FC<ViralClipProps> = ({
    title, subtitle, video_url, audio_url, clips, words,
    show_cta_overlay, cta_type, cta_text,
    trademark_url, brand_name, primary_color,
    vignette_intensity, grain_opacity,
    style, intro_style, job_metadata
}) => {
    const effectiveIntroStyle = intro_style || (style ? INTRO_STYLE_MAP[style] : undefined) || 'brand_reveal';
    const frame = useCurrentFrame();
    const { fps, durationInFrames } = useVideoConfig();

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

    const bpm = isListicle ? 128 : (isEsports ? 140 : (isFastHype ? 130 : (isFitness ? 135 : (isHeartfelt ? 75 : (isLofi ? 85 : (isStoic ? 80 : 100))))));
    const safeFps = fps || 30;
    const framesPerBeat = (60 / bpm) * safeFps;
    const beatProgress = framesPerBeat > 0 ? (frame % framesPerBeat) / framesPerBeat : 0;
    const beatScale = isNaN(beatProgress) ? 1 : interpolate(beatProgress, [0, 0.1, 0.4], [1, 1.02, 1], { extrapolateRight: 'clamp' });

    const colorGrade: GradeType = (style && COLOR_GRADE_MAP[style]) || 'default';

    const resolvedVideoUrl = resolvePath(video_url);
    const resolvedClips = clips?.map(c => ({...c, url: resolvePath(c.url) || ''}));
    const resolvedAudioUrl = resolvePath(audio_url);
    const resolvedTrademarkUrl = resolvePath(trademark_url);

    const totalClipDuration = resolvedClips?.reduce((acc, c) => acc + c.duration_in_frames, 0) || 0;
    const effectiveDuration = durationInFrames;

    const loopingClips = resolvedClips ? (() => {
        const out: Array<{ url: string; duration_in_frames: number; _playbackRate?: number }> = [];
        let covered = 0;
        let repetition = 0;
        while (covered < durationInFrames && resolvedClips.length > 0) {
            for (const clip of resolvedClips) {
                if (covered >= durationInFrames) break;
                const speed = SPEED_PATTERN[repetition % SPEED_PATTERN.length];
                const absSpeed = Math.abs(speed);
                const effDuration = absSpeed > 0.001
                    ? Math.round(clip.duration_in_frames / absSpeed)
                    : clip.duration_in_frames;
                out.push({ ...clip, duration_in_frames: effDuration, _playbackRate: speed });
                covered += effDuration;
            }
            repetition++;
        }
        return out;
    })() : [];

    const getTransitionType = (index: number): TransitionType => {
        if (style && TRANSITION_MAP[style]) {
            const types = TRANSITION_MAP[style];
            return types[index % types.length];
        }
        const types: TransitionType[] = ['zoom', 'blur', 'slide'];
        return types[index % types.length];
    };

    return (
        <AbsoluteFill style={{
            backgroundColor: 'black',
            fontFamily: 'Inter, system-ui, sans-serif',
            transform: `scale(${beatScale})`
        }}>
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

            <Sequence from={0} durationInFrames={fps * 4}>
                <IntroScene
                    type={effectiveIntroStyle}
                    title={title}
                    subtitle={subtitle}
                    brandName={brand_name}
                    primaryColor={primary_color}
                    logoUrl={resolvedTrademarkUrl}
                />
            </Sequence>

            {loopingClips && loopingClips.length > 0 ? (
                loopingClips.reduce((acc, clip, index) => {
                    const startFrame = acc.totalFrames;
                    acc.totalFrames += clip.duration_in_frames;

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
                                         <Video src={clip.url} playbackRate={((clip as Record<string, unknown>)._playbackRate as number) ?? 1} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
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

            {resolvedAudioUrl && <Audio src={resolvedAudioUrl} />}

            {(() => {
                const sfxClips = loopingClips || [];
                return sfxClips.map((_, index) => {
                    const startFrame = sfxClips.slice(0, index).reduce((acc, c) => acc + c.duration_in_frames, 0);
                    if (startFrame >= durationInFrames) return null;
                    return (
                        <React.Fragment key={`sfx-${index}`}>
                            {index > 0 && <Sequence from={startFrame - 5} durationInFrames={15}><Audio src={staticFile('sfx/whoosh.mp3')} volume={0.4} /></Sequence>}
                            {isListicle && <Sequence from={startFrame} durationInFrames={20}><Audio src={staticFile('sfx/impact.mp3')} volume={0.3} /></Sequence>}
                        </React.Fragment>
                    );
                });
            })()}

            {!isReddit && <ProgressTracker primaryColor={primary_color} />}
            <ChapterOverlay title={isListicle ? "Top 5 Rankings" : title} primaryColor={primary_color} />

            {words && words.length > 0 && (
                <WordCaptions words={words} primaryColor={primary_color} style={style} />
            )}

            {isNews && <NewsScene headline={title} />}

            {isReddit && <RedditScene redditData={job_metadata?.reddit_data} />}

            {isInvestigation && <InvestigationOverlay title={title} />}

            {isRetro && <RetroOverlay />}

            {isPodcast && <PodcastOverlay />}

            {show_cta_overlay && frame > effectiveDuration - (fps * 3.5) && (
                <Sequence from={effectiveDuration - (fps * 3.5)} durationInFrames={fps * 3.5}>
                    <CTAOverlay type={cta_type || 'engagement'} text={cta_text || ''} />
                </Sequence>
            )}
        </AbsoluteFill>
    );
};
