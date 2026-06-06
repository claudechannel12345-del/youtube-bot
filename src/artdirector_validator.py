"""Blueprint validator and repair pass for the cutaway art-director schema.

This module is intentionally not wired into the live render path yet. It exists
for Phase 3 smoke testing and for Phase 4/5 callers to import once blueprint
generation is enabled.
"""

from __future__ import annotations

import copy
import json
import math
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

from cutaway_vocab import (
    BACKGROUND_TREATMENT,
    CAMERA_INTENSITY,
    CAMERA_MOVE,
    COLOR_ROLE,
    CONNECTION_KIND,
    EASING,
    GENERATED_IMAGE_ENABLED,
    MOTION_KIND_V2,
    POSITION_MODE,
    REGISTRY_ASSETS,
    SIZE_MODE,
    TEXT_ROLE,
    BLUEPRINT_ELEMENT_KIND,
)
from environments import ENVIRONMENTS, get_environment, has_environment

try:
    from director import _clean_meaningful_text
except Exception:  # pragma: no cover - defensive import fallback for isolated use.
    def _clean_meaningful_text(text, subjects=None):
        cleaned = " ".join(str(text or "").strip().split())
        if not cleaned:
            return ""
        normalized = cleaned.lower().replace("_", " ")
        generic = {
            "label",
            "stamp",
            "clock",
            "distance",
            "earth",
            "satellite",
            "phone",
            "signal",
            "map",
            "point",
            "dot",
            "generic object",
            "generic_object",
        }
        subject_names = {
            str(subject).strip().lower().replace("_", " ")
            for subject in (subjects or [])
            if str(subject).strip()
        }
        if normalized in generic or normalized in subject_names:
            return ""
        return cleaned


MAX_ELEMENTS = 7
MAX_CONNECTIONS = 8
SAFE_X = (96, 1824)
SAFE_Y = (72, 1008)
SCALE_RANGE = (0.15, 2.0)
BOX_W_RANGE = (40, 1400)
BOX_H_RANGE = (12, 900)
TEXT_CAPS = {
    "headline": 34,
    "label": 28,
    "caption": 160,
    "quote": 160,
    "stat": 22,
    "stamp": 30,
    "callout": 42,
    "title": 34,
    "tiny_note": 42,
}

PLACEHOLDER_ASSETS = frozenset(["none", "text"])
PROP_SHAPES = frozenset(["rule", "disc", "tick"])

SCENE_CONTRACTS = {
    "caption_punch": {
        "required": {"text_roles": ["headline"]},
        "max_elements": 3,
        "max_connections": 0,
        "allowed_backgrounds": ["plain", "panel"],
    },
    "quote_stage": {
        "required": {"text_roles": ["caption"]},
        "max_elements": 3,
        "max_connections": 0,
        "caption_max": 160,
    },
    "stat_stage": {
        "required": {"text_roles": ["stat"]},
        "max_elements": 4,
        "max_connections": 2,
    },
    "comparison_stage": {
        "required": {"min_elements": 2},
        "max_elements": 6,
        "required_regions": ["left", "right"],
        "allowed_backgrounds": ["comparison_panels", "panel", "plain"],
    },
    "diagram_stage": {
        "required": {"min_elements": 2},
        "max_elements": 7,
        "max_connections": 8,
        "allowed_connections": ["line", "arrow", "range_ring", "pulse", "brace"],
    },
    "map_stage": {
        "required": {"assets_any": ["map", "map_pin", "dot", "point"]},
        "max_elements": 6,
        "allowed_backgrounds": ["map", "plain", "panel"],
    },
    "list_stage": {
        "required": {"min_text_or_label_elements": 2},
        "max_elements": 6,
        "text_cap": 34,
    },
    "timeline_stage": {
        "required": {"min_elements": 2},
        "max_elements": 6,
    },
    "object_stage": {
        "required": {"min_elements": 1},
        "max_elements": 5,
    },
    "miniature_world": {
        "required": {"min_elements": 2},
        "max_elements": 6,
        "text_roles_allowed": ["label", "stamp", "tiny_note"],
    },
    "paperwork_stage": {
        "required": {"min_elements": 1},
        "max_elements": 5,
        "allowed_backgrounds": ["paper_stack", "panel", "plain"],
    },
    "title_stage": {
        "required": {"text_roles": ["headline"]},
        "max_elements": 5,
    },
    "scene_stage": {
        "required": {},
        "max_elements": 8,
        "max_connections": 0,
        "allowed_backgrounds": ["plain"],
    },
}

