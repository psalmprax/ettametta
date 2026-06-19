import React from 'react';

export const RetroOverlay: React.FC = () => {
    return (
        <div style={{
            position: 'absolute', bottom: '60px', right: '20px',
            padding: '4px 8px', backgroundColor: 'rgba(0,0,0,0.5)',
            color: '#0f0', fontSize: '16px', fontFamily: 'monospace',
            zIndex: 50
        }}>
            REC {new Date().toLocaleDateString()}
        </div>
    );
};
