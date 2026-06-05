import type React from "react";
import {useVideoConfig} from "remotion";
import {CharacterLayer} from "./character/CharacterLayer";
import type {OctopusIntentKeyframe} from "./character/rigTypes";
import {resolveAnchors, type Anchor} from "./scene/anchors";
import {ACCENTS} from "./theme";

// Isolated octopus on a plain background, static camera, big + centered, idle at rest.
// Diagnostic-only composition to watch the legs/tips with zero scene noise.
const anchors: Anchor[] = [
  {id: "headline", x: 0.5, y: 0.18, z: 0, role: "headline"},
  {id: "stat.main", x: 0.5, y: 0.5, z: 0, role: "stat", radius: 260},
  {id: "safe.lower_left", x: 0.5, y: 0.62, z: 0, role: "character_safe"},
];

const keyframes: OctopusIntentKeyframe[] = [
  {
    time: 0,
    preset: "idle",
    position: {x: 0.32, y: 0.52},
    scale: 0.26,
    depth: 0,
    gaze: {id: "headline"},
    bodyLean: 0,
    energy: 0.4,
    expression: {curious: 0.8, neutral: 0.2},
    locomotionMode: "drift",
  },
  {
    time: 3.7,
    preset: "react",
    position: {x: 0.32, y: 0.52},
    scale: 0.26,
    depth: 0,
    gaze: {id: "stat.main"},
    bodyLean: 0.2,
    energy: 0.8,
    expression: {surprised: 0.8, curious: 0.2},
    locomotionMode: "drift",
    arms: {
      a0: {mode: "reach", target: {id: "stat.main", dx: -32, dy: 20}, reach: 0.9, curl: 0.5, priority: 0.95},
      a1: {mode: "reach", target: {id: "stat.main", dx: -235, dy: 230}, reach: 0.34, curl: 0.5, priority: 0.55},
    },
  },
];

export const OctoDebug: React.FC = () => {
  const {width, height} = useVideoConfig();
  const resolved = resolveAnchors(anchors, width, height);

  return (
    <div style={{position: "absolute", inset: 0, background: "#0a0a14"}}>
      <CharacterLayer anchors={resolved} keyframes={keyframes} accent={ACCENTS[1]} />
    </div>
  );
};
