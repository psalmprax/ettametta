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
}

export const BrandReveal: React.FC<BrandRevealProps> = ({
    brandName = "ETTAMETTA",
    logoUrl,
    primaryColor = "#00D4FF"
}) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();



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
            // Remove solid background to allow video to show through
            zIndex: 2000
        }}>
            {/* Background Glow */}
            <div style={{
                position: 'absolute',
                width: '1000px',
                height: '1000px',
                borderRadius: '50%',
                background: `radial-gradient(circle, ${primaryColor}11 0%, transparent 70%)`,
                filter: 'blur(150px)',
                opacity: logoOpacity
            }} />

            {/* Glass Container */}
            <div style={{
                background: 'rgba(255, 255, 255, 0.03)',
                backdropFilter: 'blur(32px) saturate(200%)',
                padding: '80px 120px',
                borderRadius: '80px',
                border: '1px solid rgba(255, 255, 255, 0.15)',
                boxShadow: '0 50px 100px rgba(0,0,0,0.5), inset 0 0 40px rgba(255,255,255,0.05)',
                transform: `scale(${logoScale})`,
                opacity: logoOpacity,
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
                position: 'relative',
                overflow: 'hidden'
            }}>
                {/* High-Fidelity Animated Border (Match Outro) */}
                <div style={{
                    position: 'absolute',
                    inset: 0,
                    borderRadius: '80px',
                    padding: '3px',
                    background: `linear-gradient(135deg, ${primaryColor}99, #8E2DE299, ${primaryColor}99)`,
                    WebkitMask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)',
                    WebkitMaskComposite: 'xor',
                    maskComposite: 'exclude',
                    opacity: 0.5
                }} />

                {/* Logo Placeholder / Image */}
                <div style={{
                    width: '180px',
                    height: '180px',
                    marginBottom: '40px',
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
                            borderRadius: '40px',
                            background: `linear-gradient(135deg, ${primaryColor}, #8E2DE2)`,
                            boxShadow: `0 20px 40px ${primaryColor}44`
                        }}>
                            <div style={{
                                display: 'flex',
                                justifyContent: 'center',
                                alignItems: 'center',
                                height: '100%',
                                color: 'white',
                                fontSize: '80px',
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
                    textAlign: 'center'
                }}>
                    <h1 style={{
                        color: 'white',
                        fontSize: '100px',
                        fontWeight: 900,
                        margin: 0,
                        letterSpacing: '15px',
                        textTransform: 'uppercase',
                        textShadow: `0 0 30px ${primaryColor}66`
                    }}>
                        {brandName}
                    </h1>
                    <p style={{
                        color: 'rgba(255,255,255,0.6)',
                        fontSize: '28px',
                        fontWeight: 600,
                        margin: '15px 0 0',
                        letterSpacing: '8px',
                        textTransform: 'uppercase'
                    }}>
                        {brandName === "ETTAMETTA" ? "AI Documentary Engine" : "Powered by EttaMetta"}
                    </p>
                </div>
            </div>
        </div>
    );
};
