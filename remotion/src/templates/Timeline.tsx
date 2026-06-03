import {interpolate, spring, useCurrentFrame, useVideoConfig} from "remotion";
import type React from "react";
import {fontFamily, MUTED, WHITE} from "../theme";
import type {TemplateProps} from "../types";

export const Timeline: React.FC<TemplateProps> = ({section, accent}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const events = Array.isArray(section.on_screen.events) ? section.on_screen.events.map(String).slice(0, 5) : [];
  const line = interpolate(frame, [18, 82], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const pulse = 1 + Math.sin(frame / 8) * 0.08;

  return (
    <div style={{position: "absolute", inset: 0, padding: "120px 130px", fontFamily}}>
      <h1 style={{color: WHITE, fontSize: 82, margin: 0, fontWeight: 900}}>{section.key_phrase}</h1>
      <div style={{position: "absolute", left: 180, right: 180, top: 560, height: 6, background: `${MUTED}55`}}>
        <div style={{height: 6, width: `${line * 100}%`, background: accent}} />
      </div>
      {events.map((event, i) => {
        const x = 180 + (i / Math.max(events.length - 1, 1)) * 1560;
        const pop = spring({frame: frame - 38 - i * 12, fps, config: {damping: 14, stiffness: 120}});
        return (
          <div key={event} style={{position: "absolute", left: x - 140, top: i % 2 ? 596 : 386, width: 280, opacity: pop}}>
            <div style={{width: 34, height: 34, borderRadius: "50%", background: accent, margin: "0 auto 24px", transform: `scale(${pop * (i === events.length - 1 ? pulse : 1)})`, boxShadow: `0 0 30px ${accent}`}} />
            <div style={{color: WHITE, fontSize: 30, lineHeight: 1.22, textAlign: "center", fontWeight: 700}}>{event}</div>
          </div>
        );
      })}
    </div>
  );
};
