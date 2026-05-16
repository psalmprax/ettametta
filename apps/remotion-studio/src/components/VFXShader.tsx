import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame } from 'remotion';

interface VFXShaderProps {
    type: string;
}

export const VFXShader: React.FC<VFXShaderProps> = ({ type }) => {
    const frame = useCurrentFrame();

    if (type === 'vhs_glitch') {
        // Deterministic noise based on frame — Remotion requires pure functions
        const noisePhase = Math.sin(frame * 0.5) * 0.5 + 0.5;
        const noiseOpacity = interpolate(noisePhase, [0, 1], [0.05, 0.15]);
        const glitchOffset = frame % 15 === 0 ? interpolate(Math.sin(frame), [-1, 1], [-20, 20]) : 0;
        return (
            <AbsoluteFill style={{ pointerEvents: 'none', zIndex: 99 }}>
                {/* Glitch offset bar */}
                {frame % 15 === 0 && (
                    <div style={{
                        position: 'absolute',
                        top: `${10 + ((frame * 7) % 80)}%`,
                        left: 0,
                        width: '100%',
                        height: `${2 + (frame % 5)}px`,
                        backgroundColor: `hsl(${(frame * 30) % 360}, 100%, 50%)`,
                        opacity: 0.6,
                        transform: `translateX(${glitchOffset}px)`
                    }} />
                )}
                {/* Scanlines */}
                <div style={{
                    width: '100%',
                    height: '100%',
                    background: 'repeating-linear-gradient(transparent, transparent 2px, rgba(0,0,0,0.1) 3px)',
                    opacity: 0.5
                }} />
                {/* Static Noise opacity (deterministic) */}
                <div style={{
                    width: '100%',
                    height: '100%',
                    backgroundColor: 'white',
                    opacity: noiseOpacity,
                    mixBlendMode: 'overlay'
                }} />
            </AbsoluteFill>
        );
    }

    if (type === 'blueprint') {
        return (
            <AbsoluteFill style={{ 
                pointerEvents: 'none', 
                backgroundColor: 'rgba(0, 50, 150, 0.3)', 
                mixBlendMode: 'multiply',
                zIndex: 99 
            }}>
                {/* Grid */}
                <div style={{
                    width: '100%',
                    height: '100%',
                    backgroundImage: 'linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)',
                    backgroundSize: '40px 40px'
                }} />
            </AbsoluteFill>
        );
    }

    if (type === 'green_tint') {
        return (
            <AbsoluteFill style={{ 
                pointerEvents: 'none', 
                backgroundColor: 'rgba(0, 255, 50, 0.2)', 
                mixBlendMode: 'screen',
                zIndex: 99 
            }}>
                <div style={{
                    width: '100%',
                    height: '100%',
                    background: 'radial-gradient(circle, transparent 40%, rgba(0,0,0,0.5) 100%)',
                }} />
            </AbsoluteFill>
        );
    }

    if (type === 'monochrome_grain') {
        return (
            <AbsoluteFill style={{ 
                pointerEvents: 'none', 
                backdropFilter: 'grayscale(100%) contrast(120%)',
                zIndex: 99 
            }}>
                <div style={{
                    width: '100%',
                    height: '100%',
                    backgroundColor: 'black',
                    opacity: 0.05,
                    backgroundImage: 'url("https://www.transparenttextures.com/patterns/stardust.png")'
                }} />
            </AbsoluteFill>
        );
    }

    return null;
};
