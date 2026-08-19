import React from 'react';
import { AbsoluteFill, Img, Sequence, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { MeshGradientBg, PerCharacterRise, SpotlightCard, ZoomThroughTransition } from '../components/remocn';

export const ProductShowcase: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const titleScale = spring({
    frame,
    fps,
    config: { damping: 12 },
  });

  return (
    <AbsoluteFill style={{ backgroundColor: '#0f172a', color: 'white' }}>
      <MeshGradientBg colors={['#38bdf8', '#818cf8', '#c084fc']} speed={0.5} />
      
      <Sequence from={0} durationInFrames={60}>
        <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
          <div style={{ transform: `scale(${titleScale})`, textAlign: 'center' }}>
            <h1 style={{ fontSize: '100px', fontWeight: 'bold', margin: 0, padding: 0 }}>
              <PerCharacterRise text="New Arrival" delay={10} />
            </h1>
            <p style={{ fontSize: '40px', color: '#cbd5e1' }}>
              <PerCharacterRise text="Discover the ultimate experience." delay={30} />
            </p>
          </div>
        </AbsoluteFill>
      </Sequence>

      <Sequence from={50} durationInFrames={120}>
        <ZoomThroughTransition>
          <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center', display: 'flex', flexDirection: 'row', gap: '40px' }}>
            <SpotlightCard cardWidth={400} cardHeight={600} style={{ borderRadius: '24px', padding: '20px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}>
              <div style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div style={{ flex: 1, backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: '12px' }} />
                <h2 style={{ fontSize: '32px', marginTop: '20px' }}>Product Alpha</h2>
                <p style={{ fontSize: '24px', color: '#94a3b8' }}>$299.00</p>
              </div>
            </SpotlightCard>
            <SpotlightCard cardWidth={400} cardHeight={600} style={{ borderRadius: '24px', padding: '20px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}>
              <div style={{ height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div style={{ flex: 1, backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: '12px' }} />
                <h2 style={{ fontSize: '32px', marginTop: '20px' }}>Product Beta</h2>
                <p style={{ fontSize: '24px', color: '#94a3b8' }}>$399.00</p>
              </div>
            </SpotlightCard>
          </AbsoluteFill>
        </ZoomThroughTransition>
      </Sequence>
    </AbsoluteFill>
  );
};
