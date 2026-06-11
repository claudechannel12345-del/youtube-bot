"""Deterministic blueprint preset builders for cutaway scene families.

These builders mirror the legacy Remotion family placement functions in
``remotion/src/cutaway/families`` and emit explicit Phase 3 SceneBlueprint
payloads. The legacy v1 beat fields remain the source material; these functions
only make the layout concrete for the blueprint renderer.
"""

from __future__ import annotations

import copy
import re
import json
import os
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from cutaway_vocab import MOTION_KIND_V2, REGISTRY_ASSETS
from environments import default_environment_slots, get_environment, get_vertical_environment, has_environment

TEXT_CAPS = {
    "headline": 34,
    "label": 28,
    "caption": 160,
    "stat": 22,
    "stamp": 30,
    "callout": 42,
    "tiny_note": 42,
}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENERATED_ASSETS_PATH = os.path.join(ROOT, "data", "generated_assets.json")
_GENERATED_ASSETS_CACHE: Optional[Dict[str, Any]] = None

FRAME_W = 1920.0
FRAME_H = 1080.0
SAFE_TOP = 64.0
SAFE_BOTTOM = 48.0
SAFE_SIDE = 24.0
# Landscape headline band: titles must sit fully within [HEADLINE_TOP, HEADLINE_BOTTOM] so they clear
# the rooms' back-wall top edges (which start at y~110). See _safe_text_zone.
HEADLINE_TOP = 26.0
HEADLINE_BOTTOM = 106.0

ASSET_BASE_SIZE = {
    "generic_object": (240.0, 180.0),
    "person": (172.0, 278.0),
    "person_female": (172.0, 278.0),
    "person_arms_up": (224.0, 310.0),
    "person_pointing": (254.0, 278.0),
    "person_sitting": (220.0, 278.0),
    "person_walking": (184.0, 290.0),
    "person_left": (172.0, 278.0),
    "person_right": (172.0, 278.0),
    "doctor": (172.0, 278.0),
    "scientist": (172.0, 316.0),
    "judge": (172.0, 278.0),
    "athlete": (172.0, 278.0),
    "suit": (172.0, 278.0),
    "plant": (240.0, 346.0),
    "tree": (276.0, 332.0),
    "house": (352.0, 338.0),
    "book": (276.0, 284.0),
    "box": (292.0, 304.0),
    "ball": (264.0, 264.0),
    "microphone": (192.0, 328.0),
    "laptop": (432.0, 282.0),
    "flag": (232.0, 322.0),
    "mountain_shape": (400.0, 290.0),
}

ANCHOR_POINTS = {
    "center": (960, 540),
    "center_subject": (960, 560),
    "left": (560, 560),
    "right": (1360, 560),
    "left_center": (560, 560),
    "right_center": (1360, 560),
    "top": (960, 220),
    "bottom": (960, 850),
    "map_focus": (960, 540),
    "lower_center": (960, 858),
    "upper_center": (960, 170),
    "upper_left": (370, 190),
    "upper_right": (1550, 190),
    "lower_left": (390, 850),
    "lower_right": (1530, 850),
    "headline": (960, 210),
    "stat": (960, 470),
    "diagram_core": (960, 540),
}

ASSET_ALIASES = {
    "atomic clock": "atomic_clock",
    "atomic-clock": "atomic_clock",
    "blue dot": "dot",
    "blue_dot": "dot",
    "gps satellite": "satellite",
    "gps_satellite": "satellite",
    "map pin": "map_pin",
    "mappin": "map_pin",
    "pin": "map_pin",
    "skyscraper": "building",
    "time signal": "signal",
}

LOCATION_ASSETS = frozenset(["phone", "map_pin", "dot", "point"])
SPACE_ASSETS = frozenset(["satellite", "earth", "signal", "signal_beam"])
ACTOR_POSE_ASSETS = {
    "arms_up": "person_arms_up",
    "celebrate": "person_arms_up",
    "point": "person_pointing",
    "pointing": "person_pointing",
    "sitting": "person_sitting",
    "seated": "person_sitting",
    "walking": "person_walking",
    "walk": "person_walking",
    "left": "person_left",
    "facing_left": "person_left",
    "right": "person_right",
    "facing_right": "person_right",
}

ACTOR_MOTION_ALIASES = {
    "idle": "micro_bob",
    "idle_bob": "micro_bob",
    "bob": "micro_bob",
    "point": "pulse",
    "pointing": "pulse",
    "emphasize": "pulse",
    "walk": "micro_bob",
    "walking": "micro_bob",
}


def anchor_point(anchor: str, index: int = 0, total: int = 1) -> Dict[str, float]:
    spread = index - (total - 1) / 2 if total > 1 else 0
    if anchor == "upper_band":
        return {"x": 960 + spread * 360, "y": 230 + abs(spread) * 20}
    if anchor == "lower_band":
        return {"x": 960 + spread * 360, "y": 800}
    x, y = ANCHOR_POINTS.get(anchor, (960 + spread * 330, 540))
    return {"x": x, "y": y}


def build_blueprint(beat: Dict[str, Any], sentences_timing: List[Dict[str, Any]], section: Dict[str, Any]) -> Dict[str, Any]:
    if section.get("environment") or beat.get("environment"):
        return build_scene_stage(beat, sentences_timing, section)
    family = beat.get("scene_family") or "object_stage"
    builder = PRESET_BUILDERS.get(family, build_object_stage)
    return builder(beat, sentences_timing, section)


