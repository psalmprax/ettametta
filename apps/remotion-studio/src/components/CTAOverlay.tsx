import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig, Spring } from 'remotion';

export const CTAOverlay: React.FC<{ type: 'engagement' | 'cta', text: string }> = ({ type, text }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    
    const spring = Spring({
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
            background: 'rgba(0,0,0,0.4)',
            zIndex: 100
        }}>
            <div style={{
                backgroundColor: isEngagement ? '#ff0000' : '#FFD700',
                padding: '40px 80px',
                borderRadius: '50px',
                boxShadow: '0 0 50px rgba(0,0,0,0.5)',
                transform: `scale(${interpolate(spring, [0, 1], [0.5, 1.2])})`,
                textAlign: 'center'
            }}>
                <h2 style={{
                    color: isEngagement ? 'white' : 'black',
                    fontSize: '80px',
                    margin: 0,
                    fontFamily: 'Arial Black',
                    textTransform: 'uppercase'
                }}>
                    {isEngagement ? '👍 LIKE & SUB! 🔔' : '🔗 LINK IN BIO! 💰'}
                </h2>
                <p style={{
                    color: isEngagement ? 'white' : 'black',
                    fontSize: '40px',
                    margin: '10px 0 0',
                    fontFamily: 'Arial',
                    fontWeight: 'bold'
                }}>
                    {text}
                </p>
            </div>
        </AbsoluteFill>
    );
};
