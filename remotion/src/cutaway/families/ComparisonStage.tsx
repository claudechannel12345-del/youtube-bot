import type React from "react";
import {AbsoluteFill} from "remotion";
import {CORAL, INK, PAPER} from "../../flat/theme";
import {OverlayText, Panel, Stage, renderAssets, type FamilyProps} from "./shared";

export const ComparisonStage: React.FC<FamilyProps> = ({beat, localFrame}) => (
  <AbsoluteFill>
    <Stage>
      <Panel x={220} y={210} w={640} h={590} />
      <Panel x={1060} y={210} w={640} h={590} />
      <path d="M 960 220 L 960 800" stroke={INK} strokeWidth={7} strokeLinecap="butt" />
      <circle cx={960} cy={510} r={66} fill={PAPER} stroke={INK} strokeWidth={7} />
      <text x={960} y={533} textAnchor="middle" fontSize={54} fontWeight={900} fontFamily="Inter, Arial, sans-serif" fill={CORAL}>
        VS
      </text>
      {renderAssets(beat, localFrame, (_asset, index) => {
        const sideIndex = Math.floor(index / 2);
        return {
          x: index % 2 === 0 ? 540 : 1380,
          y: 470 + sideIndex * 150,
          scale: 0.66,
        };
      })}
    </Stage>
    <OverlayText overlays={beat.text_overlays} localFrame={localFrame} />
  </AbsoluteFill>
);
