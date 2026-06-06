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

const Mandrill: RegistryRenderer = ({x, y, scale = 1, color = GOLD}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -54 -132 L -18 -194 L 0 -132 L 18 -194 L 54 -132 Z" fill={color} {...round} />
    <path d="M -132 -92 Q -178 -10 -128 102 Q -72 188 0 188 Q 72 188 128 102 Q 178 -10 132 -92 Q 86 -164 0 -164 Q -86 -164 -132 -92 Z" fill={PAPER} {...round} strokeWidth={STROKE_BOLD} />
    <path d="M -118 -82 Q -158 4 -106 88 Q -74 50 -66 -28 Q -58 -88 -28 -128 Q -82 -132 -118 -82 Z" fill={BLUE} {...round} />
    <path d="M 118 -82 Q 158 4 106 88 Q 74 50 66 -28 Q 58 -88 28 -128 Q 82 -132 118 -82 Z" fill={BLUE} {...round} />
    <path d="M -40 -128 Q -12 -150 0 -102 Q 12 -150 40 -128 Q 22 -94 0 -86 Q -22 -94 -40 -128 Z" fill={PAPER_DEEP} {...round} strokeWidth={STROKE_THIN} />
    <path d="M -40 -74 L 0 -96 L 40 -74 L 32 88 Q 0 128 -32 88 Z" fill={CORAL} {...round} />
    <path d="M -24 -54 Q 0 -68 24 -54 L 18 -16 Q 0 -4 -18 -16 Z" fill={INK} stroke="none" />
    <path d="M -54 -46 L -28 -50 M 54 -46 L 28 -50" stroke={INK} strokeWidth={STROKE_THIN} strokeLinecap="round" />
    <circle cx={-50} cy={-54} r={6} fill={INK} stroke="none" />
    <circle cx={50} cy={-54} r={6} fill={INK} stroke="none" />
    <path d="M -38 86 Q 0 110 38 86" fill="none" stroke={INK} strokeWidth={STROKE_THIN} strokeLinecap="round" />
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

const PersonFemale: RegistryRenderer = ({x, y, scale = 1, color = CORAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -66 -96 Q -58 -152 0 -152 Q 58 -152 66 -96 L 58 -42 Q 28 -70 0 -70 Q -28 -70 -58 -42 Z" fill={INK} {...round} />
    <circle cx={0} cy={-92} r={42} fill="#F0D2B8" {...round} />
    <path d="M -42 -106 Q -12 -136 42 -108" fill="none" stroke={INK} strokeWidth={STROKE_BOLD} strokeLinecap="round" />
    <circle cx={-14} cy={-96} r={5.5} fill={INK} stroke="none" />
    <circle cx={14} cy={-96} r={5.5} fill={INK} stroke="none" />
    <path d="M -40 -42 Q 0 -70 40 -42 L 74 82 L -74 82 Z" fill={color} {...round} />
    <path d="M -46 -12 L -86 54 M 46 -12 L 86 54" {...round} strokeWidth={STROKE_THIN} />
    <path d="M -28 82 L -30 126 M 28 82 L 30 126" {...round} strokeWidth={STROKE_BOLD} />
  </g>
);

const Heart: RegistryRenderer = ({x, y, scale = 1}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M 0 118 L -112 8 Q -166 -52 -120 -104 Q -76 -150 0 -86 Q 76 -150 120 -104 Q 166 -52 112 8 Z" fill={CORAL} {...round} strokeWidth={STROKE_BOLD} />
  </g>
);

const Gavel: RegistryRenderer = ({x, y, scale = 1}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <ellipse cx={76} cy={112} rx={118} ry={34} fill={PAPER_DEEP} {...round} />
    <path d="M -74 -8 L 124 132" stroke={INK} strokeWidth={STROKE_BOLD} strokeLinecap="round" />
    <rect x={-154} y={-100} width={184} height={72} rx={4} fill={PAPER_DEEP} {...sharp} transform="rotate(-35 -62 -64)" />
    <rect x={-172} y={-116} width={48} height={104} rx={3} fill={PAPER_DEEP} {...sharp} transform="rotate(-35 -148 -64)" />
    <rect x={-2} y={-116} width={48} height={104} rx={3} fill={PAPER_DEEP} {...sharp} transform="rotate(-35 22 -64)" />
    <path d="M 28 72 L 152 160" stroke={PAPER_DEEP} strokeWidth={STROKE_BOLD} strokeLinecap="round" />
    <path d="M 28 72 L 152 160" stroke={INK} strokeWidth={STROKE_THIN} strokeLinecap="round" />
  </g>
);

const GenericObject: RegistryRenderer = ({x, y, scale = 1, color = PAPER_DEEP}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <rect x={-120} y={-90} width={240} height={180} rx={8} fill={color} {...sharp} />
    <circle cx={-42} cy={-18} r={12} fill={INK} stroke="none" />
    <circle cx={42} cy={-18} r={12} fill={INK} stroke="none" />
    <path d="M -48 34 L 48 34" stroke={INK} strokeWidth={STROKE_THIN} strokeLinecap="round" />
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
