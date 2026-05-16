import React from 'react';
import { 
    AbsoluteFill, 
    interpolate, 
    spring, 
    useCurrentFrame, 
    useVideoConfig 
} from 'remotion';

export type TransitionType = 'zoom' | 'blur' | 'slide' | 'fade' | 'none';

interface SceneTransitionProps {
    children: React.ReactNode;
    type?: TransitionType;
    durationInFrames: number;
}

export const SceneTransition: React.FC<SceneTransitionProps> = ({ 
    children, 
    type = 'zoom',
    durationInFrames 
}) => {
    const frame = useCurrentFrame();
    const { fps, width } = useVideoConfig();

    // 1. Entry Animation (Spring-based)
    const entryProgress = spring({
        frame,
        fps,
        config: {
            damping: 12,
            mass: 0.5,
            stiffness: 100,
        },
    });

    // 2. Exit Animation (Last 15 frames)
    const exitThreshold = durationInFrames - 15;
    const exitProgress = spring({
        frame: frame - exitThreshold,
        fps,
        config: {
            damping: 15,
            mass: 0.8,
            stiffness: 120,
        },
    });

    // --- Transition Logics ---
    
    let style: React.CSSProperties = {};

    if (type === 'zoom') {
        const scale = interpolate(entryProgress, [0, 1], [0.9, 1]);
        const exitScale = interpolate(exitProgress, [0, 1], [1, 1.1]);
        const opacity = interpolate(entryProgress, [0, 1], [0, 1]);
        const exitOpacity = interpolate(exitProgress, [0, 1], [1, 0]);
        
        style = {
            transform: `scale(${exitProgress > 0 ? exitScale : scale})`,
            opacity: exitProgress > 0 ? exitOpacity : opacity,
        };
    } else if (type === 'blur') {
        const blur = interpolate(entryProgress, [0, 1], [20, 0]);
        const exitBlur = interpolate(exitProgress, [0, 1], [0, 20]);
        const opacity = interpolate(entryProgress, [0, 1], [0, 1]);
        
        style = {
            filter: `blur(${exitProgress > 0 ? exitBlur : blur}px)`,
            opacity: exitProgress > 0 ? (1 - exitProgress) : opacity,
        };
    } else if (type === 'slide') {
        const translateX = interpolate(entryProgress, [0, 1], [width, 0]);
        const exitTranslateX = interpolate(exitProgress, [0, 1], [0, -width]);
        
        style = {
            transform: `translateX(${exitProgress > 0 ? exitTranslateX : translateX}px)`,
        };
    } else if (type === 'fade') {
        const opacity = interpolate(entryProgress, [0, 1], [0, 1]);
        const exitOpacity = interpolate(exitProgress, [0, 1], [1, 0]);
        
        style = {
            opacity: exitProgress > 0 ? exitOpacity : opacity,
        };
    }

    return (
        <AbsoluteFill style={{ ...style, overflow: 'hidden' }}>
            {children}
        </AbsoluteFill>
    );
};
