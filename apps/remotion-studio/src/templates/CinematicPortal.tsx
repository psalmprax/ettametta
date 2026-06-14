import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig, Sequence } from 'remotion';
import { Audio, Video } from '@remotion/media';
import { z } from 'zod';
import { ThreeCanvas } from '@remotion/three';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import { CTAOverlay } from '../components/CTAOverlay';
import { AncientPortal } from '../components/AncientPortal';

export const cinematicPortalSchema = z.object({
    title: z.string(),
    subtitle: z.string(),
    video_url: z.string().optional(),
    audio_url: z.string().optional(),
    show_cta_overlay: z.boolean().optional(),
    cta_type: z.enum(['engagement', 'cta']).optional(),
    cta_text: z.string().optional(),
});

export const CinematicPortal: React.FC<z.infer<typeof cinematicPortalSchema>> = ({ 
    title, 
    subtitle, 
    video_url, 
    audio_url, 
    show_cta_overlay, 
    cta_type, 
    cta_text 
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

    return (
        <AbsoluteFill style={{ backgroundColor: '#020202' }}>
            {/* Background Video */}
            {video_url && (
                <Video 
                    src={video_url} 
                    style={{ 
                        width: '100%', 
                        height: '100%', 
                        objectFit: 'cover', 
                        opacity: 0.1 
                    }} 
                />
            )}
            
            {audio_url && <Audio src={audio_url} />}

            <AbsoluteFill style={{ opacity: show_cta_overlay ? globalOpacity : 1 }}>
                
                {/* 3D Portal Layer with Post Processing */}
                <ThreeCanvas width={width} height={height} orthographic={false} camera={{ fov: 60, position: [0, 0, 5] }}>
                    <AncientPortal primaryColor="#FF4500" />
                    {/* Cinematic Post-Processing */}
                    <EffectComposer>
                        <Bloom 
                            luminanceThreshold={0.5} 
                            luminanceSmoothing={0.9} 
                            intensity={2.0} 
                            mipmapBlur 
                        />
                    </EffectComposer>
                </ThreeCanvas>

                {/* Typography Layer (Overlayed in 2D for perfect sharpness) */}
                <AbsoluteFill style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 10 }}>
                    <h1 style={{
                        color: 'white',
                        fontSize: '120px',
                        fontWeight: 300,
                        letterSpacing: '20px',
                        margin: 0,
                        textTransform: 'uppercase',
                        textShadow: '0 0 40px rgba(255, 69, 0, 0.8)',
                        textAlign: 'center'
                    }}>
                        {title}
                    </h1>
                    <p style={{
                        color: '#FFA07A',
                        fontSize: '40px',
                        fontWeight: 400,
                        letterSpacing: '15px',
                        margin: '20px 0 0 0',
                        textTransform: 'uppercase',
                        textShadow: '0 0 20px rgba(255, 69, 0, 0.5)'
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
