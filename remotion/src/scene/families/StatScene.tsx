import {Easing, interpolate} from "remotion";
import type React from "react";
import {ACCENTS, fontFamily, MUTED, WHITE} from "../../theme";
import {cueProgress, type CueBeat} from "../CueTimeline";
import type {AnchorMap} from "../anchors";

type StatSceneProps = {
  frame: number;
  fps: number;
  anchors: AnchorMap;
  beats: CueBeat[];
  accent: string;
  title: string;
  label: string;
  targetValue: number;
};

const ringRadius = 212;
const circumference = Math.PI * 2 * ringRadius;

export const StatScene: React.FC<StatSceneProps> = ({
  frame,
  fps,
  anchors,
  beats,
  accent,
  title,
  label,
  targetValue,
}) => {
  const countBeat = beats.find((beat) => beat.kind === "count");
  const traceBeat = beats.find((beat) => beat.kind === "trace");
  const labelBeat = beats.find((beat) => beat.kind === "label");
  const countProgress = countBeat ? cueProgress(countBeat, fps, frame) : 1;
  const traceProgress = traceBeat ? cueProgress(traceBeat, fps, frame) : countProgress;
  const easedCount = Easing.out(Easing.cubic)(countProgress);
  const count = Math.round(interpolate(easedCount, [0, 1], [0, targetValue]));
  const labelOn = labelBeat ? frame / fps >= labelBeat.time : countProgress >= 1;
  const headline = anchors.headline;
  const stat = anchors["stat.main"];
  const drift = Math.sin(frame / 42) * 8;
  const tickSpin = frame * 0.18;

  return (
    <div style={{position: "absolute", inset: 0, fontFamily, color: WHITE}}>
      <div
        style={{
          position: "absolute",
          left: headline.px,
          top: headline.py,
          width: 1120,
          transform: `translate(-50%, -50%) translateY(${Math.sin(frame / 58) * 5}px)`,
          textAlign: "center",
          fontSize: 64,
          fontWeight: 900,
          letterSpacing: 0,
          lineHeight: 1.04,
          textShadow: `0 0 24px ${accent}44`,
        }}
      >
        {title}
      </div>
      <svg
        width={1920}
        height={1080}
        viewBox="0 0 1920 1080"
        style={{position: "absolute", inset: 0, overflow: "visible"}}
      >
        <g transform={`translate(${stat.px} ${stat.py + drift})`}>
          <circle r={288} fill="rgba(13,13,26,0.38)" stroke={`${accent}2f`} strokeWidth={2} />
          <circle
            r={ringRadius}
            fill="none"
            stroke="rgba(255,255,255,0.14)"
            strokeWidth={20}
          />
          <circle
            r={ringRadius}
            fill="none"
            stroke={accent}
            strokeWidth={20}
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={circumference * (1 - Easing.inOut(Easing.cubic)(traceProgress))}
            transform="rotate(-90)"
          />
          {Array.from({length: 18}, (_, i) => {
            const angle = ((i / 18) * Math.PI * 2) + tickSpin * (Math.PI / 180);
            const radius = 282 + Math.sin(frame / 26 + i) * 8;
            return (
              <circle
                key={i}
                cx={Math.cos(angle) * radius}
                cy={Math.sin(angle) * radius}
                r={i % 3 === 0 ? 4 : 2.5}
                fill={ACCENTS[i % ACCENTS.length]}
                opacity={0.3 + (i % 4) * 0.08}
              />
            );
          })}
        </g>
      </svg>
      <div
        style={{
          position: "absolute",
          left: stat.px,
          top: stat.py + drift - 18,
          transform: "translate(-50%, -50%)",
          width: 760,
          textAlign: "center",
          fontSize: 178,
          fontWeight: 900,
          letterSpacing: 0,
          lineHeight: 0.9,
          textShadow: `0 0 32px ${accent}66`,
        }}
      >
        {count.toLocaleString("en-US")}
      </div>
      <div
        style={{
          position: "absolute",
          left: stat.px,
          top: stat.py + 372 + drift,
          transform: `translate(-50%, -50%) scale(${labelOn ? 1 : 0.86})`,
          opacity: labelOn ? 1 : 0,
          width: 1040,
          paddingLeft: 72,
          paddingRight: 72,
          boxSizing: "border-box",
          textAlign: "center",
          color: MUTED,
          fontSize: 38,
          fontWeight: 800,
          letterSpacing: 0,
          lineHeight: 1.22,
        }}
      >
        {label}
      </div>
    </div>
  );
};
