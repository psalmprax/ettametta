import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig, Sequence } from 'remotion';
import { Audio, Video } from '@remotion/media';
import { z } from 'zod';
import { ThreeCanvas } from '@remotion/three';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import { CTAOverlay } from '../components/CTAOverlay';
import { LiquidMetalSphere } from '../components/LiquidMetalSphere';

export const cinematicLiquidSchema = z.object({
    title: z.string(),
    subtitle: z.string(),
    video_url: z.string().optional(),
    audio_url: z.string().optional(),
    show_cta_overlay: z.boolean().optional(),
    cta_type: z.enum(['engagement', 'cta']).optional(),
    cta_text: z.string().optional(),
    primary_color: z.string().optional(),
});

export const CinematicLiquid: React.FC<z.infer<typeof cinematicLiquidSchema>> = ({ 
    title, 
    subtitle, 
    video_url, 
    audio_url, 
    show_cta_overlay, 
    cta_type, 
    cta_text,
    primary_color: primaryColor = '#00F2FE'
}) => {
    const frame = useCurrentFrame();
    const { durationInFrames, fps, width, height } = useVideoConfig();

    const showCtaNow = show_cta_overlay && frame > durationInFrames - (fps * 2);

    const fadeOutFrame = durationInFrames - (fps * 2);
    const globalOpacity = interpolate(
        frame, 
        [fadeOutFrame - 15, fadeOutFrame], 
        [1, 0], 
        { extrapolateRight: 'clamp' }
    );

    const titleScale = interpolate(frame, [0, durationInFrames], [1, 1.1]);

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
                
                {/* 3D Liquid Metal Layer */}
                <ThreeCanvas width={width} height={height} camera={{ fov: 60, position: [0, 0, 8] }}>
                    <LiquidMetalSphere primaryColor={primaryColor} />
                    <EffectComposer>
                        <Bloom 
                            luminanceThreshold={0.7} 
                            luminanceSmoothing={0.9} 
                            intensity={1.5} 
                            mipmapBlur 
                        />
                    </EffectComposer>
                </ThreeCanvas>

                {/* Typography Layer */}
                <AbsoluteFill style={{ 
                    display: 'flex', 
                    justifyContent: 'center', 
                    alignItems: 'center', 
                    zIndex: 10,
                    pointerEvents: 'none'
                }}>
                    <h1 style={{
                        color: 'white',
                        fontSize: '110px',
                        fontWeight: 200,
                        letterSpacing: '30px',
                        margin: 0,
                        textTransform: 'uppercase',
                        textAlign: 'center',
                        transform: `scale(${titleScale})`,
                        mixBlendMode: 'overlay',
                        textShadow: '0 0 40px rgba(255,255,255,0.8)'
                    }}>
                        {title}
                    </h1>
                    <p style={{
color: primaryColor,
                    fontSize: '35px',
                    fontWeight: 400,
                    letterSpacing: '20px',
                    margin: '40px 0 0 0',
                    textTransform: 'uppercase',
                    textShadow: `0 0 20px ${primaryColor}`
                    }}>
                        {subtitle}
                    </p>
                </AbsoluteFill>

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
