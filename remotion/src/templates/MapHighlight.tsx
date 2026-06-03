import {interpolate, spring, useCurrentFrame, useVideoConfig} from "remotion";
import type React from "react";
import {fontFamily, MUTED, WHITE} from "../theme";
import type {TemplateProps} from "../types";

export const MapHighlight: React.FC<TemplateProps> = ({section, accent}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 18, stiffness: 80}});
  const pulse = interpolate(Math.sin(frame / 10), [-1, 1], [0.75, 1.35]);
  const place = String(section.on_screen.place ?? "Unknown region");

  return (
    <div style={{position: "absolute", inset: 0, padding: "110px 130px", fontFamily}}>
      <h1 style={{color: WHITE, fontSize: 80, margin: 0, fontWeight: 900}}>{section.key_phrase}</h1>
      <svg width="1660" height="700" style={{position: "absolute", left: 130, top: 285, opacity: enter}}>
        {Array.from({length: 14}, (_, i) => <line key={`v${i}`} x1={i * 128} y1="0" x2={i * 128 + Math.sin((frame + i) / 30) * 12} y2="700" stroke={`${MUTED}33`} strokeWidth="2" />)}
        {Array.from({length: 7}, (_, i) => <line key={`h${i}`} x1="0" y1={i * 104} x2="1660" y2={i * 104 + Math.cos((frame + i) / 30) * 8} stroke={`${MUTED}33`} strokeWidth="2" />)}
        <path d="M150 430 C280 250 520 290 650 180 C820 35 1030 210 1180 160 C1370 95 1490 260 1550 410 C1320 510 1100 455 930 575 C720 710 520 540 360 625 C255 680 160 565 150 430 Z" fill={`${accent}16`} stroke={`${accent}88`} strokeWidth="5" />
        <circle cx="990" cy="332" r={56 * pulse} fill="none" stroke={accent} strokeWidth="7" opacity="0.65" />
        <circle cx="990" cy="332" r="19" fill={accent} />
      </svg>
      <div style={{position: "absolute", left: 1180, top: 560, color: WHITE, fontSize: 54, fontWeight: 900, opacity: enter}}>
        {place}
      </div>
    </div>
  );
};
