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

const SphereRing: RegistryRenderer = ({x, y, scale = 1, color = TEAL}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <circle cx={0} cy={0} r={104} fill={PAPER_DEEP} {...round} strokeWidth={STROKE_BOLD} />
    <ellipse cx={0} cy={0} rx={152} ry={42} fill="none" stroke={color} strokeWidth={STROKE} />
    <path d="M -46 -92 C 20 -116 88 -68 96 8" fill="none" stroke={PAPER} strokeWidth={12} strokeLinecap="round" />
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
  const value = String(extra?.value ?? extra?.text ?? "42");
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <rect x={-178} y={-112} width={356} height={224} rx={8} fill={PAPER} {...sharp} strokeWidth={STROKE_BOLD} />
      <text x={0} y={42} textAnchor="middle" fontSize={132} fill={color} {...labelText}>
        {value}
      </text>
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

const Label: RegistryRenderer = ({x, y, scale = 1, color = PAPER, extra}) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <rect x={-170} y={-54} width={340} height={108} rx={4} fill={color} {...sharp} />
    <text x={0} y={17} textAnchor="middle" fontSize={44} fill={INK} {...labelText}>
      {String(extra?.text ?? "LABEL").slice(0, 18)}
    </text>
  </g>
);

const Stamp: RegistryRenderer = ({x, y, scale = 1, color = CORAL, extra}) => (
  <g transform={`translate(${x} ${y}) scale(${scale}) rotate(-8)`}>
    <rect x={-192} y={-58} width={384} height={116} rx={3} fill="none" stroke={color} strokeWidth={STROKE_BOLD} />
    <text x={0} y={17} textAnchor="middle" fontSize={44} fill={color} {...labelText}>
      {String(extra?.text ?? "STAMP").slice(0, 16)}
    </text>
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
  earth: ({x, y, scale = 1}: RegistryRendererProps) => <EarthArc cx={x} cy={y + 520 * scale} r={640 * scale} />,
  map_pin: Point,
  dot: Point,
  watch: Watch,
  grid: Grid,
  sphere: SphereRing,
  ring: SphereRing,
  point: Point,
  ruler: Ruler,
  arrow: ArrowProp,
  light: Light,
  einstein: Einstein,
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