ANCHORS = frozenset(
    [
        "center",
        "left",
        "right",
        "upper_left",
        "upper_right",
        "lower_left",
        "lower_right",
        "upper_center",
        "lower_center",
        "headline",
        "stat",
        "diagram_core",
    ]
)
ATTACH_POINTS = frozenset(["center", "top", "bottom", "left", "right"])
ID_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{1,40}$")

ASSET_ALIASES = {
    "atomic clock": "atomic_clock",
    "atomic-clock": "atomic_clock",
    "blue_dot": "dot",
    "blue dot": "dot",
    "gps_satellite": "satellite",
    "gps satellite": "satellite",
    "map pin": "map_pin",
    "mappin": "map_pin",
    "pin": "map_pin",
    "skyscraper": "building",
    "time signal": "signal",
}


def validate_blueprint(blueprint, scene_family):
    """Validate and repair one blueprint.

    Returns ``(repaired_blueprint, repairs)``. The two-argument signature is the
    stable public API; section/beat context is added by the section wrapper.
    """
    return _validate_blueprint(
        blueprint,
        scene_family,
        section=None,
        beat=None,
        beat_text="",
        key_phrase="",
        beat_duration=None,
    )


def validate_and_repair_section(section_plan, source):
    """Run validation over every beat in a section plan and attach repair logs."""
    repaired = copy.deepcopy(section_plan or {})
    section_index = repaired.get("section_index")
    key_phrase = str(repaired.get("key_phrase", "") or "")
    all_repairs = []

    def section_log(code, path, old, new):
        all_repairs.append({"section": section_index, "beat": None, "code": code, "path": path, "from": old, "to": new})

    section_environment = repaired.get("environment")
    if section_environment is not None and not has_environment(str(section_environment).strip()):
        old = section_environment
        repaired["environment"] = sorted(ENVIRONMENTS)[0]
        section_log("unknown_environment", "section.environment", old, repaired["environment"])

    for beat in repaired.get("beats", []) or []:
        scene_family = beat.get("scene_family", "object_stage")
        beat_id = beat.get("id")
        beat_text = _beat_text(beat)
        duration = _beat_duration(beat)
        blueprint = beat.get("blueprint")
        if not isinstance(blueprint, dict):
            blueprint = _fallback_blueprint(beat_text, key_phrase, scene_family)
            beat["blueprint"] = blueprint
        if scene_family == "scene_stage" and repaired.get("environment") and not blueprint.get("environment"):
            blueprint["environment"] = repaired.get("environment")

        fixed, repairs = _validate_blueprint(
            blueprint,
            scene_family,
            section=section_index,
            beat=beat_id,
            beat_text=beat_text,
            key_phrase=key_phrase,
            beat_duration=duration,
        )
        if scene_family == "scene_stage" and not _scene_beat_allows_text(beat):
            fixed, demotion_repairs = _drop_scene_text(fixed, section_index, beat_id)
            repairs.extend(demotion_repairs)
        beat["blueprint"] = fixed
        validation_source = "repaired_%s" % source if repairs and source == "llm" else source
        beat["validation"] = {
            "source": validation_source,
            "warnings": [],
            "repairs": repairs,
        }
        all_repairs.extend(repairs)

    repaired["validation"] = {"source": source, "repairs": all_repairs}
    return repaired


def _scene_beat_allows_text(beat):
    return beat.get("type") in ("stat_pop", "quote", "emphasize") or bool(beat.get("emphasis"))


def _drop_scene_text(bp, section, beat):
    repairs = []
    elements = bp.get("elements") or []
    fixed = []
    for index, element in enumerate(elements):
        if isinstance(element, dict) and isinstance(element.get("text"), dict):
            repairs.append({"section": section, "beat": beat, "code": "scene_text_demoted", "path": "blueprint.elements[%d]" % index, "from": element, "to": None})
            continue
        fixed.append(element)
    if len(fixed) != len(elements):
        bp = copy.deepcopy(bp)
        bp["elements"] = fixed
    return bp, repairs


