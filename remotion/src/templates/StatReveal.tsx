import {interpolate, spring, useCurrentFrame, useVideoConfig} from "remotion";
import type React from "react";
import {fontFamily, MUTED, surface, WHITE} from "../theme";
import type {TemplateProps} from "../types";

const parseStat = (raw: unknown): {value: number; suffix: string; text: string} => {
  const text = String(raw ?? "0");
  const match = text.match(/-?\d+(\.\d+)?/);
  if (!match) return {value: 0, suffix: "", text};
  const suffix = text.slice(match.index! + match[0].length);
  return {value: Number(match[0]), suffix, text};
};

export const StatReveal: React.FC<TemplateProps> = ({section, accent}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {value, suffix, text} = parseStat(section.on_screen.stat);
  const enter = spring({frame, fps, config: {damping: 16, stiffness: 90}});
  const count = interpolate(frame, [0, 72], [0, value], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const label = String(section.on_screen.label ?? "");
  const ring = interpolate(frame, [18, 84], [0, 360], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const shown = Number.isInteger(value) ? Math.round(count).toString() : count.toFixed(1);

  return (
    <div style={{position: "absolute", inset: 0, display: "grid", placeItems: "center", fontFamily}}>
      <div style={{...surface(accent), width: 1280, height: 620, borderRadius: 8, padding: 80, position: "relative"}}>
        <svg width="420" height="420" style={{position: "absolute", right: 120, top: 95, opacity: 0.95}}>
          <circle cx="210" cy="210" r="170" stroke={`${accent}33`} strokeWidth="28" fill="none" />
          <circle
            cx="210"
            cy="210"
            r="170"
            stroke={accent}
            strokeWidth="28"
            fill="none"
            strokeDasharray={`${ring * 2.96} 1100`}
            transform="rotate(-90 210 210)"
            strokeLinecap="round"
          />
        </svg>
        <div style={{transform: `translateY(${(1 - enter) * 70}px) scale(${0.85 + enter * 0.15})`, opacity: enter}}>
          <h1 style={{margin: 0, color: WHITE, fontSize: 80, fontWeight: 900, maxWidth: 760}}>{section.key_phrase}</h1>
          <div style={{color: accent, fontSize: 168, fontWeight: 900, marginTop: 38}}>
            {Number.isFinite(value) ? `${shown}${suffix}` : text}
          </div>
          <p style={{color: MUTED, fontSize: 42, margin: "18px 0 0", lineHeight: 1.2}}>{label}</p>
        </div>
      </div>
    </div>
  );
};
