import React from 'react';
import { AbsoluteFill, Sequence, useCurrentFrame } from 'remotion';
import { DirectionalWipe, InfiniteMarquee, MatrixDecode, Typewriter } from '../components/remocn';

export const NewsTicker: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: '#1e293b', color: 'white', overflow: 'hidden' }}>
      
      {/* Main Broadcast Content */}
      <Sequence from={0} durationInFrames={300}>
        <AbsoluteFill style={{ padding: '60px', paddingBottom: '200px' }}>
          <div style={{ width: '80%', padding: '40px', background: 'rgba(0,0,0,0.5)', borderRadius: '16px', borderLeft: '8px solid #ef4444' }}>
            <h1 style={{ fontSize: '60px', color: '#ef4444', textTransform: 'uppercase', marginBottom: '20px' }}>
              <Typewriter text="BREAKING NEWS" />
            </h1>
            <h2 style={{ fontSize: '48px', fontWeight: 'normal' }}>
              <MatrixDecode text="Major developments in the technology sector as new AI models are released to the public." />
            </h2>
          </div>
        </AbsoluteFill>
      </Sequence>

      {/* Lower Third Ticker */}
      <Sequence from={30} durationInFrames={270}>
        <DirectionalWipe 
          direction="right" 
          transitionStart={0} 
          transitionDuration={15}
          background="transparent"
          style={{ position: 'absolute', bottom: '80px', left: 0, width: '100%', height: '80px' }}
          from={<div />}
          to={
            <div style={{ position: 'absolute', inset: 0, backgroundColor: '#ef4444', display: 'flex', alignItems: 'center' }}>
              <div style={{ backgroundColor: 'white', color: '#ef4444', fontWeight: 'bold', fontSize: '40px', padding: '0 40px', height: '100%', display: 'flex', alignItems: 'center', zIndex: 10 }}>
                LIVE
              </div>
              <div style={{ flex: 1, overflow: 'hidden' }}>
                <InfiniteMarquee text="GLOBAL MARKETS RALLY AS TECH STOCKS SURGE • NEW AI CAPABILITIES ANNOUNCED • " speed={6} />
              </div>
            </div>
          }
        />
      </Sequence>

    </AbsoluteFill>
  );
};
