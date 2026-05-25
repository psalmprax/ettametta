import React from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig, spring } from 'remotion';

export const CTAOverlay: React.FC<{ type: 'engagement' | 'cta', text: string }> = ({ type, text }) => {
    const frame = useCurrentFrame();
    const { width, height, fps } = useVideoConfig();
    
    const springValue = spring({
        frame,
        fps,
        config: { damping: 12, stiffness: 100 }
    });

    const isEngagement = type === 'engagement';

    const containerRadius = `${Math.min(width * 0.06, 40)}px`;
    const containerPadding = `${Math.min(width * 0.05, 30)}px ${Math.min(width * 0.08, 60)}px`;
    const iconWrapperSize = `${Math.min(width * 0.18, 90)}px`;
    const svgIconSize = Math.min(width * 0.09, 45);
    const headingFontSize = `${Math.min(width * 0.07, 55)}px`;
    const actionRowGap = `${Math.min(width * 0.03, 30)}px`;
    const actionFontSize = `${Math.min(width * 0.028, 18)}px`;
    const actionIconSize = Math.min(width * 0.045, 24);
    const subtextFontSize = `${Math.min(width * 0.035, 24)}px`;

    return (
        <AbsoluteFill style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            background: 'radial-gradient(circle, rgba(10,10,11,0.2) 0%, rgba(0,0,0,0.8) 100%)',
            backdropFilter: `blur(${interpolate(springValue, [0, 1], [0, 20])}px)`,
            zIndex: 100,
            boxSizing: 'border-box'
        }}>
            <div style={{
                background: 'rgba(255, 255, 255, 0.03)',
                backdropFilter: 'blur(32px) saturate(200%)',
                padding: containerPadding,
                borderRadius: containerRadius,
                border: '1px solid rgba(255, 255, 255, 0.15)',
                boxShadow: '0 50px 100px rgba(0,0,0,0.9), inset 0 0 40px rgba(255,255,255,0.05)',
                transform: `scale(${interpolate(springValue, [0, 1], [0.6, 1])}) rotateX(${interpolate(springValue, [0, 1], [20, 0])}deg)`,
                textAlign: 'center',
                position: 'relative',
                overflow: 'hidden',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                maxWidth: '90%',
                boxSizing: 'border-box'
            }}>
                {/* High-Fidelity Animated Border */}
                <div style={{
                    position: 'absolute',
                    inset: 0,
                    borderRadius: containerRadius,
                    padding: '3px',
                    background: 'linear-gradient(135deg, rgba(0, 242, 254, 0.6), rgba(142, 45, 226, 0.6), rgba(0, 242, 254, 0.6))',
                    WebkitMask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
                    WebkitMaskComposite: 'xor',
                    maskComposite: 'exclude',
                    opacity: springValue
                }} />

                <div style={{
                    width: iconWrapperSize,
                    height: iconWrapperSize,
                    background: 'rgba(255,255,255,0.1)',
                    borderRadius: `calc(${containerRadius} * 0.5)`,
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    marginBottom: '30px',
                    boxShadow: '0 20px 40px rgba(0,0,0,0.4)',
                    boxSizing: 'border-box'
                }}>
                    <svg width={svgIconSize} height={svgIconSize} viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d={isEngagement ? "M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" : "M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"} />
                        {isEngagement ? null : <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />}
                    </svg>
                </div>

                <h2 style={{
                    color: 'white',
                    fontSize: headingFontSize,
                    margin: 0,
                    fontFamily: 'Inter, sans-serif',
                    fontWeight: 900,
                    textTransform: 'uppercase',
                    letterSpacing: '-2px',
                    textShadow: '0 0 50px rgba(0, 242, 254, 0.5)',
                    lineHeight: 1.1,
                    wordBreak: 'break-word',
                    whiteSpace: 'normal',
                    maxWidth: '100%'
                }}>
                    {isEngagement ? "JOIN THE TRIBE" : "CLICK THE LINK"}
                </h2>
                
                <div style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    justifyContent: 'center',
                    gap: actionRowGap,
                    marginTop: '30px',
                    opacity: springValue,
                    maxWidth: '100%'
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#FF0000' }}>
                        <svg width={actionIconSize} height={actionIconSize} viewBox="0 0 24 24" fill="currentColor"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
                        <span style={{ color: 'white', fontSize: actionFontSize, fontWeight: 700 }}>LIKE</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#00D4FF' }}>
                        <svg width={actionIconSize} height={actionIconSize} viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>
                        <span style={{ color: 'white', fontSize: actionFontSize, fontWeight: 700 }}>SUBSCRIBE</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#FFD700' }}>
                        <svg width={actionIconSize} height={actionIconSize} viewBox="0 0 24 24" fill="currentColor"><path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"/></svg>
                        <span style={{ color: 'white', fontSize: actionFontSize, fontWeight: 700 }}>NOTIFY</span>
                    </div>
                </div>
                
                <p style={{
                    color: 'rgba(255,255,255,0.7)',
                    fontSize: subtextFontSize,
                    margin: '25px 0 0',
                    fontFamily: 'Inter, sans-serif',
                    fontWeight: 600,
                    letterSpacing: '-0.5px',
                    maxWidth: '100%',
                    wordBreak: 'break-word',
                    whiteSpace: 'normal'
                }}>
                    {text || "Don't forget to like and subscribe for more daily insights!"}
                </p>
            </div>
        </AbsoluteFill>
    );
};
