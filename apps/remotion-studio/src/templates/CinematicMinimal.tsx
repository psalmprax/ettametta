import React from 'react';
import { AbsoluteFill, Video, Audio, interpolate, useCurrentFrame, useVideoConfig, Sequence } from 'remotion';
import { z } from 'zod';
import { CTAOverlay } from '../components/CTAOverlay';

export const cinematicMinimalSchema = z.object({
    title: z.string(),
    subtitle: z.string(),
    video_url: z.string().optional(),
    audio_url: z.string().optional(),
    primary_color: z.string().optional(),
    show_cta_overlay: z.boolean().optional(),
    cta_type: z.enum(['engagement', 'cta']).optional(),
    cta_text: z.string().optional(),
});

export const CinematicMinimal: React.FC<z.infer<typeof cinematicMinimalSchema>> = ({ title, subtitle, video_url, audio_url, primary_color = '#00F2FE', show_cta_overlay, cta_type, cta_text }) => {
    const frame = useCurrentFrame();
    const { fps, durationInFrames } = useVideoConfig();

    // Show CTA in last 2 seconds
    const showCtaNow = show_cta_overlay && frame > durationInFrames - (fps * 2);

    const opacity = interpolate(frame, [0, 40], [0, 1], {
        extrapolateRight: 'clamp',
    });

    const scale = interpolate(frame, [0, 120], [1, 1.1], {
        extrapolateRight: 'clamp',
    });

    return (
        <AbsoluteFill style={{ backgroundColor: '#0A0A0B' }}>
            {/* Background Video with Slow Zoom */}
            {video_url && (
                <div style={{ transform: `scale(${scale})`, width: '100%', height: '100%' }}>
                    <Video src={video_url} style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.4 }} />
                </div>
            )}
            {/* Audio */}
            {audio_url && <Audio src={audio_url} />}

            {/* Content Overlay */}
            {!showCtaNow && (
                <AbsoluteFill style={{
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    padding: '80px',
                    background: 'radial-gradient(circle, transparent 20%, rgba(10,10,11,0.8) 100%)'
                }}>
                    <div style={{ textAlign: 'center', opacity }}>
                        <div style={{
                            height: '4px',
                            width: '120px',
                            background: 'linear-gradient(to right, #00F2FE, #4ADE80)',
                            borderRadius: '2px',
                            margin: '0 auto 40px',
                            transform: `scaleX(${interpolate(frame, [0, 60], [0, 1], { extrapolateRight: 'clamp' })})`
                        }} />

                        <h1 style={{
                            color: 'white',
                            fontSize: '90px',
                            fontFamily: 'Inter, sans-serif',
                            fontWeight: 800,
                            letterSpacing: '-0.04em',
                            lineHeight: 1.1,
                            marginBottom: '24px',
                            textShadow: '0 0 30px rgba(0, 242, 254, 0.3)'
                        }}>
                            {title}
                        </h1>

                        <p style={{
                            color: '#8E2DE2',
                            fontSize: '28px',
                            fontFamily: 'Inter, sans-serif',
                            textTransform: 'uppercase',
                            letterSpacing: '0.4em',
                            fontWeight: 500
                        }}>
                            {subtitle}
                        </p>
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
