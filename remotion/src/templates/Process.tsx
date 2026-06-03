import {interpolate, spring, useCurrentFrame, useVideoConfig} from "remotion";
import type React from "react";
import {fontFamily, MUTED, surface, WHITE} from "../theme";
import type {TemplateProps} from "../types";

export const Process: React.FC<TemplateProps> = ({section, accent}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const steps = Array.isArray(section.on_screen.steps) ? section.on_screen.steps.map(String).slice(0, 5) : [];

  return (
    <div style={{position: "absolute", inset: 0, padding: "120px 120px", fontFamily}}>
      <h1 style={{color: WHITE, fontSize: 80, margin: "0 0 88px", fontWeight: 900}}>{section.key_phrase}</h1>
      <div style={{display: "grid", gridTemplateColumns: `repeat(${Math.max(steps.length, 1)}, 1fr)`, gap: 34, alignItems: "center"}}>
        {steps.map((step, i) => {
          const enter = spring({frame: frame - i * 16, fps, config: {damping: 16, stiffness: 95}});
          const arrow = interpolate(frame, [30 + i * 16, 58 + i * 16], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
          return (
            <div key={step} style={{position: "relative"}}>
              <div style={{...surface(accent), borderRadius: 8, minHeight: 330, padding: 36, transform: `translateY(${(1 - enter) * 80}px)`, opacity: enter}}>
                <div style={{color: accent, fontSize: 34, fontWeight: 900}}>0{i + 1}</div>
                <div style={{color: WHITE, fontSize: 34, lineHeight: 1.22, marginTop: 44, fontWeight: 800}}>{step}</div>
              </div>
              {i < steps.length - 1 ? <div style={{position: "absolute", right: -34, top: 160, width: 34 * arrow, height: 5, background: MUTED}} /> : null}
            </div>
          );
        })}
      </div>
    </div>
  );
};