def _validate_blueprint(
    blueprint,
    scene_family,
    section=None,
    beat=None,
    beat_text="",
    key_phrase="",
    beat_duration=None,
):
    bp = copy.deepcopy(blueprint if isinstance(blueprint, dict) else {})
    repairs = []

    def log(code, path, old, new):
        repairs.append({"section": section, "beat": beat, "code": code, "path": path, "from": old, "to": new})

    if bp.get("version") != 1:
        old = bp.get("version")
        bp["version"] = 1
        log("schema_version_repaired", "blueprint.version", old, 1)
    if not isinstance(bp.get("intent"), str):
        old = bp.get("intent")
        bp["intent"] = str(beat_text or key_phrase or "Cutaway")
        log("intent_repaired", "blueprint.intent", old, bp["intent"])

    _repair_background(bp, scene_family, log)
    _repair_camera(bp, log, beat_duration)

    elements = bp.get("elements")
    if not isinstance(elements, list):
        old = elements
        elements = []
        bp["elements"] = elements
        log("elements_repaired", "blueprint.elements", old, elements)

    seen_ids = set()
    cleaned_elements = []
    for index, element in enumerate(elements):
        if not isinstance(element, dict):
            log("element_dropped", "blueprint.elements[%d]" % index, element, None)
            continue
        fixed = _repair_element(element, index, seen_ids, log, beat_duration)
        if fixed:
            cleaned_elements.append(fixed)
    bp["elements"] = cleaned_elements

    _enforce_text_contract(bp, scene_family, log, beat_text, key_phrase)
    _enforce_scene_required(bp, scene_family, log, beat_text, key_phrase)
    if scene_family == "scene_stage" or bp.get("preset") == "scene_stage" or bp.get("environment"):
        _enforce_scene_stage_contract(bp, log)
    _enforce_element_limit(bp, scene_family, log)
    _repair_connections(bp, scene_family, log, beat_duration)

    if not _has_drawable_element(bp):
        old = bp.get("elements")
        bp["elements"] = [_caption_element(beat_text, key_phrase, "fallback_caption")]
        bp["connections"] = []
        bp["preset"] = "caption_punch"
        _set_background_treatment(bp, "plain")
        log("fallback_caption_injected", "blueprint.elements", old, bp["elements"])

    return bp, repairs


def _repair_background(bp, scene_family, log):
    old = bp.get("background")
    if isinstance(old, str):
        bp["background"] = {"treatment": old}
        log("background_shape_repaired", "blueprint.background", old, bp["background"])
    elif not isinstance(old, dict):
        bp["background"] = {"treatment": "plain"}
        log("background_repaired", "blueprint.background", old, bp["background"])

    treatment = bp["background"].get("treatment")
    allowed = SCENE_CONTRACTS.get(scene_family, {}).get("allowed_backgrounds")
    if treatment not in BACKGROUND_TREATMENT:
        bp["background"]["treatment"] = "plain"
        log("unknown_background", "blueprint.background.treatment", treatment, "plain")
    elif allowed and treatment not in allowed:
        fallback = allowed[0]
        bp["background"]["treatment"] = fallback
        log("background_not_allowed", "blueprint.background.treatment", treatment, fallback)

    color = bp["background"].get("colorRole")
    if color is not None and color not in ("paper", "paper_deep"):
        bp["background"]["colorRole"] = "paper"
        log("unknown_background_color", "blueprint.background.colorRole", color, "paper")

    bg_elements = bp["background"].get("elements")
    if bg_elements is not None and not isinstance(bg_elements, list):
        bp["background"]["elements"] = []
        log("background_elements_repaired", "blueprint.background.elements", bg_elements, [])


def _repair_camera(bp, log, beat_duration):
    old = bp.get("camera")
    if not isinstance(old, dict):
        bp["camera"] = {"move": "static", "target": "center", "intensity": "none"}
        log("camera_repaired", "blueprint.camera", old, bp["camera"])
    cam = bp["camera"]
    if cam.get("move") not in CAMERA_MOVE:
        old_move = cam.get("move")
        cam["move"] = "static"
        log("unknown_camera", "blueprint.camera.move", old_move, "static")
    if cam.get("intensity") not in CAMERA_INTENSITY:
        old_intensity = cam.get("intensity")
        cam["intensity"] = "none"
        log("unknown_camera_intensity", "blueprint.camera.intensity", old_intensity, "none")
    target = cam.get("target", "center")
    if isinstance(target, str):
        if target not in ANCHORS:
            cam["target"] = "center"
            log("unknown_camera_target", "blueprint.camera.target", target, "center")
    elif isinstance(target, dict):
        if not _valid_camera_ref(target):
            cam["target"] = "center"
            log("unknown_camera_target", "blueprint.camera.target", target, "center")
    else:
        cam["target"] = "center"
        log("unknown_camera_target", "blueprint.camera.target", target, "center")
    _repair_timing_fields(cam, "blueprint.camera", log, beat_duration)


