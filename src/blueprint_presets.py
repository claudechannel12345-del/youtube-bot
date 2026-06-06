"""Deterministic blueprint preset builders for cutaway scene families.

These builders mirror the legacy Remotion family placement functions in
``remotion/src/cutaway/families`` and emit explicit Phase 3 SceneBlueprint
payloads. The legacy v1 beat fields remain the source material; these functions
only make the layout concrete for the blueprint renderer.
"""

from __future__ import annotations

import re
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from cutaway_vocab import REGISTRY_ASSETS

TEXT_CAPS = {
    "headline": 34,
    "label": 28,
    "caption": 160,
    "stat": 22,
    "stamp": 30,
    "callout": 42,
    "tiny_note": 42,
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


def anchor_point(anchor: str, index: int = 0, total: int = 1) -> Dict[str, float]:
    spread = index - (total - 1) / 2 if total > 1 else 0
    if anchor == "upper_band":
        return {"x": 960 + spread * 360, "y": 230 + abs(spread) * 20}
    if anchor == "lower_band":
        return {"x": 960 + spread * 360, "y": 800}
    x, y = ANCHOR_POINTS.get(anchor, (960 + spread * 330, 540))
    return {"x": x, "y": y}


def build_blueprint(beat: Dict[str, Any], sentences_timing: List[Dict[str, Any]], section: Dict[str, Any]) -> Dict[str, Any]:
    family = beat.get("scene_family") or "object_stage"
    builder = PRESET_BUILDERS.get(family, build_object_stage)
    return builder(beat, sentences_timing, section)


def build_comparison_stage(beat: Dict[str, Any], sentences_timing: List[Dict[str, Any]], section: Dict[str, Any]) -> Dict[str, Any]:
    assets = _asset_elements(beat, _comparison_place, max_assets=4)
    label = _first_overlay(beat, roles=("label", "caption", "headline", "stamp"))
    if label:
        assets.append(_text_element(label, "comparison_label", 960, 858, "label", 1.0, z=50))
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
        _text_element({"role": "stat", "text": text, "tone": "coral_stamp"}, "stat_number", 960, 449, "counter", 2.0, z=20),
    ]
    elements.extend(_asset_elements(beat, _stat_place, max_assets=3, start_z=30))
    return _blueprint(beat, "stat_stage", "panel", elements[:4], [])


def build_caption_punch(beat: Dict[str, Any], sentences_timing: List[Dict[str, Any]], section: Dict[str, Any]) -> Dict[str, Any]:
    text = _first_overlay_text(beat) or _fallback_text(beat, section, "YES")
    elements = [
        _text_element({"role": "headline", "text": text, "tone": "ink"}, "headline", 980, 455, "generic_object", 1.0, z=20, box=(1080, 210)),
        _element("coral_underline", "prop", "arrow", 960, 590, 1.7, color_role="accent", z=10),
    ]
    return _blueprint(beat, "caption_punch", "plain", elements, [])


def build_object_stage(beat: Dict[str, Any], sentences_timing: List[Dict[str, Any]], section: Dict[str, Any]) -> Dict[str, Any]:
    elements = []
    assets = beat.get("assets") or []
    has_grounded = any(_asset_name(asset) not in SPACE_ASSETS for asset in assets)
    if has_grounded:
        elements.append(_element("ground_shadow", "texture", "ring", 960, 830, 2.0, color_role="muted", z=1, opacity=0.18))
    elements.extend(_asset_elements(beat, _object_place, max_assets=4, start_z=20))
    elements.extend(_overlay_elements(beat, start_z=50, max_items=max(0, 5 - len(elements))))
    return _blueprint(beat, "object_stage", "plain", elements[:5], [])


