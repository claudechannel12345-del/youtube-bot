import {interpolate, spring, useCurrentFrame, useVideoConfig} from "remotion";
import type React from "react";
import {fontFamily, MUTED, WHITE} from "../theme";
import type {TemplateProps} from "../types";

export const Diagram: React.FC<TemplateProps> = ({section, accent}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const parts = Array.isArray(section.on_screen.parts) ? section.on_screen.parts.map(String).slice(0, 6) : [];
  const core = spring({frame, fps, config: {damping: 16, stiffness: 100}});

  return (
    <div style={{position: "absolute", inset: 0, padding: "100px 130px", fontFamily}}>
      <h1 style={{color: WHITE, fontSize: 78, margin: 0, fontWeight: 900}}>{section.key_phrase}</h1>
      <svg width="1660" height="760" style={{position: "absolute", left: 130, top: 250}}>
        <circle cx="830" cy="360" r={150 * core} fill={`${accent}24`} stroke={accent} strokeWidth="8" />
        <circle cx="830" cy="360" r={75 * core} fill={`${MUTED}22`} stroke={`${WHITE}88`} strokeWidth="4" />
        {parts.map((part, i) => {
          const angle = (-90 + (360 / Math.max(parts.length, 1)) * i) * (Math.PI / 180);
          const x1 = 830 + Math.cos(angle) * 160;
          const y1 = 360 + Math.sin(angle) * 160;
          const x2 = 830 + Math.cos(angle) * 430;
          const y2 = 360 + Math.sin(angle) * 280;
          const draw = interpolate(frame, [26 + i * 10, 58 + i * 10], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
          const tx = x1 + (x2 - x1) * draw;
          const ty = y1 + (y2 - y1) * draw;
          return (
            <g key={part} opacity={draw}>
              <line x1={x1} y1={y1} x2={tx} y2={ty} stroke={accent} strokeWidth="5" strokeLinecap="round" />
              <circle cx={x2} cy={y2} r="12" fill={accent} />
              <text x={x2 + (x2 > 830 ? 26 : -26)} y={y2 + 12} textAnchor={x2 > 830 ? "start" : "end"} fill={WHITE} fontSize="34" fontWeight="800">{part}</text>
            </g>
          );
        })}
      </svg>
    </div>
  );
};
