/**
 * Flat-illustration primitive kit - v3: OLD (simple) level of detail, NEW sharpness.
 * Simple silhouettes like the first pass, but crisp: miter joins on structural
 * shapes, tighter corner radii, higher-contrast outlined windows, grounding shadows.
 */
import type React from "react";
import {
  BLUE,
  CORAL,
  GOLD,
  INK,
  INK_SOFT,
  PAPER,
  PAPER_DEEP,
  STROKE,
  STROKE_BOLD,
  STROKE_THIN,
  TEAL,
} from "./theme";

const round = {
  stroke: INK,
  strokeWidth: STROKE,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};
// sharp join for crisp, defined structural edges
const sharp = {
  stroke: INK,
  strokeWidth: STROKE,
  strokeLinecap: "butt" as const,
  strokeLinejoin: "miter" as const,
};

// --- grounding shadow (depth/weight, not "detail") -------------------------
export const GroundShadow: React.FC<{x: number; y: number; rx: number; ry?: number}> = ({
  x,
  y,
  rx,
  ry = 14,
}) => <ellipse cx={x} cy={y} rx={rx} ry={ry} fill={INK} opacity={0.1} />;

// --- figure (simple, sharp) -------------------------------------------------
export const Person: React.FC<{x: number; y: number; scale?: number; shirt?: string}> = ({
  x,
  y,
  scale = 1,
  shirt = CORAL,
}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -24 58 L -24 122" {...round} strokeWidth={STROKE_BOLD} />
    <path d="M 24 58 L 24 122" {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -44 -6 Q -44 -52 0 -52 Q 44 -52 44 -6 L 44 64 Q 0 84 -44 64 Z" fill={shirt} {...round} />
    <circle cx="0" cy="-92" r="42" fill="#F0D2B8" {...round} />
    <circle cx="-14" cy="-96" r="5.5" fill={INK} stroke="none" />
    <circle cx="14" cy="-96" r="5.5" fill={INK} stroke="none" />
  </g>
);

// --- city (simple, but crisp windows + sharp corners) ----------------------
export const Building: React.FC<{
  x: number;
  y: number;
  w: number;
  h: number;
  fill?: string;
}> = ({x, y, w, h, fill = PAPER_DEEP}) => {
  const cols = Math.max(2, Math.round(w / 50));
  const rows = Math.max(2, Math.round(h / 62));
  const winW = 20;
  const winH = 26;
  const gapX = (w - cols * winW) / (cols + 1);
  const gapY = (h - rows * winH) / (rows + 1);
  const windows: React.ReactNode[] = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const lit = (r * 7 + c * 3) % 4 === 0;
      windows.push(
        <rect
          key={`${r}-${c}`}
          x={x + gapX + c * (winW + gapX)}
          y={y + gapY + r * (winH + gapY)}
          width={winW}
          height={winH}
          rx={2}
          fill={lit ? GOLD : "#CFC6B2"}
          stroke={INK}
          strokeWidth={2}
        />,
      );
    }
  }
  return (
    <g>
      <rect x={x} y={y} width={w} height={h} rx={3} fill={fill} {...sharp} />
      {windows}
    </g>
  );
};

// --- location dot with pulse rings -----------------------------------------
export const LocationDot: React.FC<{x: number; y: number; pulse?: number; color?: string}> = ({
  x,
  y,
  pulse = 0,
  color = CORAL,
}) => {
  const ring = (phase: number) => {
    const p = (pulse + phase) % 1;
    return {r: 18 + p * 70, opacity: (1 - p) * 0.85};
  };
  const r1 = ring(0);
  const r2 = ring(0.5);
  return (
    <g transform={`translate(${x} ${y})`}>
      <circle cx="0" cy="0" r={r1.r} fill="none" stroke={color} strokeWidth={STROKE_THIN} opacity={r1.opacity} />
      <circle cx="0" cy="0" r={r2.r} fill="none" stroke={color} strokeWidth={STROKE_THIN} opacity={r2.opacity} />
      <circle cx="0" cy="0" r="16" fill={color} {...round} strokeWidth={STROKE_THIN} />
      <circle cx="0" cy="0" r="5.5" fill={PAPER} stroke="none" />
    </g>
  );
};

// --- concentric signal waves -----------------------------------------------
export const SignalWaves: React.FC<{
  x: number;
  y: number;
  progress: number;
  color?: string;
  spread?: number;
  count?: number;
  startAngle?: number;
  sweep?: number;
}> = ({x, y, progress, color = TEAL, spread = 220, count = 3, startAngle = -140, sweep = 100}) => {
  const a0 = (startAngle * Math.PI) / 180;
  const a1 = ((startAngle + sweep) * Math.PI) / 180;
  const arcs: React.ReactNode[] = [];
  for (let i = 0; i < count; i++) {
    const p = (progress + i / count) % 1;
    const r = 30 + p * spread;
    const x0 = x + r * Math.cos(a0);
    const y0 = y + r * Math.sin(a0);
    const x1 = x + r * Math.cos(a1);
    const y1 = y + r * Math.sin(a1);
    arcs.push(
      <path
        key={i}
        d={`M ${x0} ${y0} A ${r} ${r} 0 0 1 ${x1} ${y1}`}
        fill="none"
        stroke={color}
        strokeWidth={STROKE}
        strokeLinecap="round"
        opacity={(1 - p) * 0.95}
      />,
    );
  }
  return <g>{arcs}</g>;
};

