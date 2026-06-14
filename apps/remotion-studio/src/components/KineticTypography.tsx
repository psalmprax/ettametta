import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig, spring } from 'remotion';

export const KineticTypography: React.FC<{ primaryColor: string, title: string, subtitle: string }> = ({ primaryColor, title, subtitle }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    // Brutalist entrance animations
    const titleEnter = spring({
        frame,
        fps,
        config: { damping: 12, mass: 2, stiffness: 150 },
    });

    const subtitleEnter = spring({
        frame: frame - 15,
        fps,
        config: { damping: 10, mass: 1, stiffness: 200 },
    });

    // Continuous chaotic scaling
    const scale = interpolate(frame, [0, 60], [1, 1.05], {
        extrapolateRight: 'clamp'
    });

    return (
        <div style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            backgroundColor: '#000000',
            width: '100%',
            height: '100%',
            overflow: 'hidden',
        }}>
            {/* Title Container with Clipping */}
            <div style={{ overflow: 'hidden' }}>
                <h1 style={{
                    color: '#ffffff',
                    fontSize: '200px',
                    fontFamily: 'Helvetica, Arial, sans-serif',
                    fontWeight: 900,
                    textTransform: 'uppercase',
                    lineHeight: 0.9,
                    margin: 0,
                    transform: `translateY(${(1 - titleEnter) * 100}%) scale(${scale})`,
                    letterSpacing: '-5px'
                }}>
                    {title}
                </h1>
            </div>

            {/* Inverted Subtitle */}
            <div style={{ 
                overflow: 'hidden',
                backgroundColor: primaryColor,
                padding: '20px 40px',
                marginTop: '30px',
                transform: `rotate(${interpolate(subtitleEnter, [0, 1], [10, -2])}deg) scale(${subtitleEnter})`
            }}>
                <h2 style={{
                    color: '#000000',
                    fontSize: '60px',
                    fontFamily: 'Helvetica, Arial, sans-serif',
                    fontWeight: 800,
                    textTransform: 'uppercase',
                    margin: 0,
                    letterSpacing: '2px'
                }}>
                    {subtitle}
                </h2>
            </div>
            
            {/* Background Kinetic Elements */}
            <div style={{
                position: 'absolute',
                top: '-10%',
                left: '-10%',
                fontSize: '400px',
                fontWeight: 900,
                color: 'rgba(255,255,255,0.03)',
                transform: `rotate(${frame * 0.1}deg)`,
                pointerEvents: 'none',
                zIndex: 0
            }}>
                {title}
            </div>
        </div>
    );
};
