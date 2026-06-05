import type React from "react";
import {AbsoluteFill} from "remotion";
import {CORAL, INK} from "../../flat/theme";
import {OverlayText, Stage, renderAssets, type FamilyProps} from "./shared";

export const TimelineStage: React.FC<FamilyProps> = ({beat, localFrame}) => (
  <AbsoluteFill>
    <Stage>
      <path d="M 330 540 L 1590 540" stroke={INK} strokeWidth={8} strokeLinecap="butt" />
      {beat.assets.map((asset, index) => {
        const x = 430 + index * (1060 / Math.max(1, beat.assets.length - 1));
        return (
          <g key={asset.id}>
            <circle cx={x} cy={540} r={26} fill={CORAL} stroke={INK} strokeWidth={6} />
            {renderAssets({...beat, assets: [asset]}, localFrame, () => ({x, y: 410, scale: 0.42}))}
          </g>
        );
      })}
    </Stage>
    <OverlayText overlays={beat.text_overlays} localFrame={localFrame} />
  </AbsoluteFill>
);
