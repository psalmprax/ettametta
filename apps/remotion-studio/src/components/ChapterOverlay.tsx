import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig, spring } from 'remotion';

interface ChapterOverlayProps {
    title: string;
    primaryColor?: string;
}

export const ChapterOverlay: React.FC<ChapterOverlayProps> = ({ title, primaryColor = '#00D4FF' }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    
    const entry = spring({
        frame,
        fps,
        config: { damping: 12, stiffness: 100 }
    });

    const slideX = interpolate(entry, [0, 1], [-100, 0]);
    const opacity = interpolate(entry, [0, 1], [0, 1]);

    return (
        <div style={{
            position: 'absolute',
            top: '80px',
            left: '80px',
            display: 'flex',
            alignItems: 'center',
            gap: '20px',
            opacity,
            transform: `translateX(${slideX}px)`,
            zIndex: 1000,
        }}>
            <div style={{
                width: '12px',
                height: '60px',
                backgroundColor: primaryColor,
                borderRadius: '6px',
                boxShadow: `0 0 20px ${primaryColor}`
            }} />
            <div style={{
                backgroundColor: 'rgba(0,0,0,0.5)',
                padding: '10px 30px',
                borderRadius: '10px',
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(255,255,255,0.1)'
            }}>
                <span style={{
                    color: 'white',
                    fontSize: '36px',
                    fontWeight: 800,
                    textTransform: 'uppercase',
                    letterSpacing: '2px'
                }}>
                    {title}
                </span>
            </div>
        </div>
    );
};
