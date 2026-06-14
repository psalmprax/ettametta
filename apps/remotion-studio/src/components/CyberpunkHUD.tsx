import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';

interface CyberpunkHUDProps {
    title: string;
    subtitle: string;
    primaryColor?: string;
    secondaryColor?: string;
}

export const CyberpunkHUD: React.FC<CyberpunkHUDProps> = ({ 
    title, 
    subtitle,
    primaryColor = '#00F0FF',
    secondaryColor = '#FF003C'
}) => {
    const frame = useCurrentFrame();
    const { fps, width } = useVideoConfig();

    const entrance = spring({
        frame,
        fps,
        config: { damping: 12, stiffness: 100 }
    });

    const scale = interpolate(entrance, [0, 1], [0.5, 1]);
    const opacity = interpolate(entrance, [0, 1], [0, 1]);

    // Fast tech rotations
    const rot1 = (frame * 3) % 360;
    const rot2 = (frame * -2) % 360;
    const rot3 = (frame * 5) % 360;

    const hudSize = Math.min(width * 0.6, 900);
    const strokeWidth = 4;

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
            {/* Main HUD Container */}
            <div style={{
                width: hudSize,
                height: hudSize,
                position: 'relative',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                transform: `scale(${scale})`,
                opacity: opacity,
            }}>
                {/* SVG Ring 1 (Outer) */}
                <svg 
                    width="100%" height="100%" viewBox="0 0 100 100" 
                    style={{ position: 'absolute', transform: `rotate(${rot1}deg)`, filter: `drop-shadow(0 0 8px ${primaryColor})` }}
                >
                    <circle cx="50" cy="50" r="48" fill="none" stroke={primaryColor} strokeWidth={strokeWidth / 5} strokeDasharray="4 8" opacity="0.6"/>
                    <path d="M 50 2 A 48 48 0 0 1 98 50" fill="none" stroke={primaryColor} strokeWidth={strokeWidth / 2} />
                    <path d="M 50 98 A 48 48 0 0 1 2 50" fill="none" stroke={primaryColor} strokeWidth={strokeWidth / 2} />
                </svg>

                {/* SVG Ring 2 (Middle, Counter-rotating) */}
                <svg 
                    width="85%" height="85%" viewBox="0 0 100 100" 
                    style={{ position: 'absolute', transform: `rotate(${rot2}deg)`, filter: `drop-shadow(0 0 4px ${secondaryColor})` }}
                >
                    <circle cx="50" cy="50" r="46" fill="none" stroke={secondaryColor} strokeWidth={strokeWidth / 3} strokeDasharray="1 4" opacity="0.8"/>
                    <circle cx="50" cy="50" r="40" fill="none" stroke={secondaryColor} strokeWidth={strokeWidth / 6} opacity="0.3"/>
                    <path d="M 10 50 A 40 40 0 0 1 50 10" fill="none" stroke={secondaryColor} strokeWidth={strokeWidth} />
                    <path d="M 90 50 A 40 40 0 0 1 50 90" fill="none" stroke={secondaryColor} strokeWidth={strokeWidth} />
                </svg>

                {/* SVG Ring 3 (Inner, Fast) */}
                <svg 
                    width="70%" height="70%" viewBox="0 0 100 100" 
                    style={{ position: 'absolute', transform: `rotate(${rot3}deg)`, filter: `drop-shadow(0 0 6px ${primaryColor})` }}
                >
                    <circle cx="50" cy="50" r="45" fill="none" stroke={primaryColor} strokeWidth={strokeWidth / 4} strokeDasharray="20 10 5 10"/>
                    {/* Targeting reticle ticks */}
                    <line x1="50" y1="0" x2="50" y2="10" stroke={primaryColor} strokeWidth={1} />
                    <line x1="50" y1="90" x2="50" y2="100" stroke={primaryColor} strokeWidth={1} />
                    <line x1="0" y1="50" x2="10" y2="50" stroke={primaryColor} strokeWidth={1} />
                    <line x1="90" y1="50" x2="100" y2="50" stroke={primaryColor} strokeWidth={1} />
                </svg>

                {/* Center Core Glass */}
                <div style={{
                    width: '60%',
                    height: '60%',
                    borderRadius: '50%',
                    background: 'rgba(0, 20, 30, 0.6)',
                    backdropFilter: 'blur(10px)',
                    border: `1px solid rgba(0, 240, 255, 0.3)`,
                    boxShadow: `inset 0 0 30px rgba(0, 240, 255, 0.2), 0 0 50px rgba(0, 240, 255, 0.1)`,
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    alignItems: 'center'
                }}>
                    {/* Scanline overlay */}
                    <div style={{
                        position: 'absolute',
                        inset: 0,
                        borderRadius: '50%',
                        background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0, 240, 255, 0.05) 2px, rgba(0, 240, 255, 0.05) 4px)',
                        pointerEvents: 'none'
                    }} />

                    <p style={{
                        color: secondaryColor,
                        fontFamily: 'monospace',
                        fontSize: `${hudSize * 0.03}px`,
                        letterSpacing: '4px',
                        margin: '0 0 10px 0',
                        textShadow: `0 0 10px ${secondaryColor}`
                    }}>
                        SYS.INIT // {frame}
                    </p>
                    <h1 style={{
                        color: 'white',
                        fontSize: `${hudSize * 0.12}px`,
                        fontWeight: 900,
                        letterSpacing: '8px',
                        margin: 0,
                        textTransform: 'uppercase',
                        textShadow: `0 0 20px ${primaryColor}, -2px 0 ${secondaryColor}, 2px 0 ${primaryColor}`
                    }}>
                        {title}
                    </h1>
                    <p style={{
                        color: primaryColor,
                        fontSize: `${hudSize * 0.05}px`,
                        fontWeight: 600,
                        letterSpacing: '10px',
                        margin: '10px 0 0 0',
                        textTransform: 'uppercase',
                        textShadow: `0 0 10px ${primaryColor}`
                    }}>
                        {subtitle}
                    </p>
                </div>
            </div>
        </div>
    );
};
