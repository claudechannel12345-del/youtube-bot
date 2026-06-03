import {
  AbsoluteFill,
  Audio,
  Sequence,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import type React from "react";
import {Background} from "./Background";
import {accentFor, fontFamily, WHITE} from "./theme";
import type {ShortProps, ShortSection} from "./types";

const safe = {
  left: 82,
  right: 82,
};

const ShortSectionView: React.FC<{section: ShortSection; index: number; fps: number}> = ({
  section,
  index,
  fps,
}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const accent = accentFor(index);
  const active =
    section.captions.find((caption) => {
      const startFrame = Math.round(caption.start * fps);
      const endFrame = Math.max(startFrame + 1, Math.round(caption.end * fps));
      return frame >= startFrame && frame < endFrame;
    }) ?? section.captions[0];
  const startFrame = active ? Math.round(active.start * fps) : 0;
  const pop = spring({
    frame: Math.max(0, frame - startFrame),
    fps,
    config: {
      damping: 16,
      stiffness: 180,
      mass: 0.7,
    },
  });
  const scale = 0.92 + pop * 0.08;
  const entry = Math.min(1, frame / 18);
  const exit = Math.min(1, (durationInFrames - frame) / 18);
  const opacity = Math.max(0, Math.min(entry, exit));

  return (
    <AbsoluteFill style={{fontFamily}}>
      {section.audioSrc ? <Audio src={staticFile(section.audioSrc)} /> : null}
      <div
        style={{
          position: "absolute",
          top: 88,
          left: safe.left,
          right: safe.right,
          minHeight: 164,
          border: `3px solid ${accent}`,
          background: "rgba(13, 13, 26, 0.82)",
          boxShadow: `0 0 46px ${accent}44`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "28px 36px",
          textAlign: "center",
        }}
      >
        <div
          style={{
            color: accent,
            fontSize: 54,
            lineHeight: 1.05,
            fontWeight: 900,
            textTransform: "uppercase",
            letterSpacing: 0,
          }}
        >
          {section.key_phrase}
        </div>
      </div>
      <div
        style={{
          position: "absolute",
          left: safe.left,
          right: safe.right,
          top: 520,
          bottom: 350,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          textAlign: "center",
          opacity,
        }}
      >
        <div
          style={{
            color: WHITE,
            fontSize: 88,
            lineHeight: 1.08,
            fontWeight: 900,
            textShadow: `0 6px 0 rgba(0,0,0,0.38), 0 0 34px ${accent}66`,
            transform: `scale(${scale})`,
            maxWidth: "100%",
            overflowWrap: "break-word",
          }}
        >
          {active?.text ?? section.key_phrase}
        </div>
      </div>
      <div
        style={{
          position: "absolute",
          left: safe.left,
          right: safe.right,
          bottom: 170,
          height: 10,
          background: "rgba(255,255,255,0.16)",
        }}
      >
        <div
          style={{
            width: `${Math.max(0, Math.min(1, frame / Math.max(durationInFrames, 1))) * 100}%`,
            height: "100%",
            background: accent,
            boxShadow: `0 0 24px ${accent}`,
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

export const Short: React.FC<ShortProps> = ({sections, fps}) => {
  let offset = 0;

  return (
    <AbsoluteFill style={{backgroundColor: "#0D0D1A"}}>
      <Background />
      {sections.map((section, index) => {
        const from = offset;
        offset += section.durationInFrames;
        return (
          <Sequence
            key={`${section.audioSrc}-${index}`}
            from={from}
            durationInFrames={section.durationInFrames}
          >
            <ShortSectionView section={section} index={index} fps={fps || 30} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