def _repair_element(element, index, seen_ids, log, beat_duration):
    item = copy.deepcopy(element)
    path = "blueprint.elements[%d]" % index

    old_id = item.get("id")
    if not isinstance(old_id, str) or not ID_RE.match(old_id) or old_id in seen_ids:
        new_id = _unique_id("el%d" % index, seen_ids)
        item["id"] = new_id
        log("element_id_repaired", path + ".id", old_id, new_id)
    seen_ids.add(item["id"])

    if item.get("kind") not in BLUEPRINT_ELEMENT_KIND:
        old_kind = item.get("kind")
        item["kind"] = "prop"
        log("unknown_element_kind", path + ".kind", old_kind, "prop")

    asset = item.get("asset")
    if asset == "generated_image" and not GENERATED_IMAGE_ENABLED:
        item["asset"] = "generic_object"
        item["kind"] = "prop"
        item.pop("generated_image", None)
        log("generated_image_disabled", path + ".asset", asset, "generic_object")
    elif asset not in REGISTRY_ASSETS and asset not in PLACEHOLDER_ASSETS:
        replacement = ASSET_ALIASES.get(str(asset).strip().lower(), "generic_object")
        item["asset"] = replacement
        log("unknown_asset", path + ".asset", asset, replacement)

    prop_shape = item.get("propShape")
    if prop_shape is not None and prop_shape not in PROP_SHAPES:
        item.pop("propShape", None)
        log("unknown_prop_shape", path + ".propShape", prop_shape, None)

    _repair_position(item, path, log)
    _repair_size(item, path, log)

    color = item.get("colorRole")
    if color is not None and color not in COLOR_ROLE:
        item["colorRole"] = "accent"
        log("unknown_color", path + ".colorRole", color, "accent")

    for numeric_field in ("z", "opacity", "rotation"):
        if numeric_field in item and not _finite(item.get(numeric_field)):
            old = item.get(numeric_field)
            item[numeric_field] = 0 if numeric_field != "opacity" else 1
            log("number_repaired", path + "." + numeric_field, old, item[numeric_field])
    if "opacity" in item:
        old_opacity = item["opacity"]
        item["opacity"] = _clamp_number(item["opacity"], 0, 1)
        if item["opacity"] != old_opacity:
            log("opacity_clamped", path + ".opacity", old_opacity, item["opacity"])

    _repair_text(item, path, log)
    _repair_motion_list(item, path + ".motion", log, beat_duration)
    return item


def _repair_position(item, path, log):
    old = item.get("position")
    if not isinstance(old, dict) or old.get("mode") not in POSITION_MODE:
        item["position"] = {"mode": "point", "x": 960, "y": 540}
        log("position_repaired", path + ".position", old, item["position"])
        return

    if old["mode"] == "point":
        x = _number(old.get("x"), 960)
        y = _number(old.get("y"), 540)
        nx = _clamp_number(x, SAFE_X[0], SAFE_X[1])
        ny = _clamp_number(y, SAFE_Y[0], SAFE_Y[1])
        old["x"], old["y"] = nx, ny
        if x != nx:
            log("x_clamped", path + ".position.x", x, nx)
        if y != ny:
            log("y_clamped", path + ".position.y", y, ny)
    else:
        anchor = old.get("anchor")
        if anchor not in ANCHORS:
            old["anchor"] = "center"
            log("unknown_anchor", path + ".position.anchor", anchor, "center")
        for key in ("dx", "dy"):
            if key in old and not _finite(old.get(key)):
                previous = old.get(key)
                old[key] = 0
                log("number_repaired", path + ".position." + key, previous, 0)


def _repair_size(item, path, log):
    old = item.get("size")
    if not isinstance(old, dict) or old.get("mode") not in SIZE_MODE:
        item["size"] = {"mode": "scale", "scale": 1.0}
        log("size_repaired", path + ".size", old, item["size"])
        return
    if old["mode"] == "scale":
        scale = _number(old.get("scale"), 1.0)
        new_scale = _clamp_number(scale, SCALE_RANGE[0], SCALE_RANGE[1])
        old["scale"] = new_scale
        if scale != new_scale:
            log("scale_clamped", path + ".size.scale", scale, new_scale)
    else:
        w = _number(old.get("w"), 320)
        h = _number(old.get("h"), 180)
        nw = _clamp_number(w, BOX_W_RANGE[0], BOX_W_RANGE[1])
        nh = _clamp_number(h, BOX_H_RANGE[0], BOX_H_RANGE[1])
        old["w"], old["h"] = nw, nh
        if w != nw:
            log("box_width_clamped", path + ".size.w", w, nw)
        if h != nh:
            log("box_height_clamped", path + ".size.h", h, nh)


