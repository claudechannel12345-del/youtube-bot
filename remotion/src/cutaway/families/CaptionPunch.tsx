import type React from "react";
import {AbsoluteFill} from "remotion";
import {CORAL, fontFamily, INK} from "../../flat/theme";
import {OverlayText, Stage, type FamilyProps} from "./shared";

export const CaptionPunch: React.FC<FamilyProps> = ({beat, localFrame}) => (
  <AbsoluteFill>
    <Stage>
      <text x={960} y={520} textAnchor="middle" fontFamily={fontFamily} fontWeight={900} fontSize={132} fill={INK}>
        {beat.text_overlays[0]?.text ?? "YES"}
      </text>
      <path d="M 560 590 L 1360 590" stroke={CORAL} strokeWidth={14} strokeLinecap="butt" />
    </Stage>
    <OverlayText overlays={beat.text_overlays.slice(1)} localFrame={localFrame} />
  </AbsoluteFill>
);