def build_scene_stage(beat: Dict[str, Any], sentences_timing: List[Dict[str, Any]], section: Dict[str, Any]) -> Dict[str, Any]:
    env_id = str(beat.get("environment") or section.get("environment") or "").strip()
    if not has_environment(env_id):
        return build_object_stage(beat, sentences_timing, section)
    env_variant = str(beat.get("environment_variant") or section.get("environment_variant") or "").strip()
    vertical = bool(beat.get("vertical") or section.get("vertical") or section.get("orientation") == "vertical")
    env = get_vertical_environment(env_id, variant=env_variant) if vertical else get_environment(env_id, variant=env_variant)
    env = _safe_scene_environment(env, vertical=vertical)
    elements = [
        _shape_layer("%s_backdrop" % env_id, env["backdrop"], 5),
        _shape_layer("%s_midground" % env_id, env["midground"], 100),
    ]
    elements.extend(_environment_set_prop_elements(env))
    elements.extend(_scene_actor_elements(beat, env))
    elements.append(_shape_layer("%s_foreground" % env_id, env["foreground"], 500))

    overlay = _scene_overlay(beat)
    if overlay:
        zone = _safe_text_zone(env.get("text_zone") or {"x": 410, "y": 116, "w": 1100, "h": 120}, vertical=vertical)
        text_x = float(zone.get("x", 410)) + float(zone.get("w", 1100)) / 2
        text_y = float(zone.get("y", 116)) + float(zone.get("h", 120)) / 2
        box = (int(zone.get("w", 1100)), int(zone.get("h", 120)))
        elements.append(_text_element(overlay, "scene_text", text_x, text_y, "none", 1.0, z=900, box=box))

    return {
        "version": 1,
        "preset": "scene_stage",
        "intent": str(beat.get("id") or beat.get("type") or env_id),
        "environment": env_id,
        "environment_variant": env.get("variant", env_variant) if env_variant else env.get("variant"),
        "background": {"treatment": "plain"},
        "camera": _camera_plan(beat),
        "elements": elements,
        "connections": [],
    }


def _safe_scene_environment(env: Dict[str, Any], vertical: bool = False) -> Dict[str, Any]:
    fixed = copy.deepcopy(env)
    fixed["text_zone"] = _safe_text_zone(fixed.get("text_zone") or {}, vertical=vertical)
    frame_w, frame_h = _scene_frame(vertical)
    for slot in (fixed.get("slots") or {}).values():
        if not isinstance(slot, dict):
            continue
        slot["x"] = _clamp(float(slot.get("x", frame_w / 2)), SAFE_SIDE, frame_w - SAFE_SIDE)
        slot["y"] = _clamp(float(slot.get("y", frame_h / 2)), SAFE_TOP, frame_h - SAFE_BOTTOM)
    for prop in fixed.get("set_props") or []:
        if not isinstance(prop, dict):
            continue
        prop["x"] = _clamp(float(prop.get("x", frame_w / 2)), SAFE_SIDE, frame_w - SAFE_SIDE)
        prop["y"] = _clamp(float(prop.get("y", frame_h / 2)), SAFE_TOP, frame_h - SAFE_BOTTOM)
    return fixed


def _safe_text_zone(zone: Dict[str, Any], vertical: bool = False) -> Dict[str, float]:
    frame_w, frame_h = _scene_frame(vertical)
    w = float(zone.get("w", 1100))
    h = float(zone.get("h", 120))
    w = _clamp(w, 120.0, max(120.0, frame_w - SAFE_SIDE * 2))
    x = _clamp(float(zone.get("x", (frame_w - w) / 2)), SAFE_SIDE, max(SAFE_SIDE, frame_w - SAFE_SIDE - w))
    if not vertical:
        # Landscape headlines must live ENTIRELY in the cream band ABOVE the room (every room's back-wall
        # top edge sits at y~110-130). The old clamp pushed authored y=18-20 down to SAFE_TOP=64 with a
        # tall box, so the box bottom (152-189) collided with the wall and bisected the title. Pin the
        # title to a tight top band (y in [HEADLINE_TOP, HEADLINE_BOTTOM]) so it always clears the walls.
        h = _clamp(h, 56.0, HEADLINE_BOTTOM - HEADLINE_TOP)
        y = _clamp(float(zone.get("y", HEADLINE_TOP)), HEADLINE_TOP, HEADLINE_BOTTOM - h)
        return {"x": x, "y": y, "w": w, "h": h}
    h = _clamp(h, 64.0, max(64.0, frame_h - SAFE_TOP - SAFE_BOTTOM))
    y = _clamp(float(zone.get("y", SAFE_TOP)), SAFE_TOP, max(SAFE_TOP, frame_h - SAFE_BOTTOM - h))
    return {"x": x, "y": y, "w": w, "h": h}


