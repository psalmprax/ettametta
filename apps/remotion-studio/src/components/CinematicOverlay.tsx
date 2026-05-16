import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame } from 'remotion';

interface CinematicOverlayProps {
    vignetteIntensity?: number;
    grainOpacity?: number;
    showLetterbox?: boolean;
    chromaticAberration?: number;
    filmBurnOpacity?: number;
}

export const CinematicOverlay: React.FC<CinematicOverlayProps> = ({
    vignetteIntensity = 0.5,
    grainOpacity = 0.08,
    showLetterbox = true,
    chromaticAberration = 2,
    filmBurnOpacity = 0.15
}) => {
    const frame = useCurrentFrame();

    // Film Burn Animation (Pulse effect)
    const burnTranslateX = interpolate(frame % 120, [0, 60, 120], [-10, 10, -10]);
    const burnOpacity = interpolate(
        Math.sin(frame / 10), 
        [-1, 1], 
        [filmBurnOpacity * 0.5, filmBurnOpacity]
    );

    return (
        <AbsoluteFill style={{ pointerEvents: 'none', zIndex: 1000 }}>
            {/* 1. Chromatic Aberration Filter (SVG based for performance) */}
            <svg style={{ position: 'absolute', width: 0, height: 0 }}>
                <filter id="chromaticAberration">
                    <feColorMatrix
                        type="matrix"
                        values="1 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1 0"
                        in="SourceGraphic"
                        result="red"
                    />
                    <feOffset in="red" dx={chromaticAberration} dy="0" result="redOffset" />
                    <feColorMatrix
                        type="matrix"
                        values="0 0 0 0 0  0 1 0 0 0  0 0 0 0 0  0 0 0 1 0"
                        in="SourceGraphic"
                        result="green"
                    />
                    <feColorMatrix
                        type="matrix"
                        values="0 0 0 0 0  0 0 0 0 0  0 0 1 0 0  0 0 0 1 0"
                        in="SourceGraphic"
                        result="blue"
                    />
                    <feOffset in="blue" dx={-chromaticAberration} dy="0" result="blueOffset" />
                    <feBlend mode="screen" in="redOffset" in2="green" result="redGreen" />
                    <feBlend mode="screen" in="redGreen" in2="blueOffset" />
                </filter>
            </svg>

            {/* 2. Film Grain (Procedural) */}
            <AbsoluteFill style={{
                opacity: grainOpacity,
                backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3B%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
                mixBlendMode: 'overlay',
                filter: `contrast(150%) brightness(100%)`,
            }} />

            {/* 3. Radial Vignette (High-Quality) */}
            <AbsoluteFill style={{
                background: `radial-gradient(circle, transparent 30%, rgba(0,0,0,${vignetteIntensity * 0.2}) 60%, rgba(0,0,0,${vignetteIntensity}) 100%)`,
                mixBlendMode: 'multiply'
            }} />

            {/* 4. Film Burn / Light Leak (Dynamic) */}
            <AbsoluteFill style={{
                opacity: burnOpacity,
                background: `linear-gradient(${burnTranslateX}deg, transparent, rgba(255, 100, 0, 0.4), rgba(255, 200, 50, 0.2), transparent)`,
                mixBlendMode: 'screen',
                filter: 'blur(40px)'
            }} />

            {/* 5. Letterbox (Cinematic Aspect Ratio) */}
            {showLetterbox && (
                <>
                    <div style={{
                        position: 'absolute',
                        top: 0,
                        width: '100%',
                        height: '10%',
                        backgroundColor: 'black',
                    }} />
                    <div style={{
                        position: 'absolute',
                        bottom: 0,
                        width: '100%',
                        height: '10%',
                        backgroundColor: 'black',
                    }} />
                </>
            )}

            {/* 6. Subtle Dust/Scratches (Simulated) */}
            <AbsoluteFill style={{
                opacity: 0.03,
                backgroundImage: `url("https://www.transparenttextures.com/patterns/stardust.png")`,
                mixBlendMode: 'screen'
            }} />
        </AbsoluteFill>
    );
};
