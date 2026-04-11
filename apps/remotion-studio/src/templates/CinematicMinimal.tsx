import { AbsoluteFill, Video, Audio, interpolate, useCurrentFrame, useVideoConfig, Sequence } from 'remotion';
import { z } from 'zod';
import { CTAOverlay } from '../components/CTAOverlay';

export const cinematicMinimalSchema = z.object({
    title: z.string(),
    subtitle: z.string(),
    videoUrl: z.string().optional(),
    audioUrl: z.string().optional(),
    primaryColor: z.string().optional(),
    showCtaOverlay: z.boolean().optional(),
    ctaType: z.enum(['engagement', 'cta']).optional(),
    ctaText: z.string().optional(),
});

export const CinematicMinimal: React.FC<z.infer<typeof cinematicMinimalSchema>> = ({ title, subtitle, videoUrl, audioUrl, primaryColor = '#ffffff', showCtaOverlay, ctaType, ctaText }) => {
    const frame = useCurrentFrame();
    const { fps, durationInFrames } = useVideoConfig();

    // Show CTA in last 2 seconds
    const showCtaNow = showCtaOverlay && frame > durationInFrames - (fps * 2);

    const opacity = interpolate(frame, [0, 40], [0, 1], {
        extrapolateRight: 'clamp',
    });

    const scale = interpolate(frame, [0, 120], [1, 1.1], {
        extrapolateRight: 'clamp',
    });

    return (
        <AbsoluteFill style={{ backgroundColor: 'black' }}>
            {/* Background Video with Slow Zoom */}
            {videoUrl && (
                <div style={{ transform: `scale(${scale})`, width: '100%', height: '100%' }}>
                    <Video src={videoUrl} style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.6 }} />
                </div>
            )}

            {/* Audio */}
            {audioUrl && <Audio src={audioUrl} />}

            {/* Content Overlay */}
            {!showCtaNow && (
                <AbsoluteFill style={{
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    padding: '80px',
                    background: 'radial-gradient(circle, transparent 20%, rgba(0,0,0,0.4) 100%)'
                }}>
                    <div style={{ textAlign: 'center', opacity }}>
                        <div style={{
                            height: '2px',
                            width: '100px',
                            backgroundColor: primaryColor,
                            margin: '0 auto 40px',
                            transform: `scaleX(${interpolate(frame, [0, 60], [0, 1], { extrapolateRight: 'clamp' })})`
                        }} />

                        <h1 style={{
                            color: 'white',
                            fontSize: '80px',
                            fontFamily: 'Georgia, serif',
                            fontStyle: 'italic',
                            letterSpacing: '0.1em',
                            marginBottom: '20px'
                        }}>
                            {title}
                        </h1>

                        <p style={{
                            color: 'rgba(255,255,255,0.7)',
                            fontSize: '24px',
                            fontFamily: 'Inter, sans-serif',
                            textTransform: 'uppercase',
                            letterSpacing: '0.5em',
                            fontWeight: 300
                        }}>
                            {subtitle}
                        </p>
                    </div>
                </AbsoluteFill>
            )}

            {/* 4. CTA Overlay */}
            {showCtaNow && (
                <Sequence from={durationInFrames - (fps * 2)}>
                    <CTAOverlay type={ctaType || 'engagement'} text={ctaText || ''} />
                </Sequence>
            )}
        </AbsoluteFill>
    );
};
