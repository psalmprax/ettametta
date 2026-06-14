import React from 'react';
import { AbsoluteFill, Video, Audio, interpolate, useCurrentFrame, useVideoConfig, Sequence } from 'remotion';
import { z } from 'zod';
import { ThreeCanvas } from '@remotion/three';
import { CTAOverlay } from '../components/CTAOverlay';
import { AncientAstrolabe } from '../components/AncientAstrolabe';

export const cinematicAncientSchema = z.object({
    title: z.string(),
    subtitle: z.string(),
    video_url: z.string().optional(),
    audio_url: z.string().optional(),
    primary_color: z.string().optional(),
    show_cta_overlay: z.boolean().optional(),
    cta_type: z.enum(['engagement', 'cta']).optional(),
    cta_text: z.string().optional(),
});

export const CinematicAncient: React.FC<z.infer<typeof cinematicAncientSchema>> = ({ 
    title, 
    subtitle, 
    video_url, 
    audio_url, 
    primary_color = '#FFD700', // Default ancient gold
    show_cta_overlay, 
    cta_type, 
    cta_text 
}) => {
    const frame = useCurrentFrame();
    const { durationInFrames, fps, width, height } = useVideoConfig();

    const showCtaNow = show_cta_overlay && frame > durationInFrames - (fps * 2);

    // Smooth entry for text
    const textOpacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: 'clamp' });
    const textTranslateY = interpolate(frame, [0, 30], [40, 0], { extrapolateRight: 'clamp' });

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
                {/* 3D WebGL Canvas Layer */}
                <ThreeCanvas 
                    width={width} 
                    height={height} 
                    camera={{ position: [0, 0, 12], fov: 45 }}
                    style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
                >
                    <AncientAstrolabe primaryColor={primary_color} />
                </ThreeCanvas>

                {/* Floating Aesthetic Typography */}
                <div style={{
                    position: 'absolute',
                    bottom: '15%',
                    width: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 10,
                    opacity: textOpacity,
                    transform: `translateY(${textTranslateY}px)`
                }}>
                    <h1 style={{
                        color: 'white',
                        fontSize: '60px',
                        fontWeight: 300, // Elegant thin font
                        letterSpacing: '15px',
                        margin: 0,
                        textTransform: 'uppercase',
                        textShadow: `0 0 30px ${primary_color}88`
                    }}>
                        {title}
                    </h1>
                    <p style={{
                        color: 'rgba(255,255,255,0.7)',
                        fontSize: '24px',
                        fontWeight: 600,
                        letterSpacing: '5px',
                        marginTop: '10px',
                        textTransform: 'uppercase'
                    }}>
                        {subtitle}
                    </p>
                </div>
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
