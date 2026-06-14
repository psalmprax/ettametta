import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';

interface IridescentGlassProps {
    title: string;
    subtitle: string;
}

export const IridescentGlass: React.FC<IridescentGlassProps> = ({ title, subtitle }) => {
    const frame = useCurrentFrame();
    const { fps, width } = useVideoConfig();

    // Constant rotation for the iridescent rim
    const rotation = (frame * 2) % 360;

    // Smooth entrance spring
    const entrance = spring({
        frame,
        fps,
        config: { damping: 14, stiffness: 80 }
    });

    const scale = interpolate(entrance, [0, 1], [0.8, 1]);
    const opacity = interpolate(entrance, [0, 1], [0, 1]);
    
    // Pulse effect on the glow
    const pulse = Math.sin(frame / 15) * 0.2 + 0.8; // oscillates between 0.6 and 1.0

    const circleSize = Math.min(width * 0.5, 800);

    return (
        <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            background: 'transparent',
            zIndex: 10
        }}>
            {/* Deep Volumetric Glow behind the orb */}
            <div style={{
                position: 'absolute',
                width: circleSize * 1.8,
                height: circleSize * 1.8,
                background: 'conic-gradient(from 0deg, rgba(255,0,122,0.6), rgba(0,255,255,0.6), rgba(255,0,122,0.6))',
                filter: 'blur(120px)',
                opacity: opacity * 0.3 * pulse,
                transform: `rotate(${rotation * -0.3}deg)`,
                borderRadius: '50%'
            }} />
            
            {/* Ambient Background Glow behind the orb */}
            <div style={{
                position: 'absolute',
                width: circleSize * 1.2,
                height: circleSize * 1.2,
                background: 'conic-gradient(from 90deg, #ff00ff, #00ffff, #ff00ff)',
                filter: 'blur(60px)',
                opacity: opacity * 0.5 * pulse,
                transform: `rotate(${rotation * 0.5}deg)`,
                borderRadius: '50%'
            }} />

            {/* Main Orb Container */}
            <div style={{
                width: circleSize,
                height: circleSize,
                position: 'relative',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                transform: `scale(${scale})`,
                opacity: opacity,
            }}>
                {/* Rotating Iridescent Border Glow - Wide */}
                <div style={{
                    position: 'absolute',
                    inset: '-8px',
                    borderRadius: '50%',
                    background: `conic-gradient(from ${rotation}deg, #FF007A, #7000FF, #00E5FF, #FF007A)`,
                    filter: 'blur(16px)',
                    opacity: 0.6
                }} />
                
                {/* Sharp Inner Border */}
                <div style={{
                    position: 'absolute',
                    inset: '-2px',
                    borderRadius: '50%',
                    background: `conic-gradient(from ${rotation}deg, #FF007A, #7000FF, #00E5FF, #FF007A)`,
                    opacity: 1
                }} />

                {/* The Frosted Glass Core */}
                <div style={{
                    position: 'absolute',
                    inset: '0px',
                    borderRadius: '50%',
                    background: 'rgba(10, 10, 15, 0.45)', // Dark glass
                    backdropFilter: 'blur(60px) saturate(200%) brightness(1.3)',
                    WebkitBackdropFilter: 'blur(60px) saturate(200%) brightness(1.3)',
                    boxShadow: 'inset 0 0 80px rgba(255, 255, 255, 0.08), inset 0 2px 8px rgba(255,255,255,0.3), 0 20px 60px rgba(0,0,0,0.8)',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    alignItems: 'center',
                    overflow: 'hidden'
                }}>
                    
                    {/* Internal Light Reflection (Top Sheen) */}
                    <div style={{
                        position: 'absolute',
                        top: '-20%',
                        left: '-20%',
                        right: '-20%',
                        height: '50%',
                        background: 'radial-gradient(ellipse at top, rgba(255,255,255,0.15) 0%, transparent 70%)',
                        transform: 'rotate(-15deg)',
                        pointerEvents: 'none'
                    }} />

                    {/* Typography */}
                    <div style={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        zIndex: 2
                    }}>
                        <p style={{
                            color: 'rgba(255,255,255,0.6)',
                            fontSize: `${circleSize * 0.04}px`,
                            fontWeight: 600,
                            letterSpacing: '6px',
                            margin: '0 0 15px 0',
                            textTransform: 'uppercase'
                        }}>
                            THE PREMIER STUDIO PRESENTS
                        </p>
                        <h1 style={{
                            color: 'white',
                            fontSize: `${circleSize * 0.15}px`,
                            fontWeight: 300, // Elegant thin
                            letterSpacing: '10px',
                            margin: 0,
                            textTransform: 'uppercase',
                            textShadow: '0 4px 20px rgba(0,0,0,0.5)'
                        }}>
                            {title}
                        </h1>
                        <p style={{
                            color: '#E0E0E0',
                            fontSize: `${circleSize * 0.07}px`,
                            fontWeight: 400,
                            letterSpacing: '8px',
                            margin: '10px 0 30px 0',
                            textTransform: 'uppercase'
                        }}>
                            {subtitle}
                        </p>
                        <p style={{
                            color: 'rgba(255,255,255,0.4)',
                            fontSize: `${circleSize * 0.03}px`,
                            fontWeight: 600,
                            letterSpacing: '4px',
                            margin: 0,
                            textTransform: 'uppercase'
                        }}>
                            EST. 2026
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};