def _scene_frame(vertical: bool = False) -> Tuple[float, float]:
    return (1080.0, 1920.0) if vertical else (FRAME_W, FRAME_H)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def _fit_point_in_scene(x: float, y: float, scale: float, asset: str, vertical: bool = False) -> Tuple[float, float, float]:
    frame_w, frame_h = _scene_frame(vertical)
    base_w, base_h = _scene_asset_base_size(asset)
    safe_w = max(1.0, frame_w - SAFE_SIDE * 2)
    safe_h = max(1.0, frame_h - SAFE_TOP - SAFE_BOTTOM)
    scale = max(0.05, float(scale))
    scale = min(scale, safe_w / max(1.0, base_w), safe_h / max(1.0, base_h))
    half_w = base_w * scale / 2
    half_h = base_h * scale / 2
    return (
        _clamp(float(x), SAFE_SIDE + half_w, frame_w - SAFE_SIDE - half_w),
        _clamp(float(y), SAFE_TOP + half_h, frame_h - SAFE_BOTTOM - half_h),
        scale,
    )


def _scene_asset_base_size(asset: str) -> Tuple[float, float]:
    if _generated_asset(asset):
        return (320.0, 320.0)
    return ASSET_BASE_SIZE.get(_registry_asset(asset), (320.0, 260.0))


def build_comparison_stage(beat: Dict[str, Any], sentences_timing: List[Dict[str, Any]], section: Dict[str, Any]) -> Dict[str, Any]:
    assets = _asset_elements(beat, _comparison_place, max_assets=4)
    # Color the two sides distinctly so a comparison reads as A-vs-B (e.g. red vs blue). The script
    # can specify exact roles via beat["compare_colors"]; otherwise alternate accent/blue/green/yellow.
    side_colors = beat.get("compare_colors") or ["accent", "blue", "green", "yellow"]
    for ci, el in enumerate(assets):
        if not el.get("colorRole"):
            el["colorRole"] = side_colors[ci % len(side_colors)]
    label = _first_overlay(beat, roles=("label", "caption", "headline", "stamp"))
    if label:
        assets.append(_text_element(label, "comparison_label", 960, 868, "label", 1.0, z=50, box=(1100, 90)))
    return _blueprint(beat, "comparison_stage", "comparison_panels", assets[:6], [])


def build_diagram_stage(beat: Dict[str, Any], sentences_timing: List[Dict[str, Any]], section: Dict[str, Any]) -> Dict[str, Any]:
    asset_entries = _asset_entries(beat, _diagram_place, max_assets=6)
    if len(asset_entries) == 1 and _asset_name(asset_entries[0]["asset"]) == "satellite":
        target = _element("diagram_target", "prop", "point", 960, 720, 0.5, color_role="blue", z=30)
        asset_entries.append({"asset": {"name": "point"}, "element": target})
    elements = [entry["element"] for entry in asset_entries]
    target = _diagram_target(asset_entries)
    connections = []
    if target:
        for index, entry in enumerate(asset_entries):
            if entry["asset"].get("name") != "satellite":
                continue
            motion = None
            if entry["asset"].get("is_new") is not False:
                motion = [{"kind": "trace_line", "start": 0, "duration": round(22 / 30, 3)}]
            connections.append(
                {
                    "id": "satellite_line_%d" % (index + 1),
                    "kind": "line",
                    "from": {"element": entry["element"]["id"], "attach": "center"},
                    "to": {"element": target["element"]["id"], "attach": "center"},
                    "colorRole": "accent",
                    "z": 5,
                    "motion": motion,
                }
            )
    return _blueprint(beat, "diagram_stage", "grid", elements[:7], connections)


def build_stat_stage(beat: Dict[str, Any], sentences_timing: List[Dict[str, Any]], section: Dict[str, Any]) -> Dict[str, Any]:
    text = _overlay_text(beat, "stat") or _first_overlay_text(beat) or _fallback_text(beat, section, "100")
    elements = [
        _text_element({"role": "stat", "text": text, "tone": "coral_stamp"}, "stat_number", 960, 449, "none", 2.0, z=20, box=(720, 240)),
    ]
    # The big stat text IS the number; drop number/counter supporting assets so they don't render a
    # redundant placeholder ("42") box on top of the real stat.
    stat_beat = dict(beat)
    stat_beat["assets"] = [a for a in (beat.get("assets") or []) if a.get("name") not in ("number", "counter", "generic_object")]
    elements.extend(_asset_elements(stat_beat, _stat_place, max_assets=3, start_z=30))
    return _blueprint(beat, "stat_stage", "panel", elements[:4], [])


def build_caption_punch(beat: Dict[str, Any], sentences_timing: List[Dict[str, Any]], section: Dict[str, Any]) -> Dict[str, Any]:
    text = _first_overlay_text(beat) or _fallback_text(beat, section, "YES")
    elements = [
        _text_element({"role": "headline", "text": text, "tone": "ink"}, "headline", 980, 455, "none", 1.0, z=20, box=(1080, 210)),
        _element("coral_underline", "prop", "none", 960, 590, 1.0, color_role="accent", z=10, box=(540, 16), prop_shape="rule"),
    ]
    return _blueprint(beat, "caption_punch", "plain", elements, [])


def build_object_stage(beat: Dict[str, Any], sentences_timing: List[Dict[str, Any]], section: Dict[str, Any]) -> Dict[str, Any]:
    elements = []
    # (Removed the "ground_shadow" ring element: the ring asset rendered as a big stray circle behind
    # every object, which read as nonsense. Flat cream background is the cleaner CGP-Grey look.)
    obj_assets = _asset_elements(beat, _object_place, max_assets=4, start_z=20)
    # Route per-side colors (e.g. red vs blue) onto object scenes too, like comparison does.
    side_colors = beat.get("compare_colors")
    if side_colors:
        for ci, el in enumerate(obj_assets):
            if not el.get("colorRole"):
                el["colorRole"] = side_colors[ci % len(side_colors)]
    elements.extend(obj_assets)
    elements.extend(_overlay_elements(beat, start_z=50, max_items=max(0, 5 - len(elements))))
    return _blueprint(beat, "object_stage", "plain", elements[:5], [])


