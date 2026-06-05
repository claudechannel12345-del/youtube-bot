import type React from "react";
import {AbsoluteFill} from "remotion";
import {GroundShadow} from "../../flat/primitives";
import {INK} from "../../flat/theme";
import {OverlayText, Stage, anchorPoint, renderAssets, type FamilyProps} from "./shared";

const spaceAssets = new Set(["satellite", "earth", "signal", "signal_beam"]);

export const ObjectStage: React.FC<FamilyProps> = ({beat, localFrame}) => {
  const hasGroundedAsset = beat.assets.some((asset) => !spaceAssets.has(asset.name));
  return (
    <AbsoluteFill>
      <Stage>
        {hasGroundedAsset ? <path d="M 300 820 L 1620 820" stroke={INK} strokeWidth={8} strokeLinecap="round" opacity={0.18} /> : null}
        {hasGroundedAsset ? <GroundShadow x={960} y={830} rx={340} ry={24} /> : null}
        {renderAssets(beat, localFrame, (asset, index, total) => {
          const p = anchorPoint(asset.anchor, index, total);
          return {
            x: p.x,
            y: p.y,
            scale: asset.kind === "icon_cluster" ? 0.62 : asset.name === "phone" ? 0.72 : 0.92,
          };
        })}
      </Stage>
      <OverlayText overlays={beat.text_overlays} localFrame={localFrame} />
    </AbsoluteFill>
  );
};
