import type {ResolvedAnchor} from "../scene/anchors";

export type LocomotionMode = "idle" | "drift" | "arm_swing" | "jet" | "exit";

export type ExpressionName =
  | "neutral"
  | "curious"
  | "surprised"
  | "skeptical"
  | "thinking"
  | "excited"
  | "concerned";

export type ArmMode = "relaxed" | "point" | "reach" | "grab" | "place" | "brace" | "wave";

export type AnchorRef = {
  id: string;
  dx?: number;
  dy?: number;
};

export type ArmIntent = {
  mode: ArmMode;
  target?: AnchorRef;
  reach?: number;
  curl?: number;
  priority?: number;
};

export type OctopusIntentKeyframe = {
  time: number;
  preset?: "idle" | "point" | "multi_build" | "react" | "jet" | "exit";
  position?: {x: number; y: number};
  scale?: number;
  depth?: number;
  gaze?: AnchorRef | {x: number; y: number};
  bodyLean?: number;
  energy?: number;
  expression?: Partial<Record<ExpressionName, number>>;
  locomotionMode?: LocomotionMode;
  arms?: Record<string, ArmIntent>;
};

export type Point = {
  x: number;
  y: number;
};

export type ExpressionChannels = {
  eyeOpen: number;
  pupilScale: number;
  pupilX: number;
  pupilY: number;
  browRaise: number;
  browAngle: number;
  mouthOpen: number;
  mouthCurve: number;
  mantleSquash: number;
  glowIntensity: number;
};

export type SolvedArm = {
  id: string;
  side: -1 | 1;
  outlinePath: string;
  points: Point[];
  radii: number[];
  opacity: number;
  tip: Point;
  mode: ArmMode;
  baseAngle: number;
};

export type ResolvedPose = {
  body: {
    x: number;
    y: number;
    z: number;
    scale: number;
    rotate: number;
    bob: number;
    pulseX: number;
    pulseY: number;
  };
  gazeTarget: ResolvedAnchor | Point;
  expression: ExpressionChannels;
  arms: SolvedArm[];
  accent: string;
  frame: number;
  energy: number;
};