def _repair_text(item, path, log):
    text = item.get("text")
    if text is None:
        return
    if not isinstance(text, dict):
        item.pop("text", None)
        log("text_dropped", path + ".text", text, None)
        return

    role = text.get("role")
    if role not in TEXT_ROLE:
        text["role"] = "label"
        log("unknown_text_role", path + ".text.role", role, "label")
    if text.get("tone") not in ("ink", "muted", "coral_stamp", "warning", "quiet"):
        old_tone = text.get("tone")
        text["tone"] = "ink"
        log("unknown_text_tone", path + ".text.tone", old_tone, "ink")

    raw = text.get("text")
    cleaned = _clean_meaningful_text(raw)
    if not cleaned:
        item.pop("text", None)
        log("generic_text_dropped", path + ".text", raw, None)
        return
    cap = int(text.get("maxChars") or TEXT_CAPS.get(text["role"], 42))
    cap = min(cap, TEXT_CAPS.get(text["role"], cap))
    capped = _cap_text(cleaned, cap)
    text["text"] = capped
    text["maxChars"] = cap
    if cleaned != capped:
        log("text_capped", path + ".text.text", cleaned, capped)
    elif raw != cleaned:
        log("text_normalized", path + ".text.text", raw, cleaned)


def _repair_motion_list(container, path, log, beat_duration):
    motion = container.get("motion")
    if motion is None:
        return
    if not isinstance(motion, list):
        container["motion"] = []
        log("motion_repaired", path, motion, [])
        return
    fixed = []
    for i, step in enumerate(motion):
        if not isinstance(step, dict):
            log("motion_dropped", "%s[%d]" % (path, i), step, None)
            continue
        item = copy.deepcopy(step)
        step_path = "%s[%d]" % (path, i)
        if item.get("kind") not in MOTION_KIND_V2:
            old_kind = item.get("kind")
            item["kind"] = "pop_in"
            log("unknown_motion", step_path + ".kind", old_kind, "pop_in")
        if item.get("easing") is not None and item.get("easing") not in EASING:
            old_easing = item.get("easing")
            item["easing"] = "ease_out"
            log("unknown_easing", step_path + ".easing", old_easing, "ease_out")
        _repair_timing_fields(item, step_path, log, beat_duration)
        fixed.append(item)
    container["motion"] = fixed


def _repair_timing_fields(item, path, log, beat_duration):
    if "start" in item:
        start = _number(item.get("start"), 0.0)
        new_start = max(0.0, start)
        if beat_duration is not None:
            new_start = min(new_start, beat_duration)
        item["start"] = new_start
        if start != new_start:
            log("motion_start_clamped", path + ".start", start, new_start)
    if "duration" in item:
        duration = _number(item.get("duration"), 0.1)
        new_duration = max(0.0, duration)
        if beat_duration is not None:
            start = _number(item.get("start"), 0.0)
            new_duration = min(new_duration, max(0.0, beat_duration - start))
        item["duration"] = new_duration
        if duration != new_duration:
            log("motion_duration_clamped", path + ".duration", duration, new_duration)


def _enforce_text_contract(bp, scene_family, log, beat_text, key_phrase):
    contract = SCENE_CONTRACTS.get(scene_family, {})
    allowed_roles = contract.get("text_roles_allowed")
    text_cap = contract.get("text_cap")
    for i, element in enumerate(bp.get("elements", [])):
        text = element.get("text")
        if not isinstance(text, dict):
            continue
        if allowed_roles and text.get("role") not in allowed_roles:
            old = text.get("role")
            text["role"] = allowed_roles[0]
            log("text_role_not_allowed", "blueprint.elements[%d].text.role" % i, old, text["role"])
            _repair_text(element, "blueprint.elements[%d]" % i, log)
        if text_cap and len(text.get("text", "")) > text_cap:
            old_text = text.get("text", "")
            text["text"] = _cap_text(old_text, text_cap)
            text["maxChars"] = min(int(text.get("maxChars") or text_cap), text_cap)
            log("text_capped", "blueprint.elements[%d].text.text" % i, old_text, text["text"])