def build_list_stage(beat: Dict[str, Any], sentences_timing: List[Dict[str, Any]], section: Dict[str, Any]) -> Dict[str, Any]:
    elements = []
    assets = (beat.get("assets") or [])[:3]
    for index, asset in enumerate(assets):
        y = 247 + index * 125
        row_text = _list_row_text(asset)
        elements.append(_element("bullet_%d" % (index + 1), "prop", "none", 486, y, 0.36, color_role="accent", z=30 + index, prop_shape="disc"))
        elements.append(_text_element({"role": "label", "text": row_text, "tone": "ink"}, "row_%d" % (index + 1), 1080, y, "none", 1.15, z=20 + index, box=(820, 88)))
    if not elements:
        text = _fallback_text(beat, section, "ITEM")
        elements.append(_element("bullet_1", "prop", "none", 486, 247, 0.36, color_role="accent", z=30, prop_shape="disc"))
        elements.append(_text_element({"role": "label", "text": text, "tone": "ink"}, "row_1", 1080, 247, "none", 1.15, z=20, box=(820, 88)))
        elements.append(_element("bullet_2", "prop", "none", 486, 372, 0.36, color_role="accent", z=31, prop_shape="disc"))
        elements.append(_text_element({"role": "label", "text": "NEXT", "tone": "ink"}, "row_2", 1080, 372, "none", 1.15, z=21, box=(820, 88)))
    return _blueprint(beat, "list_stage", "plain", elements[:6], [])


def build_quote_stage(beat: Dict[str, Any], sentences_timing: List[Dict[str, Any]], section: Dict[str, Any]) -> Dict[str, Any]:
    quote = _overlay_text(beat, "caption") or _fallback_text(beat, section, "Quote")
    attribution = _overlay_text(beat, "tiny_note")
    elements = [
        _text_element({"role": "caption", "text": quote, "tone": "ink"}, "quote_body", 960, 420, "none", 1.0, z=20, box=(1200, 420)),
    ]
    if attribution:
        elements.append(_text_element({"role": "tiny_note", "text": attribution, "tone": "muted"}, "quote_attribution", 960, 700, "none", 1.0, z=30, box=(900, 86)))
    return _blueprint(beat, "quote_stage", "panel", elements[:3], [])


def build_miniature_world(beat: Dict[str, Any], sentences_timing: List[Dict[str, Any]], section: Dict[str, Any]) -> Dict[str, Any]:
    elements = _asset_elements(beat, _miniature_place, max_assets=5, start_z=20)
    stamp = _first_overlay(beat, roles=("stamp", "label", "tiny_note"))
    if stamp:
        elements.append(_text_element(stamp, "gag_stamp", 960, 858, "stamp", 1.0, z=50))
    while len(elements) < 2:
        elements.append(_element("gag_extra_%d" % len(elements), "prop", "generic_object", 790 + len(elements) * 340, 470, 0.78, z=20 + len(elements)))
    return _blueprint(beat, "miniature_world", "plain", elements[:6], [])


def build_map_stage(beat: Dict[str, Any], sentences_timing: List[Dict[str, Any]], section: Dict[str, Any]) -> Dict[str, Any]:
    assets = beat.get("assets") or []
    if not any(_asset_name(asset) in ("map", "map_pin", "dot", "point") for asset in assets):
        synthetic = {"id": "%s_map" % _safe_id(beat.get("id"), "beat"), "kind": "prop", "name": "map", "is_new": True}
        assets = [synthetic] + assets
        beat = dict(beat)
        beat["assets"] = assets
    elements = _asset_elements(beat, _map_place, max_assets=5, start_z=20)
    elements.extend(_overlay_elements(beat, start_z=50, max_items=max(0, 6 - len(elements))))
    return _blueprint(beat, "map_stage", "map", elements[:6], [])


def build_timeline_stage(beat: Dict[str, Any], sentences_timing: List[Dict[str, Any]], section: Dict[str, Any]) -> Dict[str, Any]:
    elements = [_element("timeline_axis", "connector", "ruler", 960, 540, 2.0, color_role="muted", z=5)]
    assets = (beat.get("assets") or [])[:5]
    for index, asset in enumerate(assets):
        x = 430 + index * (1060 / max(1, len(assets) - 1))
        elements.append(_element("tick_%d" % (index + 1), "prop", "dot", x, 540, 0.36, color_role="accent", z=10 + index))
        elements.append(_asset_element(asset, index, len(assets), _timeline_place, z=20 + index, used=_used_ids(elements)))
    if len(elements) < 2:
        elements.append(_element("timeline_item", "prop", "generic_object", 960, 410, 0.42, z=20))
    return _blueprint(beat, "timeline_stage", "plain", elements[:6], [])


