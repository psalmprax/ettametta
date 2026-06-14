import React from 'react';
import { 
    interpolate, 
    spring, 
    useCurrentFrame, 
    useVideoConfig
} from 'remotion';

interface BrandRevealProps {
    brandName?: string;
    logoUrl?: string;
    primaryColor?: string;
    subtitle?: string;
}

export const BrandReveal: React.FC<BrandRevealProps> = ({
    brandName = "ETTAMETTA",
    logoUrl,
    primaryColor = "#00D4FF",
    subtitle
}) => {
    const frame = useCurrentFrame();
    const { width, height, fps } = useVideoConfig();

    const containerPadding = `${Math.min(width * 0.05, 45)}px ${Math.min(width * 0.08, 65)}px`;
    const containerRadius = `${Math.min(width * 0.08, 50)}px`;
    const logoDimension = `${Math.min(width * 0.25, 140)}px`;
    const brandFontSize = `${Math.min(width * 0.08, 70)}px`;
    const subtitleFontSize = `${Math.min(width * 0.03, 22)}px`;
    const brandLetterSpacing = `${Math.min(width * 0.015, 10)}px`;
    const subtitleLetterSpacing = `${Math.min(width * 0.01, 5)}px`;

    const logoSpring = spring({
        frame,
        fps,
        config: { damping: 10, stiffness: 100 }
    });

    const textSpring = spring({
        frame: frame - 15,
        fps,
        config: { damping: 12, stiffness: 100 }
    });

    const logoScale = interpolate(logoSpring, [0, 1], [0.5, 1]);
    const logoOpacity = interpolate(logoSpring, [0, 1], [0, 1]);
    
    const textTranslateY = interpolate(textSpring, [0, 1], [40, 0]);
    const textOpacity = interpolate(textSpring, [0, 1], [0, 1]);

    return (
        <div style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            width: '100%',
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 2000,
            boxSizing: 'border-box'
        }}>
            {/* Background Glow */}
            <div style={{
                position: 'absolute',
                width: '100%',
                height: '100%',
                background: `radial-gradient(circle, ${primaryColor}11 0%, transparent 70%)`,
                filter: 'blur(150px)',
                opacity: logoOpacity
            }} />

            {/* Glass Container */}
            <div style={{
                background: 'rgba(255, 255, 255, 0.03)',
                backdropFilter: 'blur(32px) saturate(200%)',
                padding: containerPadding,
                borderRadius: containerRadius,
                border: '1px solid rgba(255, 255, 255, 0.15)',
                boxShadow: '0 50px 100px rgba(0,0,0,0.5), inset 0 0 40px rgba(255,255,255,0.05)',
                transform: `scale(${logoScale})`,
                opacity: logoOpacity,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
                position: 'relative',
                overflow: 'hidden',
                maxWidth: '90%',
                boxSizing: 'border-box'
            }}>
                {/* High-Fidelity Animated Border (Match Outro) */}
                <div style={{
                    position: 'absolute',
                    inset: 0,
                    borderRadius: containerRadius,
                    padding: '3px',
                    background: `linear-gradient(135deg, ${primaryColor}99, #8E2DE299, ${primaryColor}99)`,
                    WebkitMask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
                    WebkitMaskComposite: 'xor',
                    maskComposite: 'exclude',
                    opacity: 0.5
                }} />

                {/* Logo Placeholder / Image */}
                <div style={{
                    width: logoDimension,
                    height: logoDimension,
                    marginBottom: '25px',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    position: 'relative'
                }}>
                    {logoUrl ? (
                        <img 
                            src={logoUrl} 
                            alt={`${brandName} Logo`}
                            style={{ width: '100%', height: '100%', objectFit: 'contain' }} 
                        />
                    ) : (
                        <div style={{
                            width: '100%',
                            height: '100%',
                            borderRadius: '25%',
                            background: `linear-gradient(135deg, ${primaryColor}, #8E2DE2)`,
                            boxShadow: `0 20px 40px ${primaryColor}44`
                        }}>
                            <div style={{
                                display: 'flex',
                                justifyContent: 'center',
                                alignItems: 'center',
                                height: '100%',
                                color: 'white',
                                fontSize: `calc(${logoDimension} * 0.45)`,
                                fontWeight: 900
                            }}>
                                {brandName.charAt(0)}
                            </div>
                        </div>
                    )}
                </div>

                {/* Brand Name Text */}
                <div style={{
                    transform: `translateY(${textTranslateY}px)`,
                    opacity: textOpacity,
                    textAlign: 'center',
                    maxWidth: '100%',
                    boxSizing: 'border-box'
                }}>
                    <h1 style={{
                        color: 'white',
                        fontSize: brandFontSize,
                        fontWeight: 900,
                        margin: 0,
                        letterSpacing: brandLetterSpacing,
                        textTransform: 'uppercase',
                        textShadow: `0 0 30px ${primaryColor}66`,
                        wordBreak: 'break-word',
                        whiteSpace: 'normal'
                    }}>
                        {brandName}
                    </h1>
                    <p style={{
                        color: 'rgba(255,255,255,0.6)',
                        fontSize: subtitleFontSize,
                        fontWeight: 600,
                        margin: '15px 0 0',
                        letterSpacing: subtitleLetterSpacing,
                        textTransform: 'uppercase',
                        wordBreak: 'break-word',
                        whiteSpace: 'normal'
                    }}>
                        {subtitle || (brandName === "ETTAMETTA" ? "AI Documentary Engine" : "Powered by EttaMetta")}
                    </p>
                </div>
            </div>
        </div>
    );
};
