import type React from "react";
import {AbsoluteFill} from "remotion";
import {CORAL, INK, PAPER} from "../../flat/theme";
import {OverlayText, Stage, renderAssets, type FamilyProps} from "./shared";

export const MapStage: React.FC<FamilyProps> = ({beat, localFrame}) => (
  <AbsoluteFill>
    <Stage>
      <rect x={360} y={190} width={1200} height={660} rx={8} fill={PAPER} stroke={INK} strokeWidth={7} />
      <path d="M 460 660 C 700 420 1020 730 1460 380" fill="none" stroke={CORAL} strokeWidth={8} strokeLinecap="round" />
      {renderAssets(beat, localFrame, (asset, index, total) => ({
        x: asset.name === "map" ? 960 : 640 + index * (640 / Math.max(1, total - 1)),
        y: asset.name === "map" ? 520 : 560 + (index % 2) * 70,
        scale: asset.name === "map" ? 1.4 : 0.52,
      }))}
    </Stage>
    <OverlayText overlays={beat.text_overlays} localFrame={localFrame} />
  </AbsoluteFill>
);