def build_title_stage(beat: Dict[str, Any], sentences_timing: List[Dict[str, Any]], section: Dict[str, Any]) -> Dict[str, Any]:
    text = _first_overlay_text(beat) or _fallback_text(beat, section, "CUTAWAY")
    elements = [
        _text_element({"role": "headline", "text": text, "tone": "ink"}, "title_headline", 960, 425, "none", 1.0, z=30, box=(1060, 190)),
        _element("title_underline", "prop", "none", 960, 520, 1.0, color_role="accent", z=20, box=(520, 16), prop_shape="rule"),
    ]
    elements.extend(_asset_elements(beat, _title_place, max_assets=3, start_z=40))
    return _blueprint(beat, "title_stage", "plain", elements[:5], [])


def build_paperwork_stage(beat: Dict[str, Any], sentences_timing: List[Dict[str, Any]], section: Dict[str, Any]) -> Dict[str, Any]:
    elements = [_element("paper_slash", "prop", "none", 960, 670, 1.0, color_role="accent", z=15, rotation=-9, box=(480, 14), prop_shape="rule")]
    elements.extend(_asset_elements(beat, _paperwork_place, max_assets=4, start_z=30))
    return _blueprint(beat, "paperwork_stage", "paper_stack", elements[:5], [])


PRESET_BUILDERS: Dict[str, Callable[[Dict[str, Any], List[Dict[str, Any]], Dict[str, Any]], Dict[str, Any]]] = {
    "comparison_stage": build_comparison_stage,
    "diagram_stage": build_diagram_stage,
    "stat_stage": build_stat_stage,
    "caption_punch": build_caption_punch,
    "object_stage": build_object_stage,
    "list_stage": build_list_stage,
    "quote_stage": build_quote_stage,
    "miniature_world": build_miniature_world,
    "map_stage": build_map_stage,
    "timeline_stage": build_timeline_stage,
    "title_stage": build_title_stage,
    "paperwork_stage": build_paperwork_stage,
}


def _blueprint(beat: Dict[str, Any], preset: str, background: str, elements: List[Dict[str, Any]], connections: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "version": 1,
        "preset": preset,
        "intent": str(beat.get("id") or beat.get("type") or preset),
        "elements": elements,
        "connections": connections,
        "camera": _camera_plan(beat),
        "background": {"treatment": background},
    }


def _camera_plan(beat: Dict[str, Any]) -> Dict[str, Any]:
    camera = beat.get("camera") if isinstance(beat.get("camera"), dict) else {}
    return {
        "move": camera.get("move", "static"),
        "target": camera.get("target", "center"),
        "intensity": camera.get("intensity", "none"),
    }


def _asset_entries(beat: Dict[str, Any], placer: Callable[[Dict[str, Any], int, int], Dict[str, float]], max_assets: int, start_z: int = 20) -> List[Dict[str, Any]]:
    assets = (beat.get("assets") or [])[:max_assets]
    used = set()
    entries = []
    for index, asset in enumerate(assets):
        element = _asset_element(asset, index, len(assets), placer, z=start_z + index, used=used, motions=beat.get("motion") or [])
        entries.append({"asset": asset, "element": element})
    return entries


def _asset_elements(beat: Dict[str, Any], placer: Callable[[Dict[str, Any], int, int], Dict[str, float]], max_assets: int, start_z: int = 20) -> List[Dict[str, Any]]:
    return [entry["element"] for entry in _asset_entries(beat, placer, max_assets, start_z=start_z)]


def _shape_layer(element_id: str, shapes: List[Dict[str, Any]], z: int) -> Dict[str, Any]:
    return {
        "id": _safe_id(element_id, "env_layer"),
        "kind": "texture",
        "asset": "none",
        "position": {"mode": "point", "x": 960, "y": 540},
        "size": {"mode": "scale", "scale": 1.0},
        "z": z,
        "shapes": shapes,
    }


def _scene_actor_elements(beat: Dict[str, Any], env: Dict[str, Any]) -> List[Dict[str, Any]]:
    actors = beat.get("actors")
    if not isinstance(actors, list) or not actors:
        actors = _actors_from_assets(beat, env)
    slots = env.get("slots") or {}
    elements = []
    used = set()
    for index, actor in enumerate(actors[:4]):
        if not isinstance(actor, dict):
            continue
        slot_name = str(actor.get("slot") or "").strip()
        if slot_name not in slots:
            slot_name = _fallback_slot(env, index)
        slot = slots[slot_name]
        pose = str(actor.get("pose") or "").strip().lower().replace(" ", "_")
        asset_name = _actor_asset_name(actor, pose)
        scale = float(actor.get("scale") if actor.get("scale") is not None else slot.get("scale", 1.0))
        x, y, scale = _fit_point_in_scene(slot["x"], slot["y"], scale, asset_name, vertical=env.get("orientation") == "vertical")
        element = _element(
            _unique_id(actor.get("id") or "%s_%d" % (asset_name, index + 1), "actor_%d" % (index + 1), used),
            "prop",
            asset_name,
            x,
            y,
            scale,
            color_role=actor.get("colorRole"),
            z=int(actor.get("z") if actor.get("z") is not None else slot.get("z", 250)),
        )
        element["slot"] = slot_name
        if pose:
            element["pose"] = pose
        motion_steps = _actor_motion_steps(actor, pose)
        if motion_steps:
            element["motion"] = motion_steps
        _apply_generated(element, asset_name)
        elements.append(element)
    return elements