def build_list_stage(beat: Dict[str, Any], sentences_timing: List[Dict[str, Any]], section: Dict[str, Any]) -> Dict[str, Any]:
    elements = []
    assets = (beat.get("assets") or [])[:5]
    for index, asset in enumerate(assets):
        y = 247 + index * 125
        row_text = _list_row_text(asset)
        elements.append(_text_element({"role": "label", "text": row_text, "tone": "ink"}, "row_%d" % (index + 1), 1080, y, "label", 1.15, z=20 + index))
        if index < 2:
            elements.append(_element("bullet_%d" % (index + 1), "prop", "dot", 486, y, 0.32, color_role="accent", z=30 + index))
    if not elements:
        text = _fallback_text(beat, section, "ITEM")
        elements.append(_text_element({"role": "label", "text": text, "tone": "ink"}, "row_1", 1080, 247, "label", 1.15, z=20))
        elements.append(_text_element({"role": "label", "text": "NEXT", "tone": "ink"}, "row_2", 1080, 372, "label", 1.15, z=21))
    return _blueprint(beat, "list_stage", "plain", elements[:6], [])


def build_quote_stage(beat: Dict[str, Any], sentences_timing: List[Dict[str, Any]], section: Dict[str, Any]) -> Dict[str, Any]:
    quote = _overlay_text(beat, "caption") or _fallback_text(beat, section, "Quote")
    attribution = _overlay_text(beat, "tiny_note")
    elements = [
        _text_element({"role": "caption", "text": quote, "tone": "ink"}, "quote_card", 960, 405, "generic_object", 1.0, z=20, box=(900, 330)),
    ]
    if attribution:
        elements.append(_text_element({"role": "tiny_note", "text": attribution, "tone": "muted"}, "quote_attribution", 960, 620, "label", 1.0, z=30))
    elements.append(_element("quote_dot", "prop", "dot", 1424, 232, 0.46, color_role="accent", z=40))
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
        _text_element({"role": "headline", "text": text, "tone": "ink"}, "title_headline", 960, 425, "generic_object", 1.0, z=30, box=(1060, 190)),
        _element("title_underline", "prop", "arrow", 960, 520, 1.45, color_role="accent", z=20),
    ]
    elements.extend(_asset_elements(beat, _title_place, max_assets=3, start_z=40))
    return _blueprint(beat, "title_stage", "plain", elements[:5], [])


def build_paperwork_stage(beat: Dict[str, Any], sentences_timing: List[Dict[str, Any]], section: Dict[str, Any]) -> Dict[str, Any]:
    elements = [_element("paper_slash", "prop", "arrow", 960, 670, 1.0, color_role="accent", z=15, rotation=-9)]
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


def _asset_element(asset: Dict[str, Any], index: int, total: int, placer: Callable[[Dict[str, Any], int, int], Dict[str, float]], z: int, used: set, motions: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    place = placer(asset, index, total)
    name = _asset_name(asset)
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


def _element(element_id: str, kind: str, asset: str, x: float, y: float, scale: float, color_role: Optional[str] = None, z: int = 10, opacity: Optional[float] = None, rotation: Optional[float] = None, box: Optional[Tuple[int, int]] = None) -> Dict[str, Any]:
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
    return item


def _text_element(overlay: Dict[str, Any], element_id: str, x: float, y: float, asset: str, scale: float, z: int, box: Optional[Tuple[int, int]] = None) -> Dict[str, Any]:
    role = overlay.get("role", "label")
    text = str(overlay.get("text") or "").strip()
    tone = overlay.get("tone", "ink")
    item = _element(element_id, "stamp" if role == "stamp" or asset == "stamp" else "label", asset, x, y, scale, z=z, box=box)
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
    scale = 0.62 if asset.get("kind") == "icon_cluster" else 0.72 if name == "phone" else 0.92
    return {"x": p["x"], "y": p["y"], "scale": scale}


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
    raw = str(asset.get("name") or "generic_object").strip().lower().replace("_", " ")
    name = ASSET_ALIASES.get(raw, raw.replace(" ", "_"))
    return _registry_asset(name)


def _registry_asset(name: str) -> str:
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
