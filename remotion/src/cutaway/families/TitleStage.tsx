import type React from "react";
import {AbsoluteFill} from "remotion";
import {CORAL, INK} from "../../flat/theme";
import {OverlayText, Stage, SvgTextBlock, type FamilyProps, renderAssets} from "./shared";

export const TitleStage: React.FC<FamilyProps> = ({beat, localFrame}) => (
  <AbsoluteFill>
    <Stage>
      {renderAssets(beat, localFrame, (_asset, index, total) => ({
        x: 960 + (index - (total - 1) / 2) * 310,
        y: 670,
        scale: 0.72,
      }))}
      <SvgTextBlock text={beat.text_overlays[0]?.text ?? "CUTAWAY"} x={430} y={330} width={1060} height={190} baseSize={136} fill={INK} />
      <path d="M 620 520 L 1300 520" stroke={CORAL} strokeWidth={12} strokeLinecap="butt" />
    </Stage>
    <OverlayText overlays={beat.text_overlays.slice(1)} localFrame={localFrame} />
  </AbsoluteFill>
);