def _environment_set_prop_elements(env: Dict[str, Any]) -> List[Dict[str, Any]]:
    props = env.get("set_props")
    if not isinstance(props, list):
        return []
    elements = []
    used = set()
    for index, prop in enumerate(props):
        if not isinstance(prop, dict):
            continue
        requested_name = _prop_asset_name(prop)
        if not requested_name:
            continue
        x = float(prop.get("x", 960))
        y = float(prop.get("y", 720))
        scale = float(prop.get("scale", 1.0))
        x, y, scale = _fit_point_in_scene(x, y, scale, requested_name, vertical=env.get("orientation") == "vertical")
        z = int(prop.get("z", 120))
        element = _element(
            _unique_id(prop.get("id") or "set_%s" % requested_name, "set_prop_%d" % (index + 1), used),
            "prop",
            _registry_asset(requested_name),
            x,
            y,
            scale,
            color_role=prop.get("colorRole"),
            z=z,
        )
        element["setProp"] = True
        if _apply_generated(element, requested_name):
            element["setProp"] = True
        elements.append(element)
    return elements


def _actors_from_assets(beat: Dict[str, Any], env: Dict[str, Any]) -> List[Dict[str, Any]]:
    env_id = env.get("id")
    slots = default_environment_slots(env_id) or list((env.get("slots") or {}).keys())
    actors = []
    for index, asset in enumerate((beat.get("assets") or [])[:4]):
        actors.append(
            {
                "id": asset.get("id"),
                "asset": asset.get("name") or "person",
                "slot": slots[index % len(slots)] if slots else "",
                "colorRole": asset.get("colorRole"),
                "pose": asset.get("pose"),
                "motion": "micro_bob" if asset.get("is_new") is not False else "none",
            }
        )
    if actors:
        return actors
    return [{"asset": "person", "slot": slots[0] if slots else "", "colorRole": "accent", "pose": "idle", "motion": "micro_bob"}]


def _actor_asset_name(actor: Dict[str, Any], pose: str) -> str:
    requested = str(actor.get("asset") or actor.get("name") or "person").strip().lower().replace(" ", "_")
    if requested in ("", "person", "person_female", "generic_object"):
        posed = ACTOR_POSE_ASSETS.get(pose)
        if posed:
            return posed
    if _generated_asset(requested):
        return requested
    return _registry_asset(requested)


def _actor_motion_steps(actor: Dict[str, Any], pose: str) -> Optional[List[Dict[str, Any]]]:
    motion = actor.get("motion")
    if isinstance(motion, list):
        return motion
    motion_name = str(motion or "").strip().lower().replace(" ", "_")
    if motion_name in ("", "none"):
        if pose in ("point", "pointing"):
            motion_name = "point"
        elif pose in ("walking", "walk"):
            motion_name = "walk"
        elif pose in ("lean", "leaning"):
            motion_name = "lean"
        else:
            return None
    if motion_name in ("lean", "leaning"):
        return [{"kind": "hold", "start": 0.0, "duration": 0.45, "from": {"rotation": -2.5}, "to": {"rotation": 0}}]
    kind = ACTOR_MOTION_ALIASES.get(motion_name, motion_name)
    if kind not in MOTION_KIND_V2:
        kind = "micro_bob"
    return [{"kind": kind, "start": 0.0, "duration": 6.0}]


def _fallback_slot(env: Dict[str, Any], index: int) -> str:
    slots = default_environment_slots(env.get("id")) or list((env.get("slots") or {}).keys())
    if not slots:
        return ""
    return slots[index % len(slots)]


