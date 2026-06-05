import {Easing} from "remotion";
import {getAnchor, type AnchorMap, type ResolvedAnchor} from "../scene/anchors";
import {ACCENTS} from "../theme";
import {armOutlinePath, taperedRadii} from "./armOutline";
import {resolveAngleConstrainedChain} from "./Chain";
import {blendExpressions} from "./expressions";
import {analyticLagPoint, buoyancyBob, mantlePulse, mix, mixPoint} from "./motion";
import type {ArmIntent, OctopusIntentKeyframe, Point, ResolvedPose} from "./rigTypes";

const clamp = (value: number, min: number, max: number): number => Math.max(min, Math.min(max, value));
const smoothstep = (value: number): number => {
  const t = clamp(value, 0, 1);
  return t * t * (3 - t * 2);
};

export const ROOT_TUCK = 0.9;

const armConfigs = [
  {id: "a0", side: 1 as const, root: {x: 0.31, y: 0.43}, idle: {x: 1.02, y: 1.42}, baseAngle: 0.74, curlDir: -1 as const, length: 1.64},
  {id: "a1", side: 1 as const, root: {x: 0.17, y: 0.52}, idle: {x: 0.6, y: 1.66}, baseAngle: 1.04, curlDir: -1 as const, length: 1.58},
  {id: "a2", side: 1 as const, root: {x: 0.05, y: 0.61}, idle: {x: 0.2, y: 1.8}, baseAngle: 1.32, curlDir: -1 as const, length: 1.48},
  {id: "a3", side: -1 as const, root: {x: -0.05, y: 0.61}, idle: {x: -0.2, y: 1.8}, baseAngle: 1.82, curlDir: 1 as const, length: 1.48},
  {id: "a4", side: -1 as const, root: {x: -0.17, y: 0.52}, idle: {x: -0.6, y: 1.66}, baseAngle: 2.1, curlDir: 1 as const, length: 1.58},
  {id: "a5", side: -1 as const, root: {x: -0.31, y: 0.43}, idle: {x: -1.02, y: 1.42}, baseAngle: 2.4, curlDir: 1 as const, length: 1.64},
];

type ArmConfig = (typeof armConfigs)[number];

const defaultFrame: OctopusIntentKeyframe = {
  time: 0,
  position: {x: 0.16, y: 0.78},
  scale: 0.15,
  depth: 90,
  bodyLean: 0,
  energy: 0.4,
  expression: {curious: 1},
  locomotionMode: "drift",
  gaze: {id: "headline"},
};

const ease = (progress: number): number => Easing.inOut(Easing.cubic)(clamp(progress, 0, 1));

const findPair = (keyframes: OctopusIntentKeyframe[], time: number): [OctopusIntentKeyframe, OctopusIntentKeyframe, number] => {
  const sorted = keyframes.length > 0 ? keyframes : [defaultFrame];
  if (time <= sorted[0].time) {
    return [sorted[0], sorted[0], 0];
  }
  for (let i = 0; i < sorted.length - 1; i++) {
    const from = sorted[i];
    const to = sorted[i + 1];
    if (time >= from.time && time <= to.time) {
      return [from, to, ease((time - from.time) / Math.max(0.001, to.time - from.time))];
    }
  }
  const last = sorted[sorted.length - 1];
  return [last, last, 1];
};

const expressionKeys = ["neutral", "curious", "surprised", "skeptical", "thinking", "excited", "concerned"] as const;

const defaultArmIntent: ArmIntent = {mode: "relaxed", reach: 0, curl: 0.58, priority: 0};

const interpolateIntent = (keyframes: OctopusIntentKeyframe[], time: number): OctopusIntentKeyframe => {
  const [fromRaw, toRaw, progress] = findPair(keyframes, time);
  const from = {...defaultFrame, ...fromRaw};
  const to = {...from, ...toRaw};
  const expression = expressionKeys.reduce<NonNullable<OctopusIntentKeyframe["expression"]>>((out, key) => {
    out[key] = mix(from.expression?.[key] ?? 0, to.expression?.[key] ?? 0, progress);
    return out;
  }, {});
  const armIds = new Set([...Object.keys(from.arms ?? {}), ...Object.keys(to.arms ?? {})]);
  const arms: Record<string, ArmIntent> = {};

  armIds.forEach((id) => {
    const a = from.arms?.[id] ?? defaultArmIntent;
    const b = to.arms?.[id] ?? defaultArmIntent;
    arms[id] = {
      mode: b.mode,
      target: b.target ?? a.target,
      reach: mix(a.reach ?? 0, b.reach ?? 0, progress),
      curl: mix(a.curl ?? 0.45, b.curl ?? 0.45, progress),
      priority: mix(a.priority ?? 0, b.priority ?? 0, progress),
    };
  });

  return {
    time,
    preset: to.preset ?? from.preset,
    position: {
      x: mix(from.position?.x ?? defaultFrame.position!.x, to.position?.x ?? defaultFrame.position!.x, progress),
      y: mix(from.position?.y ?? defaultFrame.position!.y, to.position?.y ?? defaultFrame.position!.y, progress),
    },
    scale: mix(from.scale ?? defaultFrame.scale!, to.scale ?? defaultFrame.scale!, progress),
    depth: mix(from.depth ?? defaultFrame.depth!, to.depth ?? defaultFrame.depth!, progress),
    gaze: to.gaze ?? from.gaze,
    bodyLean: mix(from.bodyLean ?? 0, to.bodyLean ?? 0, progress),
    energy: mix(from.energy ?? 0.4, to.energy ?? 0.4, progress),
    expression,
    locomotionMode: to.locomotionMode ?? from.locomotionMode,
    arms,
  };
};

