import { AbsoluteFill, Video, Audio, interpolate, useCurrentFrame, useVideoConfig, Sequence, Spring } from 'remotion';
import { z } from 'zod';
import { CTAOverlay } from './components/CTAOverlay';

export const viralClipSchema = z.object({
    title: z.string(),
    subtitle: z.string(),
    videoUrl: z.string().optional(),
    audioUrl: z.string().optional(),
    showCtaOverlay: z.boolean().optional(),
    ctaType: z.enum(['engagement', 'cta']).optional(),
    ctaText: z.string().optional(),
    clips: z.array(z.object({
        url: z.string(),
        durationInFrames: z.number(),
    })).optional(),
});

const currentWordIndex = 0; // Placeholder for legacy logic if needed 
/***** SHARED CTA OVERLAY REMOVED FROM HERE *****/

export const ViralClip: React.FC<z.infer<typeof viralClipSchema>> = ({ title, subtitle, videoUrl, audioUrl, clips, showCtaOverlay, ctaType, ctaText }) => {
    const frame = useCurrentFrame();
    const { fps, durationInFrames } = useVideoConfig();

    const titleOpacity = interpolate(frame, [0, 20], [0, 1], {
        extrapolateRight: 'clamp',
    });

    // Show CTA in the last 2 seconds
    const showCtaNow = showCtaOverlay && frame > durationInFrames - (fps * 2);

    return (
        <AbsoluteFill style={{ backgroundColor: 'black' }}>
            {/* 1. Background Visuals */}
            {clips ? (
                clips.reduce((acc, clip, index) => {
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
                videoUrl && <Video src={videoUrl} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            )}

            {/* 2. Audio Track */}
            {audioUrl && <Audio src={audioUrl} />}

            {/* 3. Dynamic Overlays */}
            {!showCtaNow && (
                <AbsoluteFill style={{
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    flexDirection: 'column',
                    padding: '100px',
                    background: 'linear-gradient(to top, rgba(0,0,0,0.8), transparent)'
                }}>
                    <h1 style={{
                        color: 'white',
                        fontSize: '90px',
                        fontFamily: 'Arial',
                        fontWeight: 'bold',
                        textAlign: 'center',
                        textTransform: 'uppercase',
                        textShadow: '0 0 30px rgba(0,0,0,0.8)',
                        opacity: titleOpacity,
                        transform: `scale(${interpolate(frame, [0, 20], [0.8, 1], { extrapolateRight: 'clamp' })})`
                    }}>
                        {title}
                    </h1>
                    <p style={{
                        color: '#FFD700',
                        fontSize: '45px',
                        fontFamily: 'Arial',
                        marginTop: '20px',
                        fontWeight: 'bold',
                        textShadow: '0 0 10px rgba(0,0,0,0.5)',
                        opacity: titleOpacity
                    }}>
                        {subtitle}
                    </p>
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
