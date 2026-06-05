import type React from "react";
import {AbsoluteFill} from "remotion";
import {CORAL, fontFamily, INK} from "../../flat/theme";
import {OverlayText, Stage, type FamilyProps, renderAssets} from "./shared";

export const TitleStage: React.FC<FamilyProps> = ({beat, localFrame}) => (
  <AbsoluteFill>
    <Stage>
      {renderAssets(beat, localFrame, (_asset, index, total) => ({
        x: 960 + (index - (total - 1) / 2) * 310,
        y: 670,
        scale: 0.72,
      }))}
      <text x={960} y={465} textAnchor="middle" fontFamily={fontFamily} fontWeight={900} fontSize={136} fill={INK}>
        {beat.text_overlays[0]?.text ?? "CUTAWAY"}
      </text>
      <path d="M 620 520 L 1300 520" stroke={CORAL} strokeWidth={12} strokeLinecap="butt" />
    </Stage>
    <OverlayText overlays={beat.text_overlays.slice(1)} localFrame={localFrame} />
  </AbsoluteFill>
);