const resolveRef = (anchors: AnchorMap, ref: ArmIntent["target"]): Point => {
  if (!ref) {
    const fallback = getAnchor(anchors, "safe.lower_left");
    return {x: fallback.px, y: fallback.py};
  }
  const anchor = getAnchor(anchors, ref.id);
  return {
    x: anchor.px + (ref.dx ?? 0),
    y: anchor.py + (ref.dy ?? 0),
  };
};

const resolveGaze = (anchors: AnchorMap, gaze: OctopusIntentKeyframe["gaze"]): ResolvedAnchor | Point => {
  if (!gaze) {
    return getAnchor(anchors, "headline");
  }
  if ("id" in gaze) {
    return getAnchor(anchors, gaze.id);
  }
  return {x: gaze.x * 1920, y: gaze.y * 1080};
};

const resolveGazePoint = (anchors: AnchorMap, gaze: OctopusIntentKeyframe["gaze"]): Point => {
  const resolved = resolveGaze(anchors, gaze);
  if ("px" in resolved) {
    return {x: resolved.px, y: resolved.py};
  }
  return resolved;
};

const resolveGazeAt = (keyframes: OctopusIntentKeyframe[], anchors: AnchorMap, time: number): Point => {
  const [fromRaw, toRaw, progress] = findPair(keyframes, time);
  const from = {...defaultFrame, ...fromRaw};
  const to = {...from, ...toRaw};
  return mixPoint(resolveGazePoint(anchors, from.gaze), resolveGazePoint(anchors, to.gaze), progress);
};

const rotatePoint = (point: Point, radians: number): Point => ({
  x: point.x * Math.cos(radians) - point.y * Math.sin(radians),
  y: point.x * Math.sin(radians) + point.y * Math.cos(radians),
});

const pointFromLocal = (origin: Point, local: Point, scale: number, lean: number): Point => {
  const rotated = rotatePoint({x: local.x * scale, y: local.y * scale}, lean * 0.22);
  return {x: origin.x + rotated.x, y: origin.y + rotated.y};
};

const sampleBodyGeometry = (
  keyframes: OctopusIntentKeyframe[],
  frame: number,
  fps: number,
): {origin: Point; bodyScale: number; lean: number} => {
  const safeFps = Math.max(1, fps);
  const intent = interpolateIntent(keyframes, Math.max(0, frame / safeFps));
  const scaleNorm = clamp(intent.scale ?? 0.15, 0.08, 0.34);
  const energy = intent.energy ?? 0.4;
  const origin = {
    x: (intent.position?.x ?? 0.16) * 1920,
    y: (intent.position?.y ?? 0.78) * 1080 + buoyancyBob(Math.max(0, frame), energy),
  };

  return {
    origin,
    bodyScale: scaleNorm * 1080,
    lean: intent.bodyLean ?? 0,
  };
};

const armBaseAt = (
  keyframes: OctopusIntentKeyframe[],
  frame: number,
  fps: number,
  config: ArmConfig,
): {shoulder: Point; idleTarget: Point} => {
  const geometry = sampleBodyGeometry(keyframes, frame, fps);
  return {
    shoulder: pointFromLocal(geometry.origin, {x: config.root.x * ROOT_TUCK, y: config.root.y * ROOT_TUCK}, geometry.bodyScale, geometry.lean),
    idleTarget: pointFromLocal(geometry.origin, config.idle, geometry.bodyScale, geometry.lean),
  };
};

