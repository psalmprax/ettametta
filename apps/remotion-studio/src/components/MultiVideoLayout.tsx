import React from 'react';
import { AbsoluteFill, Video } from 'remotion';
import { KenBurns } from './KenBurns';

interface Clip {
    url: string;
    duration_in_frames: number;
}

interface MultiVideoLayoutProps {
    clips: Clip[];
    layout?: 'split-horizontal' | 'split-vertical' | 'grid' | 'single';
    primaryColor?: string;
    durationInFrames: number;
}

export const MultiVideoLayout: React.FC<MultiVideoLayoutProps> = ({
    clips,
    layout = 'split-vertical',
    primaryColor = '#00D4FF',
    durationInFrames
}) => {
    // Fallback if no clips
    if (!clips || clips.length === 0) {
        return null;
    }

    // Force layout to 'single' if only one clip
    const activeLayout = clips.length === 1 ? 'single' : layout;

    const renderVideo = (clip: Clip, index: number) => {
        if (!clip.url) return null;
        return (
            <KenBurns durationInFrames={durationInFrames} index={index}>
                <Video 
                    src={clip.url} 
                    muted 
                    style={{ 
                        width: '100%', 
                        height: '100%', 
                        objectFit: 'cover' 
                    }} 
                />
            </KenBurns>
        );
    };

    if (activeLayout === 'single') {
        return (
            <AbsoluteFill style={{ overflow: 'hidden' }}>
                {renderVideo(clips[0], 0)}
            </AbsoluteFill>
        );
    }

    if (activeLayout === 'split-vertical') {
        const v1 = clips[0];
        const v2 = clips[1] || clips[0]; // fallback if second is missing

        return (
            <AbsoluteFill style={{ display: 'flex', flexDirection: 'row', overflow: 'hidden' }}>
                {/* Left Clip */}
                <div style={{ flex: 1, height: '100%', position: 'relative', overflow: 'hidden' }}>
                    {renderVideo(v1, 0)}
                </div>

                {/* Neon Separator */}
                <div style={{
                    width: '6px',
                    height: '100%',
                    backgroundColor: primaryColor,
                    boxShadow: `0 0 20px ${primaryColor}, 0 0 40px ${primaryColor}`,
                    zIndex: 10,
                    position: 'relative'
                }} />

                {/* Right Clip */}
                <div style={{ flex: 1, height: '100%', position: 'relative', overflow: 'hidden' }}>
                    {renderVideo(v2, 1)}
                </div>
            </AbsoluteFill>
        );
    }

    if (activeLayout === 'split-horizontal') {
        const v1 = clips[0];
        const v2 = clips[1] || clips[0];

        return (
            <AbsoluteFill style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                {/* Top Clip */}
                <div style={{ flex: 1, width: '100%', position: 'relative', overflow: 'hidden' }}>
                    {renderVideo(v1, 0)}
                </div>

                {/* Neon Separator */}
                <div style={{
                    height: '6px',
                    width: '100%',
                    backgroundColor: primaryColor,
                    boxShadow: `0 0 20px ${primaryColor}, 0 0 40px ${primaryColor}`,
                    zIndex: 10,
                    position: 'relative'
                }} />

                {/* Bottom Clip */}
                <div style={{ flex: 1, width: '100%', position: 'relative', overflow: 'hidden' }}>
                    {renderVideo(v2, 1)}
                </div>
            </AbsoluteFill>
        );
    }


    if (activeLayout === 'grid') {
        // Render 3 clips: 1 main large, 2 smaller stacked
        const v1 = clips[0];
        const v2 = clips[1] || clips[0];
        const v3 = clips[2] || clips[0];

        return (
            <AbsoluteFill style={{ display: 'flex', flexDirection: 'row', overflow: 'hidden' }}>
                {/* Left Main Clip (60% width) */}
                <div style={{ width: '60%', height: '100%', position: 'relative', overflow: 'hidden' }}>
                    {renderVideo(v1, 0)}
                </div>

                {/* Vertical Divider */}
                <div style={{
                    width: '6px',
                    height: '100%',
                    backgroundColor: primaryColor,
                    boxShadow: `0 0 20px ${primaryColor}, 0 0 40px ${primaryColor}`,
                    zIndex: 10,
                    position: 'relative'
                }} />

                {/* Right Stacked Column (40% width) */}
                <div style={{ 
                    width: '40%', 
                    height: '100%', 
                    display: 'flex', 
                    flexDirection: 'column',
                    position: 'relative'
                }}>
                    {/* Top Right Clip */}
                    <div style={{ flex: 1, width: '100%', position: 'relative', overflow: 'hidden' }}>
                        {renderVideo(v2, 1)}
                    </div>

                    {/* Horizontal Divider */}
                    <div style={{
                        height: '6px',
                        width: '100%',
                        backgroundColor: primaryColor,
                        boxShadow: `0 0 20px ${primaryColor}, 0 0 40px ${primaryColor}`,
                        zIndex: 10,
                        position: 'relative'
                    }} />

                    {/* Bottom Right Clip */}
                    <div style={{ flex: 1, width: '100%', position: 'relative', overflow: 'hidden' }}>
                        {renderVideo(v3, 2)}
                    </div>
                </div>
            </AbsoluteFill>
        );
    }

    return null;
};
