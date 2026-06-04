export type AnchorRole =
  | "character_safe"
  | "headline"
  | "stat"
  | "diagram_node"
  | "diagram_core"
  | "panel"
  | "process_step"
  | "camera_target";

export type Anchor = {
  id: string;
  x: number;
  y: number;
  z?: number;
  radius?: number;
  role: AnchorRole;
  visibleFrom?: number;
  visibleTo?: number;
};

export type ResolvedAnchor = Anchor & {
  px: number;
  py: number;
  pz: number;
};

export type AnchorMap = Record<string, ResolvedAnchor>;

export const WORLD_WIDTH = 1920;
export const WORLD_HEIGHT = 1080;

export const resolveAnchor = (
  anchor: Anchor,
  width = WORLD_WIDTH,
  height = WORLD_HEIGHT,
): ResolvedAnchor => ({
  ...anchor,
  px: anchor.x * width,
  py: anchor.y * height,
  pz: anchor.z ?? 0,
});

export const resolveAnchors = (
  anchors: Anchor[],
  width = WORLD_WIDTH,
  height = WORLD_HEIGHT,
): AnchorMap =>
  anchors.reduce<AnchorMap>((map, anchor) => {
    map[anchor.id] = resolveAnchor(anchor, width, height);
    return map;
  }, {});

export const getAnchor = (anchors: AnchorMap, id: string): ResolvedAnchor =>
  anchors[id] ?? anchors["safe.lower_left"] ?? resolveAnchor({id, x: 0.5, y: 0.5, role: "camera_target"});
