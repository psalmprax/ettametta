import React from 'react';

export const PodcastOverlay: React.FC = () => {
    return (
        <div style={{
            position: 'absolute', top: '20px', right: '20px',
            padding: '8px 16px', backgroundColor: 'rgba(0,0,0,0.6)',
            borderRadius: '20px', color: 'white', fontSize: '14px',
            zIndex: 50
        }}>
            PODCAST
        </div>
    );
};
