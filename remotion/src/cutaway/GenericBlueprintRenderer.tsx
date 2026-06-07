import type React from "react";
import {interpolate, spring, useVideoConfig} from "remotion";
import {renderRegistryAsset} from "./registry";
import type {
  BackgroundPlan,
  BlueprintConnection,
  BlueprintElement,
  BlueprintSize,
  CameraPlanV2,
  ColorRole,
  ElementRef,
  MotionStep,
  PrimitiveShape,
  SceneBlueprint,
} from "./types";
import {CORAL, INK, INK_SOFT, PAPER, PAPER_DEEP, STROKE, STROKE_BOLD, STROKE_THIN} from "../flat/theme";
import {ConnectorLine, Panel, SvgTextBlock, W, H, anchorPoint, palette} from "./families/shared";

type Point = {x: number; y: number};
type Bounds = Point & {w: number; h: number; scale: number};
type ResolvedElement = BlueprintElement & {point: Point; bounds: Bounds; scale: number};
type MotionState = {opacity: number; x: number; y: number; scale: number; rotation: number; drawProgress: number};
type Attachment = "center" | "top" | "bottom" | "left" | "right" | undefined;
type TextElementKind = "label" | "headline" | "caption" | "stat" | "quote" | "title" | "tiny_note";

const assetBaseSize: Record<string, {w: number; h: number}> = {
  label: {w: 380, h: 128},
  stamp: {w: 420, h: 132},
  counter: {w: 356, h: 224},
  number: {w: 356, h: 224},
  subscribe: {w: 500, h: 160},
  person: {w: 172, h: 278},
  phone: {w: 260, h: 360},
  city: {w: 650, h: 380},
  building: {w: 200, h: 320},
  clock: {w: 240, h: 240},
  atomic_clock: {w: 300, h: 300},
  satellite: {w: 420, h: 260},
  signal: {w: 440, h: 440},
  signal_beam: {w: 282, h: 300},
  earth: {w: 340, h: 340},
  map_pin: {w: 160, h: 220},
  dot: {w: 160, h: 220},
  map: {w: 440, h: 308},
  grid: {w: 560, h: 300},
  watch: {w: 240, h: 404},
  sphere: {w: 304, h: 304},
  ring: {w: 304, h: 304},
  point: {w: 160, h: 220},
  ruler: {w: 440, h: 68},
  arrow: {w: 420, h: 116},
  light: {w: 282, h: 300},
  einstein: {w: 272, h: 342},
  mandrill: {w: 356, h: 388},
  finch: {w: 408, h: 208},
  person_female: {w: 172, h: 278},
  person_arms_up: {w: 224, h: 310},
  person_pointing: {w: 254, h: 278},
  person_sitting: {w: 220, h: 278},
  person_walking: {w: 184, h: 290},
  person_left: {w: 172, h: 278},
  person_right: {w: 172, h: 278},
  doctor: {w: 172, h: 278},
  scientist: {w: 172, h: 316},
  judge: {w: 172, h: 278},
  athlete: {w: 172, h: 278},
  suit: {w: 172, h: 278},
  heart: {w: 332, h: 282},
  gavel: {w: 420, h: 340},
  document: {w: 172, h: 236},
  eye: {w: 352, h: 264},
  car: {w: 460, h: 298},
  tree: {w: 276, h: 332},
  house: {w: 352, h: 338},
  coin: {w: 240, h: 240},
  money: {w: 352, h: 184},
  trophy: {w: 308, h: 344},
  book: {w: 276, h: 284},
  bag: {w: 308, h: 326},
  bottle: {w: 184, h: 328},
  cup: {w: 280, h: 230},
  box: {w: 292, h: 304},
  key: {w: 352, h: 116},
  lightbulb: {w: 272, h: 378},
  lock: {w: 252, h: 318},
  shield: {w: 264, h: 332},
  flag: {w: 232, h: 322},
  ball: {w: 264, h: 264},
  camera: {w: 348, h: 250},
  microphone: {w: 192, h: 328},
  laptop: {w: 432, h: 282},
  chart_bar: {w: 322, h: 264},
  chart_line: {w: 322, h: 264},
  pie_chart: {w: 264, h: 264},
  arrow_up: {w: 144, h: 324},
  arrow_down: {w: 144, h: 324},
  checkmark: {w: 304, h: 228},
  cross: {w: 232, h: 232},
  question_mark: {w: 184, h: 304},
  warning: {w: 328, h: 302},
  gear: {w: 336, h: 336},
  magnet: {w: 304, h: 260},
  brain: {w: 324, h: 316},
  dna: {w: 216, h: 288},
  pill: {w: 296, h: 116},
  syringe: {w: 394, h: 212},
  scale_justice: {w: 408, h: 286},
  ballot: {w: 276, h: 248},
  crown: {w: 352, h: 254},
  target: {w: 352, h: 352},
  sun: {w: 356, h: 356},
  cloud: {w: 374, h: 190},
  rain: {w: 270, h: 320},
  star: {w: 296, h: 278},
  moon: {w: 242, h: 256},
  mountain_shape: {w: 400, h: 290},
  wave: {w: 380, h: 212},
  fire: {w: 308, h: 280},
  plant: {w: 240, h: 346},
  coffee: {w: 304, h: 302},
  generic_object: {w: 240, h: 180},
};

