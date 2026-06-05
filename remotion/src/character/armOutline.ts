import type {Point} from "./rigTypes";
import {catmullRomToBezierPath} from "./splines";

const TANGENT_EPSILON = 0.001;

type ArmOutlineGeometry = {
  left: Point[];
  right: Point[];
  outlinePoints: Point[];
  outlineRadii: number[];
  tipTangent: Point;
  tipNormal: Point;
};

const normalFromTangent = (tangent: Point): Point => ({x: -tangent.y, y: tangent.x});

const normalize = (vector: Point, fallback: Point): Point => {
  const distance = Math.hypot(vector.x, vector.y);

  if (distance < TANGENT_EPSILON) {
    return fallback;
  }

  return {x: vector.x / distance, y: vector.y / distance};
};

const tangentFromPoints = (previous: Point, next: Point, fallback: Point): Point =>
  normalize({x: next.x - previous.x, y: next.y - previous.y}, fallback);

const stableTipTangent = (points: Point[], fallbackAngle = 0): Point => {
  const fallback = {x: Math.cos(fallbackAngle), y: Math.sin(fallbackAngle)};
  const last = points.length - 1;
  // longer baseline (outer ~4 joints) = far more stable tip direction -> the rounded cap can't
  // mirror/flip frame-to-frame. Safe now that the tip is stiffened (low curvature at the end).
  const baselineStart = Math.max(0, last - 4);
  const baseline = {
    x: points[last].x - points[baselineStart].x,
    y: points[last].y - points[baselineStart].y,
  };

  if (Math.hypot(baseline.x, baseline.y) >= TANGENT_EPSILON) {
    return normalize(baseline, fallback);
  }

  for (let i = last; i > 0; i--) {
    const tangent = tangentFromPoints(points[i - 1], points[i], fallback);
    if (Math.abs(tangent.x - fallback.x) > TANGENT_EPSILON || Math.abs(tangent.y - fallback.y) > TANGENT_EPSILON) {
      return tangent;
    }
  }

  return fallback;
};

const offsetWithTangent = (point: Point, tangent: Point, radius: number, side: -1 | 1): Point => {
  const normal = normalFromTangent(tangent);

  return {
    x: point.x + normal.x * radius * side,
    y: point.y + normal.y * radius * side,
  };
};

const stripMove = (path: string): string => path.replace(/^M [-0-9.]+ [-0-9.]+ /, "");

const mixPoint = (from: Point, to: Point, progress: number): Point => ({
  x: from.x + (to.x - from.x) * progress,
  y: from.y + (to.y - from.y) * progress,
});

const mix = (from: number, to: number, progress: number): number => from + (to - from) * progress;

export const sampleTipCap = (tip: Point, tangent: Point, radius: number, steps = 8): Point[] => {
  const kappa = 0.5522847498;
  const normal = normalFromTangent(tangent);
  const forward = {
    x: tip.x + tangent.x * radius,
    y: tip.y + tangent.y * radius,
  };
  const start = {
    x: tip.x + normal.x * radius,
    y: tip.y + normal.y * radius,
  };
  const end = {
    x: tip.x - normal.x * radius,
    y: tip.y - normal.y * radius,
  };
  const c1 = {
    x: tip.x + normal.x * radius + tangent.x * radius * kappa,
    y: tip.y + normal.y * radius + tangent.y * radius * kappa,
  };
  const c2 = {
    x: forward.x + normal.x * radius * kappa,
    y: forward.y + normal.y * radius * kappa,
  };
  const c3 = {
    x: forward.x - normal.x * radius * kappa,
    y: forward.y - normal.y * radius * kappa,
  };
  const c4 = {
    x: tip.x - normal.x * radius + tangent.x * radius * kappa,
    y: tip.y - normal.y * radius + tangent.y * radius * kappa,
  };
  const cubic = (a: Point, b: Point, c: Point, d: Point, t: number): Point => {
    const inv = 1 - t;
    const inv2 = inv * inv;
    const t2 = t * t;

    return {
      x: inv2 * inv * a.x + 3 * inv2 * t * b.x + 3 * inv * t2 * c.x + t2 * t * d.x,
      y: inv2 * inv * a.y + 3 * inv2 * t * b.y + 3 * inv * t2 * c.y + t2 * t * d.y,
    };
  };
  const halfSteps = Math.max(2, Math.floor(steps / 2));
  const samples: Point[] = [];

  for (let i = 0; i <= halfSteps; i++) {
    samples.push(cubic(start, c1, c2, forward, i / halfSteps));
  }

  for (let i = 1; i <= halfSteps; i++) {
    samples.push(cubic(forward, c3, c4, end, i / halfSteps));
  }

  return samples;
};

