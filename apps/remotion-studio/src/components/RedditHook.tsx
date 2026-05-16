import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame } from 'remotion';

interface RedditHookProps {
    subreddit: string;
    title: string;
    author: string;
    upvotes: string;
}

export const RedditHook: React.FC<RedditHookProps> = ({ subreddit, title, author, upvotes }) => {
    const frame = useCurrentFrame();

    const opacity = interpolate(frame, [0, 15, 75, 90], [0, 1, 1, 0]);
    const scale = interpolate(frame, [0, 15], [0.9, 1], { extrapolateRight: 'clamp' });

    return (
        <AbsoluteFill style={{ 
            justifyContent: 'center', 
            alignItems: 'center', 
            backgroundColor: 'rgba(0,0,0,0.85)',
            opacity 
        }}>
            <div style={{
                backgroundColor: 'white',
                borderRadius: '12px',
                width: '90%',
                padding: '30px',
                transform: `scale(${scale})`,
                boxShadow: '0 30px 90px rgba(0,0,0,0.5)',
                display: 'flex',
                flexDirection: 'column',
                gap: '15px'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{ width: '40px', height: '40px', borderRadius: '50%', backgroundColor: '#FF4500' }} />
                    <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <span style={{ fontWeight: 700, fontSize: '24px', color: '#1c1c1c' }}>r/{subreddit}</span>
                        <span style={{ fontSize: '18px', color: '#7c7c7c' }}>Posted by {author}</span>
                    </div>
                </div>
                <h2 style={{ fontSize: '36px', fontWeight: 600, color: '#1c1c1c', margin: 0, lineHeight: 1.3 }}>{title}</h2>
                <div style={{ display: 'flex', gap: '20px', color: '#7c7c7c', fontWeight: 700, fontSize: '20px' }}>
                    <span>▲ {upvotes}</span>
                    <span>💬 Comments</span>
                    <span>↗ Share</span>
                </div>
            </div>
        </AbsoluteFill>
    );
};
