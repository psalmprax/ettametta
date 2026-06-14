import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig, Sequence } from 'remotion';
import { Audio, Video } from '@remotion/media';
import { z } from 'zod';
import { ThreeCanvas } from '@remotion/three';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import { CTAOverlay } from '../components/CTAOverlay';
import { ChromaticPrism } from '../components/ChromaticPrism';

export const cinematicPrismSchema = z.object({
    title: z.string(),
    subtitle: z.string(),
    video_url: z.string().optional(),
    audio_url: z.string().optional(),
    show_cta_overlay: z.boolean().optional(),
    cta_type: z.enum(['engagement', 'cta']).optional(),
    cta_text: z.string().optional(),
    primary_color: z.string().optional(),
});

export const CinematicPrism: React.FC<z.infer<typeof cinematicPrismSchema>> = ({ 
    title, 
    subtitle, 
    video_url, 
    audio_url, 
    show_cta_overlay, 
    cta_type, 
    cta_text,
    primary_color = '#FF10F0'
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
                
                {/* 3D Prism Layer (Text is rendered inside WebGL to refract) */}
                <ThreeCanvas width={width} height={height} camera={{ fov: 60, position: [0, 0, 5] }}>
                    <ChromaticPrism primaryColor={primary_color} title={title} subtitle={subtitle} />
                    <EffectComposer>
                        <Bloom 
                            luminanceThreshold={0.6} 
                            luminanceSmoothing={0.9} 
                            intensity={1.0} 
                            mipmapBlur 
                        />
                    </EffectComposer>
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