def _enforce_scene_required(bp, scene_family, log, beat_text, key_phrase):
    contract = SCENE_CONTRACTS.get(scene_family, {})
    required = contract.get("required", {})
    elements = bp.setdefault("elements", [])

    for role in required.get("text_roles", []):
        if not _has_text_role(elements, role):
            el = _text_element(role, beat_text, key_phrase, "required_%s" % role)
            elements.append(el)
            log("required_text_added", "blueprint.elements", None, el)

    min_elements = required.get("min_elements")
    if min_elements:
        while len(elements) < min_elements:
            el = _generic_element("required_el%d" % len(elements), 420 + len(elements) * 260, 540)
            elements.append(el)
            log("required_element_added", "blueprint.elements", None, el)

    assets_any = required.get("assets_any")
    if assets_any and not any(e.get("asset") in assets_any for e in elements):
        el = _generic_element("required_map", 960, 540)
        el["asset"] = assets_any[0]
        elements.append(el)
        log("required_asset_added", "blueprint.elements", None, el)

    min_text_or_label = required.get("min_text_or_label_elements")
    if min_text_or_label:
        while _count_text_or_label(elements) < min_text_or_label:
            el = _text_element("label", beat_text, key_phrase, "required_label%d" % len(elements))
            elements.append(el)
            log("required_label_added", "blueprint.elements", None, el)

    required_regions = contract.get("required_regions", [])
    if "left" in required_regions and not _has_region(elements, "left"):
        el = _generic_element("required_left", 560, 540)
        elements.append(el)
        log("required_region_added", "blueprint.elements", None, el)
    if "right" in required_regions and not _has_region(elements, "right"):
        el = _generic_element("required_right", 1360, 540)
        elements.append(el)
        log("required_region_added", "blueprint.elements", None, el)


def _enforce_element_limit(bp, scene_family, log):
    contract = SCENE_CONTRACTS.get(scene_family, {})
    limit = min(MAX_ELEMENTS, int(contract.get("max_elements", MAX_ELEMENTS)))
    elements = bp.get("elements", [])
    if len(elements) <= limit:
        return
    old = copy.deepcopy(elements)
    required = []
    optional = []
    for element in elements:
        if isinstance(element.get("text"), dict):
            role = element["text"].get("role")
            required_roles = contract.get("required", {}).get("text_roles", [])
            if role in required_roles:
                required.append(element)
                continue
        optional.append(element)
    optional.sort(key=lambda e: _number(e.get("z"), 0), reverse=True)
    bp["elements"] = (required + optional)[:limit]
    log("too_many_elements", "blueprint.elements", old, bp["elements"])


def _enforce_scene_stage_contract(bp, log):
    env_id = str(bp.get("environment") or "").strip()
    if not has_environment(env_id):
        old = env_id
        env_id = sorted(ENVIRONMENTS)[0]
        bp["environment"] = env_id
        log("unknown_environment", "blueprint.environment", old, env_id)
    env = get_environment(env_id)
    slots = env.get("slots") or {}

    elements = bp.setdefault("elements", [])
    actor_count = 0
    text_seen = 0
    fixed = []
    for index, element in enumerate(elements):
        if not isinstance(element, dict):
            continue
        path = "blueprint.elements[%d]" % index
        has_shapes = isinstance(element.get("shapes"), list)
        has_text = isinstance(element.get("text"), dict)
        slot_name = element.get("slot")

        if has_shapes:
            z = _number(element.get("z"), 0)
            layer = str(element.get("id") or "")
            target_z = None
            if "backdrop" in layer:
                target_z = 5
            elif "midground" in layer:
                target_z = 100
            elif "foreground" in layer:
                target_z = 500
            if target_z is not None and z != target_z:
                old_z = element.get("z")
                element["z"] = target_z
                log("scene_layer_z_repaired", path + ".z", old_z, target_z)
            fixed.append(element)
            continue

        if has_text:
            text_seen += 1
            if text_seen > 1:
                log("scene_extra_text_dropped", path, element, None)
                continue
            old_z = element.get("z")
            if _number(old_z, 900) < 900:
                element["z"] = 900
                log("scene_text_z_repaired", path + ".z", old_z, 900)
            fixed.append(element)
            continue

        actor_count += 1
        if actor_count > 4:
            log("scene_extra_actor_dropped", path, element, None)
            continue
        if slot_name not in slots:
            fallback_slot = list(slots.keys())[min(actor_count - 1, max(0, len(slots) - 1))] if slots else None
            old_slot = slot_name
            if fallback_slot:
                element["slot"] = fallback_slot
                slot = slots[fallback_slot]
                element["position"] = {"mode": "point", "x": slot["x"], "y": slot["y"]}
                element["size"] = {"mode": "scale", "scale": slot["scale"]}
                log("scene_actor_slot_repaired", path + ".slot", old_slot, fallback_slot)
        old_z = element.get("z")
        z = _clamp_number(old_z, 200, 399)
        element["z"] = z
        if old_z != z:
            log("scene_actor_z_repaired", path + ".z", old_z, z)
        fixed.append(element)

    bp["elements"] = fixed


