import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig, spring } from 'remotion';

export const CTAOverlay: React.FC<{ type: 'engagement' | 'cta', text: string }> = ({ type, text }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    
    const springValue = spring({
        frame,
        fps,
        config: { stiffness: 100 }
    });

    const isEngagement = type === 'engagement';

    return (
        <AbsoluteFill style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            background: 'rgba(10, 10, 11, 0.4)',
            zIndex: 100
        }}>
            <div style={{
                background: 'rgba(255, 255, 255, 0.05)',
                backdropFilter: 'blur(24px) saturate(180%)',
                padding: '40px 80px',
                borderRadius: '40px',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                boxShadow: '0 40px 80px rgba(0,0,0,0.8)',
                transform: `scale(${interpolate(springValue, [0, 1], [0.5, 1.2])})`,
                textAlign: 'center',
                position: 'relative',
                overflow: 'hidden'
            }}>
                {/* Iridescent Border Simulation */}
                <div style={{
                    position: 'absolute',
                    inset: 0,
                    borderRadius: '40px',
                    padding: '2px',
                    background: 'linear-gradient(135deg, rgba(0, 242, 254, 0.4), rgba(142, 45, 226, 0.4))',
                    WebkitMask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
                    WebkitMaskComposite: 'xor',
                    maskComposite: 'exclude',
                }} />

                <h2 style={{
                    color: '#00F2FE',
                    fontSize: '90px',
                    margin: 0,
                    fontFamily: 'Inter, sans-serif',
                    fontWeight: 900,
                    textTransform: 'uppercase',
                    letterSpacing: '-0.02em',
                    textShadow: '0 0 40px rgba(0, 242, 254, 0.5)'
                }}>
                    {isEngagement ? 'LIKE & SUB' : 'LINK IN BIO'}
                </h2>
                <p style={{
                    color: 'white',
                    fontSize: '42px',
                    margin: '16px 0 0',
                    fontFamily: 'Inter, sans-serif',
                    fontWeight: 600,
                    opacity: 0.8
                }}>
                    {text}
                </p>
            </div>
        </AbsoluteFill>
    );
};
