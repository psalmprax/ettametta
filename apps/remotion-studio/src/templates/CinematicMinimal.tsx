import React from 'react';
import { AbsoluteFill, Video, Audio, interpolate, useCurrentFrame, useVideoConfig, Sequence } from 'remotion';
import { z } from 'zod';
import { CTAOverlay } from '../components/CTAOverlay';
import { BrandReveal } from '../components/BrandReveal';

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
    const { width, height, fps, durationInFrames } = useVideoConfig();

    // Show CTA in last 2 seconds
    const showCtaNow = show_cta_overlay && frame > durationInFrames - (fps * 2);

    const opacity = interpolate(frame, [0, 40], [0, 1], {
        extrapolateRight: 'clamp',
    });

    const scale = interpolate(frame, [0, 120], [1, 1.1], {
        extrapolateRight: 'clamp',
    });

    const containerPadding = `${Math.min(width * 0.05, 50)}px`;
    const lineMarginBottom = `${Math.min(width * 0.05, 30)}px`;
    const titleFontSize = `${Math.min(width * 0.08, 80)}px`;
    const subtitleFontSize = `${Math.min(width * 0.035, 22)}px`;
    const subtitleLetterSpacing = `${Math.min(width * 0.02, 8)}px`;

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
                <Sequence durationInFrames={durationInFrames}>
                    <BrandReveal 
                        brandName={title} 
                        subtitle={subtitle} 
                        primaryColor={primary_color} 
                    />
                </Sequence>
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