// --- phone (simple, sharp) --------------------------------------------------
export const Phone: React.FC<{x: number; y: number; scale?: number; dotPulse?: number}> = ({
  x,
  y,
  scale = 1,
  dotPulse = 0,
}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <rect x={-150} y={-300} width={300} height={600} rx={30} fill="#FFFFFF" {...round} strokeWidth={STROKE_BOLD} />
    <rect x={-122} y={-258} width={244} height={516} rx={12} fill={PAPER} {...sharp} strokeWidth={STROKE_THIN} />
    {/* abstract streets */}
    <path d="M -110 -120 L 110 -60" stroke="#CFC6B2" strokeWidth={10} strokeLinecap="round" />
    <path d="M -70 -250 L -20 250" stroke="#CFC6B2" strokeWidth={10} strokeLinecap="round" />
    <path d="M 60 -250 L 100 250" stroke="#CFC6B2" strokeWidth={10} strokeLinecap="round" />
    <path d="M -120 120 L 120 170" stroke="#CFC6B2" strokeWidth={10} strokeLinecap="round" />
    <LocationDot x={6} y={-10} pulse={dotPulse} />
    <rect x={-26} y={-286} width={52} height={10} rx={5} fill="#D9D2C0" stroke="none" />
  </g>
);

// --- satellite (simple, sharp) ----------------------------------------------
export const Satellite: React.FC<{x: number; y: number; scale?: number; rotate?: number}> = ({
  x,
  y,
  scale = 1,
  rotate = 0,
}) => (
  <g transform={`translate(${x} ${y}) scale(${scale}) rotate(${rotate})`}>
    <rect x={-180} y={-34} width={120} height={68} rx={3} fill={BLUE} {...sharp} />
    <rect x={60} y={-34} width={120} height={68} rx={3} fill={BLUE} {...sharp} />
    <path d="M -150 -34 L -150 34 M -120 -34 L -120 34 M -90 -34 L -90 34" stroke={PAPER} strokeWidth={4} />
    <path d="M 90 -34 L 90 34 M 120 -34 L 120 34 M 150 -34 L 150 34" stroke={PAPER} strokeWidth={4} />
    <rect x={-46} y={-40} width={92} height={80} rx={5} fill={GOLD} {...sharp} />
    <ellipse cx={0} cy={-66} rx={30} ry={14} fill="#FFFFFF" {...round} strokeWidth={STROKE_THIN} />
    <path d="M 0 -66 L 0 -40" {...round} strokeWidth={STROKE_THIN} />
  </g>
);

// --- globe (simple, crisp) --------------------------------------------------
export const EarthArc: React.FC<{cx: number; cy: number; r: number}> = ({cx, cy, r}) => {
  const ocean = "#2B6CB0";
  const land = "#2FAE66";
  const landStroke = Math.max(2.5, r * 0.025);
  const id = `earth-clip-${Math.round(cx)}-${Math.round(cy)}-${Math.round(r)}`;
  return (
    <g>
      <defs>
        <clipPath id={id}>
          <circle cx={cx} cy={cy} r={r - STROKE_BOLD * 0.5} />
        </clipPath>
      </defs>
      <circle cx={cx} cy={cy} r={r} fill={ocean} stroke="none" />
      <g clipPath={`url(#${id})`}>
        <path
          d={`M ${cx - r * 0.78} ${cy - r * 0.36}
              C ${cx - r * 0.62} ${cy - r * 0.62} ${cx - r * 0.22} ${cy - r * 0.66} ${cx - r * 0.1} ${cy - r * 0.42}
              C ${cx - r * 0.02} ${cy - r * 0.24} ${cx - r * 0.22} ${cy - r * 0.08} ${cx - r * 0.08} ${cy + r * 0.12}
              C ${cx - r * 0.28} ${cy + r * 0.32} ${cx - r * 0.62} ${cy + r * 0.2} ${cx - r * 0.72} ${cy - r * 0.02}
              C ${cx - r * 0.84} ${cy - r * 0.12} ${cx - r * 0.9} ${cy - r * 0.22} ${cx - r * 0.78} ${cy - r * 0.36} Z`}
          fill={land}
          stroke={INK}
          strokeWidth={landStroke}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d={`M ${cx + r * 0.06} ${cy - r * 0.68}
              C ${cx + r * 0.32} ${cy - r * 0.82} ${cx + r * 0.72} ${cy - r * 0.56} ${cx + r * 0.66} ${cy - r * 0.24}
              C ${cx + r * 0.6} ${cy - r * 0.02} ${cx + r * 0.36} ${cy + r * 0.02} ${cx + r * 0.42} ${cy + r * 0.24}
              C ${cx + r * 0.2} ${cy + r * 0.22} ${cx + r * 0.0} ${cy + r * 0.02} ${cx - r * 0.02} ${cy - r * 0.24}
              C ${cx - r * 0.04} ${cy - r * 0.42} ${cx - r * 0.12} ${cy - r * 0.58} ${cx + r * 0.06} ${cy - r * 0.68} Z`}
          fill={land}
          stroke={INK}
          strokeWidth={landStroke}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d={`M ${cx + r * 0.38} ${cy + r * 0.36}
              C ${cx + r * 0.56} ${cy + r * 0.22} ${cx + r * 0.82} ${cy + r * 0.38} ${cx + r * 0.74} ${cy + r * 0.62}
              C ${cx + r * 0.62} ${cy + r * 0.82} ${cx + r * 0.24} ${cy + r * 0.76} ${cx + r * 0.2} ${cy + r * 0.54}
              C ${cx + r * 0.16} ${cy + r * 0.42} ${cx + r * 0.26} ${cy + r * 0.42} ${cx + r * 0.38} ${cy + r * 0.36} Z`}
          fill={land}
          stroke={INK}
          strokeWidth={landStroke}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </g>
      <path
        d={`M ${cx - r * 0.38} ${cy - r * 0.78} C ${cx - r * 0.02} ${cy - r * 0.96} ${cx + r * 0.42} ${cy - r * 0.82} ${cx + r * 0.68} ${cy - r * 0.48}`}
        fill="none"
        stroke="#8CC7F0"
        strokeWidth={Math.max(5, r * 0.07)}
        strokeLinecap="round"
        opacity={0.76}
      />
      <circle cx={cx} cy={cy} r={r} fill="none" {...round} strokeWidth={STROKE_BOLD} />
    </g>
  );
};

