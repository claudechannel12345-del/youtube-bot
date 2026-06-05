import {Composition} from "remotion";
import type React from "react";
import {CutawayEpisode} from "./cutaway/CutawayEpisode";
import type {EpisodeProps as CutawayEpisodeProps} from "./cutaway/types";
import {Episode} from "./Episode";
import {GpsProof} from "./flat/GpsProof";
import {OctoDebug} from "./OctoDebug";
import {Short} from "./Short";
import {Slice} from "./scene/Slice";
import type {EpisodeProps, ShortProps} from "./types";

const defaultProps: EpisodeProps = {
  fps: 30,
  width: 1920,
  height: 1080,
  sections: [
    {
      durationInFrames: 150,
      audioSrc: "",
      template: "title_card",
      key_phrase: "COSMIC QUESTION",
      on_screen: {subtitle: "A motion graphics preview"},
      accentIndex: 0,
    },
  ],
};

const defaultShortProps: ShortProps = {
  fps: 30,
  sections: [
    {
      durationInFrames: 150,
      audioSrc: "",
      key_phrase: "COSMIC QUESTION",
      captions: [
        {
          text: "A motion graphics preview",
          start: 0,
          end: 5,
        },
      ],
    },
  ],
};

const cutawayDefaultProps: CutawayEpisodeProps = {
  schema_version: 2,
  fps: 30,
  width: 1920,
  height: 1080,
  style_version: "clean_flat_light_v1",
  sections: [
    {
      section_index: 0,
      durationInFrames: 345,
      audioSrc: "",
      key_phrase: "SPACE CLOCKS",
      narration:
        "Your phone does not ask satellites where it is. It asks them what time it is. Four answers later, the rectangle in your hand has bullied physics into drawing a little blue dot.",
      captions: [
        {text: "Your phone does not ask satellites where it is.", start: 0, end: 3.4, delivery: "skeptical"},
        {text: "It asks them what time it is.", start: 3.4, end: 5.8, delivery: "curious"},
        {
          text: "Four answers later, the rectangle in your hand has bullied physics into drawing a little blue dot.",
          start: 5.8,
          end: 11.5,
          delivery: "brisk",
        },
      ],
      beats: [
        {
          id: "gps_not_where",
          type: "establish",
          start: 0,
          end: 3.4,
          startFrame: 0,
          endFrame: 102,
          scene_family: "object_stage",
          layout: "center_subject",
          camera: {move: "hold_then_push", target: "phone", intensity: "small"},
          transition_in: "hard_cut",
          transition_out: "match_cut",
          background: {treatment: "plain"},
          assets: [
            {id: "phone", kind: "prop", name: "phone", anchor: "center_subject"},
            {id: "satellites", kind: "icon_cluster", name: "satellite", count: 3, anchor: "upper_band", colorRole: "blue"},
          ],
          text_overlays: [{role: "stamp", text: "NOT WHERE", anchor: "lower_center", tone: "coral_stamp"}],
          motion: [
            {target: "phone", kind: "micro_bob", delay: 0, duration: 3.4},
            {target: "satellites", kind: "pop_in", delay: 0.15, duration: 0.3},
          ],
        },
        {
          id: "gps_time",
          type: "diagram_build",
          start: 3.4,
          end: 5.8,
          startFrame: 102,
          endFrame: 174,
          scene_family: "diagram_stage",
          layout: "radial",
          camera: {move: "static", target: "center", intensity: "none"},
          transition_in: "match_cut",
          transition_out: "match_cut",
          background: {treatment: "plain"},
          assets: [
            {id: "phone_center", kind: "prop", name: "phone", anchor: "center"},
            {id: "satellite_a", kind: "icon", name: "satellite", anchor: "upper_left", colorRole: "blue"},
            {id: "satellite_b", kind: "icon", name: "satellite", anchor: "upper_right", colorRole: "blue"},
            {id: "clock", kind: "icon", name: "atomic_clock", anchor: "lower_left", colorRole: "accent"},
          ],
          text_overlays: [{role: "label", text: "TIME SIGNALS", anchor: "lower_center", tone: "ink"}],
          motion: [
            {target: "satellite_a", kind: "pop_in", delay: 0, duration: 0.25},
            {target: "satellite_b", kind: "pop_in", delay: 0.1, duration: 0.25},
            {target: "clock", kind: "pulse", delay: 0, duration: 2.4},
          ],
        },
        {
          id: "gps_blue_dot_gag",
          type: "cutaway_gag",
          start: 5.8,
          end: 11.5,
          startFrame: 174,
          endFrame: 345,
          scene_family: "miniature_world",
          layout: "wide_scene",
          camera: {move: "snap_zoom", target: "stamp", intensity: "small"},
          transition_in: "smash_cut",
          transition_out: "hard_cut",
          background: {treatment: "plain"},
          assets: [
            {id: "physics_label", kind: "label", name: "label", anchor: "left", variant: "PHYSICS"},
            {id: "stamp", kind: "stamp", name: "stamp", anchor: "center", variant: "APPROVED"},
            {id: "blue_dot", kind: "prop", name: "dot", anchor: "right", colorRole: "blue"},
          ],
          text_overlays: [{role: "stamp", text: "BLUE DOT", anchor: "upper_center", tone: "coral_stamp"}],
          motion: [
            {target: "stamp", kind: "stamp", delay: 0.35, duration: 0.25},
            {target: "blue_dot", kind: "pulse", delay: 0.5, duration: 4.5},
          ],
        },
      ],
    },
  ],
};

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="GpsProof"
        component={GpsProof}
        durationInFrames={600}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="Slice"
        component={Slice}
        durationInFrames={240}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="OctoDebug"
        component={OctoDebug}
        durationInFrames={240}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="Episode"
        component={Episode}
        defaultProps={defaultProps}
        calculateMetadata={({props}) => {
          const episodeProps = props as EpisodeProps;
          const sections = episodeProps.sections.length > 0 ? episodeProps.sections : defaultProps.sections;
          return {
            fps: episodeProps.fps || 30,
            width: episodeProps.width || 1920,
            height: episodeProps.height || 1080,
            durationInFrames: sections.reduce((sum, section) => sum + section.durationInFrames, 0),
          };
        }}
      />
      <Composition
        id="Cutaway"
        component={CutawayEpisode}
        defaultProps={cutawayDefaultProps}
        calculateMetadata={({props}) => {
          const episodeProps = props as CutawayEpisodeProps;
          const sections = episodeProps.sections.length > 0 ? episodeProps.sections : cutawayDefaultProps.sections;
          return {
            fps: episodeProps.fps || cutawayDefaultProps.fps,
            width: episodeProps.width || cutawayDefaultProps.width,
            height: episodeProps.height || cutawayDefaultProps.height,
            durationInFrames: sections.reduce((sum, section) => sum + section.durationInFrames, 0),
          };
        }}
      />
      <Composition
        id="Short"
        component={Short}
        defaultProps={defaultShortProps}
        calculateMetadata={({props}) => {
          const shortProps = props as ShortProps;
          const sections = shortProps.sections.length > 0 ? shortProps.sections : defaultShortProps.sections;
          return {
            fps: shortProps.fps || 30,
            width: 1080,
            height: 1920,
            durationInFrames: sections.reduce((sum, section) => sum + section.durationInFrames, 0),
          };
        }}
      />
    </>
  );
};
