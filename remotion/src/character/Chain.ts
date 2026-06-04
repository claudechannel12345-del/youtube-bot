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
  // keep more curl even on reach so the arm curves rather than straightening into a rod
  const curlAmount = curl * (1 - reachAmount * 0.45);
  // idle undulation floor: resting legs still sway (was fully gated to 0 before)
  const idleFloor = 0.55;
  const waveGate = idleFloor + (1 - idleFloor) * activityAmount;

  for (let i = 0; i < jointCount - 1; i++) {
    const segmentT = i / Math.max(1, jointCount - 2);
    const remaining = Math.max(1, jointCount - 1 - i);
    const dx = target.x - current.x;
    const dy = target.y - current.y;
    const distance = Math.max(0.001, Math.hypot(dx, dy));
    const directAngle = Math.atan2(dy, dx);
    const closeTarget = clamp((remaining * linkLength - distance) / (remaining * linkLength), 0, 1);
    // curl-wave: bends the arm along its length (shape). Stronger = more curl.
    const curlWave = Math.sin(segmentT * Math.PI * 1.04) * curlAmount * 0.72 * curlDir;
    // traveling swim-wave: continuous gentle undulation; tip-faded so the cap stays stable.
    const tipFade = 1 - Math.max(0, segmentT - 0.78) / 0.22;
    const waveAmplitude = Math.sin(segmentT * Math.PI) * (0.1 + energy * 0.12) * tipFade * waveGate;
    const swimWave = Math.sin(frame * 0.09 + armIndex * 0.9 + segmentT * 6.4) * waveAmplitude;
    const desiredAngle = directAngle + curlWave * closeTarget + swimWave;
    const rootRange = i === 0 ? maxTurn * 0.75 : maxTurn * loosenForReach;
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
