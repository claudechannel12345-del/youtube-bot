import type React from "react";
import {AbsoluteFill} from "remotion";
import {OverlayText, Stage, renderAssets, type FamilyProps} from "./shared";

export const MiniatureWorld: React.FC<FamilyProps> = ({beat, localFrame}) => (
  <AbsoluteFill>
    <Stage>
      {renderAssets(beat, localFrame, (_asset, index, total) => ({
        x: 960 + (index - (total - 1) / 2) * 340,
        y: 470,
        scale: 0.78,
      }))}
    </Stage>
    <OverlayText overlays={beat.text_overlays} localFrame={localFrame} />
  </AbsoluteFill>
);