const armTargetAt = (
  keyframes: OctopusIntentKeyframe[],
  anchors: AnchorMap,
  time: number,
  armId: string,
  shoulder: Point,
  idleTarget: Point,
): {target: Point; intent: ArmIntent; reach: number} => {
  const [fromRaw, toRaw, progress] = findPair(keyframes, time);
  const fromIntent = fromRaw.arms?.[armId] ?? defaultArmIntent;
  const toIntent = toRaw.arms?.[armId] ?? defaultArmIntent;
  const reach = clamp(mix(fromIntent.reach ?? 0, toIntent.reach ?? 0, progress), 0, 1);
  const curl = mix(fromIntent.curl ?? 0.45, toIntent.curl ?? 0.45, progress);
  const priority = mix(fromIntent.priority ?? 0, toIntent.priority ?? 0, progress);
  const fromTarget = fromIntent.target ? resolveRef(anchors, fromIntent.target) : idleTarget;
  const toTarget = toIntent.target ? resolveRef(anchors, toIntent.target) : idleTarget;
  const fromBlended = mixPoint(idleTarget, fromTarget, clamp(fromIntent.reach ?? 0, 0, 1));
  const toBlended = mixPoint(idleTarget, toTarget, clamp(toIntent.reach ?? 0, 0, 1));
  const blended = mixPoint(fromBlended, toBlended, progress);
  const distance = Math.hypot(blended.x - shoulder.x, blended.y - shoulder.y);
  const maxReach = Math.max(1, Math.hypot(idleTarget.x - shoulder.x, idleTarget.y - shoulder.y) * 2.3);
  const intent: ArmIntent = {
    mode: toIntent.mode,
    target: toIntent.target ?? fromIntent.target,
    reach,
    curl,
    priority,
  };

  if (distance <= maxReach) {
    return {target: blended, intent, reach};
  }

  const ratio = maxReach / distance;
  return {
    target: {
      x: shoulder.x + (blended.x - shoulder.x) * ratio,
      y: shoulder.y + (blended.y - shoulder.y) * ratio,
    },
    intent,
    reach,
  };
};

export const solveRig = (
  keyframes: OctopusIntentKeyframe[],
  frame: number,
  fps: number,
  anchors: AnchorMap,
  accent = ACCENTS[1],
): ResolvedPose => {
  const time = frame / fps;
  const intent = interpolateIntent(keyframes, time);
  const scaleNorm = clamp(intent.scale ?? 0.15, 0.08, 0.34);
  const bodyScale = scaleNorm * 1080;
  const bob = buoyancyBob(frame, intent.energy ?? 0.4);
  const pulse = mantlePulse(frame, intent.energy ?? 0.4);
  const body = {
    x: (intent.position?.x ?? 0.16) * 1920,
    y: (intent.position?.y ?? 0.78) * 1080 + bob,
    z: clamp(intent.depth ?? 90, -400, 300),
    scale: bodyScale,
    rotate: (intent.bodyLean ?? 0) * 12 + Math.sin(frame / 75) * 2,
    bob,
    pulseX: pulse.x * (1 + (blendExpressions(intent.expression).mantleSquash * 0.12)),
    pulseY: pulse.y * (1 - (blendExpressions(intent.expression).mantleSquash * 0.1)),
  };
  const origin = {x: body.x, y: body.y};
  const arms = armConfigs.map((config, index) => {
    const shoulder = pointFromLocal(origin, {x: config.root.x * ROOT_TUCK, y: config.root.y * ROOT_TUCK}, bodyScale, intent.bodyLean ?? 0);
    const idleTarget = pointFromLocal(origin, config.idle, bodyScale, intent.bodyLean ?? 0);
    const current = armTargetAt(keyframes, anchors, time, config.id, shoulder, idleTarget);
    const activity = smoothstep(current.reach);
    const curl = mix(0.58, clamp(current.intent.curl ?? 0.58, 0, 1), activity);
    const jointCount = 13;
    const restLength = bodyScale * config.length;
    const localBase = rotatePoint({x: Math.cos(config.baseAngle), y: Math.sin(config.baseAngle)}, (intent.bodyLean ?? 0) * 0.22);
    const baseAngle = Math.atan2(localBase.y, localBase.x);
    const targetAt = (framesAgo: number): Point => {
      const sampledFrame = Math.max(0, frame - framesAgo);
      const sampledTime = sampledFrame / Math.max(1, fps);
      const base = armBaseAt(keyframes, sampledFrame, fps, config);
      return armTargetAt(keyframes, anchors, sampledTime, config.id, base.shoulder, base.idleTarget).target;
    };
    const lagFrames = (0.055 + index * 0.012) * fps;
    const delayedTarget = targetAt(0); // TEST: lag disabled to isolate the jump
    void analyticLagPoint;
    void lagFrames;
    const linkLength = restLength / (jointCount - 1);
    const points = resolveAngleConstrainedChain({
      root: shoulder,
      target: delayedTarget,
      jointCount,
      linkLength,
      baseAngle,
      angleConstraint: 0.34 + activity * 0.12,
      curl,
      curlDir: config.curlDir,
      frame,
      armIndex: index,
      energy: intent.energy ?? 0.4,
      reach: current.reach,
      activity,
    });
    const radii = taperedRadii(points, bodyScale * (0.132 - (index % 4) * 0.003), bodyScale * 0.04);

    return {
      id: config.id,
      side: config.side,
      outlinePath: armOutlinePath(points, radii, baseAngle),
      points,
      radii,
      opacity: 0.95,
      tip: points[points.length - 1],
      mode: current.intent.mode,
      baseAngle,
    };
  });

  return {
    body,
    gazeTarget: resolveGazeAt(keyframes, anchors, time),
    expression: blendExpressions(intent.expression),
    arms,
    accent,
    frame,
    energy: intent.energy ?? 0.4,
  };
};
