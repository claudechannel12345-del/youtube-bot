import type React from "react";
import {AbsoluteFill} from "remotion";
import {CORAL, fontFamily, INK, PAPER} from "../../flat/theme";
import {OverlayText, Stage, renderAssets, type FamilyProps} from "./shared";

export const ListStage: React.FC<FamilyProps> = ({beat, localFrame}) => (
  <AbsoluteFill>
    <Stage>
      {beat.assets.slice(0, 5).map((asset, index) => (
        <g key={asset.id}>
          <rect x={430} y={205 + index * 125} width={1060} height={84} rx={8} fill={PAPER} stroke={INK} strokeWidth={5} />
          <circle cx={486} cy={247 + index * 125} r={22} fill={CORAL} stroke={INK} strokeWidth={4} />
          {renderAssets({...beat, assets: [asset], motion: beat.motion}, localFrame, () => ({x: 610, y: 247 + index * 125, scale: 0.22}))}
          <text x={720} y={265 + index * 125} fontFamily={fontFamily} fontWeight={900} fontSize={42} fill={INK}>
            {(asset.variant ?? asset.name).replace(/_/g, " ").toUpperCase()}
          </text>
        </g>
      ))}
    </Stage>
    <OverlayText overlays={beat.text_overlays} localFrame={localFrame} />
  </AbsoluteFill>
);