// --- star / sparkle ---------------------------------------------------------
export const Star: React.FC<{x: number; y: number; s?: number; color?: string}> = ({
  x,
  y,
  s = 10,
  color = INK_SOFT,
}) => (
  <path
    d={`M ${x} ${y - s} L ${x + s * 0.22} ${y - s * 0.22} L ${x + s} ${y} L ${x + s * 0.22} ${y + s * 0.22} L ${x} ${y + s} L ${x - s * 0.22} ${y + s * 0.22} L ${x - s} ${y} L ${x - s * 0.22} ${y - s * 0.22} Z`}
    fill={color}
    stroke="none"
  />
);

// --- speech bubble ----------------------------------------------------------
export const SpeechBubble: React.FC<{
  x: number;
  y: number;
  w: number;
  h: number;
  tailX: number;
  tailY: number;
  children: React.ReactNode;
  fontFamily: string;
}> = ({x, y, w, h, tailX, tailY, children, fontFamily}) => (
  <g>
    <path
      d={`M ${x} ${y + 16}
          Q ${x} ${y} ${x + 16} ${y}
          L ${x + w - 16} ${y} Q ${x + w} ${y} ${x + w} ${y + 16}
          L ${x + w} ${y + h - 16} Q ${x + w} ${y + h} ${x + w - 16} ${y + h}
          L ${x + 96} ${y + h} L ${tailX} ${tailY} L ${x + 56} ${y + h}
          L ${x + 16} ${y + h} Q ${x} ${y + h} ${x} ${y + h - 16} Z`}
      fill="#FFFFFF"
      {...round}
    />
    <foreignObject x={x + 18} y={y + 14} width={w - 36} height={h - 28}>
      <div
        style={{
          fontFamily,
          fontWeight: 800,
          color: INK,
          fontSize: 34,
          lineHeight: 1.08,
          textAlign: "center",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {children}
      </div>
    </foreignObject>
  </g>
);

// --- atomic clock (simple 12-tick, sharp) ----------------------------------
export const ClockFace: React.FC<{x: number; y: number; r: number; t: number}> = ({x, y, r, t}) => {
  const ticks: React.ReactNode[] = [];
  for (let i = 0; i < 12; i++) {
    const a = (i / 12) * Math.PI * 2;
    ticks.push(
      <path
        key={i}
        d={`M ${x + Math.cos(a) * (r - 16)} ${y + Math.sin(a) * (r - 16)} L ${x + Math.cos(a) * (r - 6)} ${y + Math.sin(a) * (r - 6)}`}
        stroke={INK}
        strokeWidth={STROKE_THIN}
        strokeLinecap="round"
      />,
    );
  }
  const minA = t * Math.PI * 2 - Math.PI / 2;
  const secA = t * 12 * Math.PI * 2 - Math.PI / 2;
  return (
    <g>
      <circle cx={x} cy={y} r={r} fill="#FFFFFF" {...round} strokeWidth={STROKE_BOLD} />
      {ticks}
      <path d={`M ${x} ${y} L ${x + Math.cos(minA) * r * 0.5} ${y + Math.sin(minA) * r * 0.5}`} {...round} strokeWidth={STROKE} />
      <path d={`M ${x} ${y} L ${x + Math.cos(secA) * r * 0.78} ${y + Math.sin(secA) * r * 0.78}`} stroke={CORAL} strokeWidth={STROKE_THIN} strokeLinecap="round" />
      <circle cx={x} cy={y} r={7} fill={INK} stroke="none" />
    </g>
  );
};
