import {union, type MultiPolygon, type Pair, type Polygon, type Ring} from "polygon-clipping";
import {buildArmOutlineGeometry, sampleTipCap} from "./armOutline";
import type {Point, SolvedArm} from "./rigTypes";

type BodyTransform = {
  x: number;
  y: number;
  scale: number;
  rotate: number;
  pulseX: number;
  pulseY: number;
};

type SilhouetteInput = {
  arms: SolvedArm[];
  mantlePath: string;
  body: BodyTransform;
  mantleScale: number;
};

const closeRing = (ring: Ring): Ring => {
  if (ring.length === 0) {
    return ring;
  }

  const first = ring[0];
  const last = ring[ring.length - 1];

  if (first[0] === last[0] && first[1] === last[1]) {
    return ring;
  }

  return [...ring, first];
};

const toRing = (points: Point[]): Ring => closeRing(points.map((point) => [point.x, point.y] as Pair));

const transformMantlePoint = (point: Point, body: BodyTransform, mantleScale: number): Point => {
  const scaled = {
    x: point.x * mantleScale * body.pulseX * (body.scale / 100),
    y: point.y * mantleScale * body.pulseY * (body.scale / 100),
  };
  const radians = body.rotate * Math.PI / 180;
  const cos = Math.cos(radians);
  const sin = Math.sin(radians);

  return {
    x: body.x + scaled.x * cos - scaled.y * sin,
    y: body.y + scaled.x * sin + scaled.y * cos,
  };
};

const cubicPoint = (a: Point, b: Point, c: Point, d: Point, t: number): Point => {
  const inv = 1 - t;
  const inv2 = inv * inv;
  const t2 = t * t;

  return {
    x: inv2 * inv * a.x + 3 * inv2 * t * b.x + 3 * inv * t2 * c.x + t2 * t * d.x,
    y: inv2 * inv * a.y + 3 * inv2 * t * b.y + 3 * inv * t2 * c.y + t2 * t * d.y,
  };
};

const sampleMantlePath = (path: string, samplesPerCurve = 14): Point[] => {
  const tokens = path.match(/[MCZ]|-?\d+(?:\.\d+)?/g) ?? [];
  const points: Point[] = [];
  let index = 0;
  let current: Point | null = null;

  while (index < tokens.length) {
    const token = tokens[index++];

    if (token === "M") {
      current = {x: Number(tokens[index++]), y: Number(tokens[index++])};
      points.push(current);
      continue;
    }

    if (token === "C" && current) {
      const c1 = {x: Number(tokens[index++]), y: Number(tokens[index++])};
      const c2 = {x: Number(tokens[index++]), y: Number(tokens[index++])};
      const end = {x: Number(tokens[index++]), y: Number(tokens[index++])};

      for (let i = 1; i <= samplesPerCurve; i++) {
        points.push(cubicPoint(current, c1, c2, end, i / samplesPerCurve));
      }

      current = end;
      continue;
    }
  }

  return points;
};

const armToPolygon = (arm: SolvedArm): Polygon | null => {
  const geometry = buildArmOutlineGeometry(arm.points, arm.radii, arm.baseAngle);

  if (!geometry) {
    return null;
  }

  const last = geometry.outlinePoints.length - 1;
  const tip = geometry.outlinePoints[last];
  const tipRadius = geometry.outlineRadii[last] ?? 5;
  const cap = sampleTipCap(tip, geometry.tipTangent, tipRadius, 8);
  const ringPoints = [
    ...geometry.left.slice(0, -1),
    ...cap,
    ...geometry.right.slice(0, -1).reverse(),
  ];

  return [toRing(ringPoints)];
};

const chaikinRing = (ring: Ring): Ring => {
  const open = ring.slice(0, -1);

  if (open.length < 4) {
    return ring;
  }

  const smoothed: Ring = [];

  open.forEach((point, index) => {
    const next = open[(index + 1) % open.length];
    smoothed.push([
      point[0] * 0.75 + next[0] * 0.25,
      point[1] * 0.75 + next[1] * 0.25,
    ]);
    smoothed.push([
      point[0] * 0.25 + next[0] * 0.75,
      point[1] * 0.25 + next[1] * 0.75,
    ]);
  });

  return closeRing(smoothed);
};

const ringToPath = (ring: Ring): string => {
  const smoothed = chaikinRing(closeRing(ring));
  const open = smoothed.slice(0, -1);

  if (open.length === 0) {
    return "";
  }

  return [
    `M ${open[0][0].toFixed(2)} ${open[0][1].toFixed(2)}`,
    ...open.slice(1).map((point) => `L ${point[0].toFixed(2)} ${point[1].toFixed(2)}`),
    "Z",
  ].join(" ");
};

const multiPolygonToPath = (multiPolygon: MultiPolygon): string =>
  multiPolygon
    .map((polygon) => polygon[0])
    .filter((ring): ring is Ring => Boolean(ring && ring.length > 2))
    .map(ringToPath)
    .filter(Boolean)
    .join(" ");

export const octopusSilhouettePath = ({arms, mantlePath, body, mantleScale}: SilhouetteInput): string => {
  const mantlePoints = sampleMantlePath(mantlePath).map((point) => transformMantlePoint(point, body, mantleScale));
  const polygons = [
    [toRing(mantlePoints)],
    ...arms
      .map(armToPolygon)
      .filter((polygon): polygon is Polygon => Boolean(polygon)),
  ];

  if (polygons.length === 0) {
    return "";
  }

  return multiPolygonToPath(union(polygons[0], ...polygons.slice(1)));
};
