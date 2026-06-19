import React from 'react';
import { NewsTicker } from '../NewsTicker';

interface NewsSceneProps {
    headline?: string;
}

export const NewsScene: React.FC<NewsSceneProps> = ({ headline }) => {
    return (
        <NewsTicker
            headline={headline || 'Breaking News'}
            breaking={true}
        />
    );
};
