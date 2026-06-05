import type React from "react";
import {AbsoluteFill, interpolate, spring, useVideoConfig} from "remotion";
import {SpeechBubble} from "../../flat/primitives";
import {CORAL, fontFamily, INK, INK_SOFT, PAPER_DEEP} from "../../flat/theme";
import {OverlayText, Stage, fitTextSize, type FamilyProps} from "./shared";

export const QuoteStage: React.FC<FamilyProps> = ({beat, localFrame}) => {
  const {fps} = useVideoConfig();
  const quote = beat.text_overlays.find((overlay) => overlay.role === "caption")?.text ?? beat.text_overlays[0]?.text ?? "";
  const attribution = beat.text_overlays.find((overlay) => overlay.role === "tiny_note")?.text ?? "";
  const pop = spring({frame: localFrame, fps, config: {damping: 15, stiffness: 170}});
  const opacity = interpolate(localFrame, [0, 14], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const settled = Math.min(1, Math.max(0, pop));
  const bob = Math.sin(localFrame / 28) * 5;
  const quoteFont = fitTextSize(quote, 820, attribution ? 260 : 330, 54, 28);

  return (
    <AbsoluteFill>
      <Stage>
        <g opacity={opacity} transform={`translate(0 ${bob}) scale(${0.94 + settled * 0.06})`} style={{transformBox: "fill-box", transformOrigin: "center"}}>
          <path d="M 420 805 L 1500 805" stroke={INK} strokeWidth={7} strokeLinecap="round" opacity={0.16} />
          <rect x={462} y={235} width={996} height={500} rx={8} fill={PAPER_DEEP} stroke={INK} strokeWidth={7} />
          <SpeechBubble x={510} y={180} w={900} h={430} tailX={650} tailY={700} fontFamily={fontFamily}>
            <div>
              <div style={{fontSize: quoteFont, lineHeight: 1.03, color: INK, overflowWrap: "anywhere"}}>&ldquo;{quote}&rdquo;</div>
              {attribution ? (
                <div style={{marginTop: 26, fontSize: 30, color: INK_SOFT, textTransform: "uppercase"}}>{attribution}</div>
              ) : null}
            </div>
          </SpeechBubble>
          <circle cx={1424} cy={232} r={32} fill={CORAL} stroke={INK} strokeWidth={7} />
        </g>
      </Stage>
      <OverlayText overlays={beat.text_overlays.filter((overlay) => overlay.role !== "caption" && overlay.role !== "tiny_note")} localFrame={localFrame} />
    </AbsoluteFill>
  );
};
