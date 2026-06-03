import {spring, useCurrentFrame, useVideoConfig} from "remotion";
import type React from "react";
import {fontFamily, MUTED, WHITE} from "../theme";
import type {TemplateProps} from "../types";

export const ListReveal: React.FC<TemplateProps> = ({section, accent}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const items = Array.isArray(section.on_screen.items) ? section.on_screen.items.map(String).slice(0, 6) : [];
  const drift = Math.sin(frame / 52) * 10;

  return (
    <div style={{position: "absolute", inset: 0, padding: "110px 150px", fontFamily, transform: `translateY(${drift}px)`}}>
      <h1 style={{color: WHITE, fontSize: 82, margin: "0 0 70px", fontWeight: 900}}>{section.key_phrase}</h1>
      <div style={{display: "grid", gap: 28}}>
        {items.map((item, i) => {
          const enter = spring({frame: frame - i * 12, fps, config: {damping: 17, stiffness: 90}});
          return (
            <div key={item} style={{display: "grid", gridTemplateColumns: "42px 1fr", gap: 28, alignItems: "center", opacity: enter, transform: `translateX(${(1 - enter) * -90}px)`}}>
              <div style={{width: 28, height: 28, borderRadius: "50%", background: accent, boxShadow: `0 0 22px ${accent}`}} />
              <div style={{color: i % 2 ? MUTED : WHITE, fontSize: 42, lineHeight: 1.18, fontWeight: 800}}>{item}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
