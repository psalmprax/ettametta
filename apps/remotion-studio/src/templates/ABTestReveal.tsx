import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export const ABTestReveal: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Spring animation for scale
  const scale = spring({
    fps,
    frame,
    config: {
      damping: 12,
      stiffness: 90,
    },
  });

  // Interpolate opacity over the first 15 frames
  const opacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{ backgroundColor: '#111827', justifyContent: 'center', alignItems: 'center' }}>
      <div
        style={{
          opacity,
          transform: `scale(${scale})`,
          color: '#38bdf8',
          fontSize: 120,
          fontWeight: 'bold',
          fontFamily: 'sans-serif',
          letterSpacing: '0.05em',
        }}
      >
        ETTAMETTA
      </div>
    </AbsoluteFill>
  );
};
