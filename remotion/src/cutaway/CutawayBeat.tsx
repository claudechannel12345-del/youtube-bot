import type React from "react";
import {AbsoluteFill, interpolate, Sequence, spring, useCurrentFrame, useVideoConfig} from "remotion";
import {CaptionPunch} from "./families/CaptionPunch";
import {ComparisonStage} from "./families/ComparisonStage";
import {DiagramStage} from "./families/DiagramStage";
import {ListStage} from "./families/ListStage";
import {MapStage} from "./families/MapStage";
import {MiniatureWorld} from "./families/MiniatureWorld";
import {ObjectStage} from "./families/ObjectStage";
import {PaperworkStage} from "./families/PaperworkStage";
import {QuoteStage} from "./families/QuoteStage";
import {StatStage} from "./families/StatStage";
import {TimelineStage} from "./families/TimelineStage";
import {TitleStage} from "./families/TitleStage";
import type {DirectedBeat, LegacyDirectedBeat, SceneFamily} from "./types";
import {PAPER} from "../flat/theme";

const familyForBeatType: Record<string, SceneFamily> = {
  establish: "object_stage",
  illustrate: "object_stage",
  stat_pop: "stat_stage",
  compare: "comparison_stage",
  diagram_build: "diagram_stage",
  process: "list_stage",
  map_focus: "map_stage",
  list_reveal: "list_stage",
  quote: "quote_stage",
  cutaway_gag: "miniature_world",
  emphasize: "caption_punch",
  transition: "caption_punch",
};

const familyComponents: Record<SceneFamily, React.FC<{beat: LegacyDirectedBeat; localFrame: number}>> = {
  title_stage: TitleStage,
  object_stage: ObjectStage,
  diagram_stage: DiagramStage,
  map_stage: MapStage,
  comparison_stage: ComparisonStage,
  timeline_stage: TimelineStage,
  list_stage: ListStage,
  stat_stage: StatStage,
  paperwork_stage: PaperworkStage,
  miniature_world: MiniatureWorld,
  quote_stage: QuoteStage,
  caption_punch: CaptionPunch,
};

const edgeStyle = (beat: DirectedBeat, localFrame: number, duration: number, fps: number): React.CSSProperties => {
  const edge = Math.min(10, Math.max(3, Math.floor(duration / 4)));
  const inProgress = interpolate(localFrame, [0, edge], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const outProgress = interpolate(localFrame, [duration - edge, duration], [1, 0], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const pop = spring({frame: localFrame, fps, config: {damping: 15, stiffness: 190}});
  const smash = spring({frame: localFrame, fps, config: {damping: 9, stiffness: 260}});
  const opacityIn = beat.transition_in === "hard_cut" || beat.transition_in === "match_cut" ? 1 : inProgress;
  const opacityOut = beat.transition_out === "hard_cut" || beat.transition_out === "match_cut" ? 1 : outProgress;
  const dipOpacity = beat.transition_in === "dip_to_bg" ? inProgress : 1;
  const scaleIn =
    beat.transition_in === "pop_cut" ? 0.88 + Math.min(1, pop) * 0.12 : beat.transition_in === "smash_cut" ? 1.16 - Math.min(1, smash) * 0.16 : 1;
  const scaleOut = beat.transition_out === "smash_cut" ? interpolate(localFrame, [duration - edge, duration], [1, 0.92], {extrapolateLeft: "clamp", extrapolateRight: "clamp"}) : 1;
  return {
    opacity: opacityIn * opacityOut * dipOpacity,
    transform: `scale(${scaleIn * scaleOut})`,
    transformOrigin: "center",
    backgroundColor: beat.transition_in === "dip_to_bg" || beat.transition_out === "dip_to_bg" ? PAPER : undefined,
  };
};

const cameraStyle = (beat: DirectedBeat, localFrame: number, duration: number): React.CSSProperties => {
  const intensity = {none: 0, small: 1, medium: 2, large: 3}[beat.camera.intensity] ?? 1;
  const p = interpolate(localFrame, [0, Math.max(1, duration)], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const delayed = interpolate(localFrame, [duration * 0.35, duration], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  const snap = spring({frame: localFrame, fps: 30, config: {damping: 10, stiffness: 230}});
  let scale = 1;
  let x = 0;
  let y = 0;
  if (beat.camera.move === "push_in") {
    scale = 1 + p * 0.035 * intensity;
  } else if (beat.camera.move === "hold_then_push") {
    scale = 1 + delayed * 0.03 * intensity;
  } else if (beat.camera.move === "pull_back") {
    scale = 1.08 - p * 0.035 * intensity;
  } else if (beat.camera.move === "pan_left") {
    x = p * -36 * intensity;
  } else if (beat.camera.move === "pan_right") {
    x = p * 36 * intensity;
  } else if (beat.camera.move === "snap_zoom") {
    scale = 1 + Math.min(1, snap) * 0.055 * intensity;
  } else if (beat.camera.move === "tilt_down") {
    y = p * 32 * intensity;
  } else if (beat.camera.move === "parallax_drift") {
    x = Math.sin(localFrame / 30) * 14 * intensity;
    y = Math.cos(localFrame / 42) * 8 * intensity;
  }
  return {
    transform: `translate(${x}px, ${y}px) scale(${scale})`,
    transformOrigin: "center",
  };
};

const CutawayBeatInner: React.FC<{beat: DirectedBeat; duration: number}> = ({beat, duration}) => {
  const localFrame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const family = beat.type === "cutaway_gag" ? "miniature_world" : beat.scene_family || familyForBeatType[beat.type] || "caption_punch";
  const Family = familyComponents[family] ?? CaptionPunch;
  const legacyBeat = beat as LegacyDirectedBeat;
  return (
    <AbsoluteFill style={{backgroundColor: PAPER}}>
      <AbsoluteFill style={edgeStyle(beat, localFrame, duration, fps)}>
        <AbsoluteFill style={cameraStyle(beat, localFrame, duration)}>
          <Family beat={legacyBeat} localFrame={localFrame} />
        </AbsoluteFill>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const CutawayBeat: React.FC<{beat: DirectedBeat}> = ({beat}) => {
  const duration = Math.max(1, beat.endFrame - beat.startFrame);
  return (
    <Sequence from={beat.startFrame} durationInFrames={duration}>
      <CutawayBeatInner beat={beat} duration={duration} />
    </Sequence>
  );
};
