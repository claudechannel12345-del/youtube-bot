import {AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig} from "remotion";
import type React from "react";
import {BG, ACCENTS} from "./theme";

const particles = Array.from({length: 70}, (_, i) => ({
  left: (i * 137) % 1920,
  top: (i * 211) % 1080,
  size: 2 + (i % 5),
  speed: 0.15 + (i % 7) * 0.03,
  color: ACCENTS[i % ACCENTS.length],
}));

export const Background: React.FC = () => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const spin = interpolate(frame % 360, [0, 360], [0, 360]);
  const glow = interpolate(
    Math.sin((frame / Math.max(durationInFrames, 1)) * Math.PI * 2),
    [-1, 1],
    [0.35, 0.72],
  );

  return (
    <AbsoluteFill style={{backgroundColor: BG, overflow: "hidden"}}>
      <div
        style={{
          position: "absolute",
          inset: -120,
          background:
            "radial-gradient(circle at 25% 15%, rgba(155,93,229,0.18), transparent 32%), radial-gradient(circle at 78% 72%, rgba(6,214,160,0.12), transparent 34%)",
          opacity: glow,
          transform: `rotate(${spin * 0.02}deg) scale(1.05)`,
        }}
      />
      {particles.map((p, i) => {
        const drift = (frame * p.speed + i * 17) % 120;
        const opacity = 0.18 + ((i % 6) * 0.04);
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: p.left,
              top: p.top,
              width: p.size,
              height: p.size,
              borderRadius: "50%",
              backgroundColor: p.color,
              opacity,
              transform: `translate(${Math.sin((frame + i) / 48) * 22}px, ${drift - 60}px)`,
              boxShadow: `0 0 ${p.size * 5}px ${p.color}`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
