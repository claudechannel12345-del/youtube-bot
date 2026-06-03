import {interpolate, spring, useCurrentFrame, useVideoConfig} from "remotion";
import type React from "react";
import {fontFamily, MUTED, surface, WHITE} from "../theme";
import type {TemplateProps} from "../types";

export const TitleCard: React.FC<TemplateProps> = ({section, accent}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 18, stiffness: 95}});
  const sub = spring({frame: frame - 14, fps, config: {damping: 20, stiffness: 80}});
  const line = interpolate(frame, [22, 58], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const subtitle = String(section.on_screen.subtitle ?? "");
  const drift = Math.sin(frame / 58) * 8;

  return (
    <div style={{position: "absolute", inset: 0, display: "grid", placeItems: "center", fontFamily}}>
      <div
        style={{
          ...surface(accent),
          width: 1360,
          minHeight: 470,
          borderRadius: 8,
          padding: "86px 104px",
          transform: `translateY(${(1 - enter) * 90 + drift}px) scale(${0.94 + enter * 0.06})`,
          opacity: enter,
        }}
      >
        <h1 style={{margin: 0, color: WHITE, fontSize: 106, lineHeight: 1.02, fontWeight: 900}}>
          {section.key_phrase}
        </h1>
        <div style={{height: 8, width: `${line * 55}%`, background: accent, marginTop: 34, borderRadius: 8}} />
        {subtitle ? (
          <p style={{margin: "38px 0 0", color: MUTED, fontSize: 42, lineHeight: 1.22, opacity: sub}}>
            {subtitle}
          </p>
        ) : null}
      </div>
    </div>
  );
};
