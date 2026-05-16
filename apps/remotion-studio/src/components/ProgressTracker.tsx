import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';

interface ProgressTrackerProps {
    primaryColor?: string;
}

export const ProgressTracker: React.FC<ProgressTrackerProps> = ({ primaryColor = '#00D4FF' }) => {
    const frame = useCurrentFrame();
    const { durationInFrames } = useVideoConfig();
    
    const progress = (frame / durationInFrames) * 100;

    return (
        <div style={{
            position: 'absolute',
            bottom: '40px',
            left: '100px',
            right: '100px',
            height: '10px',
            backgroundColor: 'rgba(255,255,255,0.1)',
            borderRadius: '5px',
            overflow: 'hidden',
            zIndex: 1000,
            backdropFilter: 'blur(5px)'
        }}>
            <div style={{
                width: `${progress}%`,
                height: '100%',
                backgroundColor: primaryColor,
                boxShadow: `0 0 15px ${primaryColor}`,
                transition: 'width 0.1s linear'
            }} />
        </div>
    );
};
