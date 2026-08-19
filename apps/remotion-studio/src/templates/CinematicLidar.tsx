import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig, Sequence } from 'remotion';
import { Audio, Video } from '@remotion/media';
import { z } from 'zod';
import { ThreeCanvas } from '@remotion/three';
import { EffectComposer, Bloom, Glitch } from '@react-three/postprocessing';
import { GlitchMode } from 'postprocessing';
import * as THREE from 'three';
import { CTAOverlay } from '../components/CTAOverlay';
import { LidarPointCloud } from '../components/LidarPointCloud';

export const cinematicLidarSchema = z.object({
    title: z.string(),
    subtitle: z.string(),
    video_url: z.string().optional(),
    audio_url: z.string().optional(),
    show_cta_overlay: z.boolean().optional(),
    cta_type: z.enum(['engagement', 'cta']).optional(),
    cta_text: z.string().optional(),
    primary_color: z.string().optional(),
});

export const CinematicLidar: React.FC<z.infer<typeof cinematicLidarSchema>> = ({ 
    title, 
    subtitle, 
    video_url, 
    audio_url, 
    show_cta_overlay, 
    cta_type, 
    cta_text,
    primary_color: primaryColor = '#00FF00' // Hacker green default
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
        <AbsoluteFill style={{ backgroundColor: '#000800' }}>
            {/* Background Video */}
            {video_url && (
                <Video 
                    src={video_url} 
                    style={{ 
                        width: '100%', 
                        height: '100%', 
                        objectFit: 'cover', 
                        opacity: 0.1,
                        filter: 'grayscale(100%) contrast(200%)'
                    }} 
                />
            )}
            
            {audio_url && <Audio src={audio_url} />}

            <AbsoluteFill style={{ opacity: show_cta_overlay ? globalOpacity : 1 }}>
                
                {/* 3D Lidar Point Cloud Layer */}
                <ThreeCanvas width={width} height={height} camera={{ fov: 60, position: [0, 0, 10] }}>
                    <LidarPointCloud primaryColor={primaryColor} />
                    <EffectComposer enableNormalPass={false}>
                        <Bloom 
                            luminanceThreshold={0.2} 
                            luminanceSmoothing={0.9} 
                            intensity={2.0} 
                            mipmapBlur 
                        />
                        <Glitch
                            delay={new THREE.Vector2(1.5, 3.5)}
                            duration={new THREE.Vector2(0.1, 0.3)}
                            strength={new THREE.Vector2(0.1, 0.5)}
                            mode={GlitchMode.SPORADIC}
                            active={true}
                            ratio={0.85}
                        />
                    </EffectComposer>
                </ThreeCanvas>

                {/* Typography Layer */}
                <AbsoluteFill style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 10, pointerEvents: 'none' }}>
                    <h1 style={{
                        color: 'white',
                        fontSize: '120px',
                        fontWeight: 900,
                        fontFamily: 'monospace',
                        letterSpacing: '5px',
                        margin: 0,
                        textTransform: 'uppercase',
                        textAlign: 'center',
                        textShadow: `0 0 20px ${primaryColor}`
                    }}>
                        {title}
                    </h1>
                    <p style={{
color: primaryColor,
                    fontSize: '40px',
                    fontWeight: 400,
                    fontFamily: 'monospace',
                    letterSpacing: '10px',
                    margin: '20px 0 0 0',
                    textTransform: 'uppercase',
                    textShadow: `0 0 10px ${primaryColor}`
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
