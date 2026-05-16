import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';

interface NewsTickerProps {
    headline: string;
    breaking?: boolean;
}

export const NewsTicker: React.FC<NewsTickerProps> = ({ headline, breaking = true }) => {
    const frame = useCurrentFrame();
    const { width } = useVideoConfig();

    const x = interpolate(frame, [0, 300], [width, -width], { extrapolateRight: 'clamp' });

    return (
        <div style={{
            position: 'absolute',
            bottom: '100px',
            left: 0,
            right: 0,
            height: '80px',
            backgroundColor: 'rgba(0,0,0,0.9)',
            display: 'flex',
            alignItems: 'center',
            overflow: 'hidden',
            borderTop: '4px solid #ff0000',
            zIndex: 100
        }}>
            {breaking && (
                <div style={{
                    backgroundColor: '#ff0000',
                    color: 'white',
                    padding: '0 30px',
                    height: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    fontWeight: 900,
                    fontSize: '28px',
                    textTransform: 'uppercase',
                    zIndex: 101,
                    boxShadow: '10px 0 30px rgba(0,0,0,0.5)'
                }}>
                    Breaking News
                </div>
            )}
            <div style={{
                whiteSpace: 'nowrap',
                fontSize: '32px',
                color: 'white',
                fontWeight: 600,
                transform: `translateX(${x}px)`,
                paddingLeft: '50px'
            }}>
                {headline} • {headline} • {headline}
            </div>
        </div>
    );
};