const tipCapPath = (tip: Point, tangent: Point, radius: number): string => {
  const normal = normalFromTangent(tangent);
  const kappa = 0.5522847498;
  const forward = {
    x: tip.x + tangent.x * radius,
    y: tip.y + tangent.y * radius,
  };
  const c1 = {
    x: tip.x + normal.x * radius + tangent.x * radius * kappa,
    y: tip.y + normal.y * radius + tangent.y * radius * kappa,
  };
  const c2 = {
    x: forward.x + normal.x * radius * kappa,
    y: forward.y + normal.y * radius * kappa,
  };
  const c3 = {
    x: forward.x - normal.x * radius * kappa,
    y: forward.y - normal.y * radius * kappa,
  };
  const c4 = {
    x: tip.x - normal.x * radius + tangent.x * radius * kappa,
    y: tip.y - normal.y * radius + tangent.y * radius * kappa,
  };

  return [
    `C ${c1.x.toFixed(2)} ${c1.y.toFixed(2)} ${c2.x.toFixed(2)} ${c2.y.toFixed(2)} ${forward.x.toFixed(2)} ${forward.y.toFixed(2)}`,
    `C ${c3.x.toFixed(2)} ${c3.y.toFixed(2)} ${c4.x.toFixed(2)} ${c4.y.toFixed(2)} ${(tip.x - normal.x * radius).toFixed(2)} ${(tip.y - normal.y * radius).toFixed(2)}`,
  ].join(" ");
};

export const buildArmOutlineGeometry = (points: Point[], radii: number[], fallbackAngle = 0): ArmOutlineGeometry | null => {
  const sourceLast = points.length - 1;

  if (sourceLast < 1) {
    return null;
  }

  const tipPrepA = mixPoint(points[sourceLast - 1], points[sourceLast], 0.68);
  const tipPrepB = mixPoint(points[sourceLast - 1], points[sourceLast], 0.86);
  const tipRadius = radii[sourceLast] ?? 5;
  const tipPrepRadiusA = mix(radii[sourceLast - 1] ?? tipRadius, tipRadius, 0.68);
  const tipPrepRadiusB = mix(radii[sourceLast - 1] ?? tipRadius, tipRadius, 0.86);
  const outlinePoints = [...points.slice(0, sourceLast), tipPrepA, tipPrepB, points[sourceLast]];
  const outlineRadii = [...radii.slice(0, sourceLast), tipPrepRadiusA, tipPrepRadiusB, tipRadius];
  const last = outlinePoints.length - 1;
  const tipTangent = stableTipTangent(points, fallbackAngle);
  const tipNormal = normalFromTangent(tipTangent);

  // the last 3 outline points (tipPrepA, tipPrepB, tip) are bunched in the final segment;
  // give them all the SAME stable tip tangent so the tip edges can't wiggle/cross.
  const edgeTangent = (index: number): Point =>
    index >= last - 2
      ? tipTangent
      : tangentFromPoints(
          outlinePoints[Math.max(0, index - 1)],
          outlinePoints[Math.min(last, index + 1)],
          tipTangent,
        );
  const left = outlinePoints.map((point, index) =>
    offsetWithTangent(point, edgeTangent(index), outlineRadii[index] ?? outlineRadii[outlineRadii.length - 1] ?? 3, 1),
  );
  const right = outlinePoints.map((point, index) =>
    offsetWithTangent(point, edgeTangent(index), outlineRadii[index] ?? outlineRadii[outlineRadii.length - 1] ?? 3, -1),
  );

  return {left, right, outlinePoints, outlineRadii, tipTangent, tipNormal};
};

export const armOutlinePath = (points: Point[], radii: number[], fallbackAngle = 0): string => {
  const geometry = buildArmOutlineGeometry(points, radii, fallbackAngle);

  if (!geometry) {
    return "";
  }

  const {left, right, outlinePoints, outlineRadii, tipTangent} = geometry;
  const last = outlinePoints.length - 1;
  const root = outlinePoints[0];
  const leftPath = catmullRomToBezierPath(left, 0.18);
  const rightPath = stripMove(catmullRomToBezierPath([...right].reverse(), 0.18));
  const rootRadius = outlineRadii[0] ?? 8;
  const tipRadius = outlineRadii[last] ?? 5;

  return [
    leftPath,
    tipCapPath(outlinePoints[last], tipTangent, tipRadius),
    rightPath,
    `Q ${root.x.toFixed(2)} ${(root.y - rootRadius * 0.28).toFixed(2)} ${left[0].x.toFixed(2)} ${left[0].y.toFixed(2)}`,
    "Z",
  ].join(" ");
};

export const taperedRadii = (points: Point[], baseRadius: number, tipRadius: number): number[] => {
  if (points.length === 0) {
    return [];
  }

  const distances = points.reduce<number[]>((out, point, index) => {
    if (index === 0) {
      out.push(0);
      return out;
    }

    const previous = points[index - 1];
    out.push(out[index - 1] + Math.hypot(point.x - previous.x, point.y - previous.y));
    return out;
  }, []);
  const total = distances[distances.length - 1] || 1;
  const tipFloor = Math.max(tipRadius, baseRadius * 0.42);

  return distances.map((distance) => {
    const u = distance / total;
    const profile =
      u < 0.12
        ? mix(1, 0.97, u / 0.12)
        : u < 0.4
          ? mix(0.97, 0.82, (u - 0.12) / 0.28)
          : u < 0.72
            ? mix(0.82, 0.56, (u - 0.4) / 0.32)
            : mix(0.56, 0.46, (u - 0.72) / 0.28);

    return Math.max(tipFloor, baseRadius * profile);
  });
};
