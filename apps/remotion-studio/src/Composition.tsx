import { AbsoluteFill, Video, Audio, interpolate, useCurrentFrame, useVideoConfig, Sequence, spring, staticFile } from 'remotion';
import { z } from 'zod';
import { CTAOverlay } from './components/CTAOverlay';

export const viralClipSchema = z.object({
    title: z.string(),
    subtitle: z.string().optional(),
    videoUrl: z.string().optional(),
    audioUrl: z.string().optional(),
    showCtaOverlay: z.boolean().optional(),
    ctaType: z.enum(['engagement', 'cta']).optional(),
    ctaText: z.string().optional(),
    timeline: z.array(z.object({
        text: z.string(),
        role: z.string(),
        start: z.number(),
        duration: z.number(),
        style: z.string().optional()
    })).optional(),
    clips: z.array(z.object({
        url: z.string(),
        durationInFrames: z.number(),
    })).optional(),
    trademarkUrl: z.string().optional(),
    brandName: z.string().optional(),
    primaryColor: z.string().optional(),
});

export const ViralClip: React.FC<z.infer<typeof viralClipSchema>> = ({ 
    title, subtitle, videoUrl, audioUrl, clips, timeline, 
    showCtaOverlay, ctaType, ctaText,
    trademarkUrl, brandName, primaryColor 
}) => {
    const frame = useCurrentFrame();
    const { fps, durationInFrames } = useVideoConfig();

    const titleOpacity = interpolate(frame, [0, 20], [0, 1], {
        extrapolateRight: 'clamp',
    });

    const introOpacity = interpolate(frame, [0, 15, 45, 60], [0, 1, 1, 0], {
        extrapolateRight: 'clamp',
    });

    const introScale = spring({
        frame,
        fps,
        config: { damping: 12 }
    });

    // Show CTA in the last 2 seconds
    const showCtaNow = showCtaOverlay && frame > durationInFrames - (fps * 2);

    // Normalize video URL for local loading (Hardened symlink support)
    const resolvePath = (url?: string) => {
        if (!url) return undefined;
        if (url.startsWith('http')) return url;
        if (url.startsWith('./assets/') || url.startsWith('assets/')) {
            return staticFile(url.replace('./', ''));
        }
        return url;
    };

    const resolvedVideoUrl = resolvePath(videoUrl);
    const resolvedClips = clips?.map(c => ({...c, url: resolvePath(c.url) || ''}));
    const resolvedAudioUrl = resolvePath(audioUrl);
    const resolvedLogoUrl = resolvePath(trademarkUrl);

    return (
        <AbsoluteFill style={{ backgroundColor: 'black' }}>
            {/* 1. Background Visuals */}
            {resolvedClips ? (
                resolvedClips.reduce((acc, clip, index) => {
                    const startFrame = acc.totalFrames;
                    acc.totalFrames += clip.durationInFrames;
                    acc.elements.push(
                        <Sequence key={index} from={startFrame} durationInFrames={clip.durationInFrames}>
                            <Video src={clip.url} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                        </Sequence>
                    );
                    return acc;
                }, { elements: [] as JSX.Element[], totalFrames: 0 }).elements
            ) : (
                resolvedVideoUrl && <Video src={resolvedVideoUrl} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            )}

            {/* 2. Audio Track */}
            {resolvedAudioUrl && <Audio src={resolvedAudioUrl} />}

            {/* 3. Trademark Overlay (Intro Sting & Watermark) */}
            {resolvedLogoUrl && (
                <AbsoluteFill>
                    {/* Intro Sting (0-2s) */}
                    <Sequence from={0} durationInFrames={fps * 2}>
                        <AbsoluteFill style={{ 
                            justifyContent: 'center', 
                            alignItems: 'center', 
                            opacity: introOpacity,
                            transform: `scale(${introScale})`
                        }}>
                            <div style={{ 
                                backgroundColor: 'rgba(0,0,0,0.8)', 
                                padding: '40px', 
                                borderRadius: '30px',
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                border: `4px solid ${primaryColor || '#FFFFFF'}`
                            }}>
                                <img src={resolvedLogoUrl} style={{ width: '250px', height: '250px', borderRadius: '50%' }} />
                                {brandName && <h1 style={{ 
                                    color: 'white', 
                                    fontSize: '60px', 
                                    marginTop: '20px',
                                    fontFamily: 'Arial Black'
                                }}>{brandName}</h1>}
                            </div>
                        </AbsoluteFill>
                    </Sequence>

                    {/* Corner Watermark (Persistent) */}
                    <AbsoluteFill style={{ 
                        justifyContent: 'flex-start', 
                        alignItems: 'flex-end',
                        padding: '40px',
                        opacity: 0.3
                    }}>
                        <img src={resolvedLogoUrl} style={{ width: '100px', height: '100px', borderRadius: '50%' }} />
                    </AbsoluteFill>
                </AbsoluteFill>
            )}

            {/* 4. Dynamic Timeline Captions (The 10/10 Polish) */}
            {!showCtaNow && timeline && timeline.map((seg, i) => (
                <Sequence key={i} from={Math.floor(seg.start * fps)} durationInFrames={Math.floor(seg.duration * fps)}>
                    <AbsoluteFill style={{
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        padding: '80px',
                        background: 'linear-gradient(to top, rgba(0,0,0,0.6), transparent)'
                    }}>
                        <h2 style={{
                            color: seg.style === 'high_impact' ? '#FFD700' : 'white',
                            fontSize: seg.style === 'high_impact' ? '110px' : '85px',
                            fontFamily: 'Arial Black, sans-serif',
                            textTransform: 'uppercase',
                            textAlign: 'center',
                            textShadow: '0 0 20px rgba(0,0,0,0.9)',
                            padding: '20px',
                            backgroundColor: 'rgba(0,0,0,0.4)',
                            borderRadius: '15px'
                        }}>
                            {seg.text}
                        </h2>
                    </AbsoluteFill>
                </Sequence>
            ))}

            {/* 4. Legacy Title Fallback (if no timeline) */}
            {!showCtaNow && !timeline && (
                <AbsoluteFill style={{
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    flexDirection: 'column',
                    padding: '100px'
                }}>
                    <h1 style={{ color: 'white', fontSize: '90px', opacity: titleOpacity }}>{title}</h1>
                    {subtitle && <p style={{ color: '#FFD700', fontSize: '45px' }}>{subtitle}</p>}
                </AbsoluteFill>
            )}

            {/* 5. CTA Overlay */}
            {showCtaNow && (
                <Sequence from={durationInFrames - (fps * 2)}>
                    <CTAOverlay type={ctaType || 'engagement'} text={ctaText || ''} />
                </Sequence>
            )}
        </AbsoluteFill>
    );
};
