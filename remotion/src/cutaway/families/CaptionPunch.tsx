import type React from "react";
import {AbsoluteFill} from "remotion";
import {CORAL, INK} from "../../flat/theme";
import {OverlayText, Stage, SvgTextBlock, type FamilyProps} from "./shared";

export const CaptionPunch: React.FC<FamilyProps> = ({beat, localFrame}) => (
  <AbsoluteFill>
    <Stage>
      <SvgTextBlock text={beat.text_overlays[0]?.text ?? "YES"} x={440} y={350} width={1080} height={210} baseSize={132} fill={INK} />
      <path d="M 560 590 L 1360 590" stroke={CORAL} strokeWidth={14} strokeLinecap="butt" />
    </Stage>
    <OverlayText overlays={beat.text_overlays.slice(1)} localFrame={localFrame} />
  </AbsoluteFill>
);
