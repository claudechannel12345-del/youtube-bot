import {Easing, interpolate} from "remotion";
import type React from "react";
import {getAnchor, type AnchorMap} from "./anchors";

export type CameraMove = {
  move: "push_in";
  target: string;
  time: number;
  duration: number;
  zoom?: number;
  z?: number;
  rotateX?: number;
  rotateY?: number;
  ease?: "ease" | "linear";
};

export type CameraState = {
  x: number;
  y: number;
  z: number;
  zoom: number;
  rotateX: number;
  rotateY: number;
};

type SceneCameraProps = {
  anchors: AnchorMap;
  camera: CameraMove;
  frame: number;
  fps: number;
  children: React.ReactNode;
};

const centeredCamera = (anchors: AnchorMap, targetId: string): Pick<CameraState, "x" | "y"> => {
  const target = getAnchor(anchors, targetId);
  return {
    x: target.px - 960,
    y: target.py - 540,
  };
};

export const getCameraState = (
  anchors: AnchorMap,
  camera: CameraMove,
  frame: number,
  fps: number,
): CameraState => {
  const start = camera.time * fps;
  const end = (camera.time + camera.duration) * fps;
  const easing = camera.ease === "linear" ? Easing.linear : Easing.inOut(Easing.cubic);
  const progress = interpolate(frame, [start, end], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing,
  });
  const focus = centeredCamera(anchors, camera.target);

  return {
    x: focus.x * progress * 0.08,
    y: focus.y * progress * 0.08,
    z: interpolate(progress, [0, 1], [0, camera.z ?? 44]),
    zoom: interpolate(progress, [0, 1], [1, camera.zoom ?? 1.08]),
    rotateX: interpolate(progress, [0, 1], [0, camera.rotateX ?? -0.5]),
    rotateY: interpolate(progress, [0, 1], [0, camera.rotateY ?? 0.7]),
  };
};

export const SceneCamera: React.FC<SceneCameraProps> = ({anchors, camera, frame, fps, children}) => {
  const state = getCameraState(anchors, camera, frame, fps);

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        transformStyle: "preserve-3d",
        transform: `translate3d(${-state.x}px, ${-state.y}px, ${-state.z}px) rotateX(${-state.rotateX}deg) rotateY(${-state.rotateY}deg) scale(${state.zoom})`,
        transformOrigin: "50% 50%",
      }}
    >
      {children}
    </div>
  );
};
