import type {RegistryAssetName} from "./registry";
import {anchorPoint} from "./families/shared";
import type {
  AssetKind,
  BackgroundPlan,
  BlueprintConnection,
  BlueprintElement,
  BlueprintElementKind,
  BlueprintText,
  CameraPlanV2,
  ColorRole,
  DirectedBeat,
  MotionKindV2,
  MotionStep,
  SceneBlueprint,
  TextOverlay,
  TextRole,
  VisualAsset,
} from "./types";

const locationAssetNames = new Set(["phone", "map_pin", "dot", "point"]);

const textCaps: Record<TextRole, number> = {
  headline: 34,
  label: 28,
  caption: 160,
  stat: 22,
  stamp: 30,
  callout: 42,
  tiny_note: 42,
};

const sanitizeId = (raw: string, fallback: string): string => {
  const cleaned = raw.replace(/[^a-zA-Z0-9_]/g, "_").replace(/^[^a-zA-Z]+/, "");
  return cleaned.length >= 2 ? cleaned.slice(0, 40) : fallback;
};

const uniqueId = (raw: string, fallback: string, used: Set<string>): string => {
  const base = sanitizeId(raw, fallback);
  let id = base;
  let suffix = 2;
  while (used.has(id)) {
    id = `${base}_${suffix}`;
    suffix += 1;
  }
  used.add(id);
  return id;
};

const kindForAsset = (kind: AssetKind, name: string): BlueprintElementKind => {
  if (name === "label") {
    return "label";
  }
  if (name === "stamp") {
    return "stamp";
  }
  if (kind === "connector") {
    return "connector";
  }
  if (kind === "map_shape") {
    return "map_shape";
  }
  if (kind === "chart") {
    return "chart";
  }
  if (kind === "panel") {
    return "panel";
  }
  if (kind === "stamp") {
    return "stamp";
  }
  if (kind === "texture") {
    return "texture";
  }
  return "prop";
};

const placementFor = (beat: DirectedBeat, asset: VisualAsset, index: number, total: number): {x: number; y: number; scale: number} => {
  if (beat.scene_family === "diagram_stage") {
    const p = anchorPoint(asset.anchor, index, total);
    return {
      x: p.x,
      y: p.y,
      scale: asset.name === "earth" ? 1.5 : asset.name === "satellite" ? 0.56 : asset.name === "phone" ? 0.5 : asset.kind === "icon_cluster" ? 0.5 : 0.78,
    };
  }
  if (beat.scene_family === "object_stage") {
    const p = anchorPoint(asset.anchor, index, total);
    return {
      x: p.x,
      y: p.y,
      scale: asset.kind === "icon_cluster" ? 0.62 : asset.name === "phone" ? 0.72 : 0.92,
    };
  }
  if (beat.scene_family === "comparison_stage") {
    const sideIndex = Math.floor(index / 2);
    return {
      x: index % 2 === 0 ? 540 : 1380,
      y: 470 + sideIndex * 150,
      scale: 0.66,
    };
  }
  if (beat.scene_family === "map_stage") {
    return {
      x: asset.name === "map" ? 960 : 640 + index * (640 / Math.max(1, total - 1)),
      y: asset.name === "map" ? 520 : 560 + (index % 2) * 70,
      scale: asset.name === "map" ? 1.4 : 0.52,
    };
  }
  if (beat.scene_family === "list_stage") {
    return {x: 610, y: 247 + index * 125, scale: 0.22};
  }
  if (beat.scene_family === "timeline_stage") {
    return {x: 430 + index * (1060 / Math.max(1, total - 1)), y: 410, scale: 0.42};
  }
  if (beat.scene_family === "stat_stage") {
    return {x: 960 + (index - (total - 1) / 2) * 360, y: 760, scale: 0.58};
  }
  if (beat.scene_family === "paperwork_stage") {
    return {x: 960 + (index - (total - 1) / 2) * 280, y: 690, scale: 0.58};
  }
  if (beat.scene_family === "miniature_world") {
    return {x: 960 + (index - (total - 1) / 2) * 340, y: 470, scale: 0.78};
  }
  if (beat.scene_family === "title_stage") {
    return {x: 960 + (index - (total - 1) / 2) * 310, y: 670, scale: 0.72};
  }
  const p = anchorPoint(asset.anchor, index, total);
  return {x: p.x, y: p.y, scale: 1.05};
};

