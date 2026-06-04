import {useCurrentFrame, useVideoConfig} from "remotion";
import type React from "react";
import {DepthPlane} from "../scene/DepthPlane";
import type {AnchorMap} from "../scene/anchors";
import {CosmicOctopus} from "./CosmicOctopus";
import {solveRig} from "./solveRig";
import type {OctopusIntentKeyframe} from "./rigTypes";

type CharacterLayerProps = {
  anchors: AnchorMap;
  keyframes: OctopusIntentKeyframe[];
  accent: string;
};

export const CharacterLayer: React.FC<CharacterLayerProps> = ({anchors, keyframes, accent}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const pose = solveRig(keyframes, frame, fps, anchors, accent);

  return (
    <DepthPlane z={pose.body.z}>
      <CosmicOctopus pose={pose} />
    </DepthPlane>
  );
};
