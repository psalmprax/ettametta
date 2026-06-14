import React from 'react';
import { AbsoluteFill, Video, Audio, interpolate, useCurrentFrame, useVideoConfig, Sequence } from 'remotion';
import { z } from 'zod';
import { CTAOverlay } from '../components/CTAOverlay';
import { IridescentGlass } from '../components/IridescentGlass';

export const cinematicIridescentSchema = z.object({
    title: z.string(),
    subtitle: z.string(),
    video_url: z.string().optional(),
    audio_url: z.string().optional(),
    show_cta_overlay: z.boolean().optional(),
    cta_type: z.enum(['engagement', 'cta']).optional(),
    cta_text: z.string().optional(),
});

export const CinematicIridescent: React.FC<z.infer<typeof cinematicIridescentSchema>> = ({ 
    title, 
    subtitle, 
    video_url, 
    audio_url, 
    show_cta_overlay, 
    cta_type, 
    cta_text 
}) => {
    const frame = useCurrentFrame();
    const { durationInFrames, fps } = useVideoConfig();

    const showCtaNow = show_cta_overlay && frame > durationInFrames - (fps * 2);

    const fadeOutFrame = durationInFrames - (fps * 2);
    const globalOpacity = interpolate(
        frame, 
        [fadeOutFrame - 15, fadeOutFrame], 
        [1, 0], 
        { extrapolateRight: 'clamp' }
    );

    return (
        <AbsoluteFill style={{ backgroundColor: '#050505' }}>
            {/* Background Video */}
            {video_url && (
                <Video 
                    src={video_url} 
                    style={{ 
                        width: '100%', 
                        height: '100%', 
                        objectFit: 'cover', 
                        opacity: 0.15 
                    }} 
                />
            )}
            
            {audio_url && <Audio src={audio_url} />}

            <AbsoluteFill style={{ opacity: show_cta_overlay ? globalOpacity : 1 }}>
                <IridescentGlass title={title} subtitle={subtitle} />
            </AbsoluteFill>

            {/* CTA Overlay Layer */}
            {showCtaNow && (
                <Sequence from={durationInFrames - (fps * 2)}>
                    <CTAOverlay type={cta_type || 'engagement'} text={cta_text || ''} />
                </Sequence>
            )}
        </AbsoluteFill>
    );
};
