import type React from "react";
import {AbsoluteFill, interpolate} from "remotion";
import {CORAL} from "../../flat/theme";
import {ConnectorLine, OverlayText, Stage, anchorPoint, renderAssets, type FamilyProps} from "./shared";

export const DiagramStage: React.FC<FamilyProps> = ({beat, localFrame}) => {
  const progress = interpolate(localFrame, [0, 22], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const center = anchorPoint("center");
  return (
    <AbsoluteFill>
      <Stage>
        {beat.assets
          .filter((asset) => asset.anchor !== "center" && asset.anchor !== "center_subject")
          .slice(0, 6)
          .map((asset, index, arr) => (
            <ConnectorLine key={asset.id} from={anchorPoint(asset.anchor, index, arr.length)} to={center} progress={progress} color={CORAL} />
          ))}
        {renderAssets(beat, localFrame, (asset, index, total) => {
          const p = anchorPoint(asset.anchor, index, total);
          return {x: p.x, y: p.y, scale: asset.name === "phone" ? 0.55 : asset.kind === "icon_cluster" ? 0.5 : 0.78};
        })}
      </Stage>
      <OverlayText overlays={beat.text_overlays} localFrame={localFrame} />
    </AbsoluteFill>
  );
};
