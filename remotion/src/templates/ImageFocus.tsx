import {OffthreadVideo, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from "remotion";
import type React from "react";
import {fontFamily, MUTED, WHITE} from "../theme";
import type {TemplateProps} from "../types";

export const ImageFocus: React.FC<TemplateProps> = ({section, accent}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const enter = spring({frame, fps, config: {damping: 18, stiffness: 90}});
  const scan = interpolate(frame % 120, [0, 120], [-20, 110]);
  const overlay = String(section.on_screen.overlay_text ?? section.key_phrase);
  const video = typeof section.on_screen.video === "string" ? section.on_screen.video : "";

  if (video) {
    return (
      <div style={{position: "absolute", inset: 0, fontFamily, overflow: "hidden", background: "#000"}}>
        <OffthreadVideo src={staticFile(video)} style={{position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover"}} />
        <div style={{position: "absolute", inset: 0, background: "linear-gradient(90deg, rgba(0,0,0,0.72), rgba(0,0,0,0.22) 52%, rgba(0,0,0,0.58))"}} />
        <div style={{position: "absolute", left: 120, right: 120, bottom: 92, transform: `translateY(${(1 - enter) * 34}px)`, opacity: enter}}>
          <div style={{width: 118, height: 8, background: accent, marginBottom: 30}} />
          <h1 style={{color: WHITE, fontSize: 78, margin: "0 0 24px", fontWeight: 900, lineHeight: 0.98, maxWidth: 1160}}>{section.key_phrase}</h1>
          <div style={{color: WHITE, fontSize: 52, fontWeight: 800, maxWidth: 1020, lineHeight: 1.05}}>
            {overlay}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{position: "absolute", inset: 0, padding: "90px 120px", fontFamily}}>
      <h1 style={{color: WHITE, fontSize: 76, margin: "0 0 44px", fontWeight: 900}}>{section.key_phrase}</h1>
      <div style={{position: "relative", height: 720, borderRadius: 8, overflow: "hidden", border: `4px solid ${accent}`, transform: `scale(${0.96 + enter * 0.04})`, opacity: enter}}>
        <div style={{position: "absolute", inset: 0, background: `linear-gradient(135deg, ${accent}55, rgba(255,255,255,0.08) 38%, rgba(13,13,26,0.96)), radial-gradient(circle at 70% 38%, ${accent}55, transparent 28%)`}} />
        <div style={{position: "absolute", inset: 0, backgroundImage: `linear-gradient(${MUTED}22 2px, transparent 2px), linear-gradient(90deg, ${MUTED}22 2px, transparent 2px)`, backgroundSize: "64px 64px", transform: `translate(${Math.sin(frame / 45) * 16}px, ${Math.cos(frame / 45) * 16}px)`}} />
        <div style={{position: "absolute", left: `${scan}%`, top: 0, width: 90, bottom: 0, background: `${WHITE}18`, transform: "skewX(-12deg)"}} />
        <div style={{position: "absolute", left: 72, bottom: 66, color: WHITE, fontSize: 70, fontWeight: 900, maxWidth: 1020, lineHeight: 1.04}}>
          {overlay}
        </div>
      </div>
    </div>
  );
};
