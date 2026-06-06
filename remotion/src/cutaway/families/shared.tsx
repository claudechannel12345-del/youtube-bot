import type React from "react";
import {interpolate, spring, useVideoConfig} from "remotion";
import {renderRegistryAsset} from "../registry";
import type {LegacyDirectedBeat, MotionCue, TextOverlay, VisualAsset} from "../types";
import {BLUE, CORAL, fontFamily, GOLD, INK, INK_SOFT, PAPER, PAPER_DEEP, STROKE, STROKE_THIN, TEAL} from "../../flat/theme";

export const W = 1920;
export const H = 1080;

export type FamilyProps = {
  beat: LegacyDirectedBeat;
  localFrame: number;
};

type Placement = {x: number; y: number; scale?: number; extra?: Record<string, unknown>};
type OverlayMetrics = {fontSize: number; width: number; minHeight: number};

export const palette = {
  ink: INK,
  accent: CORAL,
  blue: BLUE,
  green: TEAL,
  yellow: GOLD,
  lavender: "#7A5BD8",
  muted: INK_SOFT,
  white: "#FFFFFF",
};

export const colorFor = (asset: VisualAsset): string => {
  if (!asset.colorRole) {
    return CORAL;
  }
  return palette[asset.colorRole] ?? CORAL;
};

export const anchorPoint = (anchor: string, index = 0, total = 1): {x: number; y: number} => {
  const spread = total > 1 ? index - (total - 1) / 2 : 0;
  const anchors: Record<string, {x: number; y: number}> = {
    center: {x: 960, y: 540},
    center_subject: {x: 960, y: 560},
    upper_band: {x: 960 + spread * 360, y: 230 + Math.abs(spread) * 20},
    lower_band: {x: 960 + spread * 360, y: 800},
    left: {x: 560, y: 560},
    right: {x: 1360, y: 560},
    left_center: {x: 560, y: 560},
    right_center: {x: 1360, y: 560},
    top: {x: 960, y: 220},
    bottom: {x: 960, y: 850},
    map_focus: {x: 960, y: 540},
    lower_center: {x: 960, y: 858},
    upper_center: {x: 960, y: 170},
    upper_left: {x: 370, y: 190},
    upper_right: {x: 1550, y: 190},
    lower_left: {x: 390, y: 850},
    lower_right: {x: 1530, y: 850},
    headline: {x: 960, y: 210},
    stat: {x: 960, y: 470},
    diagram_core: {x: 960, y: 540},
  };
  return anchors[anchor] ?? {x: 960 + spread * 330, y: 540};
};

export const Stage: React.FC<{children: React.ReactNode}> = ({children}) => (
  <svg viewBox={`0 0 ${W} ${H}`} width="100%" height="100%">
    {children}
  </svg>
);

const cueFor = (asset: VisualAsset, cues: MotionCue[]): MotionCue | undefined => {
  if (asset.is_new === false) {
    return undefined;
  }
  return cues.find((cue) => cue.target === asset.id || cue.target === asset.name);
};

const idleTransform = (asset: VisualAsset, localFrame: number, index: number): string => {
  const phase = localFrame / (26 + (index % 4) * 5) + index * 0.9;
  if (asset.name === "satellite") {
    return `translate(${Math.sin(phase) * 8}px ${Math.cos(phase * 0.8) * 6}px)`;
  }
  if (asset.name === "signal" || asset.name === "signal_beam") {
    return `scale(${1 + Math.sin(phase) * 0.025})`;
  }
  return `translate(0 ${Math.sin(phase) * 5}px)`;
};

