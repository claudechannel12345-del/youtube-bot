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

// A clearer "colorful monkey face": rounded ears, forward close-set eyes, a central vertical CORAL
// muzzle, and the signature BLUE ridged cheek pads flanking it.
const Mandrill: RegistryRenderer = ({x, y, scale = 1}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <circle cx={-116} cy={-34} r={28} fill={PAPER_DEEP} {...round} strokeWidth={STROKE_BOLD} />
    <circle cx={116} cy={-34} r={28} fill={PAPER_DEEP} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -118 -56 Q -118 -150 0 -150 Q 118 -150 118 -56 Q 118 96 0 152 Q -118 96 -118 -56 Z" fill={PAPER} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -28 -44 Q -86 -26 -80 74 Q -54 96 -40 72 Q -48 6 -28 -44 Z" fill={BLUE} {...round} />
    <path d="M 28 -44 Q 86 -26 80 74 Q 54 96 40 72 Q 48 6 28 -44 Z" fill={BLUE} {...round} />
    <path d="M -64 -6 Q -66 38 -56 70 M -48 -14 Q -50 32 -44 66" fill="none" stroke={INK} strokeWidth={STROKE_THIN} strokeLinecap="round" />
    <path d="M 64 -6 Q 66 38 56 70 M 48 -14 Q 50 32 44 66" fill="none" stroke={INK} strokeWidth={STROKE_THIN} strokeLinecap="round" />
    <path d="M -26 -50 Q 0 -60 26 -50 L 32 98 Q 0 124 -32 98 Z" fill={CORAL} {...round} strokeWidth={STROKE_BOLD} />
    <circle cx={-9} cy={92} r={4.5} fill={INK} stroke="none" />
    <circle cx={9} cy={92} r={4.5} fill={INK} stroke="none" />
    <path d="M -68 -86 Q -44 -100 -22 -88 M 22 -88 Q 44 -100 68 -86" fill="none" stroke={INK} strokeWidth={STROKE} strokeLinecap="round" />
    <circle cx={-42} cy={-66} r={9} fill={INK} stroke="none" />
    <circle cx={42} cy={-66} r={9} fill={INK} stroke="none" />
  </g>
);

const Finch: RegistryRenderer = ({x, y, scale = 1}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -104 -10 Q -70 -82 26 -78 Q 104 -76 130 -14 Q 94 58 2 58 Q -74 58 -104 -10 Z" fill={PAPER} {...round} />
    <path d="M 118 -36 L 184 -12 L 118 12 Z" fill={CORAL} {...sharp} />
    <path d="M -94 -14 L -144 -54 L -130 18 Z" fill={PAPER_DEEP} {...round} />
    <path d="M -36 -44 Q -2 -18 -30 24" fill="none" stroke={INK} strokeWidth={STROKE_THIN} strokeLinecap="round" />
    <circle cx={66} cy={-38} r={6} fill={INK} stroke="none" />
    <path d="M -24 56 L -34 96 M 30 56 L 42 96" stroke={INK} strokeWidth={STROKE_THIN} strokeLinecap="round" />
    <path d="M -50 96 L -18 96 M 28 96 L 60 96" stroke={INK} strokeWidth={STROKE_THIN} strokeLinecap="round" />
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
    <rect x={-78} y={104} width={156} height={30} rx={10} fill={PAPER_DEEP} {...round} strokeWidth={STROKE_BOLD} />
    {/* gavel, gently tilted */}
    <g transform="rotate(-16 0 0)">
      {/* handle */}
      <rect x={-12} y={-6} width={24} height={108} rx={11} fill={PAPER} {...round} strokeWidth={STROKE_BOLD} />
      {/* cylinder head */}
      <rect x={-92} y={-66} width={184} height={64} rx={14} fill={PAPER_DEEP} {...round} strokeWidth={STROKE_BOLD} />
      {/* end bands */}
      <path d="M -58 -66 L -58 -2 M 58 -66 L 58 -2" stroke={INK} strokeWidth={STROKE} strokeLinecap="round" />
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

export const registry = {
  person: ({x, y, scale = 1, color = CORAL}: RegistryRendererProps) => <Person x={x} y={y} scale={scale} shirt={color} />,
  person_female: PersonFemale,
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
