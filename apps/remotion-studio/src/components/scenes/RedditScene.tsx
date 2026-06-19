import React from 'react';
import { Sequence, useVideoConfig } from 'remotion';
import { RedditHook } from '../RedditHook';

interface RedditSceneProps {
    redditData?: Record<string, unknown>;
}

export const RedditScene: React.FC<RedditSceneProps> = ({ redditData }) => {
    const { fps } = useVideoConfig();

    if (!redditData) return null;

    return (
        <Sequence from={0} durationInFrames={fps * 3}>
            <RedditHook {...(redditData as any)} />
        </Sequence>
    );
};