export const motionTransform = (cue: MotionCue | undefined, localFrame: number, fps: number): {opacity: number; transform: string} => {
  if (!cue || cue.kind === "none") {
    return {opacity: 1, transform: ""};
  }
  const start = cue.delay * fps;
  const duration = Math.max(1, cue.duration * fps);
  const f = localFrame - start;
  const progress = interpolate(f, [0, duration], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const pop = spring({frame: f, fps, config: {damping: 14, stiffness: 180}});
  const clampedPop = Math.max(0, Math.min(1.15, pop));
  if (cue.kind === "pop_in" || cue.kind === "stamp") {
    return {opacity: progress, transform: `scale(${0.72 + clampedPop * 0.28})`};
  }
  if (cue.kind === "slide_in") {
    return {opacity: progress, transform: `translate(${-80 + progress * 80}px 0)`};
  }
  if (cue.kind === "draw_on" || cue.kind === "trace_line" || cue.kind === "wipe_reveal") {
    return {opacity: progress, transform: `scaleX(${Math.max(0.02, progress)})`};
  }
  if (cue.kind === "micro_bob") {
    return {opacity: 1, transform: `translate(0 ${Math.sin(localFrame / 9) * 7}px)`};
  }
  if (cue.kind === "pulse") {
    return {opacity: 1, transform: `scale(${1 + Math.sin(localFrame / 8) * 0.045})`};
  }
  if (cue.kind === "orbit") {
    return {opacity: 1, transform: `rotate(${localFrame * 1.2}deg)`};
  }
  return {opacity: 1, transform: ""};
};

export const renderAssets = (
  beat: LegacyDirectedBeat,
  localFrame: number,
  placements?: (asset: VisualAsset, index: number, total: number) => Placement,
): React.ReactNode => {
  const {fps} = useVideoConfig();
  return beat.assets.map((asset, index) => {
    if ((asset.name === "label" || asset.name === "stamp") && !asset.variant?.trim()) {
      return null;
    }
    const count = Math.max(1, asset.count ?? 1);
    const items = Array.from({length: count}, (_, subIndex) => {
      const syntheticIndex = count > 1 ? subIndex : index;
      const total = count > 1 ? count : beat.assets.length;
      const place: Placement = placements?.(asset, syntheticIndex, total) ?? anchorPoint(asset.anchor, syntheticIndex, total);
      const cue = cueFor(asset, beat.motion);
      const motion = motionTransform(cue, localFrame, fps);
      const extra = {...place.extra, text: asset.variant};
      return (
        <g
          key={`${asset.id}-${subIndex}`}
          style={{
            opacity: motion.opacity,
            transform: `${idleTransform(asset, localFrame, index + subIndex)} ${motion.transform}`.trim(),
            transformBox: "fill-box",
            transformOrigin: "center",
          }}
        >
          {renderRegistryAsset(asset.name, {
            x: place.x,
            y: place.y,
            scale: place.scale ?? 1.05,
            color: colorFor(asset),
            localFrame: localFrame + subIndex * 8,
            extra,
          })}
        </g>
      );
    });
    return items;
  });
};

const overlayMetrics = (overlay: TextOverlay): OverlayMetrics => {
  const len = overlay.text.trim().length;
  const base = overlay.role === "headline" ? 88 : overlay.role === "stat" ? 116 : overlay.role === "tiny_note" ? 36 : 56;
  const width = overlay.role === "headline" ? 980 : overlay.role === "stat" ? 980 : overlay.role === "caption" ? 860 : 720;
  const lineCount = len > 72 ? 4 : len > 42 ? 3 : len > 20 ? 2 : 1;
  const fontSize = Math.max(26, Math.min(base, (width * lineCount) / Math.max(1, len) * 1.55, 210 / (lineCount * 1.03)));
  return {fontSize, width, minHeight: Math.ceil(fontSize * lineCount * 1.06)};
};

const overlayStyle = (overlay: TextOverlay, metrics: OverlayMetrics): React.CSSProperties => {
  const isStamp = overlay.role === "stamp" || overlay.tone === "coral_stamp";
  const color = overlay.tone === "muted" || overlay.tone === "quiet" ? INK_SOFT : overlay.tone === "coral_stamp" || overlay.tone === "warning" ? CORAL : INK;
  return {
    color,
    fontFamily,
    fontWeight: 900,
    fontSize: metrics.fontSize,
    lineHeight: 1.02,
    letterSpacing: 0,
    textAlign: "center",
    textTransform: "uppercase",
    border: isStamp ? `${STROKE}px solid ${CORAL}` : undefined,
    padding: isStamp ? "14px 28px" : undefined,
    background: isStamp ? PAPER : undefined,
    width: metrics.width,
    maxWidth: metrics.width,
    minHeight: isStamp ? metrics.minHeight + 28 : metrics.minHeight,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    overflowWrap: "anywhere",
    whiteSpace: "normal",
  };
};

const safeOverlayPoint = (point: {x: number; y: number}, metrics: OverlayMetrics): {x: number; y: number} => {
  const margin = 72;
  const halfW = metrics.width / 2 + 36;
  const halfH = metrics.minHeight / 2 + 28;
  return {
    x: Math.max(margin + halfW, Math.min(W - margin - halfW, point.x)),
    y: Math.max(margin + halfH, Math.min(H - margin - halfH, point.y)),
  };
};

export const fitTextSize = (text: string, maxWidth: number, maxHeight: number, base: number, min = 24): number => {
  const normalized = text.trim();
  const words = normalized.split(/\s+/).filter(Boolean);
  const longest = words.reduce((max, word) => Math.max(max, word.length), 1);
  const chars = Math.max(normalized.length, 1);
  const lineCount = chars > 88 ? 4 : chars > 48 ? 3 : chars > 22 ? 2 : 1;
  return Math.max(
    min,
    Math.min(base, (maxWidth / longest) * 1.45, (maxWidth * lineCount) / chars * 1.6, maxHeight / (lineCount * 1.06)),
  );
};

export const SvgTextBlock: React.FC<{
  text: string;
  x: number;
  y: number;
  width: number;
  height: number;
  baseSize: number;
  fill?: string;
  align?: "left" | "center";
}> = ({text, x, y, width, height, baseSize, fill = INK, align = "center"}) => (
  <foreignObject x={x} y={y} width={width} height={height}>
    <div
      style={{
        color: fill,
        fontFamily,
        fontWeight: 900,
        fontSize: fitTextSize(text, width, height, baseSize),
        lineHeight: 1.03,
        letterSpacing: 0,
        textAlign: align,
        textTransform: "uppercase",
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: align === "left" ? "flex-start" : "center",
        overflowWrap: "anywhere",
        whiteSpace: "normal",
      }}
    >
      {text}
    </div>
  </foreignObject>
);

export const OverlayText: React.FC<{overlays: TextOverlay[]; localFrame: number}> = ({overlays, localFrame}) => {
  const {fps} = useVideoConfig();
  return (
    <>
      {overlays.map((overlay, index) => {
        const metrics = overlayMetrics(overlay);
        const point = safeOverlayPoint(anchorPoint(overlay.anchor, index, overlays.length), metrics);
        const cue = {kind: overlay.role === "stamp" ? "stamp" : "pop_in", delay: index * 0.08, duration: 0.25, target: overlay.role} as MotionCue;
        const motion = motionTransform(cue, localFrame, fps);
        const stampRotate = overlay.role === "stamp" || overlay.tone === "coral_stamp" ? " rotate(-4deg)" : "";
        return (
          <div
            key={`${overlay.role}-${overlay.text}-${index}`}
            style={{
              position: "absolute",
              left: point.x,
              top: point.y,
              opacity: motion.opacity,
              transform: `translate(-50%, -50%) ${motion.transform}${stampRotate}`,
              transformOrigin: "center",
              ...overlayStyle(overlay, metrics),
            }}
          >
            {overlay.text}
          </div>
        );
      })}
    </>
  );
};

export const ConnectorLine: React.FC<{from: {x: number; y: number}; to: {x: number; y: number}; progress?: number; color?: string}> = ({
  from,
  to,
  progress = 1,
  color = CORAL,
}) => {
  const x2 = from.x + (to.x - from.x) * progress;
  const y2 = from.y + (to.y - from.y) * progress;
  return <path d={`M ${from.x} ${from.y} L ${x2} ${y2}`} stroke={color} strokeWidth={STROKE} strokeLinecap="round" fill="none" />;
};

export const Panel: React.FC<{x: number; y: number; w: number; h: number; children?: React.ReactNode}> = ({x, y, w, h, children}) => (
  <g>
    <rect x={x} y={y} width={w} height={h} rx={8} fill={PAPER} stroke={INK} strokeWidth={STROKE_THIN} />
    {children}
  </g>
);