const defaultBaseSize = {w: 320, h: 260};
const placeholderAssets = new Set(["generic_object", "none", "text", undefined]);
const textElementKinds = new Set<TextElementKind>(["label", "headline", "caption", "stat", "quote", "title", "tiny_note"]);

const colorForRole = (role?: ColorRole): string => (role ? palette[role] ?? CORAL : CORAL);

const textColorForTone = (tone?: string): string => {
  if (tone === "muted" || tone === "quiet") {
    return INK_SOFT;
  }
  if (tone === "coral_stamp" || tone === "warning") {
    return CORAL;
  }
  return INK;
};

const sizeScale = (asset: string, size: BlueprintSize): {scale: number; w: number; h: number} => {
  const base = assetBaseSize[asset] ?? defaultBaseSize;
  if (size.mode === "box") {
    const scale = Math.min(size.w / base.w, size.h / base.h);
    return {scale, w: size.w, h: size.h};
  }
  return {scale: size.scale, w: base.w * size.scale, h: base.h * size.scale};
};

const resolvePosition = (element: BlueprintElement, index: number, total: number): Point => {
  if (element.position.mode === "point") {
    return {x: element.position.x, y: element.position.y};
  }
  const p = anchorPoint(element.position.anchor, index, total);
  return {x: p.x + (element.position.dx ?? 0), y: p.y + (element.position.dy ?? 0)};
};

const resolveElements = (elements: BlueprintElement[]): ResolvedElement[] =>
  elements.map((element, index) => {
    const point = resolvePosition(element, index, elements.length);
    const size = sizeScale(element.asset, element.size);
    return {
      ...element,
      point,
      scale: size.scale,
      bounds: {x: point.x, y: point.y, w: size.w, h: size.h, scale: size.scale},
    };
  });

const attachmentPoint = (bounds: Bounds, attach: Attachment): Point => {
  if (attach === "top") {
    return {x: bounds.x, y: bounds.y - bounds.h / 2};
  }
  if (attach === "bottom") {
    return {x: bounds.x, y: bounds.y + bounds.h / 2};
  }
  if (attach === "left") {
    return {x: bounds.x - bounds.w / 2, y: bounds.y};
  }
  if (attach === "right") {
    return {x: bounds.x + bounds.w / 2, y: bounds.y};
  }
  return {x: bounds.x, y: bounds.y};
};

const resolveRef = (ref: ElementRef | string | undefined, elementMap: Map<string, ResolvedElement>): Point => {
  if (!ref) {
    return anchorPoint("center");
  }
  if (typeof ref === "string") {
    return anchorPoint(ref);
  }
  if ("point" in ref) {
    return ref.point;
  }
  if ("anchor" in ref) {
    return anchorPoint(ref.anchor);
  }
  const element = elementMap.get(ref.element);
  return element ? attachmentPoint(element.bounds, ref.attach) : anchorPoint("center");
};

