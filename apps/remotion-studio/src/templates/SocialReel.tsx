import React from 'react';
import { AbsoluteFill, Sequence, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { InfiniteMarquee, MatrixDecode, StaggeredFadeUp, TrackingIn } from '../components/remocn';

export const SocialReel: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
    frame,
    fps,
    config: { damping: 12 },
  });

  return (
    <AbsoluteFill style={{ backgroundColor: '#09090b', color: 'white' }}>
      
      {/* Background Marquee */}
      <AbsoluteFill style={{ opacity: 0.1, transform: 'rotate(-10deg) scale(1.5)', justifyContent: 'center' }}>
        <InfiniteMarquee text="TRENDING NOW • GO VIRAL • TRENDING NOW • GO VIRAL • " speed={4} />
      </AbsoluteFill>
      
      <Sequence from={0} durationInFrames={45}>
        <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
          <div style={{ transform: `scale(${scale})`, textAlign: 'center' }}>
            <h1 style={{ fontSize: '120px', fontWeight: '900', textTransform: 'uppercase', lineHeight: '1.1' }}>
              <TrackingIn text="STOP" />
              <br />
              <span style={{ color: '#ec4899' }}>SCROLLING</span>
            </h1>
          </div>
        </AbsoluteFill>
      </Sequence>

      <Sequence from={45} durationInFrames={60}>
        <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center', padding: '60px' }}>
          <h2 style={{ fontSize: '80px', fontWeight: 'bold', textAlign: 'center' }}>
            <MatrixDecode text="You need to see this." />
          </h2>
        </AbsoluteFill>
      </Sequence>

      <Sequence from={105} durationInFrames={75}>
        <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center', padding: '60px' }}>
          <div style={{ fontSize: '60px', fontWeight: 'bold', textAlign: 'left', width: '100%' }}>
            <StaggeredFadeUp 
              items={[
                "🔥 Secret strategy revealed",
                "📈 10x your engagement",
                "⏱️ Takes just 5 minutes"
              ]} 
              staggerDelay={10} 
            />
          </div>
        </AbsoluteFill>
      </Sequence>

    </AbsoluteFill>
  );
};
