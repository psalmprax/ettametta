import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';

interface NewsTickerProps {
    headline: string;
    breaking?: boolean;
}

export const NewsTicker: React.FC<NewsTickerProps> = ({ headline, breaking = true }) => {
    const frame = useCurrentFrame();
    const { width } = useVideoConfig();

    const x = interpolate(frame, [0, 300], [width, -width * 1.5], { extrapolateRight: 'clamp' });

    const tickerHeight = `${Math.min(width * 0.08, 80)}px`;
    const labelFontSize = `${Math.min(width * 0.03, 24)}px`;
    const tickerFontSize = `${Math.min(width * 0.035, 28)}px`;

    return (
        <div style={{
            position: 'absolute',
            bottom: '100px',
            left: 0,
            right: 0,
            height: tickerHeight,
            backgroundColor: 'rgba(0,0,0,0.9)',
            display: 'flex',
            alignItems: 'center',
            overflow: 'hidden',
            borderTop: '4px solid #ff0000',
            zIndex: 100,
            boxSizing: 'border-box'
        }}>
            {breaking && (
                <div style={{
                    backgroundColor: '#ff0000',
                    color: 'white',
                    padding: '0 20px',
                    height: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    fontWeight: 900,
                    fontSize: labelFontSize,
                    textTransform: 'uppercase',
                    zIndex: 101,
                    boxShadow: '10px 0 30px rgba(0,0,0,0.5)',
                    flexShrink: 0
                }}>
                    Breaking News
                </div>
            )}
            <div style={{
                whiteSpace: 'nowrap',
                fontSize: tickerFontSize,
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