const progressForStep = (step: MotionStep, localFrame: number, fps: number): number => {
  const start = step.start * fps;
  const duration = Math.max(1, step.duration * fps);
  const frame = localFrame - start;
  if (step.easing === "spring") {
    return Math.max(0, Math.min(1, spring({frame, fps, config: {damping: 14, stiffness: 180}})));
  }
  const base = interpolate(frame, [0, duration], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  if (step.easing === "ease_out") {
    return 1 - (1 - base) * (1 - base);
  }
  if (step.easing === "ease_in_out") {
    return base < 0.5 ? 2 * base * base : 1 - Math.pow(-2 * base + 2, 2) / 2;
  }
  return base;
};

const lerp = (from: number, to: number, p: number): number => from + (to - from) * p;

const applyMotion = (steps: MotionStep[] | undefined, localFrame: number, fps: number): MotionState => {
  const state: MotionState = {opacity: 1, x: 0, y: 0, scale: 1, rotation: 0, drawProgress: 1};
  for (const step of steps ?? []) {
    const p = progressForStep(step, localFrame, fps);
    const from = step.from ?? {};
    const to = step.to ?? {};
    if (step.kind === "enter" || step.kind === "pop_in" || step.kind === "stamp") {
      state.opacity *= lerp(from.opacity ?? 0, to.opacity ?? 1, p);
      state.scale *= lerp(from.scale ?? 0.72, to.scale ?? 1, p);
    } else if (step.kind === "exit" || step.kind === "pop_out") {
      state.opacity *= lerp(from.opacity ?? 1, to.opacity ?? 0, p);
      state.scale *= lerp(from.scale ?? 1, to.scale ?? 0.86, p);
    } else if (step.kind === "slide_in") {
      state.opacity *= lerp(from.opacity ?? 0, to.opacity ?? 1, p);
      state.x += lerp(from.x ?? -80, to.x ?? 0, p);
      state.y += lerp(from.y ?? 0, to.y ?? 0, p);
    } else if (step.kind === "slide_out") {
      state.opacity *= lerp(from.opacity ?? 1, to.opacity ?? 0, p);
      state.x += lerp(from.x ?? 0, to.x ?? 80, p);
      state.y += lerp(from.y ?? 0, to.y ?? 0, p);
    } else if (step.kind === "draw_on" || step.kind === "trace_line" || step.kind === "draw_path" || step.kind === "wipe_reveal") {
      state.drawProgress *= p;
    } else if (step.kind === "pulse" || step.kind === "highlight") {
      state.scale *= 1 + Math.sin(localFrame / 8) * 0.045;
    } else if (step.kind === "micro_bob") {
      state.y += Math.sin(localFrame / 9) * 7;
    } else if (step.kind === "orbit") {
      state.rotation += localFrame * 1.2;
    } else if (step.kind === "shake_once") {
      state.x += Math.sin(p * Math.PI * 8) * (1 - p) * 18;
    }
    state.opacity *= lerp(from.opacity ?? 1, to.opacity ?? 1, p);
    state.x += lerp(from.x ?? 0, to.x ?? 0, p);
    state.y += lerp(from.y ?? 0, to.y ?? 0, p);
    state.scale *= lerp(from.scale ?? 1, to.scale ?? 1, p);
    state.rotation += lerp(from.rotation ?? 0, to.rotation ?? 0, p);
  }
  return state;
};

const cameraStyle = (camera: CameraPlanV2, target: Point, localFrame: number, duration: number, fps: number): React.CSSProperties => {
  const intensity = {none: 0, small: 1, medium: 2, large: 3}[camera.intensity] ?? 1;
  const start = (camera.start ?? 0) * fps;
  const cameraDuration = camera.duration ? Math.max(1, camera.duration * fps) : Math.max(1, duration);
  const frame = Math.max(0, localFrame - start);
  const p = interpolate(frame, [0, cameraDuration], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const delayed = interpolate(frame, [cameraDuration * 0.35, cameraDuration], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const snap = spring({frame, fps, config: {damping: 10, stiffness: 230}});
  let scale = 1;
  let x = 0;
  let y = 0;
  if (camera.move === "push_in") {
    scale = 1 + p * 0.035 * intensity;
  } else if (camera.move === "hold_then_push") {
    scale = 1 + delayed * 0.03 * intensity;
  } else if (camera.move === "pull_back") {
    scale = 1.08 - p * 0.035 * intensity;
  } else if (camera.move === "pan_left") {
    x = p * -36 * intensity;
  } else if (camera.move === "pan_right") {
    x = p * 36 * intensity;
  } else if (camera.move === "snap_zoom") {
    scale = 1 + Math.min(1, snap) * 0.055 * intensity;
  } else if (camera.move === "tilt_down") {
    y = p * 32 * intensity;
  } else if (camera.move === "parallax_drift") {
    x = Math.sin(localFrame / 30) * 14 * intensity;
    y = Math.cos(localFrame / 42) * 8 * intensity;
  }
  return {
    transform: `translate(${x}px, ${y}px) scale(${scale})`,
    transformOrigin: `${target.x}px ${target.y}px`,
  };
};

const Background: React.FC<{background: BackgroundPlan}> = ({background}) => {
  if (background.treatment === "panel") {
    return <Panel x={260} y={170} w={1400} h={740} />;
  }
  if (background.treatment === "grid") {
    return (
      <g opacity={0.28}>
        {Array.from({length: 13}, (_, i) => (
          <path key={`v${i}`} d={`M ${300 + i * 120} 160 L ${300 + i * 120} 900`} stroke={INK} strokeWidth={STROKE_THIN} />
        ))}
        {Array.from({length: 8}, (_, i) => (
          <path key={`h${i}`} d={`M 240 ${210 + i * 100} L 1680 ${210 + i * 100}`} stroke={INK} strokeWidth={STROKE_THIN} />
        ))}
      </g>
    );
  }
  if (background.treatment === "comparison_panels") {
    return (
      <g>
        <Panel x={220} y={210} w={640} h={590} />
        <Panel x={1060} y={210} w={640} h={590} />
        <path d="M 960 220 L 960 800" stroke={INK} strokeWidth={STROKE} strokeLinecap="butt" />
        <circle cx={960} cy={510} r={66} fill={PAPER} stroke={INK} strokeWidth={STROKE} />
        <text x={960} y={533} textAnchor="middle" fontSize={54} fontWeight={900} fontFamily="Inter, Arial, sans-serif" fill={CORAL}>
          VS
        </text>
      </g>
    );
  }
  if (background.treatment === "paper_stack") {
    return (
      <g>
        <rect x={610} y={220} width={620} height={720} rx={6} fill={PAPER_DEEP} stroke={INK} strokeWidth={STROKE_THIN} transform="rotate(-4 920 580)" />
        <rect x={690} y={160} width={620} height={720} rx={6} fill={PAPER_DEEP} stroke={INK} strokeWidth={STROKE_THIN} transform="rotate(4 1000 520)" />
        <rect x={650} y={190} width={620} height={720} rx={6} fill={PAPER} stroke={INK} strokeWidth={8} />
        <path d="M 760 340 L 1160 340 M 760 430 L 1160 430 M 760 520 L 1080 520" stroke={INK} strokeWidth={5} strokeLinecap="round" opacity={0.35} />
      </g>
    );
  }
  if (background.treatment === "map") {
    return (
      <g>
        <rect x={360} y={190} width={1200} height={660} rx={8} fill={PAPER} stroke={INK} strokeWidth={STROKE} />
        <path d="M 460 660 C 700 420 1020 730 1460 380" fill="none" stroke={CORAL} strokeWidth={8} strokeLinecap="round" />
      </g>
    );
  }
  return null;
};

const renderTextFallback = (element: ResolvedElement): React.ReactNode => {
  if (!element.text || element.asset === "label" || element.asset === "stamp" || element.asset === "counter" || element.asset === "number") {
    return null;
  }
  return renderFittedText(element);
};

const baseTextSize = (role: string): number => {
  if (role === "headline" || role === "title") {
    return 112;
  }
  if (role === "stat") {
    return 120;
  }
  if (role === "quote" || role === "caption") {
    return 56;
  }
  if (role === "label") {
    return 64;
  }
  if (role === "tiny_note") {
    return 36;
  }
  return 56;
};

const isTextOnlyElement = (element: ResolvedElement): boolean => {
  if (!element.text?.text) {
    return false;
  }
  return textElementKinds.has(element.kind as TextElementKind) || placeholderAssets.has(element.asset);
};

const renderFittedText = (element: ResolvedElement): React.ReactNode => {
  if (!element.text?.text) {
    return null;
  }
  const width = element.size.mode === "box" ? element.size.w : Math.max(300, element.bounds.w);
  const height = element.size.mode === "box" ? element.size.h : Math.max(100, element.bounds.h);
  const align = element.id.startsWith("row_") ? "left" : "center";
  return (
    <SvgTextBlock
      text={element.text.text}
      x={element.point.x - width / 2}
      y={element.point.y - height / 2}
      width={width}
      height={height}
      baseSize={baseTextSize(element.text.role)}
      fill={textColorForTone(element.text.tone)}
      align={align}
    />
  );
};

const renderPropShape = (element: ResolvedElement): React.ReactNode => {
  const color = colorForRole(element.colorRole ?? "accent");
  if (element.propShape === "rule") {
    const width = element.size.mode === "box" ? element.size.w : Math.max(120, element.bounds.w);
    const height = element.size.mode === "box" ? element.size.h : Math.max(12, Math.min(16, element.scale * 14));
    return <rect x={element.point.x - width / 2} y={element.point.y - height / 2} width={width} height={height} rx={height / 2} fill={color} />;
  }
  if (element.propShape === "disc" || element.propShape === "tick") {
    const radius = element.size.mode === "box" ? Math.min(element.size.w, element.size.h) / 2 : Math.max(6, element.scale * 18);
    if (element.propShape === "tick") {
      return (
        <path
          d={`M ${element.point.x - radius * 1.1} ${element.point.y} L ${element.point.x - radius * 0.25} ${element.point.y + radius * 0.85} L ${element.point.x + radius * 1.25} ${element.point.y - radius}`}
          fill="none"
          stroke={color}
          strokeWidth={Math.max(8, radius * 0.55)}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      );
    }
    return <circle cx={element.point.x} cy={element.point.y} r={radius} fill={color} />;
  }
  return null;
};

type ShapeBounds = {minX: number; minY: number; maxX: number; maxY: number};

const expandBounds = (bounds: ShapeBounds | null, x: number | undefined, y: number | undefined): ShapeBounds | null => {
  if (typeof x !== "number" || typeof y !== "number" || Number.isNaN(x) || Number.isNaN(y)) {
    return bounds;
  }
  if (!bounds) {
    return {minX: x, minY: y, maxX: x, maxY: y};
  }
  return {
    minX: Math.min(bounds.minX, x),
    minY: Math.min(bounds.minY, y),
    maxX: Math.max(bounds.maxX, x),
    maxY: Math.max(bounds.maxY, y),
  };
};

const mergeBounds = (bounds: ShapeBounds | null, next: ShapeBounds | null): ShapeBounds | null => {
  if (!next) {
    return bounds;
  }
  if (!bounds) {
    return next;
  }
  return {
    minX: Math.min(bounds.minX, next.minX),
    minY: Math.min(bounds.minY, next.minY),
    maxX: Math.max(bounds.maxX, next.maxX),
    maxY: Math.max(bounds.maxY, next.maxY),
  };
};

const boundsForShape = (shape: PrimitiveShape): ShapeBounds | null => {
  if (shape.type === "rect") {
    const x = shape.x ?? 0;
    const y = shape.y ?? 0;
    const w = shape.w ?? 0;
    const h = shape.h ?? 0;
    return {minX: x, minY: y, maxX: x + w, maxY: y + h};
  }
  if (shape.type === "circle") {
    const cx = shape.cx ?? 0;
    const cy = shape.cy ?? 0;
    const r = shape.r ?? 0;
    return {minX: cx - r, minY: cy - r, maxX: cx + r, maxY: cy + r};
  }
  if (shape.type === "ellipse") {
    const cx = shape.cx ?? 0;
    const cy = shape.cy ?? 0;
    const rx = shape.r ?? 0;
    const ry = shape.ry ?? rx;
    return {minX: cx - rx, minY: cy - ry, maxX: cx + rx, maxY: cy + ry};
  }
  if (shape.type === "line") {
    return mergeBounds(expandBounds(null, shape.x1, shape.y1), expandBounds(null, shape.x2, shape.y2));
  }
  if (shape.type === "polygon") {
    let bounds: ShapeBounds | null = null;
    for (let i = 0; i < (shape.points ?? []).length - 1; i += 2) {
      bounds = expandBounds(bounds, shape.points?.[i], shape.points?.[i + 1]);
    }
    return bounds;
  }
  if (shape.type === "path") {
    const values = (shape.d ?? "").match(/-?\d*\.?\d+(?:e[-+]?\d+)?/gi)?.map(Number) ?? [];
    let bounds: ShapeBounds | null = null;
    for (let i = 0; i < values.length - 1; i += 2) {
      bounds = expandBounds(bounds, values[i], values[i + 1]);
    }
    return bounds;
  }
  return null;
};

const boundsForShapes = (shapes: PrimitiveShape[]): ShapeBounds | null =>
  shapes.reduce<ShapeBounds | null>((bounds, shape) => mergeBounds(bounds, boundsForShape(shape)), null);

const localShapeTransform = (element: ResolvedElement): string => {
  const bounds = boundsForShapes(element.shapes ?? []);
  if (!bounds) {
    return `translate(${element.point.x} ${element.point.y}) scale(${element.scale})`;
  }
  const shapeW = Math.max(1, bounds.maxX - bounds.minX);
  const shapeH = Math.max(1, bounds.maxY - bounds.minY);
  const targetW = element.size.mode === "box" ? element.size.w : 320 * element.size.scale;
  const targetH = element.size.mode === "box" ? element.size.h : 320 * element.size.scale;
  const fitScale = Math.min(targetW / shapeW, targetH / shapeH);
  const centerX = bounds.minX + shapeW / 2;
  const centerY = bounds.minY + shapeH / 2;
  return `translate(${element.point.x} ${element.point.y}) scale(${fitScale}) translate(${-centerX} ${-centerY})`;
};

// Draw primitive shape lists. Environment layers use absolute frame coords; generated assets set
// shapeSpace="local" and are fitted into the element's resolved box.
const renderShapes = (element: ResolvedElement): React.ReactNode => {
  if (!element.shapes || element.shapes.length === 0) {
    return null;
  }
  const localSpace = element.shapeSpace === "local";
  const nodes = (
    <>
      {element.shapes.map((s, i) => {
        const fill = !s.fill || s.fill === "none" ? "none" : palette[s.fill] ?? CORAL;
        const strokeProps = s.stroke
          ? {
              stroke: INK,
              strokeWidth: s.strokeW ?? STROKE,
              strokeLinejoin: "round" as const,
              strokeLinecap: "round" as const,
              vectorEffect: localSpace ? ("non-scaling-stroke" as const) : undefined,
            }
          : {stroke: "none" as const};
        const common = {key: i, fill, opacity: s.opacity ?? 1, ...strokeProps};
        if (s.type === "rect") return <rect x={s.x} y={s.y} width={s.w} height={s.h} rx={s.rx ?? 0} {...common} />;
        if (s.type === "circle") return <circle cx={s.cx} cy={s.cy} r={s.r} {...common} />;
        if (s.type === "ellipse") return <ellipse cx={s.cx} cy={s.cy} rx={s.r} ry={s.ry} {...common} />;
        if (s.type === "line") return <line x1={s.x1} y1={s.y1} x2={s.x2} y2={s.y2} {...common} />;
        if (s.type === "polygon") return <polygon points={(s.points ?? []).join(" ")} {...common} />;
        if (s.type === "path") return <path d={s.d} {...common} />;
        return null;
      })}
    </>
  );
  if (localSpace) {
    return <g transform={localShapeTransform(element)}>{nodes}</g>;
  }
  return nodes;
};

const ElementNode: React.FC<{element: ResolvedElement; localFrame: number}> = ({element, localFrame}) => {
  const {fps} = useVideoConfig();
  const motion = applyMotion(element.motion, localFrame, fps);
  const text = element.text?.text;
  const shapes = element.shapes && element.shapes.length ? renderShapes(element) : null;
  const textOnly = isTextOnlyElement(element);
  const propShape = element.kind === "prop" && element.propShape ? renderPropShape(element) : null;
  return (
    <g
      style={{
        opacity: (element.opacity ?? 1) * motion.opacity,
        transform: `translate(${motion.x}px ${motion.y}px) scale(${motion.scale}) rotate(${(element.rotation ?? 0) + motion.rotation}deg)`,
        transformBox: "fill-box",
        transformOrigin: "center",
      }}
    >
      {shapes}
      {!shapes && propShape}
      {!shapes && !propShape && textOnly ? renderFittedText(element) : null}
      {!shapes && !propShape && !textOnly
        ? renderRegistryAsset(element.asset, {
            x: element.point.x,
            y: element.point.y,
            scale: element.scale,
            color: colorForRole(element.colorRole),
            localFrame,
            extra: {text},
          })
        : null}
      {!shapes && !propShape && !textOnly ? renderTextFallback(element) : null}
    </g>
  );
};

const ConnectionNode: React.FC<{connection: BlueprintConnection; elementMap: Map<string, ResolvedElement>; localFrame: number}> = ({
  connection,
  elementMap,
  localFrame,
}) => {
  const {fps} = useVideoConfig();
  const motion = applyMotion(connection.motion, localFrame, fps);
  const from = resolveRef(connection.from, elementMap);
  const to = resolveRef(connection.to, elementMap);
  const color = colorForRole(connection.colorRole);
  if (connection.kind === "range_ring" || connection.kind === "pulse") {
    const pulse = connection.kind === "pulse" ? 1 + Math.sin(localFrame / 8) * 0.08 : 1;
    return <circle cx={from.x} cy={from.y} r={152 * pulse * motion.drawProgress} fill="none" stroke={color} strokeWidth={STROKE} strokeLinecap="round" opacity={0.82 * motion.opacity} />;
  }
  if (connection.kind === "brace") {
    return (
      <path
        d={`M ${from.x} ${from.y} C ${from.x} ${from.y + 70}, ${to.x} ${to.y - 70}, ${to.x} ${to.y}`}
        fill="none"
        stroke={color}
        strokeWidth={STROKE_BOLD}
        strokeLinecap="round"
        opacity={motion.opacity}
      />
    );
  }
  const x2 = from.x + (to.x - from.x) * motion.drawProgress;
  const y2 = from.y + (to.y - from.y) * motion.drawProgress;
  const angle = Math.atan2(to.y - from.y, to.x - from.x);
  return (
    <g opacity={motion.opacity}>
      <ConnectorLine from={from} to={to} progress={motion.drawProgress} color={color} />
      {connection.kind === "arrow" ? (
        <path
          d={`M ${x2} ${y2} l ${Math.cos(angle + 2.55) * 34} ${Math.sin(angle + 2.55) * 34} M ${x2} ${y2} l ${Math.cos(angle - 2.55) * 34} ${Math.sin(angle - 2.55) * 34}`}
          stroke={color}
          strokeWidth={STROKE}
          strokeLinecap="round"
          fill="none"
        />
      ) : null}
    </g>
  );
};

export const GenericBlueprintRenderer: React.FC<{blueprint: SceneBlueprint; localFrame: number; duration: number}> = ({
  blueprint,
  localFrame,
  duration,
}) => {
  const {fps, width, height} = useVideoConfig();
  const backgroundElements = resolveElements(blueprint.background.elements ?? []);
  const foregroundElements = resolveElements(blueprint.elements);
  const elements = [...backgroundElements, ...foregroundElements];
  const elementMap = new Map(elements.map((element) => [element.id, element]));
  const cameraTarget = resolveRef(blueprint.camera.target, elementMap);
  const connections = [...(blueprint.connections ?? [])].sort((a, b) => (a.z ?? 0) - (b.z ?? 0));
  const sortedBackgroundElements = [...backgroundElements].sort((a, b) => (a.z ?? 0) - (b.z ?? 0));
  const sortedElements = [...foregroundElements].sort((a, b) => (a.z ?? 0) - (b.z ?? 0));

  return (
    <svg viewBox={`0 0 ${width || W} ${height || H}`} width="100%" height="100%" style={cameraStyle(blueprint.camera, cameraTarget, localFrame, duration, fps)}>
      <Background background={blueprint.background} />
      {sortedBackgroundElements.map((element) => (
        <ElementNode key={element.id} element={element} localFrame={localFrame} />
      ))}
      {connections.map((connection) => (
        <ConnectionNode key={connection.id} connection={connection} elementMap={elementMap} localFrame={localFrame} />
      ))}
      {sortedElements.map((element) => (
        <ElementNode key={element.id} element={element} localFrame={localFrame} />
      ))}
    </svg>
  );
};