def _scene_overlay(beat: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    overlays = [o for o in (beat.get("text_overlays") or []) if isinstance(o, dict) and str(o.get("text") or "").strip()]
    if not overlays:
        return None
    for role in ("stat", "caption", "stamp", "headline", "label"):
        for overlay in overlays:
            if overlay.get("role") == role:
                return overlay
    return overlays[0]


def _asset_element(asset: Dict[str, Any], index: int, total: int, placer: Callable[[Dict[str, Any], int, int], Dict[str, float]], z: int, used: set, motions: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    place = placer(asset, index, total)
    requested_name = _canonical_asset_name(asset)
    if _generated_asset(requested_name):
        element = _element(
            _unique_id(asset.get("id") or requested_name or "asset", "asset_%d" % (index + 1), used),
            "texture",
            "none",
            place["x"],
            place["y"],
            place.get("scale", 1.0),
            color_role=asset.get("colorRole"),
            z=z,
        )
        _apply_generated(element, requested_name)
        motion = _motion_for_asset(asset, motions or [])
        if motion:
            element["motion"] = motion
        return element
    name = _registry_asset(requested_name)
    element = _element(
        _unique_id(asset.get("id") or name or "asset", "asset_%d" % (index + 1), used),
        _kind_for_asset(asset.get("kind"), name),
        name,
        place["x"],
        place["y"],
        place.get("scale", 1.0),
        color_role=asset.get("colorRole"),
        z=z,
    )
    text = _text_for_asset(asset, name)
    if text:
        element["text"] = text
    motion = _motion_for_asset(asset, motions or [])
    if motion:
        element["motion"] = motion
    return element


def _apply_generated(element: Dict[str, Any], requested_name: str) -> bool:
    generated = _generated_asset(requested_name)
    if not generated:
        return False
    element["asset"] = "none"
    element["kind"] = "texture"
    element["generatedAssetName"] = requested_name
    element["shapeSpace"] = "local"
    element["shapes"] = copy.deepcopy(generated.get("shapes") or [])
    return True


def _element(element_id: str, kind: str, asset: str, x: float, y: float, scale: float, color_role: Optional[str] = None, z: int = 10, opacity: Optional[float] = None, rotation: Optional[float] = None, box: Optional[Tuple[int, int]] = None, prop_shape: Optional[str] = None) -> Dict[str, Any]:
    item = {
        "id": _safe_id(element_id, "element"),
        "kind": kind,
        "asset": _registry_asset(asset),
        "position": {"mode": "point", "x": round(float(x), 3), "y": round(float(y), 3)},
        "size": {"mode": "box", "w": box[0], "h": box[1]} if box else {"mode": "scale", "scale": round(float(scale), 3)},
        "z": z,
    }
    if color_role:
        item["colorRole"] = color_role
    if opacity is not None:
        item["opacity"] = opacity
    if rotation is not None:
        item["rotation"] = rotation
    if prop_shape:
        item["propShape"] = prop_shape
    return item


def _text_element(overlay: Dict[str, Any], element_id: str, x: float, y: float, asset: str, scale: float, z: int, box: Optional[Tuple[int, int]] = None) -> Dict[str, Any]:
    role = overlay.get("role", "label")
    text = str(overlay.get("text") or "").strip()
    tone = overlay.get("tone", "ink")
    kind = "stamp" if role == "stamp" or asset == "stamp" else role if role in ("headline", "label", "caption", "stat", "quote", "title", "tiny_note") else "label"
    item = _element(element_id, kind, asset, x, y, scale, z=z, box=box)
    item["text"] = {"role": role, "text": text, "tone": tone, "maxChars": TEXT_CAPS.get(role, 42), "fit": "multi_line" if role == "caption" else "auto"}
    item["motion"] = [{"kind": "stamp" if role == "stamp" else "pop_in", "start": 0, "duration": 0.25}]
    return item


def _overlay_elements(beat: Dict[str, Any], start_z: int, max_items: int) -> List[Dict[str, Any]]:
    overlays = (beat.get("text_overlays") or [])[:max_items]
    elements = []
    for index, overlay in enumerate(overlays):
        p = anchor_point(overlay.get("anchor", "lower_center"), index, len(overlays))
        asset = "stamp" if overlay.get("role") == "stamp" or overlay.get("tone") == "coral_stamp" else "label"
        scale = 1.35 if overlay.get("role") == "headline" else 1.0
        elements.append(_text_element(overlay, "%s_%d" % (overlay.get("role", "text"), index + 1), p["x"], p["y"], asset, scale, z=start_z + index))
    return elements


def _comparison_place(asset: Dict[str, Any], index: int, total: int) -> Dict[str, float]:
    side_index = index // 2
    return {"x": 540 if index % 2 == 0 else 1380, "y": 470 + side_index * 150, "scale": 0.66}


def _diagram_place(asset: Dict[str, Any], index: int, total: int) -> Dict[str, float]:
    p = anchor_point(asset.get("anchor", "center"), index, total)
    name = _asset_name(asset)
    scale = 1.5 if name == "earth" else 0.56 if name == "satellite" else 0.5 if name == "phone" or asset.get("kind") == "icon_cluster" else 0.78
    return {"x": p["x"], "y": p["y"], "scale": scale}


def _object_place(asset: Dict[str, Any], index: int, total: int) -> Dict[str, float]:
    p = anchor_point(asset.get("anchor", "center"), index, total)
    name = _asset_name(asset)
    # Scale by how many assets share the stage so a single subject fills the frame instead of floating
    # tiny in dead space (owner: scenes felt plain/bare).
    base = 1.55 if total <= 1 else 1.1 if total == 2 else 0.9
    if asset.get("kind") == "icon_cluster":
        base = 0.62
    elif name == "phone":
        base *= 0.8
    return {"x": p["x"], "y": p["y"], "scale": base}


def _stat_place(asset: Dict[str, Any], index: int, total: int) -> Dict[str, float]:
    return {"x": 960 + (index - (total - 1) / 2) * 360, "y": 760, "scale": 0.58}


def _miniature_place(asset: Dict[str, Any], index: int, total: int) -> Dict[str, float]:
    return {"x": 960 + (index - (total - 1) / 2) * 340, "y": 470, "scale": 0.78}


def _map_place(asset: Dict[str, Any], index: int, total: int) -> Dict[str, float]:
    name = _asset_name(asset)
    return {
        "x": 960 if name == "map" else 640 + index * (640 / max(1, total - 1)),
        "y": 520 if name == "map" else 560 + (index % 2) * 70,
        "scale": 1.4 if name == "map" else 0.52,
    }


def _timeline_place(asset: Dict[str, Any], index: int, total: int) -> Dict[str, float]:
    return {"x": 430 + index * (1060 / max(1, total - 1)), "y": 410, "scale": 0.42}


def _title_place(asset: Dict[str, Any], index: int, total: int) -> Dict[str, float]:
    return {"x": 960 + (index - (total - 1) / 2) * 310, "y": 670, "scale": 0.72}


def _paperwork_place(asset: Dict[str, Any], index: int, total: int) -> Dict[str, float]:
    return {"x": 960 + (index - (total - 1) / 2) * 280, "y": 690, "scale": 0.58}


def _diagram_target(asset_entries: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for entry in asset_entries:
        if _asset_name(entry["asset"]) in LOCATION_ASSETS:
            return entry
    for entry in asset_entries:
        if _asset_name(entry["asset"]) == "earth":
            return entry
    return None


def _first_overlay(beat: Dict[str, Any], roles: Iterable[str]) -> Optional[Dict[str, Any]]:
    role_set = set(roles)
    for overlay in beat.get("text_overlays") or []:
        if overlay.get("role") in role_set and str(overlay.get("text") or "").strip():
            return overlay
    return None


def _first_overlay_text(beat: Dict[str, Any]) -> str:
    overlay = _first_overlay(beat, roles=("headline", "stat", "caption", "label", "stamp", "tiny_note"))
    return str(overlay.get("text") or "").strip() if overlay else ""


def _overlay_text(beat: Dict[str, Any], role: str) -> str:
    overlay = _first_overlay(beat, roles=(role,))
    return str(overlay.get("text") or "").strip() if overlay else ""


def _fallback_text(beat: Dict[str, Any], section: Dict[str, Any], fallback: str) -> str:
    return str(beat.get("text") or beat.get("key_phrase") or section.get("key_phrase") or fallback).strip() or fallback


def _list_row_text(asset: Dict[str, Any]) -> str:
    variant = str(asset.get("variant") or "").strip()
    if variant:
        return variant.replace("_", " ").upper()
    name = _asset_name(asset)
    labels = {
        "clock": "ATOMIC CLOCK",
        "atomic_clock": "ATOMIC CLOCK",
        "earth": "RELATIVITY",
        "dot": "BLUE DOT",
        "point": "LOCATION POINT",
        "map_pin": "MAP PIN",
        "light": "LIGHT SPEED",
        "phone": "YOUR PHONE",
        "satellite": "GPS SATELLITE",
        "signal": "RADIO SIGNAL",
        "signal_beam": "RADIO SIGNAL",
    }
    return labels.get(name, name.replace("_", " ").upper())


def _asset_name(asset: Dict[str, Any]) -> str:
    return _registry_asset(_canonical_asset_name(asset))


def _canonical_asset_name(asset: Dict[str, Any]) -> str:
    raw = str(asset.get("name") or "generic_object").strip().lower().replace("_", " ")
    return ASSET_ALIASES.get(raw, raw.replace(" ", "_"))


def _prop_asset_name(prop: Dict[str, Any]) -> str:
    raw = str(prop.get("asset") or prop.get("name") or "").strip().lower().replace("_", " ")
    return ASSET_ALIASES.get(raw, raw.replace(" ", "_"))


def _load_generated_assets() -> Dict[str, Any]:
    global _GENERATED_ASSETS_CACHE
    if _GENERATED_ASSETS_CACHE is not None:
        return _GENERATED_ASSETS_CACHE
    try:
        with open(GENERATED_ASSETS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    _GENERATED_ASSETS_CACHE = data if isinstance(data, dict) else {}
    return _GENERATED_ASSETS_CACHE


def _generated_asset(name: str) -> Optional[Dict[str, Any]]:
    item = _load_generated_assets().get(str(name or "").strip())
    if isinstance(item, dict) and isinstance(item.get("shapes"), list):
        return item
    return None


def _registry_asset(name: str) -> str:
    if name in ("none", "text"):
        return name
    return name if name in REGISTRY_ASSETS else "generic_object"


def _kind_for_asset(kind: Optional[str], name: str) -> str:
    if name == "label":
        return "label"
    if name == "stamp":
        return "stamp"
    if kind in ("connector", "map_shape", "chart", "panel", "stamp", "texture"):
        return kind
    return "prop"


def _text_for_asset(asset: Dict[str, Any], name: str) -> Optional[Dict[str, Any]]:
    text = str(asset.get("variant") or "").strip()
    if not text or name not in ("label", "stamp", "counter", "number"):
        return None
    role = "stamp" if name == "stamp" else "stat" if name in ("counter", "number") else "label"
    return {"role": role, "text": text, "tone": "coral_stamp" if role == "stamp" else "ink", "maxChars": TEXT_CAPS[role], "fit": "auto"}


def _motion_for_asset(asset: Dict[str, Any], motions: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
    if asset.get("is_new") is False:
        return None
    for cue in motions:
        if cue.get("target") in (asset.get("id"), asset.get("name")) and cue.get("kind") != "none":
            return [{"kind": cue.get("kind", "pop_in"), "start": float(cue.get("delay", 0)), "duration": float(cue.get("duration", 0.25))}]
    return None


def _safe_id(raw: Any, fallback: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", str(raw or fallback))
    cleaned = re.sub(r"^[^a-zA-Z]+", "", cleaned)
    return (cleaned or fallback)[:40]


def _unique_id(raw: Any, fallback: str, used: set) -> str:
    base = _safe_id(raw, fallback)
    if len(base) < 2:
        base = fallback
    candidate = base
    suffix = 2
    while candidate in used:
        candidate = ("%s_%d" % (base[:36], suffix))[:40]
        suffix += 1
    used.add(candidate)
    return candidate


def _used_ids(elements: List[Dict[str, Any]]) -> set:
    return {str(element.get("id")) for element in elements}
