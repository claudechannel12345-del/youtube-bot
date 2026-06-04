import {useCurrentFrame, useVideoConfig} from "remotion";
import type React from "react";
import {CharacterLayer} from "../character/CharacterLayer";
import type {OctopusIntentKeyframe} from "../character/rigTypes";
import {ACCENTS} from "../theme";
import {DepthPlane} from "./DepthPlane";
import {SceneCamera, type CameraMove} from "./SceneCamera";
import {SceneWorld} from "./SceneWorld";
import {resolveAnchors, type Anchor} from "./anchors";
import type {CueBeat} from "./CueTimeline";
import {StatScene} from "./families/StatScene";

const accent = ACCENTS[1];

const anchors: Anchor[] = [
  {id: "headline", x: 0.5, y: 0.22, z: 0, role: "headline"},
  {id: "stat.main", x: 0.5, y: 0.5, z: 0, role: "stat", radius: 260},
  {id: "safe.lower_left", x: 0.24, y: 0.61, z: 90, role: "character_safe"},
];

const contentBeats: CueBeat[] = [
  {id: "beat_count", time: 1.5, duration: 2.0, kind: "count", target: "stat.main", value: 12840, actor: "content", emphasis: 0.7},
  {id: "beat_ring", time: 1.5, duration: 2.0, kind: "trace", target: "stat.main", actor: "content", emphasis: 0.6},
  {id: "beat_label", time: 3.6, duration: 0.12, kind: "label", target: "stat.main", value: "signals mapped in one clean pass", actor: "content", emphasis: 0.55},
];

const camera: CameraMove = {
  move: "push_in",
  target: "stat.main",
  time: 0,
  duration: 8,
  zoom: 1.08,
  z: 46,
  rotateX: -0.35,
  rotateY: 0.55,
  ease: "ease",
};

const characterKeyframes: OctopusIntentKeyframe[] = [
  {
    time: 0,
    preset: "idle",
    position: {x: 0.23, y: 0.61},
    scale: 0.135,
    depth: 100,
    gaze: {id: "headline"},
    bodyLean: -0.2,
    energy: 0.35,
    expression: {curious: 0.78, neutral: 0.22},
    locomotionMode: "drift",
  },
  {
    time: 0.4,
    preset: "idle",
    position: {x: 0.24, y: 0.61},
    scale: 0.145,
    depth: 100,
    gaze: {id: "headline"},
    bodyLean: -0.05,
    energy: 0.4,
    expression: {curious: 0.85, neutral: 0.15},
    locomotionMode: "drift",
  },
  {
    time: 2.0,
    preset: "react",
    position: {x: 0.24, y: 0.6},
    scale: 0.15,
    depth: 110,
    gaze: {id: "stat.main"},
    bodyLean: 0.3,
    energy: 0.6,
    expression: {curious: 0.58, surprised: 0.42},
    locomotionMode: "drift",
    arms: {
      a0: {mode: "reach", target: {id: "stat.main", dx: -40, dy: 28}, reach: 0.8, curl: 0.5, priority: 0.9},
      a1: {mode: "reach", target: {id: "stat.main", dx: -210, dy: 200}, reach: 0.3, curl: 0.52, priority: 0.4},
      a2: {mode: "relaxed", reach: 0.04, curl: 0.62, priority: 0.1},
      a5: {mode: "relaxed", reach: 0.04, curl: 0.62, priority: 0.1},
    },
  },
  {
    time: 3.7,
    preset: "react",
    position: {x: 0.235, y: 0.6},
    scale: 0.153,
    depth: 124,
    gaze: {id: "stat.main"},
    bodyLean: -0.18,
    energy: 0.8,
    expression: {surprised: 0.8, curious: 0.2},
    locomotionMode: "drift",
    arms: {
      a0: {mode: "reach", target: {id: "stat.main", dx: -32, dy: 20}, reach: 0.9, curl: 0.5, priority: 0.95},
      a1: {mode: "reach", target: {id: "stat.main", dx: -235, dy: 230}, reach: 0.34, curl: 0.5, priority: 0.55},
      a5: {mode: "brace", target: {id: "safe.lower_left", dx: -44, dy: 0}, reach: 0.18, curl: 0.58, priority: 0.35},
    },
  },
  {
    time: 6.5,
    preset: "idle",
    position: {x: 0.24, y: 0.61},
    scale: 0.145,
    depth: 96,
    gaze: {id: "headline"},
    bodyLean: 0.05,
    energy: 0.42,
    expression: {curious: 0.7, neutral: 0.3},
    locomotionMode: "drift",
    arms: {
      a0: {mode: "relaxed", reach: 0.1, curl: 0.42, priority: 0.2},
      a1: {mode: "relaxed", reach: 0.08, curl: 0.48, priority: 0.2},
      a3: {mode: "relaxed", reach: 0.08, curl: 0.5, priority: 0.2},
    },
  },
];

export const Slice: React.FC = () => {
  const frame = useCurrentFrame();
  const {width, height, fps} = useVideoConfig();
  const resolvedAnchors = resolveAnchors(anchors, width, height);

  return (
    <SceneWorld>
      <SceneCamera anchors={resolvedAnchors} camera={camera} frame={frame} fps={fps}>
        <DepthPlane z={0}>
          <StatScene
            frame={frame}
            fps={fps}
            anchors={resolvedAnchors}
            beats={contentBeats}
            accent={accent}
            title="A signal cluster becomes visible"
            label="signals mapped in one clean pass"
            targetValue={12840}
          />
        </DepthPlane>
        <CharacterLayer anchors={resolvedAnchors} keyframes={characterKeyframes} accent={accent} />
      </SceneCamera>
    </SceneWorld>
  );
};
