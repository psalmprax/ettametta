import React from 'react';
import { AbsoluteFill, Video, Audio, interpolate, useCurrentFrame, useVideoConfig, spring, Sequence } from 'remotion';
import { z } from 'zod';
import { CTAOverlay } from '../components/CTAOverlay';

export const hormoziStyleSchema = z.object({
    text: z.string(),
    video_url: z.string().optional(),
    audio_url: z.string().optional(),
    highlight_color: z.string().optional(),
    show_cta_overlay: z.boolean().optional(),
    cta_type: z.enum(['engagement', 'cta']).optional(),
    cta_text: z.string().optional(),
});

export const HormoziStyle: React.FC<z.infer<typeof hormoziStyleSchema>> = ({ text, video_url, audio_url, highlight_color = '#00ff00', show_cta_overlay, cta_type, cta_text }) => {
    const frame = useCurrentFrame();
    const { fps, durationInFrames } = useVideoConfig();

    const words = text.split(' ');
    // Show CTA in last 2 seconds
    const showCtaNow = show_cta_overlay && frame > durationInFrames - (fps * 2);
    const wordsPerSecond = 3;
    const currentWordIndex = Math.floor(frame / (fps / wordsPerSecond)) % words.length;

    const springValue = spring({
        frame: frame % (fps / wordsPerSecond),
        fps,
        config: { stiffness: 100 }
    });

    return (
        <AbsoluteFill style={{ backgroundColor: 'black' }}>
            {/* Background Video */}
            {video_url && (
                <Video src={video_url} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            )}

            {/* Audio */}
            {audio_url && <Audio src={audio_url} />}

            {/* Content Overlay */}
            {!showCtaNow && (
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
                        border: `4px solid ${highlight_color}`,
                        transform: `scale(${interpolate(springValue, [0, 1], [0.9, 1.2])})`,
                        boxShadow: `0 0 50px ${highlight_color}44`
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
            )}

            {/* 4. CTA Overlay */}
            {showCtaNow && (
                <Sequence from={durationInFrames - (fps * 2)}>
                    <CTAOverlay type={cta_type || 'engagement'} text={cta_text || ''} />
                </Sequence>
            )}
        </AbsoluteFill>
    );
};
