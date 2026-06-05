import type React from "react";
import {AbsoluteFill} from "remotion";
import {CORAL, INK, PAPER} from "../../flat/theme";
import {OverlayText, Stage, SvgTextBlock, renderAssets, type FamilyProps} from "./shared";

export const StatStage: React.FC<FamilyProps> = ({beat, localFrame}) => (
  <AbsoluteFill>
    <Stage>
      <rect x={510} y={250} width={900} height={430} rx={8} fill={PAPER} stroke={INK} strokeWidth={7} />
      <SvgTextBlock
        text={beat.text_overlays.find((overlay) => overlay.role === "stat")?.text ?? beat.text_overlays[0]?.text ?? "100"}
        x={590}
        y={334}
        width={740}
        height={230}
        baseSize={176}
        fill={CORAL}
      />
      {renderAssets(beat, localFrame, (_asset, index, total) => ({
        x: 960 + (index - (total - 1) / 2) * 360,
        y: 760,
        scale: 0.58,
      }))}
    </Stage>
    <OverlayText overlays={beat.text_overlays.filter((overlay) => overlay.role !== "stat")} localFrame={localFrame} />
  </AbsoluteFill>
);
