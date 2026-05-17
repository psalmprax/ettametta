import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame } from 'remotion';

interface KenBurnsProps {
    children: React.ReactNode;
    durationInFrames: number;
    index: number;
}

export const KenBurns: React.FC<KenBurnsProps> = ({ children, durationInFrames, index }) => {
    const frame = useCurrentFrame();
    
    // Create variety based on index
    const directions = [
        { x: [-2, 2], y: [-2, 2], scale: [1.1, 1.25] },   // TL -> BR
        { x: [2, -2], y: [-2, 2], scale: [1.1, 1.25] },   // TR -> BL
        { x: [0, 0], y: [-3, 3], scale: [1.05, 1.2] },    // Top -> Bottom
        { x: [-3, 3], y: [0, 0], scale: [1.15, 1.05] },   // Out -> In
    ];
    
    const dir = directions[index % directions.length];
    
    const safeDuration = Math.max(1, durationInFrames);
    
    const scale = interpolate(frame, [0, safeDuration], dir.scale, { extrapolateRight: 'clamp' });
    const translateX = interpolate(frame, [0, safeDuration], dir.x, { extrapolateRight: 'clamp' });
    const translateY = interpolate(frame, [0, safeDuration], dir.y, { extrapolateRight: 'clamp' });

    return (
        <AbsoluteFill style={{
            transform: `scale(${scale}) translateX(${translateX}%) translateY(${translateY}%)`,
            overflow: 'hidden'
        }}>
            {children}
        </AbsoluteFill>
    );
};
