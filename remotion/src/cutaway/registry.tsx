import type React from "react";
import {Building, ClockFace, EarthArc, LocationDot, Person, Phone, Satellite, SignalWaves} from "../flat/primitives";
import {BLUE, CORAL, GOLD, INK, INK_SOFT, PAPER, PAPER_DEEP, STROKE, STROKE_BOLD, STROKE_THIN, TEAL} from "../flat/theme";

export type RegistryRendererProps = {
  x: number;
  y: number;
  scale?: number;
  color?: string;
  localFrame: number;
  extra?: Record<string, unknown>;
};

type RegistryRenderer = (props: RegistryRendererProps) => React.ReactNode;

const sharp = {
  stroke: INK,
  strokeWidth: STROKE,
  strokeLinecap: "butt" as const,
  strokeLinejoin: "miter" as const,
};

const round = {
  stroke: INK,
  strokeWidth: STROKE,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

const labelText = {
  fontFamily: "Inter, Arial, sans-serif",
  fontWeight: 900,
  letterSpacing: 0,
};

const fitFontSize = (text: string, maxWidth: number, maxHeight: number, base: number, min = 20): number => {
  const words = text.trim().split(/\s+/).filter(Boolean);
  const longest = words.reduce((max, word) => Math.max(max, word.length), 1);
  const chars = Math.max(text.length, 1);
  const lineCount = chars > 30 ? 3 : chars > 14 ? 2 : 1;
  const byLongestWord = (maxWidth / longest) * 1.45;
  const byAllText = (maxWidth * lineCount) / chars * 1.65;
  const byHeight = maxHeight / (lineCount * 1.08);
  return Math.max(min, Math.min(base, byLongestWord, byAllText, byHeight));
};

const SvgFitText: React.FC<{
  text: string;
  x: number;
  y: number;
  w: number;
  h: number;
  color: string;
  baseSize: number;
}> = ({text, x, y, w, h, color, baseSize}) => (
  <foreignObject x={x - w / 2} y={y - h / 2} width={w} height={h}>
    <div
      style={{
        ...labelText,
        width: "100%",
        height: "100%",
        color,
        fontSize: fitFontSize(text, w, h, baseSize),
        lineHeight: 1.02,
        textAlign: "center",
        textTransform: "uppercase",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        overflowWrap: "anywhere",
        wordBreak: "normal",
        whiteSpace: "normal",
      }}
    >
      {text}
    </div>
  </foreignObject>
);

const Watch: RegistryRenderer = ({x, y, scale = 1, localFrame}) => {
  const wobble = Math.sin(localFrame / 5) * 4;
  return (
    <g transform={`translate(${x} ${y}) scale(${scale}) rotate(${wobble})`}>
      <rect x={-38} y={-142} width={76} height={74} rx={8} fill={PAPER_DEEP} {...sharp} />
      <rect x={-38} y={68} width={76} height={74} rx={8} fill={PAPER_DEEP} {...sharp} />
      <ClockFace x={0} y={0} r={82} t={(localFrame % 60) / 60} />
    </g>
  );
};

const Grid: RegistryRenderer = ({x, y, scale = 1, color = BLUE, localFrame}) => {
  const bend = Math.sin(localFrame / 18) * 18;
  const lines = Array.from({length: 7}, (_, i) => -240 + i * 80);
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      {lines.map((v) => (
        <path key={`h${v}`} d={`M -280 ${v / 2} C -80 ${v / 2 + bend} 80 ${v / 2 - bend} 280 ${v / 2}`} fill="none" stroke={color} strokeWidth={STROKE_THIN} />
      ))}
      {lines.map((v) => (
        <path key={`v${v}`} d={`M ${v} -150 C ${v + bend} -50 ${v - bend} 50 ${v} 150`} fill="none" stroke={color} strokeWidth={STROKE_THIN} />
      ))}
      <rect x={-280} y={-150} width={560} height={300} fill="none" {...sharp} />
    </g>
  );
};

