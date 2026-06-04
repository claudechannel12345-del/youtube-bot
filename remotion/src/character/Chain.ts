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
  // keep most of the curl even on reach so the arm S-curves rather than straightening into a rod
  const curlAmount = curl * (1 - reachAmount * 0.2);
  // idle undulation floor: resting legs sway with real life (raised for more movement)
  const idleFloor = 0.7;
  const waveGate = idleFloor + (1 - idleFloor) * activityAmount;

  for (let i = 0; i < jointCount - 1; i++) {
    const segmentT = i / Math.max(1, jointCount - 2);
    const remaining = Math.max(1, jointCount - 1 - i);
    const dx = target.x - current.x;
    const dy = target.y - current.y;
    const distance = Math.max(0.001, Math.hypot(dx, dy));
    const directAngle = Math.atan2(dy, dx);
    const closeTarget = clamp((remaining * linkLength - distance) / (remaining * linkLength), 0, 1);
    // curl-wave: idle = single arc (curls toward a near target, relaxes when reaching far);
    // reach = an S-curve that PERSISTS even when the arm extends, so a pointing arm makes an
    // S ending aimed at the target instead of straightening into a rod. Both profiles -> 0 at
    // the tip, so directAngle wins there and the tip lands on the target.
    const idleArc = Math.sin(segmentT * Math.PI * 1.04) * closeTarget;
    const reachS = Math.sin(segmentT * Math.PI * 2.0);
    const curlShape = idleArc * (1 - reachAmount) + reachS * reachAmount * 1.25;
    const curlWave = curlShape * curlAmount * 1.05 * curlDir;
    // traveling swim-wave: continuous gentle undulation; tip-faded so the cap stays stable.
    const tipFade = 1 - Math.max(0, segmentT - 0.78) / 0.22;
    const waveAmplitude = Math.sin(segmentT * Math.PI) * (0.13 + energy * 0.13) * tipFade * waveGate;
    const swimWave = Math.sin(frame * 0.09 + armIndex * 0.9 + segmentT * 6.4) * waveAmplitude;
    const desiredAngle = directAngle + curlWave + swimWave;
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
