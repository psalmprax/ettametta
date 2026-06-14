import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig, Sequence } from 'remotion';
import { Audio, Video } from '@remotion/media';
import { z } from 'zod';
import { CTAOverlay } from '../components/CTAOverlay';
import { KineticTypography } from '../components/KineticTypography';

export const cinematicKineticSchema = z.object({
    title: z.string(),
    subtitle: z.string(),
    video_url: z.string().optional(),
    audio_url: z.string().optional(),
    show_cta_overlay: z.boolean().optional(),
    cta_type: z.enum(['engagement', 'cta']).optional(),
    cta_text: z.string().optional(),
    primary_color: z.string().optional(),
});

export const CinematicKinetic: React.FC<z.infer<typeof cinematicKineticSchema>> = ({ 
    title, 
    subtitle, 
    video_url, 
    audio_url, 
    show_cta_overlay, 
    cta_type, 
    cta_text,
    primary_color = '#FFFF00' // High-vis yellow default
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
        <AbsoluteFill style={{ backgroundColor: '#000000' }}>
            {/* Background Video */}
            {video_url && (
                <Video 
                    src={video_url} 
                    style={{ 
                        width: '100%', 
                        height: '100%', 
                        objectFit: 'cover', 
                        opacity: 0.2,
                        filter: 'grayscale(100%) contrast(150%)'
                    }} 
                />
            )}
            
            {audio_url && <Audio src={audio_url} />}

            <AbsoluteFill style={{ opacity: show_cta_overlay ? globalOpacity : 1 }}>
                <KineticTypography primaryColor={primary_color} title={title} subtitle={subtitle} />
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
