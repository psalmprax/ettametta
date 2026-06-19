import React from 'react';
import { ThreeCanvas } from '@remotion/three';
import { BrandReveal } from '../BrandReveal';
import { CyberpunkHUD } from '../CyberpunkHUD';
import { IridescentGlass } from '../IridescentGlass';
import { AncientPortal } from '../AncientPortal';
import { AncientAstrolabe } from '../AncientAstrolabe';
import { LiquidMetalSphere } from '../LiquidMetalSphere';

interface IntroSceneProps {
    type: string;
    title?: string;
    subtitle?: string;
    brandName?: string;
    primaryColor?: string;
    logoUrl?: string;
}

const ThreeCanvasIntro: React.FC<{
    primaryColor?: string;
    fov?: number;
    cameraPosition?: [number, number, number];
    children: React.ReactNode;
    titleText: string;
    subtitleText: string;
    color: string;
    glowShadow: string;
}> = ({ primaryColor, fov = 60, cameraPosition = [0, 0, 5], children, titleText, subtitleText, color, glowShadow }) => (
    <>
        <ThreeCanvas
            width={1080}
            height={1920}
            orthographic={false}
            camera={{ fov, position: cameraPosition }}
            style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
        >
            {children}
        </ThreeCanvas>
        <div style={{
            position: 'absolute', bottom: '15%', width: '100%', textAlign: 'center', zIndex: 10,
            display: 'flex', flexDirection: 'column', alignItems: 'center'
        }}>
            <h1 style={{
                color: 'white', fontSize: '60px', fontWeight: 300, letterSpacing: '15px',
                margin: 0, textTransform: 'uppercase',
                textShadow: glowShadow
            }}>
                {titleText}
            </h1>
            <p style={{
                color, fontSize: '24px', fontWeight: 400,
                letterSpacing: '8px', margin: '15px 0 0 0', textTransform: 'uppercase',
                textShadow: primaryColor ? `0 0 20px ${primaryColor}44` : undefined
            }}>
                {subtitleText}
            </p>
        </div>
    </>
);

export const IntroScene: React.FC<IntroSceneProps> = ({
    type, title, subtitle, brandName, primaryColor, logoUrl
}) => {
    const displayTitle = brandName || title || 'ETTAMETTA';
    const displaySubtitle = subtitle || 'AI Documentary Engine';

    switch (type) {
        case 'cyberpunk':
            return (
                <CyberpunkHUD
                    title={displayTitle}
                    subtitle={displaySubtitle}
                    primaryColor={primaryColor || '#00F0FF'}
                    secondaryColor="#FF003C"
                />
            );

        case 'iridescent':
            return (
                <IridescentGlass
                    title={displayTitle}
                    subtitle={displaySubtitle}
                />
            );

        case 'portal':
            return (
                <ThreeCanvasIntro
                    primaryColor={primaryColor}
                    titleText={displayTitle}
                    subtitleText={displaySubtitle}
                    color="#FFA07A"
                    glowShadow="0 0 40px rgba(255, 69, 0, 0.8)"
                >
                    <AncientPortal primaryColor={primaryColor || '#FF4500'} />
                </ThreeCanvasIntro>
            );

        case 'astrolabe':
            return (
                <ThreeCanvasIntro
                    primaryColor={primaryColor}
                    fov={45}
                    cameraPosition={[0, 0, 12]}
                    titleText={displayTitle}
                    subtitleText={displaySubtitle}
                    color="rgba(255,255,255,0.7)"
                    glowShadow={`0 0 30px ${primaryColor || '#FFD700'}88`}
                >
                    <AncientAstrolabe primaryColor={primaryColor || '#FFD700'} />
                </ThreeCanvasIntro>
            );

        case 'liquid_metal':
            return (
                <ThreeCanvasIntro
                    primaryColor={primaryColor}
                    fov={45}
                    cameraPosition={[0, 0, 5]}
                    titleText={displayTitle}
                    subtitleText={displaySubtitle}
                    color="rgba(0,212,255,0.7)"
                    glowShadow={`0 0 40px ${primaryColor || '#00D4FF'}66`}
                >
                    <LiquidMetalSphere primaryColor={primaryColor || '#00D4FF'} />
                </ThreeCanvasIntro>
            );

        case 'brand_reveal':
        default:
            return (
                <BrandReveal
                    brandName={brandName}
                    logoUrl={logoUrl}
                    primaryColor={primaryColor}
                />
            );
    }
};
