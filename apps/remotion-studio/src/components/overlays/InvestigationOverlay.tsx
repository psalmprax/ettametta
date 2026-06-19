import React from 'react';

interface InvestigationOverlayProps {
    title?: string;
}

export const InvestigationOverlay: React.FC<InvestigationOverlayProps> = ({ title }) => {
    return (
        <div style={{
            position: 'absolute', top: '10px', left: '10px',
            padding: '6px 12px', backgroundColor: 'rgba(0,255,0,0.15)',
            border: '1px solid rgba(0,255,0,0.4)', borderRadius: '4px',
            color: '#0f0', fontSize: '14px', fontFamily: 'monospace',
            zIndex: 50
        }}>
            INVESTIGATION: {title || 'CLASSIFIED'}
        </div>
    );
};
