import React from 'react';
import { AbsoluteFill, Video, Audio, interpolate, useCurrentFrame, useVideoConfig, Sequence } from 'remotion';
import { z } from 'zod';
import { ThreeCanvas } from '@remotion/three';
import { CTAOverlay } from '../components/CTAOverlay';
import { ThreeDText } from '../components/ThreeDText';

export const cinematic3DSchema = z.object({
    title: z.string(),
    subtitle: z.string(),
    video_url: z.string().optional(),
    audio_url: z.string().optional(),
    primary_color: z.string().optional(),
    show_cta_overlay: z.boolean().optional(),
    cta_type: z.enum(['engagement', 'cta']).optional(),
    cta_text: z.string().optional(),
});

export const Cinematic3D: React.FC<z.infer<typeof cinematic3DSchema>> = ({ 
    title, 
    subtitle, 
    video_url, 
    audio_url, 
    primary_color = '#00F2FE', 
    show_cta_overlay, 
    cta_type, 
    cta_text 
}) => {
    const frame = useCurrentFrame();
    const { durationInFrames, fps, width, height } = useVideoConfig();

    // Show CTA in last 2 seconds
    const showCtaNow = show_cta_overlay && frame > durationInFrames - (fps * 2);

    // Fade out 3D text right before the CTA
    const opacity3D = interpolate(
        frame, 
        [durationInFrames - (fps * 2) - 15, durationInFrames - (fps * 2)], 
        [1, 0], 
        { extrapolateRight: 'clamp' }
    );

    return (
        <AbsoluteFill style={{ backgroundColor: '#0A0A0B' }}>
            {/* Background Video */}
            {video_url && (
                <Video 
                    src={video_url} 
                    style={{ 
                        width: '100%', 
                        height: '100%', 
                        objectFit: 'cover', 
                        opacity: 0.3 
                    }} 
                />
            )}
            
            {/* Audio */}
            {audio_url && <Audio src={audio_url} />}

            {/* 3D WebGL Canvas Layer */}
            <AbsoluteFill style={{ opacity: show_cta_overlay ? opacity3D : 1 }}>
                <ThreeCanvas 
                    width={width} 
                    height={height} 
                    camera={{ position: [0, 0, 15], fov: 45 }}
                >
                    <ambientLight intensity={0.5} />
                    <ThreeDText 
                        text={title} 
                        subtitle={subtitle} 
                        primaryColor={primary_color} 
                    />
                </ThreeCanvas>
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
