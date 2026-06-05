import type React from "react";
import {AbsoluteFill, interpolate} from "remotion";
import {CORAL, STROKE, TEAL} from "../../flat/theme";
import {ConnectorLine, OverlayText, Stage, anchorPoint, colorFor, renderAssets, type FamilyProps} from "./shared";
import type {VisualAsset} from "../types";

const locationAssetNames = new Set(["phone", "map_pin", "dot", "point"]);

const placementFor = (asset: VisualAsset, index: number, total: number) => {
  const p = anchorPoint(asset.anchor, index, total);
  return {
    x: p.x,
    y: p.y,
    scale: asset.name === "earth" ? 1.5 : asset.name === "satellite" ? 0.56 : asset.name === "phone" ? 0.5 : asset.kind === "icon_cluster" ? 0.5 : 0.78,
  };
};

export const DiagramStage: React.FC<FamilyProps> = ({beat, localFrame}) => {
  const progress = interpolate(localFrame, [0, 22], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const center = anchorPoint("center");
  const placements = beat.assets.map((asset, index) => placementFor(asset, index, beat.assets.length));
  const locationIndex = beat.assets.findIndex((asset) => locationAssetNames.has(asset.name));
  const earthIndex = beat.assets.findIndex((asset) => asset.name === "earth");
  const target = placements[locationIndex >= 0 ? locationIndex : earthIndex >= 0 ? earthIndex : -1] ?? center;
  const satelliteRanges = beat.assets.flatMap((asset, index) => {
    if (asset.name !== "satellite") {
      return [];
    }
    const p = placements[index];
    const dx = target.x - p.x;
    const dy = target.y - p.y;
    const radius = Math.hypot(dx, dy);
    return [{asset, p, radius}];
  });
  return (
    <AbsoluteFill>
      <Stage>
        {satelliteRanges.map(({asset, p, radius}) => (
          <circle
            key={`${asset.id}-range`}
            cx={p.x}
            cy={p.y}
            r={Math.max(24, radius * progress)}
            fill="none"
            stroke={asset.colorRole ? colorFor(asset) : TEAL}
            strokeWidth={STROKE}
            strokeLinecap="round"
            opacity={0.58}
          />
        ))}
        {beat.assets
          .filter((asset) => asset.anchor !== "center" && asset.anchor !== "center_subject")
          .slice(0, 6)
          .map((asset) => (
            <ConnectorLine
              key={asset.id}
              from={anchorPoint(asset.anchor)}
              to={center}
              progress={asset.is_new === false ? 1 : progress}
              color={CORAL}
            />
          ))}
        {renderAssets(beat, localFrame, placementFor)}
      </Stage>
      <OverlayText overlays={beat.text_overlays} localFrame={localFrame} />
    </AbsoluteFill>
  );
};
