import {interpolate, spring, useCurrentFrame, useVideoConfig} from "remotion";
import type React from "react";
import {fontFamily, MUTED, surface, WHITE} from "../theme";
import type {TemplateProps} from "../types";

export const Comparison: React.FC<TemplateProps> = ({section, accent}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const leftIn = spring({frame, fps, config: {damping: 18, stiffness: 85}});
  const rightIn = spring({frame: frame - 10, fps, config: {damping: 18, stiffness: 85}});
  const divider = interpolate(frame, [18, 56], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const bob = Math.sin(frame / 34) * 7;
  const left = String(section.on_screen.left ?? "");
  const right = String(section.on_screen.right ?? "");

  return (
    <div style={{position: "absolute", inset: 0, padding: "110px 120px", fontFamily}}>
      <h1 style={{color: WHITE, fontSize: 76, margin: "0 0 70px", fontWeight: 900}}>{section.key_phrase}</h1>
      <div style={{display: "grid", gridTemplateColumns: "1fr 1fr", gap: 76, position: "relative"}}>
        <div style={{...surface(accent), borderRadius: 8, padding: 58, minHeight: 520, transform: `translateX(${(1 - leftIn) * -180}px) translateY(${bob}px)`, opacity: leftIn}}>
          <div style={{color: accent, fontSize: 32, fontWeight: 800, marginBottom: 34}}>{String(section.on_screen.left_label ?? "Before")}</div>
          <div style={{color: WHITE, fontSize: 58, lineHeight: 1.12, fontWeight: 800}}>{left}</div>
        </div>
        <div style={{...surface(accent), borderRadius: 8, padding: 58, minHeight: 520, transform: `translateX(${(1 - rightIn) * 180}px) translateY(${-bob}px)`, opacity: rightIn}}>
          <div style={{color: accent, fontSize: 32, fontWeight: 800, marginBottom: 34}}>{String(section.on_screen.right_label ?? "After")}</div>
          <div style={{color: WHITE, fontSize: 58, lineHeight: 1.12, fontWeight: 800}}>{right}</div>
        </div>
        <div style={{position: "absolute", left: "50%", top: 0, width: 5, height: `${divider * 100}%`, background: MUTED, opacity: 0.5}} />
      </div>
    </div>
  );
};
