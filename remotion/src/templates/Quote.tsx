import {interpolate, spring, useCurrentFrame, useVideoConfig} from "remotion";
import type React from "react";
import {fontFamily, MUTED, surface, WHITE} from "../theme";
import type {TemplateProps} from "../types";

export const Quote: React.FC<TemplateProps> = ({section, accent}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const mark = spring({frame, fps, config: {damping: 15, stiffness: 100}});
  const reveal = interpolate(frame, [24, 72], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const attribution = interpolate(frame, [76, 106], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});

  return (
    <div style={{position: "absolute", inset: 0, display: "grid", placeItems: "center", fontFamily}}>
      <div style={{...surface(accent), borderRadius: 8, width: 1320, minHeight: 620, padding: "72px 96px", position: "relative"}}>
        <div style={{position: "absolute", color: accent, fontSize: 190, top: 12, left: 58, transform: `scale(${mark})`, opacity: mark}}>&quot;</div>
        <h1 style={{color: WHITE, fontSize: 54, lineHeight: 1.18, fontWeight: 800, margin: "92px 0 0", clipPath: `inset(0 ${100 - reveal * 100}% 0 0)`}}>
          {String(section.on_screen.quote ?? section.key_phrase)}
        </h1>
        <p style={{color: MUTED, fontSize: 34, marginTop: 52, opacity: attribution}}>
          {String(section.on_screen.attribution ?? "")}
        </p>
      </div>
    </div>
  );
};
