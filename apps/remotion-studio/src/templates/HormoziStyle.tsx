import { AbsoluteFill, Video, Audio, interpolate, useCurrentFrame, useVideoConfig, Spring } from 'remotion';
import { z } from 'zod';

export const hormoziStyleSchema = z.object({
    text: z.string(),
    videoUrl: z.string().optional(),
    audioUrl: z.string().optional(),
    highlightColor: z.string().optional(),
});

export const HormoziStyle: React.FC<z.infer<typeof hormoziStyleSchema>> = ({ text, videoUrl, audioUrl, highlightColor = '#00ff00' }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    const words = text.split(' ');
    const wordsPerSecond = 3;
    const currentWordIndex = Math.floor(frame / (fps / wordsPerSecond)) % words.length;

    const spring = Spring({
        frame: frame % (fps / wordsPerSecond),
        fps,
        config: { stiffness: 100 }
    });

    return (
        <AbsoluteFill style={{ backgroundColor: 'black' }}>
            {/* Background Video */}
            {videoUrl && (
                <Video src={videoUrl} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            )}

            {/* Audio */}
            {audioUrl && <Audio src={audioUrl} />}

            {/* Content Overlay */}
            <AbsoluteFill style={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                padding: '40px'
            }}>
                <div style={{
                    backgroundColor: 'rgba(0,0,0,0.85)',
                    padding: '20px 60px',
                    borderRadius: '20px',
                    border: `4px solid ${highlightColor}`,
                    transform: `scale(${interpolate(spring, [0, 1], [0.9, 1.2])})`,
                    boxShadow: `0 0 50px ${highlightColor}44`
                }}>
                    <h1 style={{
                        color: 'white',
                        fontSize: '120px',
                        fontFamily: '"Arial Black", sans-serif',
                        textTransform: 'uppercase',
                        textAlign: 'center',
                        margin: 0,
                        lineHeight: 1
                    }}>
                        {words[currentWordIndex]}
                    </h1>
                </div>
            </AbsoluteFill>
        </AbsoluteFill>
    );
};
