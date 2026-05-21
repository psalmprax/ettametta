import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig, spring } from 'remotion';

interface ChapterOverlayProps {
    title: string;
    primaryColor?: string;
}

export const ChapterOverlay: React.FC<ChapterOverlayProps> = ({ title, primaryColor = '#00D4FF' }) => {
    const frame = useCurrentFrame();
    const { width, height, fps } = useVideoConfig();
    
    const entry = spring({
        frame,
        fps,
        config: { damping: 12, stiffness: 100 }
    });

    const slideX = interpolate(entry, [0, 1], [-100, 0]);
    const opacity = interpolate(entry, [0, 1], [0, 1]);

    const overlayTop = `${Math.min(width * 0.05, 50)}px`;
    const overlayLeft = `${Math.min(width * 0.05, 50)}px`;
    
    const barWidth = `${Math.max(4, Math.min(width * 0.015, 10))}px`;
    const barHeight = `${Math.min(width * 0.07, 45)}px`;
    const containerRadius = `${Math.min(width * 0.02, 10)}px`;
    const containerPadding = `${Math.min(width * 0.015, 10)}px ${Math.min(width * 0.03, 20)}px`;
    const fontSizeVal = `${Math.min(width * 0.04, 26)}px`;

    // Maximum width allowed is the screen width minus safety margin (left position + bar + gap)
    const maxContainerWidth = `calc(${width}px - ${Math.min(width * 0.1, 100)}px - 60px)`;

    return (
        <div style={{
            position: 'absolute',
            top: overlayTop,
            left: overlayLeft,
            display: 'flex',
            alignItems: 'center',
            gap: '15px',
            opacity,
            transform: `translateX(${slideX}px)`,
            zIndex: 1000,
            maxWidth: maxContainerWidth,
            boxSizing: 'border-box'
        }}>
            <div style={{
                width: barWidth,
                height: barHeight,
                backgroundColor: primaryColor,
                borderRadius: '6px',
                boxShadow: `0 0 20px ${primaryColor}`,
                flexShrink: 0
            }} />
            <div style={{
                backgroundColor: 'rgba(0,0,0,0.5)',
                padding: containerPadding,
                borderRadius: containerRadius,
                backdropFilter: 'blur(10px)',
                border: '1px solid rgba(255,255,255,0.1)',
                boxSizing: 'border-box',
                overflow: 'hidden',
                display: 'flex',
                alignItems: 'center'
            }}>
                <span style={{
                    color: 'white',
                    fontSize: fontSizeVal,
                    fontWeight: 800,
                    textTransform: 'uppercase',
                    letterSpacing: '1px',
                    wordBreak: 'break-word',
                    whiteSpace: 'normal'
                }}>
                    {title}
                </span>
            </div>
        </div>
    );
};
