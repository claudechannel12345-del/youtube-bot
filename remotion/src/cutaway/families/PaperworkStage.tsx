import type React from "react";
import {AbsoluteFill} from "remotion";
import {CORAL, INK, PAPER} from "../../flat/theme";
import {OverlayText, Stage, renderAssets, type FamilyProps} from "./shared";

export const PaperworkStage: React.FC<FamilyProps> = ({beat, localFrame}) => (
  <AbsoluteFill>
    <Stage>
      <rect x={650} y={190} width={620} height={720} rx={6} fill={PAPER} stroke={INK} strokeWidth={8} />
      <path d="M 760 340 L 1160 340 M 760 430 L 1160 430 M 760 520 L 1080 520" stroke={INK} strokeWidth={5} strokeLinecap="round" opacity={0.35} />
      <path d="M 740 705 L 1180 635" stroke={CORAL} strokeWidth={12} strokeLinecap="butt" />
      {renderAssets(beat, localFrame, (_asset, index, total) => ({
        x: 960 + (index - (total - 1) / 2) * 280,
        y: 690,
        scale: 0.58,
      }))}
    </Stage>
    <OverlayText overlays={beat.text_overlays} localFrame={localFrame} />
  </AbsoluteFill>
);
