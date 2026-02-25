import { AbsoluteFill, Video, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { z } from 'zod';

export const viralClipSchema = z.object({
    title: z.string(),
    subtitle: z.string(),
    videoUrl: z.string(),
});

export const ViralClip: React.FC<z.infer<typeof viralClipSchema>> = ({ title, subtitle, videoUrl }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    const opacity = interpolate(frame, [0, 30], [0, 1], {
        extrapolateRight: 'clamp',
    });

    return (
        <AbsoluteFill style={{ backgroundColor: 'black' }}>
            <Video src={videoUrl} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />

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
                    fontSize: '80px',
                    fontFamily: 'Arial',
                    textAlign: 'center',
                    textShadow: '0 0 20px rgba(0,0,0,0.5)',
                    opacity
                }}>
                    {title}
                </h1>
                <p style={{
                    color: '#FFD700',
                    fontSize: '40px',
                    fontFamily: 'Arial',
                    marginTop: '20px',
                    opacity
                }}>
                    {subtitle}
                </p>
            </AbsoluteFill>
        </AbsoluteFill>
    );
};