def _repair_connections(bp, scene_family, log, beat_duration):
    connections = bp.get("connections", [])
    if connections is None:
        bp["connections"] = []
        return
    if not isinstance(connections, list):
        bp["connections"] = []
        log("connections_repaired", "blueprint.connections", connections, [])
        return
    element_ids = {e.get("id") for e in bp.get("elements", []) if isinstance(e, dict)}
    contract = SCENE_CONTRACTS.get(scene_family, {})
    allowed_connections = contract.get("allowed_connections")
    max_connections = min(MAX_CONNECTIONS, int(contract.get("max_connections", MAX_CONNECTIONS)))
    fixed = []
    for i, connection in enumerate(connections):
        path = "blueprint.connections[%d]" % i
        if len(fixed) >= max_connections:
            log("too_many_connections", path, connection, None)
            continue
        if not isinstance(connection, dict):
            log("connection_dropped", path, connection, None)
            continue
        conn = copy.deepcopy(connection)
        kind = conn.get("kind")
        if kind not in CONNECTION_KIND:
            log("bad_connection", path + ".kind", kind, None)
            continue
        if allowed_connections and kind not in allowed_connections:
            log("bad_connection", path + ".kind", kind, None)
            continue
        if not _valid_ref(conn.get("from"), element_ids):
            log("bad_connection", path + ".from", conn.get("from"), None)
            continue
        if conn.get("to") is not None and not _valid_ref(conn.get("to"), element_ids):
            log("bad_connection", path + ".to", conn.get("to"), None)
            continue
        if conn.get("colorRole") is not None and conn.get("colorRole") not in COLOR_ROLE:
            old_color = conn.get("colorRole")
            conn["colorRole"] = "accent"
            log("unknown_color", path + ".colorRole", old_color, "accent")
        _repair_motion_list(conn, path + ".motion", log, beat_duration)
        fixed.append(conn)
    bp["connections"] = fixed


def _valid_ref(ref, element_ids, allow_element=True):
    if isinstance(ref, str):
        return ref in ANCHORS or (allow_element and ref in element_ids)
    if not isinstance(ref, dict):
        return False
    if "element" in ref:
        if not allow_element or ref.get("element") not in element_ids:
            return False
        attach = ref.get("attach")
        return attach is None or attach in ATTACH_POINTS
    if "anchor" in ref:
        return ref.get("anchor") in ANCHORS
    if "point" in ref and isinstance(ref.get("point"), dict):
        point = ref["point"]
        return _finite(point.get("x")) and _finite(point.get("y"))
    return False


def _valid_camera_ref(ref):
    if "element" in ref:
        attach = ref.get("attach")
        return isinstance(ref.get("element"), str) and (attach is None or attach in ATTACH_POINTS)
    return _valid_ref(ref, set(), allow_element=False)


def _has_drawable_element(bp):
    for element in bp.get("elements", []):
        if not isinstance(element, dict):
            continue
        if element.get("asset") in REGISTRY_ASSETS or isinstance(element.get("text"), dict) or element.get("propShape") in PROP_SHAPES or isinstance(element.get("shapes"), list):
            return True
    return False


def _fallback_blueprint(beat_text, key_phrase, scene_family):
    family = scene_family if scene_family in SCENE_CONTRACTS else "caption_punch"
    return {
        "version": 1,
        "preset": family,
        "intent": str(beat_text or key_phrase or "Fallback cutaway"),
        "background": {"treatment": "plain"},
        "camera": {"move": "static", "target": "center", "intensity": "none"},
        "elements": [_caption_element(beat_text, key_phrase, "fallback_caption")],
        "connections": [],
    }


def _caption_element(beat_text, key_phrase, element_id):
    return _text_element("headline", beat_text, key_phrase, element_id)


def _text_element(role, beat_text, key_phrase, element_id):
    text = _fallback_text(beat_text, key_phrase, role)
    asset = "stamp" if role == "stamp" else "none"
    return {
        "id": element_id,
        "kind": role if role != "stamp" else "stamp",
        "asset": asset,
        "position": {"mode": "point", "x": 960, "y": 540},
        "size": {"mode": "scale", "scale": 1.0},
        "text": {"role": role, "text": text, "tone": "ink", "maxChars": TEXT_CAPS.get(role, 42)},
        "z": 100,
        "motion": [{"kind": "pop_in", "start": 0.0, "duration": 0.25}],
    }


def _generic_element(element_id, x, y):
    return {
        "id": element_id,
        "kind": "prop",
        "asset": "generic_object",
        "position": {"mode": "point", "x": x, "y": y},
        "size": {"mode": "scale", "scale": 0.8},
        "z": 1,
    }


def _fallback_text(beat_text, key_phrase, role):
    raw = _clean_meaningful_text(beat_text) or _clean_meaningful_text(key_phrase) or "CUTAWAY"
    return _cap_text(raw.upper(), TEXT_CAPS.get(role, 42))


