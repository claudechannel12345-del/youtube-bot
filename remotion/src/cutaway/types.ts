export type BeatType =
  | "establish"
  | "illustrate"
  | "stat_pop"
  | "compare"
  | "diagram_build"
  | "map_focus"
  | "list_reveal"
  | "cutaway_gag"
  | "emphasize"
  | "transition";

export type Importance = "low" | "medium" | "high" | "must_hit";

export type ComedyRoles =
  | "deadpan_literalization"
  | "scale_absurdity"
  | "bureaucracy_metaphor"
  | "wrong_tool"
  | "overly_literal_label"
  | "quiet_contradiction";

export type SceneFamily =
  | "title_stage"
  | "object_stage"
  | "diagram_stage"
  | "map_stage"
  | "comparison_stage"
  | "timeline_stage"
  | "list_stage"
  | "stat_stage"
  | "paperwork_stage"
  | "miniature_world"
  | "caption_punch";

export type Layout =
  | "center_subject"
  | "left_right"
  | "top_down_stack"
  | "radial"
  | "map_focus"
  | "timeline_horizontal"
  | "three_panel"
  | "paper_stack"
  | "wide_scene"
  | "caption_only";

export type CameraMove =
  | "static"
  | "hold_then_push"
  | "push_in"
  | "pull_back"
  | "pan_left"
  | "pan_right"
  | "snap_zoom"
  | "tilt_down"
  | "parallax_drift";

export type CameraIntensity = "none" | "small" | "medium" | "large";

export type Transition =
  | "hard_cut"
  | "pop_cut"
  | "wipe_left"
  | "wipe_right"
  | "match_cut"
  | "smash_cut"
  | "dip_to_bg";

export type AssetKind =
  | "prop"
  | "icon"
  | "icon_cluster"
  | "figure"
  | "label"
  | "connector"
  | "map_shape"
  | "chart"
  | "panel"
  | "stamp"
  | "texture";

export type MotionKind =
  | "none"
  | "pop_in"
  | "pop_out"
  | "slide_in"
  | "slide_out"
  | "draw_on"
  | "count_up"
  | "stamp"
  | "shake_once"
  | "micro_bob"
  | "orbit"
  | "pulse"
  | "trace_line"
  | "wipe_reveal";

export type TextRole =
  | "headline"
  | "label"
  | "caption"
  | "stat"
  | "stamp"
  | "callout"
  | "tiny_note";

export type Delivery =
  | "neutral"
  | "curious"
  | "question"
  | "brisk"
  | "weighty"
  | "surprised"
  | "skeptical"
  | "ominous"
  | "warm_cta";

export type BackgroundTreatment = "plain" | "panel" | "grid";

export type AnchorId = string;

export type EpisodeProps = {
  schema_version: 1;
  fps: number;
  width: number;
  height: number;
  style_version: "clean_flat_light_v1";
  sections: CutawaySection[];
};

export type CutawaySection = {
  section_index: number;
  durationInFrames: number;
  audioSrc: string;
  key_phrase: string;
  narration?: string;
  captions: SentenceTiming[];
  beats: DirectedBeat[];
};

export type SentenceTiming = {
  text: string;
  start: number;
  end: number;
  delivery: Delivery;
};

export type DirectedBeat = {
  id: string;
  type: BeatType;
  start: number;
  end: number;
  startFrame: number;
  endFrame: number;
  scene_family: SceneFamily;
  layout: Layout;
  camera: CameraPlan;
  transition_in: Transition;
  transition_out: Transition;
  background: BackgroundTreatment;
  assets: VisualAsset[];
  text_overlays: TextOverlay[];
  motion: MotionCue[];
};

export type VisualAsset = {
  id: string;
  kind: AssetKind;
  name: string;
  anchor: AnchorId;
  pose?: string;
  count?: number;
  variant?: string;
  colorRole?: "ink" | "accent" | "blue" | "green" | "yellow" | "lavender" | "muted";
};

export type TextOverlay = {
  role: TextRole;
  text: string;
  anchor: AnchorId;
  tone: "ink" | "muted" | "coral_stamp" | "warning" | "quiet";
};

export type MotionCue = {
  target: string;
  kind: MotionKind;
  delay: number;
  duration: number;
};

export type CameraPlan = {
  move: CameraMove;
  target: AnchorId;
  intensity: CameraIntensity;
};

export type BEAT_TYPES = BeatType;
export type IMPORTANCE = Importance;
export type COMEDY_ROLES = ComedyRoles;
export type SCENE_FAMILY = SceneFamily;
export type LAYOUT = Layout;
export type CAMERA_MOVE = CameraMove;
export type CAMERA_INTENSITY = CameraIntensity;
export type TRANSITION = Transition;
export type ASSET_KIND = AssetKind;
export type MOTION_KIND = MotionKind;
export type TEXT_ROLE = TextRole;
