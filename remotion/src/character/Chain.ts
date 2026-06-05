import type {Point} from "./rigTypes";

type ChainInput = {
  root: Point;
  target: Point;
  jointCount: number;
  linkLength: number;
  baseAngle: number;
  angleConstraint: number;
  curl: number;
  curlDir: -1 | 1;
  frame: number;
  armIndex: number;
  energy: number;
  reach: number;
  activity: number;
};

const clamp = (value: number, min: number, max: number): number => Math.max(min, Math.min(max, value));

const smooth = (value: number): number => {
  const t = clamp(value, 0, 1);
  return t * t * (3 - t * 2);
};

const normalizeAngle = (angle: number): number => {
  let out = angle;
  while (out > Math.PI) {
    out -= Math.PI * 2;
  }
  while (out < -Math.PI) {
    out += Math.PI * 2;
  }
  return out;
};

const clampAngleAround = (angle: number, center: number, range: number): number => {
  const delta = normalizeAngle(angle - center);
  return center + clamp(delta, -range, range);
};

// Angle-constrained "follow-the-target" chain (the iter8 motion that read well):
// each joint aims at the target with a clamped bend, plus a curl-wave (shape) and a
// traveling swim-wave (life). Stateless / frame-local. The swim-wave has an IDLE FLOOR
// so resting legs gently undulate instead of freezing.
export const resolveAngleConstrainedChain = ({
  root,
  target,
  jointCount,
  linkLength,
  baseAngle,
  angleConstraint,
  curl,
  curlDir,
  frame,
  armIndex,
  energy,
  reach,
  activity,
}: ChainInput): Point[] => {
  const points: Point[] = [root];
  let current = root;
  let previousAngle = baseAngle;
  const maxTurn = clamp(angleConstraint, 0.08, Math.PI);
  const reachAmount = clamp(reach, 0, 1);
  const activityAmount = clamp(activity, 0, 1);
  const loosenForReach = 1 + reachAmount * 0.42;
  // keep most of the curl even on reach so the arm S-curves rather than straightening into a rod
  const curlAmount = curl * (1 - reachAmount * 0.2);
  // idle undulation floor: resting legs sway SUBTLY (lowered - was moving too much at rest)
  const idleFloor = 0.3;
  const waveGate = idleFloor + (1 - idleFloor) * activityAmount;

  for (let i = 0; i < jointCount - 1; i++) {
    const segmentT = i / Math.max(1, jointCount - 2);
    const remaining = Math.max(1, jointCount - 1 - i);
    const dx = target.x - current.x;
    const dy = target.y - current.y;
    const distance = Math.max(0.001, Math.hypot(dx, dy));
    const directAngle = Math.atan2(dy, dx);
    const closeTarget = clamp((remaining * linkLength - distance) / (remaining * linkLength), 0, 1);
    // tip calm-down: wave + curl fade to ~0 over the outer ~40% so the tip stays STABLE (no flip).
    const tipFade = smooth((1 - segmentT) / 0.4);
    // base fade: keep the reach-S out of the first ~32% so the base extends OUTWARD and the S
    // forms in the mid-outer arm (stops the arm curving back / clipping into the body).
    const baseFade = smooth(segmentT / 0.32);
    // idle = single arc (relaxes when reaching far); reach = an S that forms mid-outer and
    // persists when extended, so a pointing arm S-curves toward the target instead of a rod.
    const idleArc = Math.sin(segmentT * Math.PI * 1.04) * closeTarget;
    const reachS = Math.sin(segmentT * Math.PI * 2.0) * baseFade;
    const curlShape = idleArc * (1 - reachAmount) + reachS * reachAmount * 0.75;
    const curlWave = curlShape * curlAmount * 0.95 * curlDir * (0.4 + 0.6 * tipFade);
    // traveling swim-wave: subtle, slow, tip-faded so the cap stays stable.
    const waveAmplitude = Math.sin(segmentT * Math.PI) * (0.07 + energy * 0.08) * tipFade * waveGate;
    const swimWave = Math.sin(frame * 0.058 + armIndex * 0.9 + segmentT * 6.0) * waveAmplitude;
    const desiredAngle = directAngle + curlWave + swimWave;
    // stiffen the last ~30% of the arm so the TIP stays nearly straight (low curvature).
    // a curved tip is what self-intersects / flips the rounded cap; a straight tip is stable.
    const tipStiffen = 1 - smooth((segmentT - 0.68) / 0.32) * 0.88;
    const rootRange = (i === 0 ? maxTurn * 0.75 : maxTurn * loosenForReach) * tipStiffen;
    const angle = clampAngleAround(desiredAngle, previousAngle, rootRange);
    const next = {
      x: current.x + Math.cos(angle) * linkLength,
      y: current.y + Math.sin(angle) * linkLength,
    };

    points.push(next);
    current = next;
    previousAngle = angle;
  }

  return points;
};
