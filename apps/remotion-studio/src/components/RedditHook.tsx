import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';

interface RedditHookProps {
    subreddit: string;
    title: string;
    author: string;
    upvotes: string;
}

export const RedditHook: React.FC<RedditHookProps> = ({ subreddit, title, author, upvotes }) => {
    const frame = useCurrentFrame();
    const { width, height } = useVideoConfig();

    const opacity = interpolate(frame, [0, 15, 75, 90], [0, 1, 1, 0]);
    const scale = interpolate(frame, [0, 15], [0.9, 1], { extrapolateRight: 'clamp' });

    const cardPadding = `${Math.min(width * 0.05, 30)}px`;
    const avatarSize = `${Math.min(width * 0.08, 40)}px`;
    const subredditFontSize = `${Math.min(width * 0.045, 24)}px`;
    const authorFontSize = `${Math.min(width * 0.035, 18)}px`;
    const titleFontSize = `${Math.min(width * 0.065, 34)}px`;
    const statsFontSize = `${Math.min(width * 0.038, 20)}px`;
    const cardGap = `${Math.min(width * 0.03, 15)}px`;

    return (
        <AbsoluteFill style={{ 
            justifyContent: 'center', 
            alignItems: 'center', 
            backgroundColor: 'rgba(0,0,0,0.85)',
            opacity,
            boxSizing: 'border-box'
        }}>
            <div style={{
                backgroundColor: 'white',
                borderRadius: '12px',
                width: '90%',
                maxWidth: '90%',
                padding: cardPadding,
                transform: `scale(${scale})`,
                boxShadow: '0 30px 90px rgba(0,0,0,0.5)',
                display: 'flex',
                flexDirection: 'column',
                gap: cardGap,
                boxSizing: 'border-box'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', width: '100%' }}>
                    <div style={{ 
                        width: avatarSize, 
                        height: avatarSize, 
                        borderRadius: '50%', 
                        backgroundColor: '#FF4500',
                        flexShrink: 0
                    }} />
                    <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
                        <span style={{ 
                            fontWeight: 700, 
                            fontSize: subredditFontSize, 
                            color: '#1c1c1c',
                            wordBreak: 'break-word',
                            whiteSpace: 'normal'
                        }}>
                            r/{subreddit}
                        </span>
                        <span style={{ 
                            fontSize: authorFontSize, 
                            color: '#7c7c7c',
                            wordBreak: 'break-word',
                            whiteSpace: 'normal'
                        }}>
                            Posted by {author}
                        </span>
                    </div>
                </div>
                <h2 style={{ 
                    fontSize: titleFontSize, 
                    fontWeight: 600, 
                    color: '#1c1c1c', 
                    margin: 0, 
                    lineHeight: 1.3,
                    wordBreak: 'break-word',
                    whiteSpace: 'normal',
                    width: '100%'
                }}>{title}</h2>
                <div style={{ 
                    display: 'flex', 
                    flexWrap: 'wrap',
                    gap: '15px', 
                    color: '#7c7c7c', 
                    fontWeight: 700, 
                    fontSize: statsFontSize,
                    width: '100%'
                }}>
                    <span>▲ {upvotes}</span>
                    <span>💬 Comments</span>
                    <span>↗ Share</span>
                </div>
            </div>
        </AbsoluteFill>
    );
};