def _has_text_role(elements, role):
    return any(isinstance(e.get("text"), dict) and e["text"].get("role") == role for e in elements)


def _count_text_or_label(elements):
    return sum(1 for e in elements if e.get("asset") == "label" or isinstance(e.get("text"), dict))


def _has_region(elements, region):
    for element in elements:
        position = element.get("position", {})
        if not isinstance(position, dict) or position.get("mode") != "point":
            continue
        x = _number(position.get("x"), 960)
        if region == "left" and x < 960:
            return True
        if region == "right" and x > 960:
            return True
    return False


def _beat_text(beat):
    for overlay in beat.get("text_overlays", []) or []:
        if isinstance(overlay, dict) and overlay.get("text"):
            return str(overlay.get("text"))
    return str(beat.get("text", "") or beat.get("intent", "") or "")


def _beat_duration(beat):
    if _finite(beat.get("end")) and _finite(beat.get("start")):
        return max(0.0, float(beat["end"]) - float(beat["start"]))
    if _finite(beat.get("endFrame")) and _finite(beat.get("startFrame")):
        return max(0.0, (float(beat["endFrame"]) - float(beat["startFrame"])) / 30.0)
    return None


def _cap_text(text, cap):
    cleaned = " ".join(str(text or "").strip().split())
    if len(cleaned) <= cap:
        return cleaned
    if cap <= 1:
        return cleaned[:cap]
    return cleaned[: cap - 1].rstrip() + "..."


def _set_background_treatment(bp, treatment):
    if not isinstance(bp.get("background"), dict):
        bp["background"] = {}
    bp["background"]["treatment"] = treatment


def _unique_id(base, seen):
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", str(base or "el"))
    if not safe or not safe[0].isalpha():
        safe = "el_" + safe
    safe = safe[:38]
    candidate = safe
    i = 1
    while candidate in seen or not ID_RE.match(candidate):
        suffix = "_%d" % i
        candidate = safe[: 41 - len(suffix)] + suffix
        i += 1
    return candidate


def _number(value, fallback):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return fallback
    if not math.isfinite(result):
        return fallback
    return result


def _finite(value):
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _clamp_number(value, lo, hi):
    value = _number(value, lo)
    return max(lo, min(hi, value))


def _smoke_bad_section():
    elements = [
        {
            "id": "1bad",
            "kind": "prop",
            "asset": "gps_satellite",
            "position": {"mode": "point", "x": -250, "y": 2000},
            "size": {"mode": "scale", "scale": 8},
            "colorRole": "neon",
            "motion": [{"kind": "teleport", "start": -1, "duration": 99}],
            "z": 1,
        },
        {
            "id": "dup",
            "kind": "label",
            "asset": "label",
            "position": {"mode": "point", "x": 960, "y": 930},
            "size": {"mode": "box", "w": 9999, "h": 5},
            "text": {
                "role": "label",
                "text": "THIS LABEL IS FAR TOO LONG FOR THE LABEL ROLE AND SHOULD BE CAPPED",
                "tone": "loud",
            },
            "z": 80,
        },
        {
            "id": "dup",
            "kind": "generated_image",
            "asset": "generated_image",
            "position": {"mode": "anchor", "anchor": "not_real"},
            "size": {"mode": "scale", "scale": 1},
            "z": 70,
        },
    ]
    for i in range(8):
        elements.append(
            {
                "id": "extra_%d" % i,
                "kind": "prop",
                "asset": "phone",
                "position": {"mode": "point", "x": 300 + i * 80, "y": 500},
                "size": {"mode": "scale", "scale": 0.4},
                "z": i,
            }
        )
    return {
        "section_index": 3,
        "key_phrase": "GPS proof",
        "beats": [
            {
                "id": "bad_beat",
                "start": 0,
                "end": 2,
                "scene_family": "diagram_stage",
                "blueprint": {
                    "version": 7,
                    "intent": None,
                    "background": {"treatment": "sparkles"},
                    "camera": {"move": "dolly", "target": "void", "intensity": "huge"},
                    "elements": elements,
                    "connections": [
                        {"id": "c1", "kind": "arrow", "from": {"element": "missing"}, "to": {"element": "dup"}},
                        {"id": "c2", "kind": "laser", "from": {"element": "dup"}, "to": {"anchor": "center"}},
                    ],
                },
            }
        ],
    }


if __name__ == "__main__":
    repaired_section = validate_and_repair_section(_smoke_bad_section(), source="llm")
    print(json.dumps(repaired_section["validation"]["repairs"], indent=2, sort_keys=True))