const RangeCircle: RegistryRenderer = ({x, y, scale = 1, color = TEAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <circle cx={0} cy={0} r={152} fill="none" stroke={color} strokeWidth={STROKE} strokeLinecap="round" opacity={0.82} />
  </g>
);

const Point: RegistryRenderer = ({x, y, scale = 1, color = BLUE}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <LocationDot x={0} y={0} color={color} pulse={0.2} />
  </g>
);

const Ruler: RegistryRenderer = ({x, y, scale = 1, color = GOLD}) => (
  <g transform={`translate(${x} ${y}) scale(${scale}) rotate(-8)`}>
    <rect x={-220} y={-34} width={440} height={68} rx={3} fill={color} {...sharp} />
    {Array.from({length: 12}, (_, i) => (
      <path key={i} d={`M ${-190 + i * 35} -34 L ${-190 + i * 35} ${i % 2 === 0 ? 14 : 0}`} stroke={INK} strokeWidth={STROKE_THIN} />
    ))}
  </g>
);

const ArrowProp: RegistryRenderer = ({x, y, scale = 1, color = CORAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -190 0 L 150 0" stroke={color} strokeWidth={STROKE_BOLD} strokeLinecap="butt" />
    <path d="M 150 -58 L 230 0 L 150 58 Z" fill={color} {...sharp} />
  </g>
);

const Light: RegistryRenderer = ({x, y, scale = 1, color = GOLD}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -42 -70 L 170 -150 L 170 150 L -42 70 Z" fill={color} opacity={0.45} stroke="none" />
    <rect x={-112} y={-72} width={90} height={144} rx={5} fill={PAPER_DEEP} {...sharp} />
    <path d="M -22 -56 L 20 -34 L 20 34 L -22 56 Z" fill={color} {...sharp} />
  </g>
);

const Einstein: RegistryRenderer = ({x, y, scale = 1, color = CORAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -92 -80 L -136 -142 L -72 -124 L -42 -176 L -8 -122 L 34 -178 L 58 -118 L 126 -138 L 84 -78 Z" fill={PAPER} {...round} />
    <circle cx={0} cy={-62} r={82} fill="#F0D2B8" {...round} />
    <path d="M -34 -70 L -8 -72 M 34 -70 L 8 -72" stroke={INK} strokeWidth={STROKE_THIN} strokeLinecap="round" />
    <path d="M -48 -26 Q 0 -52 48 -26 Q 16 6 0 -10 Q -16 6 -48 -26 Z" fill={INK} stroke="none" />
    <path d="M -82 88 Q 0 32 82 88 L 112 164 L -112 164 Z" fill={color} {...round} />
  </g>
);

const MapProp: RegistryRenderer = ({x, y, scale = 1, color = TEAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -220 -118 L -74 -154 L 74 -118 L 220 -154 L 220 118 L 74 154 L -74 118 L -220 154 Z" fill={PAPER_DEEP} {...sharp} />
    <path d="M -74 -154 L -74 118 M 74 -118 L 74 154" stroke={INK} strokeWidth={STROKE_THIN} />
    <path d="M -190 10 C -82 -52 24 76 190 8" fill="none" stroke={color} strokeWidth={STROKE} strokeLinecap="round" />
    <LocationDot x={72} y={26} color={CORAL} pulse={0} />
  </g>
);

const Coffee: RegistryRenderer = ({x, y, scale = 1, color = CORAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -104 -70 L 76 -70 L 54 96 L -80 96 Z" fill={PAPER_DEEP} {...sharp} />
    <path d="M 76 -34 C 152 -42 152 54 60 48" fill="none" stroke={INK} strokeWidth={STROKE} />
    <path d="M -58 -132 C -84 -166 -36 -172 -58 -206 M 0 -132 C -24 -166 24 -172 0 -206 M 58 -132 C 34 -166 82 -172 58 -206" fill="none" stroke={INK_SOFT} strokeWidth={STROKE_THIN} strokeLinecap="round" />
    <LocationDot x={-12} y={8} color={color} pulse={0} />
  </g>
);

const Counter: RegistryRenderer = ({x, y, scale = 1, color = CORAL, extra}) => {
  const value = String(extra?.value ?? extra?.text ?? "42").trim() || "42";
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <rect x={-178} y={-112} width={356} height={224} rx={8} fill={PAPER} {...sharp} strokeWidth={STROKE_BOLD} />
      <SvgFitText text={value} x={0} y={4} w={304} h={164} color={color} baseSize={132} />
    </g>
  );
};

const Subscribe: RegistryRenderer = ({x, y, scale = 1, color = CORAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <rect x={-250} y={-80} width={500} height={160} rx={8} fill={color} {...sharp} strokeWidth={STROKE_BOLD} />
    <path d="M -176 -32 L -176 32 L -118 0 Z" fill={PAPER} stroke="none" />
    <text x={44} y={22} textAnchor="middle" fontSize={58} fill={PAPER} {...labelText}>
      SUBSCRIBE
    </text>
  </g>
);

const Label: RegistryRenderer = ({x, y, scale = 1, color = PAPER, extra}) => {
  const text = String(extra?.text ?? "LABEL").trim() || "LABEL";
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <rect x={-190} y={-64} width={380} height={128} rx={4} fill={color} {...sharp} />
      <SvgFitText text={text} x={0} y={1} w={330} h={86} color={INK} baseSize={44} />
    </g>
  );
};

const Stamp: RegistryRenderer = ({x, y, scale = 1, color = CORAL, extra}) => {
  const text = String(extra?.text ?? "STAMP").trim() || "STAMP";
  return (
    <g transform={`translate(${x} ${y}) scale(${scale}) rotate(-8)`}>
      <rect x={-210} y={-66} width={420} height={132} rx={3} fill="none" stroke={color} strokeWidth={STROKE_BOLD} />
      <SvgFitText text={text} x={0} y={0} w={356} h={88} color={color} baseSize={44} />
    </g>
  );
};

// A readable mandrill face: big ears, high brow, blue cheek pads, and the signature coral nose/muzzle.
const Mandrill: RegistryRenderer = ({x, y, scale = 1}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <circle cx={-124} cy={-40} r={40} fill={PAPER_DEEP} {...round} strokeWidth={STROKE_BOLD} />
    <circle cx={124} cy={-40} r={40} fill={PAPER_DEEP} {...round} strokeWidth={STROKE_BOLD} />
    <circle cx={-124} cy={-40} r={18} fill={PAPER} stroke="none" />
    <circle cx={124} cy={-40} r={18} fill={PAPER} stroke="none" />
    <path d="M -120 -62 Q -112 -160 0 -166 Q 112 -160 120 -62 Q 118 88 0 158 Q -118 88 -120 -62 Z" fill={PAPER} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -92 -70 Q -50 -118 0 -102 Q 50 -118 92 -70" fill={PAPER_DEEP} {...round} strokeWidth={STROKE} />
    <path d="M -32 -50 Q -96 -28 -84 78 Q -56 110 -36 76 Q -50 10 -32 -50 Z" fill={BLUE} {...round} />
    <path d="M 32 -50 Q 96 -28 84 78 Q 56 110 36 76 Q 50 10 32 -50 Z" fill={BLUE} {...round} />
    <path d="M -70 -6 Q -74 36 -60 76 M -52 -18 Q -56 30 -46 68" fill="none" stroke={INK} strokeWidth={STROKE_THIN} strokeLinecap="round" />
    <path d="M 70 -6 Q 74 36 60 76 M 52 -18 Q 56 30 46 68" fill="none" stroke={INK} strokeWidth={STROKE_THIN} strokeLinecap="round" />
    <path d="M -28 -54 Q 0 -70 28 -54 L 36 92 Q 18 124 0 130 Q -18 124 -36 92 Z" fill={CORAL} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -24 38 Q 0 52 24 38" fill="none" stroke={INK} strokeWidth={STROKE_THIN} strokeLinecap="round" />
    <circle cx={-10} cy={90} r={5} fill={INK} stroke="none" />
    <circle cx={10} cy={90} r={5} fill={INK} stroke="none" />
    <path d="M -70 -88 Q -44 -104 -20 -88 M 20 -88 Q 44 -104 70 -88" fill="none" stroke={INK} strokeWidth={STROKE} strokeLinecap="round" />
    <circle cx={-42} cy={-66} r={9} fill={INK} stroke="none" />
    <circle cx={42} cy={-66} r={9} fill={INK} stroke="none" />
  </g>
);

const Finch: RegistryRenderer = ({x, y, scale = 1}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -116 -8 Q -76 -90 32 -82 Q 116 -76 142 -18 Q 116 62 2 66 Q -78 64 -116 -8 Z" fill={PAPER} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -112 -8 L -170 -58 L -150 26 Z" fill={PAPER_DEEP} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -48 -38 Q 8 -24 34 42 Q -38 58 -76 4 Z" fill={GOLD} opacity={0.42} {...round} strokeWidth={STROKE_THIN} />
    <path d="M 130 -38 L 204 -10 L 130 18 Z" fill={CORAL} {...sharp} strokeWidth={STROKE_BOLD} />
    <path d="M 142 -10 L 204 -10" stroke={INK} strokeWidth={STROKE_THIN} strokeLinecap="round" />
    <circle cx={76} cy={-42} r={7} fill={INK} stroke="none" />
    <path d="M -18 60 L -30 104 M 38 58 L 52 102" stroke={INK} strokeWidth={STROKE} strokeLinecap="round" />
    <path d="M -50 104 L -14 104 M 34 102 L 72 102" stroke={INK} strokeWidth={STROKE_THIN} strokeLinecap="round" />
  </g>
);

// Identical to Person (same head, NO hair, same narrow shoulders) - differs ONLY by clothing: an
// A-line dress instead of the straight torso. Owner: "just change the clothes, not the hair, and make
// the shoulder area less broad."
const PersonFemale: RegistryRenderer = ({x, y, scale = 1, color = CORAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -18 78 L -18 122" {...round} strokeWidth={STROKE_BOLD} />
    <path d="M 18 78 L 18 122" {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -42 -6 Q -42 -52 0 -52 Q 42 -52 42 -6 L 62 80 Q 0 96 -62 80 Z" fill={color} {...round} />
    <circle cx={0} cy={-92} r={42} fill="#F0D2B8" {...round} />
    <circle cx={-14} cy={-96} r={5.5} fill={INK} stroke="none" />
    <circle cx={14} cy={-96} r={5.5} fill={INK} stroke="none" />
  </g>
);

const PersonArmsUp: RegistryRenderer = ({x, y, scale = 1, color = CORAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -42 -8 L -96 -88 M 42 -8 L 96 -88" {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -24 58 L -24 122 M 24 58 L 24 122" {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -44 -6 Q -44 -52 0 -52 Q 44 -52 44 -6 L 44 64 Q 0 84 -44 64 Z" fill={color} {...round} />
    <circle cx={0} cy={-92} r={42} fill="#F0D2B8" {...round} />
    <circle cx={-14} cy={-96} r={5.5} fill={INK} stroke="none" />
    <circle cx={14} cy={-96} r={5.5} fill={INK} stroke="none" />
  </g>
);

const PersonPointing: RegistryRenderer = ({x, y, scale = 1, color = CORAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -44 10 L -94 58 M 42 -8 L 126 -28" {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -24 58 L -24 122 M 24 58 L 24 122" {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -44 -6 Q -44 -52 0 -52 Q 44 -52 44 -6 L 44 64 Q 0 84 -44 64 Z" fill={color} {...round} />
    <circle cx={0} cy={-92} r={42} fill="#F0D2B8" {...round} />
    <circle cx={-14} cy={-96} r={5.5} fill={INK} stroke="none" />
    <circle cx={14} cy={-96} r={5.5} fill={INK} stroke="none" />
  </g>
);

const PersonSitting: RegistryRenderer = ({x, y, scale = 1, color = CORAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <rect x={-86} y={56} width={172} height={38} rx={10} fill={PAPER_DEEP} {...round} />
    <path d="M -46 14 L -100 48 M 46 14 L 100 48" {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -50 92 L -86 136 M 50 92 L 86 136" {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -44 -6 Q -44 -52 0 -52 Q 44 -52 44 -6 L 44 64 Q 0 84 -44 64 Z" fill={color} {...round} />
    <circle cx={0} cy={-92} r={42} fill="#F0D2B8" {...round} />
    <circle cx={-14} cy={-96} r={5.5} fill={INK} stroke="none" />
    <circle cx={14} cy={-96} r={5.5} fill={INK} stroke="none" />
  </g>
);

const PersonWalking: RegistryRenderer = ({x, y, scale = 1, color = CORAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -42 0 L -92 48 M 42 0 L 88 44" {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -18 58 L -78 132 M 22 58 L 76 126" {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -44 -6 Q -44 -52 0 -52 Q 44 -52 44 -6 L 44 64 Q 0 84 -44 64 Z" fill={color} {...round} />
    <circle cx={0} cy={-92} r={42} fill="#F0D2B8" {...round} />
    <circle cx={-14} cy={-96} r={5.5} fill={INK} stroke="none" />
    <circle cx={14} cy={-96} r={5.5} fill={INK} stroke="none" />
  </g>
);

const PersonFacing: RegistryRenderer = ({x, y, scale = 1, color = CORAL, extra}) => {
  const flip = extra?.facing === "left" ? -1 : 1;
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <g transform={`scale(${flip} 1)`}>
        <path d="M -24 58 L -24 122 M 24 58 L 24 122" {...round} strokeWidth={STROKE_BOLD} />
        <path d="M -44 -6 Q -44 -52 0 -52 Q 44 -52 44 -6 L 44 64 Q 0 84 -44 64 Z" fill={color} {...round} />
        <circle cx={0} cy={-92} r={42} fill="#F0D2B8" {...round} />
        <path d="M 12 -126 Q 46 -118 52 -88 Q 42 -102 10 -96 Z" fill={PAPER_DEEP} {...round} strokeWidth={STROKE_THIN} />
        <circle cx={-10} cy={-96} r={5.5} fill={INK} stroke="none" />
        <circle cx={18} cy={-94} r={5.5} fill={INK} stroke="none" />
      </g>
    </g>
  );
};

const RolePerson: RegistryRenderer = ({x, y, scale = 1, color = CORAL, extra}) => {
  const role = String(extra?.role ?? "suit");
  const coat = role === "doctor" || role === "scientist";
  const robe = role === "judge";
  const athlete = role === "athlete";
  const suit = role === "suit";
  const shirt = coat ? PAPER : robe ? INK : athlete ? TEAL : suit ? BLUE : color;
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <path d="M -24 58 L -24 122 M 24 58 L 24 122" {...round} strokeWidth={STROKE_BOLD} />
      <path d="M -44 -6 Q -44 -52 0 -52 Q 44 -52 44 -6 L 44 64 Q 0 84 -44 64 Z" fill={shirt} {...round} />
      {coat ? <path d="M 0 -44 L 0 76 M -30 -4 L 30 -4" stroke={BLUE} strokeWidth={STROKE_THIN} strokeLinecap="round" /> : null}
      {robe ? <rect x={-58} y={-20} width={116} height={98} rx={5} fill={INK} stroke="none" /> : null}
      {athlete ? <path d="M -30 8 L 30 8 M 0 -34 L 0 50" stroke={PAPER} strokeWidth={STROKE_THIN} strokeLinecap="round" /> : null}
      {suit ? <path d="M -22 -34 L 0 -2 L 22 -34 M 0 -2 L 0 72" fill="none" stroke={PAPER} strokeWidth={STROKE_THIN} strokeLinecap="round" /> : null}
      <circle cx={0} cy={-92} r={42} fill="#F0D2B8" {...round} />
      {role === "scientist" ? <path d="M -36 -116 L 0 -154 L 36 -116" fill={PAPER} {...round} strokeWidth={STROKE_THIN} /> : null}
      {role === "doctor" ? <path d="M -32 -140 L 32 -140 L 32 -116 L -32 -116 Z M 0 -148 L 0 -108 M -18 -128 L 18 -128" fill={PAPER} stroke={INK} strokeWidth={STROKE_THIN} /> : null}
      {role === "judge" ? <path d="M -50 -124 Q 0 -154 50 -124" fill="none" stroke={PAPER_DEEP} strokeWidth={STROKE_BOLD} strokeLinecap="round" /> : null}
      <circle cx={-14} cy={-96} r={5.5} fill={INK} stroke="none" />
      <circle cx={14} cy={-96} r={5.5} fill={INK} stroke="none" />
    </g>
  );
};

const Heart: RegistryRenderer = ({x, y, scale = 1}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M 0 118 L -112 8 Q -166 -52 -120 -104 Q -76 -150 0 -86 Q 76 -150 120 -104 Q 166 -52 112 8 Z" fill={CORAL} {...round} strokeWidth={STROKE_BOLD} />
  </g>
);

// Upright, clearly-readable gavel: a horizontal cylinder head (with banded ends) on a handle, resting
// over a sound block.
const Gavel: RegistryRenderer = ({x, y, scale = 1}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    {/* sound block */}
    <ellipse cx={0} cy={120} rx={118} ry={34} fill={PAPER_DEEP} {...round} strokeWidth={STROKE_BOLD} />
    <rect x={-104} y={95} width={208} height={38} rx={10} fill={PAPER_DEEP} stroke="none" />
    <path d="M -104 96 L 104 96 M -88 132 L 88 132" stroke={INK} strokeWidth={STROKE_THIN} strokeLinecap="round" />
    {/* gavel, gently tilted */}
    <g transform="rotate(-24 0 0)">
      {/* handle */}
      <rect x={-15} y={-8} width={30} height={182} rx={13} fill={PAPER} {...round} strokeWidth={STROKE_BOLD} />
      <path d="M 0 164 L 0 210" stroke={INK} strokeWidth={STROKE_BOLD} strokeLinecap="round" />
      {/* cylinder head */}
      <rect x={-122} y={-82} width={244} height={76} rx={16} fill={PAPER_DEEP} {...round} strokeWidth={STROKE_BOLD} />
      {/* end bands */}
      <rect x={-148} y={-70} width={42} height={52} rx={10} fill={PAPER} {...round} strokeWidth={STROKE} />
      <rect x={106} y={-70} width={42} height={52} rx={10} fill={PAPER} {...round} strokeWidth={STROKE} />
      <path d="M -74 -82 L -74 -6 M 74 -82 L 74 -6" stroke={INK} strokeWidth={STROKE} strokeLinecap="round" />
    </g>
  </g>
);

// A plain neutral box (NO cartoon face). This is the fallback for unknown assets, so it must look
// clean, not like a face peering out of the scene.
const GenericObject: RegistryRenderer = ({x, y, scale = 1, color = PAPER_DEEP}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <rect x={-110} y={-80} width={220} height={160} rx={16} fill={color} {...round} strokeWidth={STROKE_BOLD} />
  </g>
);

// A bold flat eye - the "Second Glance" brand mark (almond + coral iris + ink pupil + glint).
const Eye: RegistryRenderer = ({x, y, scale = 1, color = CORAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -176 0 Q 0 -132 176 0 Q 0 132 -176 0 Z" fill={PAPER} {...round} strokeWidth={STROKE_BOLD} />
    <circle cx={0} cy={0} r={72} fill={color} {...round} strokeWidth={STROKE_BOLD} />
    <circle cx={0} cy={0} r={31} fill={INK} stroke="none" />
    <circle cx={24} cy={-24} r={12} fill={PAPER} stroke="none" />
  </g>
);

// A sheet of paper with text lines - for "from a test" / document / paperwork beats.
const Document: RegistryRenderer = ({x, y, scale = 1}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <rect x={-86} y={-118} width={172} height={236} rx={10} fill={PAPER} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -56 -70 L 56 -70 M -56 -30 L 56 -30 M -56 10 L 56 10 M -56 50 L 18 50" stroke={INK} strokeWidth={STROKE_THIN} strokeLinecap="round" />
  </g>
);

const Car: RegistryRenderer = ({x, y, scale = 1, color = CORAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -170 26 L -132 -58 L 72 -58 L 142 26 Z" fill={color} {...round} strokeWidth={STROKE_BOLD} />
    <rect x={-210} y={-4} width={420} height={112} rx={18} fill={color} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -106 -54 L -54 -112 L 44 -112 L 88 -54 Z" fill={PAPER} {...round} />
    <circle cx={-116} cy={112} r={36} fill={INK} stroke="none" />
    <circle cx={116} cy={112} r={36} fill={INK} stroke="none" />
    <circle cx={-116} cy={112} r={14} fill={PAPER} stroke="none" />
    <circle cx={116} cy={112} r={14} fill={PAPER} stroke="none" />
  </g>
);

const Tree: RegistryRenderer = ({x, y, scale = 1, color = TEAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <rect x={-24} y={16} width={48} height={132} rx={8} fill={GOLD} {...round} />
    <circle cx={0} cy={-72} r={92} fill={color} {...round} strokeWidth={STROKE_BOLD} />
    <circle cx={-72} cy={-28} r={58} fill={color} {...round} />
    <circle cx={74} cy={-24} r={60} fill={color} {...round} />
  </g>
);

const House: RegistryRenderer = ({x, y, scale = 1, color = PAPER_DEEP}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -176 -10 L 0 -154 L 176 -10 Z" fill={CORAL} {...round} strokeWidth={STROKE_BOLD} />
    <rect x={-138} y={-10} width={276} height={194} rx={10} fill={color} {...round} strokeWidth={STROKE_BOLD} />
    <rect x={-32} y={70} width={64} height={114} rx={6} fill={PAPER} {...sharp} />
    <rect x={-104} y={36} width={54} height={48} rx={4} fill={PAPER} {...sharp} />
    <rect x={50} y={36} width={54} height={48} rx={4} fill={PAPER} {...sharp} />
  </g>
);

const Coin: RegistryRenderer = ({x, y, scale = 1, color = GOLD}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <circle cx={0} cy={0} r={120} fill={color} {...round} strokeWidth={STROKE_BOLD} />
    <circle cx={0} cy={0} r={82} fill="none" stroke={INK} strokeWidth={STROKE_THIN} />
    <path d="M -30 -54 L 34 -54 M 0 -54 L 0 64 M -38 64 L 38 64" stroke={INK} strokeWidth={STROKE_BOLD} strokeLinecap="round" />
  </g>
);

const Money: RegistryRenderer = ({x, y, scale = 1, color = TEAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale}) rotate(-5)`}>
    <rect x={-176} y={-92} width={352} height={184} rx={12} fill={PAPER} {...round} strokeWidth={STROKE_BOLD} />
    <rect x={-132} y={-50} width={264} height={100} rx={8} fill={color} opacity={0.22} stroke="none" />
    <circle cx={0} cy={0} r={46} fill={color} {...round} />
    <path d="M -142 -56 L -92 -56 M 92 56 L 142 56" stroke={INK} strokeWidth={STROKE_THIN} strokeLinecap="round" />
  </g>
);

const Trophy: RegistryRenderer = ({x, y, scale = 1, color = GOLD}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -82 -116 L 82 -116 L 58 20 Q 0 74 -58 20 Z" fill={color} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -82 -86 L -154 -86 Q -148 4 -62 -4 M 82 -86 L 154 -86 Q 148 4 62 -4" fill="none" stroke={INK} strokeWidth={STROKE_BOLD} strokeLinecap="round" />
    <path d="M 0 66 L 0 122 M -74 122 L 74 122 L 100 172 L -100 172 Z" fill={color} {...round} />
  </g>
);

const Book: RegistryRenderer = ({x, y, scale = 1, color = BLUE}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -138 -138 L -8 -104 L -8 142 L -138 108 Z" fill={color} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M 138 -138 L 8 -104 L 8 142 L 138 108 Z" fill={PAPER_DEEP} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M 0 -104 L 0 142" stroke={INK} strokeWidth={STROKE} strokeLinecap="round" />
    <path d="M 38 -48 L 104 -66 M 38 6 L 104 -12 M 38 60 L 92 46" stroke={INK_SOFT} strokeWidth={STROKE_THIN} strokeLinecap="round" />
  </g>
);

const Bag: RegistryRenderer = ({x, y, scale = 1, color = CORAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -116 -28 Q -102 -130 0 -130 Q 102 -130 116 -28" fill="none" stroke={INK} strokeWidth={STROKE_BOLD} strokeLinecap="round" />
    <rect x={-154} y={-42} width={308} height={238} rx={18} fill={color} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -74 34 L 74 34" stroke={INK} strokeWidth={STROKE_THIN} strokeLinecap="round" />
  </g>
);

const Bottle: RegistryRenderer = ({x, y, scale = 1, color = TEAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <rect x={-44} y={-158} width={88} height={66} rx={10} fill={PAPER_DEEP} {...round} />
    <path d="M -72 -92 L 72 -92 L 92 170 L -92 170 Z" fill={color} {...round} strokeWidth={STROKE_BOLD} />
    <rect x={-54} y={-8} width={108} height={74} rx={8} fill={PAPER} {...sharp} />
  </g>
);

const Cup: RegistryRenderer = ({x, y, scale = 1, color = PAPER_DEEP}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -102 -96 L 92 -96 L 66 134 L -66 134 Z" fill={color} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M 92 -46 C 178 -54 174 76 64 66" fill="none" stroke={INK} strokeWidth={STROKE_BOLD} strokeLinecap="round" />
    <path d="M -62 -38 L 56 -38" stroke={INK_SOFT} strokeWidth={STROKE_THIN} strokeLinecap="round" />
  </g>
);

const BoxProp: RegistryRenderer = ({x, y, scale = 1, color = GOLD}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -146 -54 L 0 -126 L 146 -54 L 0 18 Z" fill={PAPER_DEEP} {...round} />
    <path d="M -146 -54 L 0 18 L 0 178 L -146 94 Z" fill={color} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M 146 -54 L 0 18 L 0 178 L 146 94 Z" fill={PAPER} {...round} strokeWidth={STROKE_BOLD} />
  </g>
);

const Key: RegistryRenderer = ({x, y, scale = 1, color = GOLD}) => (
  <g transform={`translate(${x} ${y}) scale(${scale}) rotate(-12)`}>
    <circle cx={-112} cy={0} r={58} fill="none" stroke={color} strokeWidth={STROKE_BOLD} />
    <path d="M -54 0 L 176 0 M 96 0 L 96 58 M 138 0 L 138 38" stroke={color} strokeWidth={STROKE_BOLD} strokeLinecap="butt" />
  </g>
);

const Lightbulb: RegistryRenderer = ({x, y, scale = 1, color = GOLD}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -86 -40 Q -86 -138 0 -138 Q 86 -138 86 -40 Q 86 28 42 76 L -42 76 Q -86 28 -86 -40 Z" fill={color} {...round} strokeWidth={STROKE_BOLD} />
    <rect x={-42} y={76} width={84} height={72} rx={10} fill={PAPER_DEEP} {...round} />
    <path d="M -98 -164 L -136 -204 M 98 -164 L 136 -204 M 0 -176 L 0 -230" stroke={INK} strokeWidth={STROKE_THIN} strokeLinecap="round" />
  </g>
);

const Lock: RegistryRenderer = ({x, y, scale = 1, color = BLUE}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -82 -30 L -82 -90 Q -82 -164 0 -164 Q 82 -164 82 -90 L 82 -30" fill="none" stroke={INK} strokeWidth={STROKE_BOLD} strokeLinecap="round" />
    <rect x={-126} y={-36} width={252} height={190} rx={18} fill={color} {...round} strokeWidth={STROKE_BOLD} />
    <circle cx={0} cy={40} r={18} fill={INK} stroke="none" />
    <path d="M 0 58 L 0 98" stroke={INK} strokeWidth={STROKE} strokeLinecap="round" />
  </g>
);

const Shield: RegistryRenderer = ({x, y, scale = 1, color = BLUE}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M 0 -162 L 132 -110 L 112 30 Q 80 116 0 166 Q -80 116 -112 30 L -132 -110 Z" fill={color} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M 0 -104 L 0 104 M -68 -72 L 68 -72" stroke={INK} strokeWidth={STROKE_THIN} strokeLinecap="round" />
  </g>
);

const Flag: RegistryRenderer = ({x, y, scale = 1, color = CORAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -112 -150 L -112 172" stroke={INK} strokeWidth={STROKE_BOLD} strokeLinecap="round" />
    <path d="M -112 -140 L 120 -118 L 78 -20 L -112 -42 Z" fill={color} {...round} strokeWidth={STROKE_BOLD} />
  </g>
);

const Ball: RegistryRenderer = ({x, y, scale = 1, color = PAPER}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <circle cx={0} cy={0} r={132} fill={color} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -112 -62 Q 0 -14 112 -62 M -112 62 Q 0 14 112 62 M 0 -132 Q -42 0 0 132 M 0 -132 Q 42 0 0 132" fill="none" stroke={INK} strokeWidth={STROKE_THIN} strokeLinecap="round" />
  </g>
);

const CameraProp: RegistryRenderer = ({x, y, scale = 1, color = PAPER_DEEP}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <rect x={-174} y={-78} width={348} height={196} rx={18} fill={color} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -100 -78 L -64 -132 L 34 -132 L 70 -78 Z" fill={color} {...round} />
    <circle cx={28} cy={20} r={68} fill={PAPER} {...round} strokeWidth={STROKE_BOLD} />
    <circle cx={28} cy={20} r={30} fill={INK} stroke="none" />
    <rect x={-142} y={-34} width={54} height={34} rx={5} fill={CORAL} stroke="none" />
  </g>
);

const Microphone: RegistryRenderer = ({x, y, scale = 1, color = INK}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <rect x={-58} y={-156} width={116} height={198} rx={58} fill={PAPER_DEEP} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -96 -22 Q -94 98 0 98 Q 94 98 96 -22" fill="none" stroke={color} strokeWidth={STROKE_BOLD} strokeLinecap="round" />
    <path d="M 0 98 L 0 164 M -74 164 L 74 164 M -34 -92 L 34 -92 M -34 -38 L 34 -38" stroke={color} strokeWidth={STROKE_THIN} strokeLinecap="round" />
  </g>
);

const Laptop: RegistryRenderer = ({x, y, scale = 1, color = BLUE}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <rect x={-156} y={-126} width={312} height={210} rx={12} fill={PAPER} {...round} strokeWidth={STROKE_BOLD} />
    <rect x={-118} y={-86} width={236} height={132} rx={4} fill={color} opacity={0.26} stroke="none" />
    <path d="M -216 104 L 216 104 L 170 156 L -170 156 Z" fill={PAPER_DEEP} {...round} strokeWidth={STROKE_BOLD} />
  </g>
);

const ChartBar: RegistryRenderer = ({x, y, scale = 1, color = BLUE}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -158 132 L 164 132 M -158 132 L -158 -132" stroke={INK} strokeWidth={STROKE} strokeLinecap="round" />
    <rect x={-104} y={12} width={54} height={120} fill={color} {...sharp} />
    <rect x={-28} y={-58} width={54} height={190} fill={CORAL} {...sharp} />
    <rect x={48} y={-104} width={54} height={236} fill={GOLD} {...sharp} />
  </g>
);

const ChartLine: RegistryRenderer = ({x, y, scale = 1, color = TEAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -158 132 L 164 132 M -158 132 L -158 -132" stroke={INK} strokeWidth={STROKE} strokeLinecap="round" />
    <path d="M -118 66 L -42 12 L 28 34 L 120 -86" fill="none" stroke={color} strokeWidth={STROKE_BOLD} strokeLinecap="round" strokeLinejoin="round" />
    {[-118, -42, 28, 120].map((cx, i) => <circle key={cx} cx={cx} cy={[66, 12, 34, -86][i]} r={13} fill={PAPER} {...round} />)}
  </g>
);

const PieChart: RegistryRenderer = ({x, y, scale = 1}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <circle cx={0} cy={0} r={132} fill={PAPER} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M 0 0 L 0 -132 A 132 132 0 0 1 124 44 Z" fill={CORAL} {...sharp} />
    <path d="M 0 0 L 124 44 A 132 132 0 0 1 -84 102 Z" fill={BLUE} {...sharp} />
    <path d="M 0 -132 L 0 0 L 124 44 M 0 0 L -84 102" stroke={INK} strokeWidth={STROKE_THIN} />
  </g>
);

const ArrowUp: RegistryRenderer = ({x, y, scale = 1, color = TEAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M 0 154 L 0 -88" stroke={color} strokeWidth={STROKE_BOLD} strokeLinecap="butt" />
    <path d="M -72 -72 L 0 -162 L 72 -72 Z" fill={color} {...sharp} />
  </g>
);

const ArrowDown: RegistryRenderer = ({x, y, scale = 1, color = CORAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M 0 -154 L 0 88" stroke={color} strokeWidth={STROKE_BOLD} strokeLinecap="butt" />
    <path d="M -72 72 L 0 162 L 72 72 Z" fill={color} {...sharp} />
  </g>
);

const Checkmark: RegistryRenderer = ({x, y, scale = 1, color = TEAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -138 8 L -42 104 L 152 -124" fill="none" stroke={color} strokeWidth={STROKE_BOLD * 1.25} strokeLinecap="round" strokeLinejoin="round" />
  </g>
);

const Cross: RegistryRenderer = ({x, y, scale = 1, color = CORAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -116 -116 L 116 116 M 116 -116 L -116 116" stroke={color} strokeWidth={STROKE_BOLD * 1.2} strokeLinecap="round" />
  </g>
);

const QuestionMark: RegistryRenderer = ({x, y, scale = 1, color = BLUE}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -74 -70 Q -62 -152 16 -152 Q 92 -152 92 -78 Q 92 -28 30 8 Q 0 26 0 66" fill="none" stroke={color} strokeWidth={STROKE_BOLD} strokeLinecap="round" />
    <circle cx={0} cy={130} r={18} fill={color} stroke="none" />
  </g>
);

const Warning: RegistryRenderer = ({x, y, scale = 1, color = GOLD}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M 0 -162 L 164 140 L -164 140 Z" fill={color} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M 0 -48 L 0 54" stroke={INK} strokeWidth={STROKE_BOLD} strokeLinecap="round" />
    <circle cx={0} cy={96} r={14} fill={INK} stroke="none" />
  </g>
);

const Gear: RegistryRenderer = ({x, y, scale = 1, color = PAPER_DEEP}) => {
  const teeth = Array.from({length: 8}, (_, i) => i * 45);
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      {teeth.map((deg) => <rect key={deg} x={-22} y={-168} width={44} height={68} rx={6} fill={color} {...sharp} transform={`rotate(${deg})`} />)}
      <circle cx={0} cy={0} r={116} fill={color} {...round} strokeWidth={STROKE_BOLD} />
      <circle cx={0} cy={0} r={46} fill={PAPER} {...round} />
    </g>
  );
};

const Magnet: RegistryRenderer = ({x, y, scale = 1, color = CORAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -112 -114 L -112 28 Q -112 130 0 130 Q 112 130 112 28 L 112 -114" fill="none" stroke={color} strokeWidth={70} strokeLinecap="butt" />
    <path d="M -152 -114 L -72 -114 M 72 -114 L 152 -114" stroke={INK} strokeWidth={STROKE_BOLD} strokeLinecap="round" />
  </g>
);

const Brain: RegistryRenderer = ({x, y, scale = 1, color = CORAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -24 -126 Q -116 -136 -128 -42 Q -182 -18 -144 58 Q -138 128 -42 126 Q -12 158 38 126 Q 136 132 144 42 Q 180 2 132 -48 Q 126 -136 28 -126 Q 4 -154 -24 -126 Z" fill={color} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -24 -126 L -24 126 M -102 -36 Q -46 -48 -24 -12 M 24 -72 Q 88 -72 102 -22 M 24 34 Q 82 44 94 96" fill="none" stroke={INK} strokeWidth={STROKE_THIN} strokeLinecap="round" />
  </g>
);

const Dna: RegistryRenderer = ({x, y, scale = 1, color = BLUE}) => {
  const ys = [-132, -82, -32, 18, 68, 118];
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <path d="M -72 -144 C 118 -72 -118 72 72 144" fill="none" stroke={color} strokeWidth={STROKE_BOLD} strokeLinecap="round" />
      <path d="M 72 -144 C -118 -72 118 72 -72 144" fill="none" stroke={CORAL} strokeWidth={STROKE_BOLD} strokeLinecap="round" />
      {ys.map((yy) => <path key={yy} d={`M -58 ${yy} L 58 ${yy}`} stroke={INK} strokeWidth={STROKE_THIN} strokeLinecap="round" />)}
    </g>
  );
};

const Pill: RegistryRenderer = ({x, y, scale = 1}) => (
  <g transform={`translate(${x} ${y}) scale(${scale}) rotate(-28)`}>
    <rect x={-148} y={-58} width={296} height={116} rx={58} fill={PAPER} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M 0 -58 L 0 58" stroke={INK} strokeWidth={STROKE} />
    <path d="M 0 -58 L 90 -58 Q 148 -58 148 0 Q 148 58 90 58 L 0 58 Z" fill={CORAL} stroke="none" />
  </g>
);

const Syringe: RegistryRenderer = ({x, y, scale = 1, color = TEAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale}) rotate(-32)`}>
    <rect x={-70} y={-52} width={190} height={104} rx={10} fill={PAPER} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M 120 0 L 218 0 M 218 0 L 258 -34 M -136 0 L -70 0 M -136 -54 L -136 54" stroke={INK} strokeWidth={STROKE_BOLD} strokeLinecap="round" />
    <path d="M -20 -52 L -20 52 M 36 -52 L 36 52" stroke={INK_SOFT} strokeWidth={STROKE_THIN} />
    <rect x={-68} y={-50} width={70} height={100} fill={color} opacity={0.28} stroke="none" />
  </g>
);

const ScaleJustice: RegistryRenderer = ({x, y, scale = 1, color = GOLD}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M 0 -150 L 0 136 M -108 136 L 108 136 M -170 -80 L 170 -80" stroke={INK} strokeWidth={STROKE_BOLD} strokeLinecap="round" />
    <path d="M -122 -80 L -184 30 L -62 30 Z M 122 -80 L 62 30 L 184 30 Z" fill={color} {...round} />
    <path d="M -204 30 Q -122 82 -42 30 M 42 30 Q 122 82 204 30" fill="none" stroke={INK} strokeWidth={STROKE} strokeLinecap="round" />
  </g>
);

const Ballot: RegistryRenderer = ({x, y, scale = 1, color = BLUE}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <rect x={-138} y={-124} width={276} height={248} rx={12} fill={PAPER} {...round} strokeWidth={STROKE_BOLD} />
    <rect x={-86} y={-66} width={46} height={46} rx={4} fill="none" {...sharp} />
    <path d="M -78 -42 L -62 -24 L -28 -72" fill="none" stroke={color} strokeWidth={STROKE} strokeLinecap="round" />
    <path d="M -12 -42 L 82 -42 M -86 38 L 82 38" stroke={INK_SOFT} strokeWidth={STROKE_THIN} strokeLinecap="round" />
  </g>
);

const Crown: RegistryRenderer = ({x, y, scale = 1, color = GOLD}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -142 92 L -176 -96 L -58 4 L 0 -132 L 58 4 L 176 -96 L 142 92 Z" fill={color} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -126 122 L 126 122" stroke={INK} strokeWidth={STROKE_BOLD} strokeLinecap="round" />
    <circle cx={0} cy={-132} r={16} fill={CORAL} stroke="none" />
  </g>
);

const Target: RegistryRenderer = ({x, y, scale = 1, color = CORAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <circle cx={0} cy={0} r={146} fill={PAPER} {...round} strokeWidth={STROKE_BOLD} />
    <circle cx={0} cy={0} r={96} fill="none" stroke={color} strokeWidth={STROKE_BOLD} />
    <circle cx={0} cy={0} r={42} fill={color} stroke="none" />
    <path d="M -176 0 L -124 0 M 124 0 L 176 0 M 0 -176 L 0 -124 M 0 124 L 0 176" stroke={INK} strokeWidth={STROKE_THIN} strokeLinecap="round" />
  </g>
);

const Sun: RegistryRenderer = ({x, y, scale = 1, color = GOLD}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    {Array.from({length: 10}, (_, i) => <path key={i} d="M 0 -178 L 0 -126" stroke={INK} strokeWidth={STROKE_THIN} strokeLinecap="round" transform={`rotate(${i * 36})`} />)}
    <circle cx={0} cy={0} r={96} fill={color} {...round} strokeWidth={STROKE_BOLD} />
  </g>
);

const Cloud: RegistryRenderer = ({x, y, scale = 1, color = PAPER}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -150 42 Q -170 -36 -86 -46 Q -54 -116 30 -82 Q 76 -110 126 -58 Q 194 -50 184 42 Z" fill={color} {...round} strokeWidth={STROKE_BOLD} />
  </g>
);

const Rain: RegistryRenderer = ({x, y, scale = 1, color = BLUE}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <Cloud x={0} y={-72} scale={0.72} color={PAPER_DEEP} localFrame={0} />
    {[-92, -36, 22, 84].map((cx, i) => <path key={cx} d={`M ${cx} 28 L ${cx - 28} ${118 + (i % 2) * 22}`} stroke={color} strokeWidth={STROKE} strokeLinecap="round" />)}
  </g>
);

const StarProp: RegistryRenderer = ({x, y, scale = 1, color = GOLD}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M 0 -152 L 38 -48 L 148 -48 L 58 18 L 92 126 L 0 60 L -92 126 L -58 18 L -148 -48 L -38 -48 Z" fill={color} {...round} strokeWidth={STROKE_BOLD} />
  </g>
);

const Moon: RegistryRenderer = ({x, y, scale = 1, color = GOLD}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M 76 -128 Q 0 -92 0 0 Q 0 92 76 128 Q -104 104 -122 0 Q -104 -104 76 -128 Z" fill={color} {...round} strokeWidth={STROKE_BOLD} />
  </g>
);

const MountainShape: RegistryRenderer = ({x, y, scale = 1, color = BLUE}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -190 132 L -66 -120 L 16 -8 L 82 -158 L 210 132 Z" fill={color} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -66 -120 L -28 -68 L -82 -54 M 82 -158 L 122 -82 L 58 -72" fill={PAPER} stroke={INK} strokeWidth={STROKE_THIN} strokeLinejoin="round" />
  </g>
);

const Wave: RegistryRenderer = ({x, y, scale = 1, color = BLUE}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -190 60 Q -92 -30 0 60 T 190 60 L 190 136 L -190 136 Z" fill={color} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -158 96 Q -82 48 -6 96 T 150 96" fill="none" stroke={PAPER} strokeWidth={STROKE_THIN} strokeLinecap="round" />
  </g>
);

const Fire: RegistryRenderer = ({x, y, scale = 1, color = CORAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M 0 144 Q -118 84 -82 -24 Q -60 -90 -6 -136 Q -10 -54 42 -18 Q 72 -70 82 -112 Q 154 -10 112 72 Q 82 126 0 144 Z" fill={color} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M 0 102 Q -52 62 -28 8 Q -8 -36 28 -66 Q 30 -16 56 8 Q 84 64 0 102 Z" fill={GOLD} stroke="none" />
  </g>
);

const Plant: RegistryRenderer = ({x, y, scale = 1, color = TEAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M 0 126 L 0 -80" stroke={INK} strokeWidth={STROKE_BOLD} strokeLinecap="round" />
    <path d="M 0 -42 Q -104 -86 -118 -4 Q -52 26 0 -42 Z M 0 -8 Q 106 -58 120 24 Q 50 54 0 -8 Z M 0 -80 Q -42 -154 24 -166 Q 62 -112 0 -80 Z" fill={color} {...round} />
    <rect x={-78} y={116} width={156} height={64} rx={8} fill={PAPER_DEEP} {...round} strokeWidth={STROKE_BOLD} />
  </g>
);

export const registry = {
  person: ({x, y, scale = 1, color = CORAL}: RegistryRendererProps) => <Person x={x} y={y} scale={scale} shirt={color} />,
  person_female: PersonFemale,
  person_arms_up: PersonArmsUp,
  person_pointing: PersonPointing,
  person_sitting: PersonSitting,
  person_walking: PersonWalking,
  person_left: (props: RegistryRendererProps) => <PersonFacing {...props} extra={{...(props.extra ?? {}), facing: "left"}} />,
  person_right: (props: RegistryRendererProps) => <PersonFacing {...props} extra={{...(props.extra ?? {}), facing: "right"}} />,
  doctor: (props: RegistryRendererProps) => <RolePerson {...props} extra={{...(props.extra ?? {}), role: "doctor"}} />,
  scientist: (props: RegistryRendererProps) => <RolePerson {...props} extra={{...(props.extra ?? {}), role: "scientist"}} />,
  judge: (props: RegistryRendererProps) => <RolePerson {...props} extra={{...(props.extra ?? {}), role: "judge"}} />,
  athlete: (props: RegistryRendererProps) => <RolePerson {...props} extra={{...(props.extra ?? {}), role: "athlete"}} />,
  suit: (props: RegistryRendererProps) => <RolePerson {...props} extra={{...(props.extra ?? {}), role: "suit"}} />,
  phone: ({x, y, scale = 1, localFrame}: RegistryRendererProps) => <Phone x={x} y={y} scale={scale} dotPulse={(localFrame / 45) % 1} />,
  city: ({x, y, scale = 1}: RegistryRendererProps) => (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <Building x={-230} y={-240} w={180} h={300} />
      <Building x={-20} y={-320} w={190} h={380} />
      <Building x={210} y={-210} w={170} h={270} />
    </g>
  ),
  building: ({x, y, scale = 1, color = PAPER_DEEP}: RegistryRendererProps) => (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <Building x={-100} y={-260} w={200} h={320} fill={color} />
    </g>
  ),
  clock: ({x, y, scale = 1, localFrame}: RegistryRendererProps) => (
    // Scale the whole group (not just the radius) so the outline thins with the
    // clock; otherwise a small clock keeps the full-size ring and reads as a tire.
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <ClockFace x={0} y={0} r={120} t={(localFrame % 60) / 60} />
    </g>
  ),
  atomic_clock: ({x, y, scale = 1, localFrame}: RegistryRendererProps) => (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <ClockFace x={0} y={0} r={150} t={(localFrame % 60) / 60} />
    </g>
  ),
  satellite: ({x, y, scale = 1, localFrame}: RegistryRendererProps) => <Satellite x={x} y={y} scale={scale} rotate={Math.sin(localFrame / 30) * 4} />,
  signal: ({x, y, scale = 1, color = CORAL, localFrame}: RegistryRendererProps) => <SignalWaves x={x} y={y} progress={(localFrame / 50) % 1} color={color} spread={220 * scale} />,
  signal_beam: Light,
  earth: ({x, y, scale = 1}: RegistryRendererProps) => (
    // Scale the whole group (not just r) so the outline thins with the globe - otherwise a
    // small earth keeps the full-size border and reads as a wheel (same as the old clock bug).
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <EarthArc cx={0} cy={0} r={170} />
    </g>
  ),
  map_pin: Point,
  dot: Point,
  watch: Watch,
  grid: Grid,
  sphere: RangeCircle,
  ring: RangeCircle,
  point: Point,
  ruler: Ruler,
  arrow: ArrowProp,
  light: Light,
  einstein: Einstein,
  mandrill: Mandrill,
  finch: Finch,
  heart: Heart,
  gavel: Gavel,
  document: Document,
  eye: Eye,
  car: Car,
  tree: Tree,
  house: House,
  coin: Coin,
  money: Money,
  trophy: Trophy,
  book: Book,
  bag: Bag,
  bottle: Bottle,
  cup: Cup,
  box: BoxProp,
  key: Key,
  lightbulb: Lightbulb,
  lock: Lock,
  shield: Shield,
  flag: Flag,
  ball: Ball,
  camera: CameraProp,
  microphone: Microphone,
  laptop: Laptop,
  chart_bar: ChartBar,
  chart_line: ChartLine,
  pie_chart: PieChart,
  arrow_up: ArrowUp,
  arrow_down: ArrowDown,
  checkmark: Checkmark,
  cross: Cross,
  question_mark: QuestionMark,
  warning: Warning,
  gear: Gear,
  magnet: Magnet,
  brain: Brain,
  dna: Dna,
  pill: Pill,
  syringe: Syringe,
  scale_justice: ScaleJustice,
  ballot: Ballot,
  crown: Crown,
  target: Target,
  sun: Sun,
  cloud: Cloud,
  rain: Rain,
  star: StarProp,
  moon: Moon,
  mountain_shape: MountainShape,
  wave: Wave,
  fire: Fire,
  plant: Plant,
  map: MapProp,
  coffee: Coffee,
  counter: Counter,
  number: Counter,
  subscribe: Subscribe,
  label: Label,
  stamp: Stamp,
  generic_object: GenericObject,
} satisfies Record<string, RegistryRenderer>;

export type RegistryAssetName = keyof typeof registry;

export const registryAssetNames = Object.keys(registry).sort();

export const renderRegistryAsset = (name: string, props: RegistryRendererProps): React.ReactNode => {
  const renderer = (registry as Record<string, RegistryRenderer>)[name] ?? registry.generic_object;
  return renderer(props);
};
