import React from 'react';

import { interpolate, useCurrentFrame } from "remotion";

export interface StaggeredFadeUpProps {
  text?: string;
  items?: string[];
  staggerDelay?: number;
  distance?: number;
  fontSize?: number;
  color?: string;
  fontWeight?: number;
  speed?: number;
  className?: string;
  background?: string;
}

export function StaggeredFadeUp({
  text = "",
  items,
  staggerDelay = 4,
  distance = 20,
  fontSize = 72,
  color = "#171717",
  fontWeight = 600,
  speed = 1,
  className,
  background = "transparent",
}: StaggeredFadeUpProps) {
  const frame = useCurrentFrame() * speed;

  const words = text ? text.split("") : [];

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background,
      }}
    >
      <span
        className={className}
        style={{
          fontSize,
          fontWeight,
          color,
          letterSpacing: "-0.03em",
          fontFamily:
            "var(--font-geist-sans), -apple-system, BlinkMacSystemFont, sans-serif",
          width: items ? "100%" : undefined,
        }}
      >
        {items ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "20px", width: "100%" }}>
            {items.map((item, idx) => {
              const local = frame - idx * staggerDelay;
              const opacity = interpolate(local, [0, 12], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              });
              const y = interpolate(local, [0, 12], [distance, 0], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              });
              return (
                <div
                  key={idx}
                  style={{
                    opacity,
                    transform: `translateY(${y}px)`,
                  }}
                >
                  {item}
                </div>
              );
            })}
          </div>
        ) : (
          words.map((word, i) => {
            const local = frame - i * staggerDelay;
            const opacity = interpolate(local, [0, 12], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            });
            const y = interpolate(local, [0, 12], [distance, 0], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            });
            return (
              <span
                key={i}
                style={{
                  display: "inline-block",
                  marginRight: "0.25em",
                  opacity,
                  transform: `translateY(${y}px)`,
                }}
              >
                {word}
              </span>
            );
          })
        )}
      </span>
    </div>
  );
}