const motionForAsset = (beat: DirectedBeat, asset: VisualAsset): MotionStep[] | undefined => {
  const cue = (beat.motion ?? []).find((item) => item.target === asset.id || item.target === asset.name);
  if (!cue || cue.kind === "none" || asset.is_new === false) {
    return undefined;
  }
  return [{kind: cue.kind as MotionKindV2, start: cue.delay, duration: cue.duration}];
};

const textForAsset = (asset: VisualAsset): BlueprintText | undefined => {
  const text = asset.variant?.trim();
  if (!text || (asset.name !== "label" && asset.name !== "stamp" && asset.name !== "counter" && asset.name !== "number")) {
    return undefined;
  }
  const role: TextRole = asset.name === "stamp" ? "stamp" : asset.name === "counter" || asset.name === "number" ? "stat" : "label";
  return {
    role,
    text,
    tone: asset.name === "stamp" ? "coral_stamp" : "ink",
    maxChars: textCaps[role],
    fit: "auto",
  };
};

const overlayElement = (overlay: TextOverlay, index: number, total: number, used: Set<string>): BlueprintElement => {
  const p = anchorPoint(overlay.anchor, index, total);
  const isStamp = overlay.role === "stamp" || overlay.tone === "coral_stamp";
  const id = uniqueId(`${overlay.role}_${index + 1}`, `text_${index + 1}`, used);
  return {
    id,
    kind: isStamp ? "stamp" : "label",
    asset: isStamp ? "stamp" : "label",
    position: {mode: "point", x: p.x, y: p.y},
    size: {mode: "scale", scale: isStamp ? 1 : overlay.role === "headline" ? 1.35 : 1},
    text: {
      role: overlay.role,
      text: overlay.text,
      tone: overlay.tone,
      maxChars: textCaps[overlay.role],
      fit: overlay.role === "caption" ? "multi_line" : "auto",
    },
    z: 40 + index,
    motion: [{kind: isStamp ? "stamp" : "pop_in", start: index * 0.08, duration: 0.25}],
  };
};

const backgroundPlan = (beat: DirectedBeat): BackgroundPlan => {
  const background = beat.background;
  if (typeof background === "string") {
    return {treatment: background};
  }
  return background;
};

const cameraPlan = (beat: DirectedBeat): CameraPlanV2 => {
  const camera = beat.camera;
  return {
    move: camera.move,
    target: camera.target,
    intensity: camera.intensity,
    start: camera.start,
    duration: camera.duration,
  };
};

const diagramConnections = (beat: DirectedBeat, assetElements: Array<{asset: VisualAsset; element: BlueprintElement}>): BlueprintConnection[] => {
  if (beat.scene_family !== "diagram_stage") {
    return [];
  }
  const targetEntry =
    assetElements.find((entry) => locationAssetNames.has(entry.asset.name)) ??
    assetElements.find((entry) => entry.asset.name === "earth");
  if (!targetEntry) {
    return [];
  }
  return assetElements
    .filter((entry) => entry.asset.name === "satellite")
    .map((entry, index) => ({
      id: `satellite_line_${index + 1}`,
      kind: "line",
      from: {element: entry.element.id, attach: "center"},
      to: {element: targetEntry.element.id, attach: "center"},
      colorRole: "accent" as ColorRole,
      z: 5,
      motion: entry.asset.is_new === false ? undefined : [{kind: "trace_line" as MotionKindV2, start: 0, duration: 22 / 30}],
    }));
};

export const legacyBeatToBlueprint = (beat: DirectedBeat): SceneBlueprint => {
  const used = new Set<string>();
  const assets = beat.assets ?? [];
  const assetElements = assets.map((asset, index) => {
    const place = placementFor(beat, asset, index, assets.length);
    const id = uniqueId(asset.id || asset.name, `asset_${index + 1}`, used);
    const element: BlueprintElement = {
      id,
      kind: kindForAsset(asset.kind, asset.name),
      asset: asset.name as RegistryAssetName,
      position: {mode: "point", x: place.x, y: place.y},
      size: {mode: "scale", scale: place.scale},
      colorRole: asset.colorRole,
      text: textForAsset(asset),
      z: 10 + index,
      motion: motionForAsset(beat, asset),
    };
    return {asset, element};
  });
  const overlayElements = (beat.text_overlays ?? []).map((overlay, index, overlays) => overlayElement(overlay, index, overlays.length, used));
  return {
    version: 1,
    preset: beat.scene_family,
    intent: beat.id,
    elements: [...assetElements.map((entry) => entry.element), ...overlayElements],
    connections: diagramConnections(beat, assetElements),
    camera: cameraPlan(beat),
    background: backgroundPlan(beat),
  };
};
