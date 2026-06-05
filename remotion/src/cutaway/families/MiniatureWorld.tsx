import type React from "react";
import {AbsoluteFill} from "remotion";
import {CORAL, INK, PAPER_DEEP} from "../../flat/theme";
import {OverlayText, Stage, renderAssets, type FamilyProps} from "./shared";

export const MiniatureWorld: React.FC<FamilyProps> = ({beat, localFrame}) => (
  <AbsoluteFill>
    <Stage>
      <path d="M 280 780 C 560 720 1360 720 1640 780 L 1640 850 L 280 850 Z" fill={PAPER_DEEP} stroke={INK} strokeWidth={7} />
      <path d="M 430 755 L 1480 755" stroke={CORAL} strokeWidth={7} strokeLinecap="round" />
      {renderAssets(beat, localFrame, (_asset, index, total) => ({
        x: 960 + (index - (total - 1) / 2) * 300,
        y: index % 2 === 0 ? 610 : 680,
        scale: 0.62,
      }))}
    </Stage>
    <OverlayText overlays={beat.text_overlays} localFrame={localFrame} />
  </AbsoluteFill>
);
