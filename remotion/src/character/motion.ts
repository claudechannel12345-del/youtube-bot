import type {Point} from "./rigTypes";

export const mix = (from: number, to: number, progress: number): number => from + (to - from) * progress;

export const mixPoint = (from: Point, to: Point, progress: number): Point => ({
  x: mix(from.x, to.x, progress),
  y: mix(from.y, to.y, progress),
});

export const analyticLagPoint = (
  current: Point,
  previous: Point,
  older: Point,
  lagFrames: number,
): Point => {
  const totalDelta = Math.hypot(current.x - older.x, current.y - older.y);
  const recentDelta = Math.hypot(current.x - previous.x, current.y - previous.y);

  if (totalDelta < 0.001 || recentDelta < 0.001) {
    return current;
  }

  const lag = Math.max(0.08, Math.min(0.34, lagFrames * 0.12));

  return {
    x: mix(current.x, previous.x, lag),
    y: mix(current.y, previous.y, lag),
  };
};

export const applyPerpendicularUndulation = (
  points: Point[],
  frame: number,
  armIndex: number,
  energy: number,
  reach: number,
): Point[] => {
  if (points.length < 3) {
    return points;
  }

  return points.map((point, index) => {
    if (index === 0) {
      return point;
    }
    const previous = points[Math.max(0, index - 1)];
    const next = points[Math.min(points.length - 1, index + 1)];
    const dx = next.x - previous.x;
    const dy = next.y - previous.y;
    const distance = Math.max(0.001, Math.hypot(dx, dy));
    const normal = {x: -dy / distance, y: dx / distance};
    const segmentT = index / (points.length - 1);
    const shoulderDecay = Math.sin(segmentT * Math.PI);
    const tipReachDecay = 1 - Math.max(0, segmentT - 0.72) / 0.28 * reach;
    const wave = Math.sin(frame * 0.095 + armIndex * 0.88 + segmentT * 7.2);
    const amplitude = 16 * (0.35 + energy) * shoulderDecay * Math.max(0.18, tipReachDecay);
    return {
      x: point.x + normal.x * wave * amplitude,
      y: point.y + normal.y * wave * amplitude,
    };
  });
};

export const buoyancyBob = (frame: number, energy: number): number => Math.sin(frame / 42 + 0.7) * 8 * (0.45 + energy);

export const mantlePulse = (frame: number, energy: number): {x: number; y: number} => {
  const pulse = Math.sin(frame / 33) * 0.018 * (0.35 + energy);
  return {
    x: 1 + pulse,
    y: 1 - pulse * 0.75,
  };
};
