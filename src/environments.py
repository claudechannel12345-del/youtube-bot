"""Authored hero environments for section-level scene staging.

Each environment is a deterministic 1920x1080 composition made from primitive
shape lists plus named actor slots. The renderer already understands
BlueprintElement.shapes, so callers wrap these layers as texture elements.
"""

from __future__ import annotations

import copy
import json
import os
import re
from typing import Any, Callable, Dict, Optional, Tuple


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENERATED_ENVIRONMENTS_PATH = os.path.join(ROOT, "data", "generated_environments.json")
_GENERATED_ENVIRONMENTS_CACHE: Optional[Dict[str, Any]] = None

FRAME_W = 1920.0
FRAME_H = 1080.0
SAFE_TOP = 64.0
SAFE_BOTTOM = 48.0


def _slot_depth(y: float, z: int) -> str:
    if z < 180 or y < 540:
        return "background"
    if z >= 280 or y >= 760:
        return "foreground"
    return "midground"


def _slot(x: float, y: float, scale: float, z: int) -> Dict[str, Any]:
    return {"x": x, "y": y, "scale": scale, "z": z, "depth": _slot_depth(y, z)}


def _text_zone(x: float, y: float, w: float, h: float) -> Dict[str, float]:
    return {"x": x, "y": y, "w": w, "h": h}


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, float(value)))


def _clamp_safe_area_centers(env: Dict[str, Any]) -> Dict[str, Any]:
    zone = copy.deepcopy(env.get("text_zone") or _text_zone(120, SAFE_TOP, 760, 150))
    zone["x"] = _clamp(float(zone.get("x", 120)), 0.0, max(0.0, FRAME_W - float(zone.get("w", 0))))
    zone["y"] = _clamp(float(zone.get("y", SAFE_TOP)), SAFE_TOP, max(SAFE_TOP, FRAME_H - SAFE_BOTTOM - float(zone.get("h", 0))))
    env["text_zone"] = zone
    for slot in (env.get("slots") or {}).values():
        if isinstance(slot, dict):
            slot["x"] = _clamp(float(slot.get("x", FRAME_W / 2)), 0.0, FRAME_W)
            slot["y"] = _clamp(float(slot.get("y", FRAME_H / 2)), SAFE_TOP, FRAME_H - SAFE_BOTTOM)
    for prop in env.get("set_props") or []:
        if isinstance(prop, dict):
            prop["x"] = _clamp(float(prop.get("x", FRAME_W / 2)), 0.0, FRAME_W)
            prop["y"] = _clamp(float(prop.get("y", FRAME_H / 2)), SAFE_TOP, FRAME_H - SAFE_BOTTOM)
    return env


def _parse_environment_ref(environment_id: str, variant: str | None = None) -> Tuple[str, str]:
    raw = str(environment_id or "").strip()
    env_id, inline_variant = (raw.split(":", 1) + [""])[:2] if ":" in raw else (raw, "")
    chosen_variant = str(variant or inline_variant or "").strip().lower()
    return env_id.strip(), chosen_variant


def _overlaps_text_zone(x: float, y: float, w: float, h: float, zone: Dict[str, float]) -> bool:
    return not (
        x + w < float(zone.get("x", 0))
        or x > float(zone.get("x", 0)) + float(zone.get("w", 0))
        or y + h < float(zone.get("y", 0))
        or y > float(zone.get("y", 0)) + float(zone.get("h", 0))
    )


def _transform_path_d(d: str, transform) -> str:
    numbers = [float(match.group(0)) for match in re.finditer(r"-?\d+(?:\.\d+)?", str(d or ""))]
    transformed = []
    for i in range(0, len(numbers), 2):
        x = numbers[i]
        y = numbers[i + 1] if i + 1 < len(numbers) else 0
        tx, ty = transform(x, y)
        transformed.extend([tx, ty])
    index = 0

    def repl(match):
        nonlocal index
        value = transformed[index] if index < len(transformed) else float(match.group(0))
        index += 1
        return _fmt(value)

    return re.sub(r"-?\d+(?:\.\d+)?", repl, str(d or ""))


def _fmt(value: float) -> str:
    text = "%.3f" % float(value)
    return text.rstrip("0").rstrip(".")


def _transform_shape(shape: Dict[str, Any], transform, scale: float) -> Dict[str, Any]:
    out = copy.deepcopy(shape)
    kind = out.get("type")
    if kind == "rect":
        x, y = transform(float(out.get("x", 0)), float(out.get("y", 0)))
        out["x"], out["y"] = x, y
        out["w"] = float(out.get("w", 0)) * scale
        out["h"] = float(out.get("h", 0)) * scale
        if out.get("rx") is not None:
            out["rx"] = float(out.get("rx", 0)) * scale
    elif kind in ("circle", "ellipse"):
        x, y = transform(float(out.get("cx", 0)), float(out.get("cy", 0)))
        out["cx"], out["cy"] = x, y
        out["r"] = float(out.get("r", 0)) * scale
        if out.get("ry") is not None:
            out["ry"] = float(out.get("ry", 0)) * scale
    elif kind == "line":
        x1, y1 = transform(float(out.get("x1", 0)), float(out.get("y1", 0)))
        x2, y2 = transform(float(out.get("x2", 0)), float(out.get("y2", 0)))
        out["x1"], out["y1"], out["x2"], out["y2"] = x1, y1, x2, y2
    elif kind == "polygon":
        points = out.get("points") or []
        fixed = []
        for i in range(0, len(points), 2):
            x = float(points[i])
            y = float(points[i + 1]) if i + 1 < len(points) else 0
            tx, ty = transform(x, y)
            fixed.extend([tx, ty])
        out["points"] = fixed
    elif kind == "path":
        out["d"] = _transform_path_d(str(out.get("d", "")), transform)
    if out.get("strokeW") is not None:
        out["strokeW"] = max(1, float(out.get("strokeW", 1)) * scale)
    return out


def _shape_bbox(shape: Dict[str, Any]) -> Tuple[float, float, float, float] | None:
    kind = shape.get("type")
    if kind == "rect":
        return (float(shape.get("x", 0)), float(shape.get("y", 0)), float(shape.get("w", 0)), float(shape.get("h", 0)))
    if kind == "circle":
        r = float(shape.get("r", 0))
        return (float(shape.get("cx", 0)) - r, float(shape.get("cy", 0)) - r, r * 2, r * 2)
    if kind == "ellipse":
        r = float(shape.get("r", 0))
        ry = float(shape.get("ry", r))
        return (float(shape.get("cx", 0)) - r, float(shape.get("cy", 0)) - ry, r * 2, ry * 2)
    if kind == "line":
        x1, y1, x2, y2 = float(shape.get("x1", 0)), float(shape.get("y1", 0)), float(shape.get("x2", 0)), float(shape.get("y2", 0))
        return (min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
    if kind == "polygon":
        points = shape.get("points") or []
        xs = [float(points[i]) for i in range(0, len(points), 2)]
        ys = [float(points[i]) for i in range(1, len(points), 2)]
        if xs and ys:
            return (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
    return None


def _clear_text_zone(shapes: list, zone: Dict[str, float]) -> list:
    fixed = []
    for shape in shapes:
        bbox = _shape_bbox(shape)
        if bbox and _overlaps_text_zone(bbox[0], bbox[1], bbox[2], bbox[3], zone):
            continue
        fixed.append(shape)
    return fixed


def _verticalize_environment(env: Dict[str, Any]) -> Dict[str, Any]:
    """Crop/scale a 1920x1080 environment into a 1080x1920 stage."""
    scale = 1920.0 / 1080.0

    def transform(x: float, y: float) -> Tuple[float, float]:
        return ((float(x) - 960.0) * scale + 540.0, float(y) * scale)

    out = copy.deepcopy(env)
    out["orientation"] = "vertical"
    out["text_zone"] = _text_zone(90, 78, 900, 210)
    for layer in ("backdrop", "midground", "foreground"):
        out[layer] = [_transform_shape(shape, transform, scale) for shape in out.get(layer, [])]
    out["backdrop"] = _clear_text_zone(out["backdrop"], out["text_zone"])
    out["midground"] = _clear_text_zone(out["midground"], out["text_zone"])
    out["slots"] = {}
    for name, slot in (env.get("slots") or {}).items():
        x, y = transform(float(slot.get("x", 960)), float(slot.get("y", 540)))
        out["slots"][name] = _slot(x, y, float(slot.get("scale", 1.0)) * 1.45, int(slot.get("z", 250)))
    out["set_props"] = []
    for prop in env.get("set_props") or []:
        if not isinstance(prop, dict):
            continue
        x, y = transform(float(prop.get("x", 960)), float(prop.get("y", 720)))
        fixed = copy.deepcopy(prop)
        fixed["x"] = max(0.0, min(1080.0, x))
        fixed["y"] = max(0.0, min(1920.0, y))
        fixed["scale"] = float(prop.get("scale", 1.0)) * 1.45
        fixed["z"] = int(prop.get("z", 120))
        out["set_props"].append(fixed)
    return _document_slots(out)


def _top_corner(env: Dict[str, Any], w: float = 190, h: float = 170) -> Tuple[float, float]:
    zone = env.get("text_zone") or {}
    right = (1545.0, 86.0)
    left = (170.0, 92.0)
    return left if _overlaps_text_zone(right[0], right[1], w, h, zone) else right


def _crowd_shapes(env: Dict[str, Any]) -> list:
    zone = env.get("text_zone") or {}
    shapes = []
    tones = ("muted", "ink", "blue", "accent", "green")
    for row, cy in enumerate((180, 245, 310)):
        for i, cx in enumerate(range(220, 1710, 95)):
            if _overlaps_text_zone(cx - 22, cy - 22, 44, 44, zone):
                continue
            shapes.append({"type": "circle", "cx": cx + (row % 2) * 22, "cy": cy, "r": 18, "fill": tones[(i + row) % len(tones)], "opacity": 0.42})
    return shapes[:36]


def _apply_day_variant(env: Dict[str, Any]) -> None:
    x, y = _top_corner(env)
    env["backdrop"].extend(
        [
            {"type": "circle", "cx": x + 85, "cy": y + 70, "r": 58, "fill": "yellow", "opacity": 0.5, "stroke": True, "strokeW": 6},
            {"type": "line", "x1": x + 85, "y1": y - 18, "x2": x + 85, "y2": y + 6, "stroke": True, "strokeW": 5},
            {"type": "line", "x1": x + 10, "y1": y + 70, "x2": x + 36, "y2": y + 70, "stroke": True, "strokeW": 5},
            {"type": "line", "x1": x + 134, "y1": y + 70, "x2": x + 160, "y2": y + 70, "stroke": True, "strokeW": 5},
        ]
    )


def _apply_night_variant(env: Dict[str, Any]) -> None:
    x, y = _top_corner(env)
    env["backdrop"].insert(0, {"type": "rect", "x": 0, "y": 0, "w": 1920, "h": 1080, "fill": "ink", "opacity": 0.08})
    env["backdrop"].extend(
        [
            {"type": "circle", "cx": x + 88, "cy": y + 64, "r": 58, "fill": "lavender", "opacity": 0.55, "stroke": True, "strokeW": 6},
            {"type": "circle", "cx": x + 112, "cy": y + 48, "r": 54, "fill": "paper", "opacity": 0.72},
        ]
    )
    zone = env.get("text_zone") or {}
    for i, (sx, sy) in enumerate(((270, 150), (420, 310), (630, 210), (1230, 170), (1510, 345), (1710, 220))):
        if _overlaps_text_zone(sx - 16, sy - 16, 32, 32, zone):
            continue
        env["backdrop"].append({"type": "circle", "cx": sx, "cy": sy, "r": 7 + (i % 3) * 2, "fill": "white", "stroke": True, "strokeW": 3})


def _apply_crowded_variant(env: Dict[str, Any]) -> None:
    env["backdrop"].extend(_crowd_shapes(env))


def _apply_empty_variant(env: Dict[str, Any]) -> None:
    # Keep authored architecture intact, but make the scene feel intentionally unoccupied.
    env["midground"].append({"type": "path", "d": "M420 780 C720 725 1180 725 1500 780", "fill": "none", "stroke": True, "strokeW": 6, "opacity": 0.45})
    env["foreground"].append({"type": "line", "x1": 250, "y1": 955, "x2": 1670, "y2": 955, "stroke": True, "strokeW": 5, "opacity": 0.35})


def _apply_variant(env: Dict[str, Any], variant: str) -> Dict[str, Any]:
    clean_variant = str(variant or "").strip().lower()
    if clean_variant in ("", "base", "default"):
        return env
    if clean_variant == "day":
        _apply_day_variant(env)
    elif clean_variant == "night":
        _apply_night_variant(env)
    elif clean_variant == "crowded":
        _apply_crowded_variant(env)
    elif clean_variant == "empty":
        _apply_empty_variant(env)
    else:
        return env
    env["variant"] = clean_variant
    return env


def _slot_role(slot_name: str) -> str:
    lowered = str(slot_name or "").lower()
    if any(token in lowered for token in ("screen", "board", "sign", "monitor", "vault", "peak", "city", "planet", "goal")):
        return "background_prop"
    if any(token in lowered for token in ("item", "sample", "mic", "book", "mat", "counter", "table", "luggage", "ballot", "prop", "pack")):
        return "set_prop"
    if any(token in lowered for token in ("left", "right", "center", "host", "guest", "person", "visitor", "doctor", "nurse", "worker", "traveler", "farmer", "voter", "reader", "athlete", "climber", "server", "teacher", "student", "fighter", "referee", "judge", "lawyer", "witness")):
        return "actor"
    return "staged_subject"


def _document_slots(env: Dict[str, Any]) -> Dict[str, Any]:
    docs = {}
    for name, slot in (env.get("slots") or {}).items():
        docs[name] = {
            "role": slot.get("role") or _slot_role(name),
            "depth": slot.get("depth") or _slot_depth(float(slot.get("y", 0)), int(slot.get("z", 0))),
            "position": "x=%s y=%s" % (slot.get("x"), slot.get("y")),
            "scale": slot.get("scale"),
            "z": slot.get("z"),
        }
    env["slot_docs"] = docs
    return env


def _floor_lines(y0: int, y1: int, left: int = 0, right: int = 1920, count: int = 4) -> list[Dict[str, Any]]:
    shapes: list[Dict[str, Any]] = []
    step = (y1 - y0) / max(1, count)
    for i in range(count):
        y = y0 + int(step * (i + 1))
        inset = int((i + 1) * 42)
        shapes.append({"type": "line", "x1": left + inset, "y1": y, "x2": right - inset, "y2": y, "stroke": True, "strokeW": 3, "opacity": 0.28})
    return shapes


def _is_corner_dot_artifact(shape: Dict[str, Any]) -> bool:
    if shape.get("type") != "circle":
        return False
    cx = float(shape.get("cx", 960))
    cy = float(shape.get("cy", 540))
    radius = float(shape.get("r", 0))
    fill = str(shape.get("fill") or "")
    opacity = float(shape.get("opacity", 1))
    is_lower_corner = cy >= 850 and (cx <= 380 or cx >= 1540)
    is_gray_fill = fill in {"ink", "muted", "paper_deep"}
    return is_lower_corner and is_gray_fill and 24 <= radius <= 80 and opacity <= 0.6


def _remove_corner_dot_artifacts(env: Dict[str, Any]) -> Dict[str, Any]:
    env["foreground"] = [shape for shape in env.get("foreground", []) if not _is_corner_dot_artifact(shape)]
    return env


def _enrich_environment(env: Dict[str, Any]) -> Dict[str, Any]:
    """Keep returned environments clean while preserving authored structure."""
    return _remove_corner_dot_artifacts(env)


def build_arena() -> Dict[str, Any]:
    bg = []
    bg.append({"type": "rect", "x": 0, "y": 600, "w": 1920, "h": 480, "fill": "paper_deep"})
    bg.append({"type": "rect", "x": 120, "y": 150, "w": 1680, "h": 250, "rx": 8, "fill": "paper_deep"})
    tones = ["muted", "ink", "blue", "accent"]
    for r, cy in enumerate((205, 268, 331)):
        for i, cx in enumerate(range(190, 1760, 66)):
            bg.append(
                {
                    "type": "circle",
                    "cx": cx + (r % 2) * 14,
                    "cy": cy,
                    "r": 17,
                    "fill": tones[(i + r) % 4],
                    "opacity": 0.5,
                }
            )
    for lx in (840, 1080):
        bg.append({"type": "polygon", "points": [lx, 0, lx - 90, 170, lx + 90, 170], "fill": "yellow", "opacity": 0.22})
    bg.append({"type": "rect", "x": 808, "y": 56, "w": 304, "h": 132, "rx": 12, "fill": "paper", "stroke": True, "strokeW": 8})
    bg.append({"type": "line", "x1": 960, "y1": 70, "x2": 960, "y2": 174, "stroke": True, "strokeW": 5})
    bg.extend(
        [
            {"type": "rect", "x": 86, "y": 430, "w": 1748, "h": 64, "rx": 8, "fill": "paper", "stroke": True, "strokeW": 6, "opacity": 0.82},
            {"type": "line", "x1": 180, "y1": 464, "x2": 1740, "y2": 464, "stroke": True, "strokeW": 4, "opacity": 0.35},
            {"type": "rect", "x": 620, "y": 84, "w": 90, "h": 46, "rx": 6, "fill": "accent", "stroke": True, "strokeW": 5},
            {"type": "rect", "x": 1210, "y": 84, "w": 90, "h": 46, "rx": 6, "fill": "blue", "stroke": True, "strokeW": 5},
        ]
    )

    mid = []
    mid.append({"type": "polygon", "points": [620, 652, 1300, 652, 1500, 958, 420, 958], "fill": "muted", "stroke": True, "strokeW": 10})
    mid.append({"type": "polygon", "points": [684, 694, 1236, 694, 1404, 922, 516, 922], "fill": "none", "stroke": True, "strokeW": 5})
    mid.append({"type": "rect", "x": 430, "y": 922, "w": 120, "h": 46, "rx": 6, "fill": "accent", "stroke": True, "strokeW": 6})
    mid.append({"type": "rect", "x": 1370, "y": 922, "w": 120, "h": 46, "rx": 6, "fill": "blue", "stroke": True, "strokeW": 6})
    mid.extend(_floor_lines(720, 930, 480, 1440, 3))
    mid.append({"type": "ellipse", "cx": 960, "cy": 808, "r": 140, "ry": 46, "fill": "none", "stroke": True, "strokeW": 5, "opacity": 0.45})

    fg = []
    for ry in (986, 1046):
        fg.append({"type": "line", "x1": 40, "y1": ry, "x2": 1880, "y2": ry, "stroke": True, "strokeW": 14})
    for px in (62, 1818):
        fg.append({"type": "rect", "x": px, "y": 940, "w": 40, "h": 140, "rx": 6, "fill": "paper_deep", "stroke": True, "strokeW": 8})

    return {
        "id": "arena",
        "backdrop": bg,
        "midground": mid,
        "foreground": fg,
        "text_zone": _text_zone(96, 36, 600, 112),
        "slots": {
            "red_corner": _slot(770, 706, 1.45, 210),
            "blue_corner": _slot(1150, 706, 1.45, 211),
            "referee_center": _slot(965, 812, 1.9, 300),
        },
    }


def build_courtroom() -> Dict[str, Any]:
    bg = [
        {"type": "rect", "x": 0, "y": 610, "w": 1920, "h": 470, "fill": "paper_deep"},
        {"type": "rect", "x": 180, "y": 110, "w": 1560, "h": 520, "rx": 10, "fill": "paper", "stroke": True, "strokeW": 8},
        {"type": "line", "x1": 180, "y1": 352, "x2": 1740, "y2": 352, "stroke": True, "strokeW": 5},
        {"type": "rect", "x": 300, "y": 175, "w": 164, "h": 260, "rx": 4, "fill": "blue", "stroke": True, "strokeW": 6},
        {"type": "rect", "x": 300, "y": 175, "w": 164, "h": 44, "fill": "accent"},
        {"type": "rect", "x": 300, "y": 263, "w": 164, "h": 44, "fill": "white"},
        {"type": "line", "x1": 482, "y1": 160, "x2": 482, "y2": 470, "stroke": True, "strokeW": 5},
        {"type": "rect", "x": 1220, "y": 220, "w": 340, "h": 220, "rx": 8, "fill": "paper_deep", "stroke": True, "strokeW": 6},
        {"type": "rect", "x": 1328, "y": 174, "w": 120, "h": 40, "rx": 5, "fill": "yellow", "stroke": True, "strokeW": 5},
        {"type": "line", "x1": 1255, "y1": 286, "x2": 1525, "y2": 286, "stroke": True, "strokeW": 4, "opacity": 0.35},
        {"type": "line", "x1": 1255, "y1": 346, "x2": 1500, "y2": 346, "stroke": True, "strokeW": 4, "opacity": 0.35},
        {"type": "rect", "x": 705, "y": 170, "w": 510, "h": 120, "rx": 8, "fill": "paper_deep", "stroke": True, "strokeW": 6, "opacity": 0.72},
    ]
    mid = [
        {"type": "polygon", "points": [620, 420, 1320, 420, 1430, 650, 510, 650], "fill": "paper_deep", "stroke": True, "strokeW": 10},
        {"type": "rect", "x": 545, "y": 560, "w": 870, "h": 120, "rx": 8, "fill": "ink", "opacity": 0.88},
        {"type": "rect", "x": 1170, "y": 635, "w": 250, "h": 210, "rx": 8, "fill": "paper", "stroke": True, "strokeW": 8},
        {"type": "rect", "x": 430, "y": 705, "w": 330, "h": 125, "rx": 8, "fill": "paper", "stroke": True, "strokeW": 8},
        {"type": "rect", "x": 1460, "y": 705, "w": 250, "h": 120, "rx": 8, "fill": "paper_deep", "stroke": True, "strokeW": 7},
        {"type": "rect", "x": 688, "y": 508, "w": 90, "h": 34, "rx": 4, "fill": "yellow", "stroke": True, "strokeW": 4},
        {"type": "rect", "x": 820, "y": 508, "w": 90, "h": 34, "rx": 4, "fill": "accent", "stroke": True, "strokeW": 4},
        {"type": "rect", "x": 952, "y": 508, "w": 90, "h": 34, "rx": 4, "fill": "blue", "stroke": True, "strokeW": 4},
    ]
    fg = [
        {"type": "rect", "x": 145, "y": 875, "w": 1630, "h": 54, "rx": 8, "fill": "paper_deep", "stroke": True, "strokeW": 8},
        {"type": "line", "x1": 160, "y1": 825, "x2": 1760, "y2": 825, "stroke": True, "strokeW": 10},
        {"type": "line", "x1": 160, "y1": 930, "x2": 1760, "y2": 930, "stroke": True, "strokeW": 10},
    ]
    return {
        "id": "courtroom",
        "backdrop": bg,
        "midground": mid,
        "foreground": fg,
        "text_zone": _text_zone(410, 20, 1100, 88),
        "slots": {
            "judge_bench": _slot(960, 468, 1.0, 205),
            "witness_stand": _slot(1300, 720, 1.25, 260),
            "defendant_left": _slot(590, 745, 1.35, 275),
            "lawyer_right": _slot(1515, 755, 1.35, 285),
            "gallery": _slot(960, 842, 1.15, 235),
        },
    }


def build_newsroom() -> Dict[str, Any]:
    bg = [
        {"type": "rect", "x": 0, "y": 620, "w": 1920, "h": 460, "fill": "paper_deep"},
        {"type": "rect", "x": 170, "y": 112, "w": 1580, "h": 510, "rx": 10, "fill": "paper", "stroke": True, "strokeW": 8},
        {"type": "rect", "x": 615, "y": 170, "w": 690, "h": 350, "rx": 12, "fill": "blue", "stroke": True, "strokeW": 8},
        {"type": "path", "d": "M720 330 C820 250 890 395 980 305 C1070 215 1160 385 1230 280", "stroke": True, "strokeW": 8, "fill": "none"},
        {"type": "circle", "cx": 838, "cy": 308, "r": 18, "fill": "accent", "stroke": True, "strokeW": 5},
        {"type": "circle", "cx": 1108, "cy": 305, "r": 18, "fill": "yellow", "stroke": True, "strokeW": 5},
        {"type": "rect", "x": 210, "y": 250, "w": 260, "h": 170, "rx": 8, "fill": "paper_deep", "stroke": True, "strokeW": 6},
        {"type": "rect", "x": 1430, "y": 245, "w": 270, "h": 178, "rx": 8, "fill": "paper_deep", "stroke": True, "strokeW": 6},
        {"type": "rect", "x": 250, "y": 285, "w": 180, "h": 28, "rx": 4, "fill": "accent", "stroke": True, "strokeW": 4},
        {"type": "rect", "x": 1468, "y": 286, "w": 190, "h": 28, "rx": 4, "fill": "yellow", "stroke": True, "strokeW": 4},
        {"type": "line", "x1": 230, "y1": 460, "x2": 500, "y2": 460, "stroke": True, "strokeW": 5, "opacity": 0.38},
        {"type": "line", "x1": 1410, "y1": 464, "x2": 1718, "y2": 464, "stroke": True, "strokeW": 5, "opacity": 0.38},
    ]
    mid = [
        {"type": "polygon", "points": [545, 695, 1375, 695, 1510, 900, 410, 900], "fill": "paper", "stroke": True, "strokeW": 10},
        {"type": "line", "x1": 620, "y1": 755, "x2": 1300, "y2": 755, "stroke": True, "strokeW": 5},
        {"type": "rect", "x": 815, "y": 735, "w": 350, "h": 95, "rx": 8, "fill": "paper_deep", "stroke": True, "strokeW": 6},
        {"type": "rect", "x": 700, "y": 790, "w": 92, "h": 34, "rx": 4, "fill": "white", "stroke": True, "strokeW": 4},
        {"type": "rect", "x": 1188, "y": 788, "w": 104, "h": 34, "rx": 4, "fill": "white", "stroke": True, "strokeW": 4},
    ]
    fg = [
        {"type": "polygon", "points": [430, 850, 1490, 850, 1580, 1008, 340, 1008], "fill": "paper_deep", "stroke": True, "strokeW": 10},
        {"type": "line", "x1": 430, "y1": 850, "x2": 1490, "y2": 850, "stroke": True, "strokeW": 14},
        {"type": "rect", "x": 92, "y": 890, "w": 240, "h": 150, "rx": 8, "fill": "ink", "opacity": 0.22},
        {"type": "rect", "x": 1600, "y": 910, "w": 210, "h": 126, "rx": 8, "fill": "ink", "opacity": 0.2},
    ]
    return {
        "id": "newsroom",
        "backdrop": bg,
        "midground": mid,
        "foreground": fg,
        "text_zone": _text_zone(410, 20, 1100, 88),
        "slots": {
            "anchor_center": _slot(960, 704, 1.45, 260),
            "screen": _slot(960, 360, 0.95, 80),
            "desk_props": _slot(1060, 774, 0.55, 310),
        },
    }


def build_lab() -> Dict[str, Any]:
    bg = [
        {"type": "rect", "x": 0, "y": 615, "w": 1920, "h": 465, "fill": "paper_deep"},
        {"type": "rect", "x": 170, "y": 135, "w": 640, "h": 350, "rx": 8, "fill": "white", "stroke": True, "strokeW": 8},
        {"type": "path", "d": "M245 400 L360 315 L475 352 L615 240 L735 292", "fill": "none", "stroke": True, "strokeW": 7},
        {"type": "line", "x1": 240, "y1": 420, "x2": 730, "y2": 420, "stroke": True, "strokeW": 4},
        {"type": "line", "x1": 240, "y1": 180, "x2": 240, "y2": 420, "stroke": True, "strokeW": 4},
        {"type": "rect", "x": 1040, "y": 170, "w": 620, "h": 320, "rx": 8, "fill": "paper", "stroke": True, "strokeW": 8},
        {"type": "rect", "x": 1110, "y": 390, "w": 64, "h": 70, "rx": 6, "fill": "blue", "stroke": True, "strokeW": 5},
        {"type": "rect", "x": 1210, "y": 330, "w": 64, "h": 130, "rx": 6, "fill": "green", "stroke": True, "strokeW": 5},
        {"type": "rect", "x": 1310, "y": 260, "w": 64, "h": 200, "rx": 6, "fill": "accent", "stroke": True, "strokeW": 5},
        {"type": "circle", "cx": 1182, "cy": 276, "r": 28, "fill": "yellow", "stroke": True, "strokeW": 5},
        {"type": "circle", "cx": 1450, "cy": 320, "r": 46, "fill": "lavender", "stroke": True, "strokeW": 5},
        {"type": "path", "d": "M146 555 C420 505 620 550 850 515 C1035 488 1260 520 1768 500", "fill": "none", "stroke": True, "strokeW": 5, "opacity": 0.25},
    ]
    mid = [
        {"type": "polygon", "points": [320, 690, 1600, 690, 1710, 858, 210, 858], "fill": "paper", "stroke": True, "strokeW": 10},
        {"type": "line", "x1": 360, "y1": 748, "x2": 1550, "y2": 748, "stroke": True, "strokeW": 5},
        {"type": "rect", "x": 460, "y": 604, "w": 165, "h": 110, "rx": 6, "fill": "paper_deep", "stroke": True, "strokeW": 6},
        {"type": "ellipse", "cx": 1350, "cy": 628, "r": 94, "ry": 28, "fill": "lavender", "stroke": True, "strokeW": 6},
        {"type": "rect", "x": 820, "y": 625, "w": 90, "h": 58, "rx": 6, "fill": "yellow", "stroke": True, "strokeW": 5},
        {"type": "circle", "cx": 910, "cy": 634, "r": 18, "fill": "accent", "stroke": True, "strokeW": 4},
        {"type": "rect", "x": 1450, "y": 612, "w": 118, "h": 80, "rx": 6, "fill": "paper_deep", "stroke": True, "strokeW": 5},
    ]
    fg = [
        {"type": "polygon", "points": [130, 880, 1790, 880, 1920, 1080, 0, 1080], "fill": "paper_deep", "stroke": True, "strokeW": 10},
        {"type": "line", "x1": 130, "y1": 880, "x2": 1790, "y2": 880, "stroke": True, "strokeW": 14},
        {"type": "rect", "x": 72, "y": 818, "w": 150, "h": 260, "rx": 8, "fill": "paper", "stroke": True, "strokeW": 8},
        {"type": "line", "x1": 96, "y1": 874, "x2": 198, "y2": 874, "stroke": True, "strokeW": 5},
    ]
    return {
        "id": "lab",
        "backdrop": bg,
        "midground": mid,
        "foreground": fg,
        "text_zone": _text_zone(610, 22, 700, 112),
        "slots": {
            "presenter": _slot(940, 640, 1.45, 260),
            "board": _slot(490, 305, 0.92, 80),
            "sample_left": _slot(520, 620, 0.62, 220),
            "sample_right": _slot(1350, 610, 0.62, 220),
        },
    }


def build_street() -> Dict[str, Any]:
    bg = [
        {"type": "rect", "x": 0, "y": 610, "w": 1920, "h": 470, "fill": "paper_deep"},
        {"type": "rect", "x": 150, "y": 220, "w": 210, "h": 410, "fill": "paper_deep", "stroke": True, "strokeW": 7},
        {"type": "rect", "x": 390, "y": 150, "w": 250, "h": 480, "fill": "paper", "stroke": True, "strokeW": 7},
        {"type": "rect", "x": 1280, "y": 185, "w": 270, "h": 445, "fill": "paper", "stroke": True, "strokeW": 7},
        {"type": "rect", "x": 1580, "y": 260, "w": 190, "h": 370, "fill": "paper_deep", "stroke": True, "strokeW": 7},
        {"type": "path", "d": "M0 612 C360 562 575 640 900 585 C1220 530 1510 570 1920 515", "fill": "none", "stroke": True, "strokeW": 5, "opacity": 0.22},
    ]
    for bx in (205, 455, 535, 1340, 1430, 1635):
        for by in (275, 350, 425, 500):
            bg.append({"type": "rect", "x": bx, "y": by, "w": 42, "h": 50, "rx": 3, "fill": "white", "stroke": True, "strokeW": 3})
    mid = [
        {"type": "polygon", "points": [0, 690, 1920, 690, 1920, 920, 0, 920], "fill": "muted", "stroke": True, "strokeW": 8},
        {"type": "line", "x1": 0, "y1": 792, "x2": 1920, "y2": 792, "stroke": True, "strokeW": 5},
        {"type": "line", "x1": 120, "y1": 858, "x2": 420, "y2": 858, "stroke": True, "strokeW": 6, "opacity": 0.55},
        {"type": "line", "x1": 760, "y1": 858, "x2": 1060, "y2": 858, "stroke": True, "strokeW": 6, "opacity": 0.55},
        {"type": "line", "x1": 1390, "y1": 858, "x2": 1690, "y2": 858, "stroke": True, "strokeW": 6, "opacity": 0.55},
        {"type": "rect", "x": 1320, "y": 475, "w": 190, "h": 100, "rx": 6, "fill": "yellow", "stroke": True, "strokeW": 7},
        {"type": "line", "x1": 1415, "y1": 575, "x2": 1415, "y2": 710, "stroke": True, "strokeW": 9},
        {"type": "rect", "x": 580, "y": 625, "w": 210, "h": 84, "rx": 10, "fill": "blue", "stroke": True, "strokeW": 7},
        {"type": "circle", "cx": 630, "cy": 713, "r": 28, "fill": "paper", "stroke": True, "strokeW": 5},
        {"type": "circle", "cx": 742, "cy": 713, "r": 28, "fill": "paper", "stroke": True, "strokeW": 5},
    ]
    fg = [
        {"type": "line", "x1": 80, "y1": 918, "x2": 1840, "y2": 918, "stroke": True, "strokeW": 13},
        {"type": "line", "x1": 80, "y1": 980, "x2": 1840, "y2": 980, "stroke": True, "strokeW": 13},
        {"type": "rect", "x": 210, "y": 888, "w": 36, "h": 122, "rx": 5, "fill": "paper_deep", "stroke": True, "strokeW": 6},
        {"type": "rect", "x": 1668, "y": 888, "w": 36, "h": 122, "rx": 5, "fill": "paper_deep", "stroke": True, "strokeW": 6},
    ]
    return {
        "id": "street",
        "backdrop": bg,
        "midground": mid,
        "foreground": fg,
        "text_zone": _text_zone(675, 50, 570, 132),
        "slots": {
            "pedestrian_center": _slot(960, 730, 1.45, 270),
            "pedestrian_left": _slot(690, 745, 1.28, 245),
            "pedestrian_right": _slot(1230, 745, 1.28, 246),
            "sign": _slot(1415, 515, 0.7, 130),
        },
    }


def build_office() -> Dict[str, Any]:
    bg = [
        {"type": "rect", "x": 0, "y": 610, "w": 1920, "h": 470, "fill": "paper_deep"},
        {"type": "rect", "x": 175, "y": 130, "w": 1570, "h": 500, "rx": 8, "fill": "paper", "stroke": True, "strokeW": 8},
        {"type": "rect", "x": 1160, "y": 190, "w": 360, "h": 300, "rx": 8, "fill": "blue", "opacity": 0.35, "stroke": True, "strokeW": 7},
        {"type": "line", "x1": 1340, "y1": 190, "x2": 1340, "y2": 490, "stroke": True, "strokeW": 5},
        {"type": "line", "x1": 1160, "y1": 340, "x2": 1520, "y2": 340, "stroke": True, "strokeW": 5},
        {"type": "rect", "x": 370, "y": 240, "w": 420, "h": 245, "rx": 8, "fill": "paper_deep", "stroke": True, "strokeW": 7},
        {"type": "line", "x1": 410, "y1": 302, "x2": 740, "y2": 302, "stroke": True, "strokeW": 5, "opacity": 0.42},
        {"type": "line", "x1": 410, "y1": 366, "x2": 690, "y2": 366, "stroke": True, "strokeW": 5, "opacity": 0.42},
        {"type": "rect", "x": 850, "y": 184, "w": 150, "h": 190, "rx": 8, "fill": "paper_deep", "stroke": True, "strokeW": 6},
        {"type": "circle", "cx": 925, "cy": 268, "r": 42, "fill": "green", "stroke": True, "strokeW": 5},
    ]
    mid = [
        {"type": "polygon", "points": [555, 665, 1370, 665, 1520, 904, 410, 904], "fill": "paper", "stroke": True, "strokeW": 10},
        {"type": "rect", "x": 760, "y": 590, "w": 390, "h": 120, "rx": 7, "fill": "paper_deep", "stroke": True, "strokeW": 8},
        {"type": "line", "x1": 540, "y1": 756, "x2": 1390, "y2": 756, "stroke": True, "strokeW": 5},
        {"type": "rect", "x": 1210, "y": 645, "w": 118, "h": 72, "rx": 6, "fill": "yellow", "stroke": True, "strokeW": 5},
        {"type": "rect", "x": 600, "y": 637, "w": 95, "h": 78, "rx": 6, "fill": "white", "stroke": True, "strokeW": 5},
        {"type": "circle", "cx": 1018, "cy": 650, "r": 18, "fill": "accent", "stroke": True, "strokeW": 4},
    ]
    fg = [
        {"type": "polygon", "points": [300, 865, 1620, 865, 1740, 1080, 180, 1080], "fill": "paper_deep", "stroke": True, "strokeW": 10},
        {"type": "line", "x1": 300, "y1": 865, "x2": 1620, "y2": 865, "stroke": True, "strokeW": 14},
        {"type": "rect", "x": 74, "y": 830, "w": 180, "h": 250, "rx": 8, "fill": "paper", "stroke": True, "strokeW": 8},
        {"type": "rect", "x": 1660, "y": 850, "w": 154, "h": 230, "rx": 8, "fill": "paper", "stroke": True, "strokeW": 8},
    ]
    return {
        "id": "office",
        "backdrop": bg,
        "midground": mid,
        "foreground": fg,
        "text_zone": _text_zone(610, 20, 700, 96),
        "slots": {
            "person_behind_desk": _slot(960, 615, 1.32, 245),
            "person_left": _slot(610, 735, 1.25, 270),
            "person_right": _slot(1320, 735, 1.25, 271),
            "screen": _slot(580, 360, 0.88, 80),
        },
    }


def build_classroom() -> Dict[str, Any]:
    bg = [
        {"type": "rect", "x": 0, "y": 0, "w": 1920, "h": 625, "fill": "paper"},
        {"type": "rect", "x": 0, "y": 625, "w": 1920, "h": 455, "fill": "paper_deep"},
    ]
    mid = [
        {"type": "line", "x1": 130, "y1": 625, "x2": 1790, "y2": 625, "stroke": True, "strokeW": 8, "opacity": 0.55},
    ]
    fg = [
        {"type": "line", "x1": 130, "y1": 890, "x2": 1790, "y2": 890, "stroke": True, "strokeW": 10, "opacity": 0.65},
    ]
    return {
        "id": "classroom",
        "backdrop": bg,
        "midground": mid,
        "foreground": fg,
        "text_zone": _text_zone(610, 18, 700, 96),
        "slots": {
            "teacher": _slot(960, 565, 1.35, 235),
            "board": _slot(960, 300, 1.0, 80),
            "student_left": _slot(540, 710, 1.05, 265),
            "student_right": _slot(1375, 710, 1.05, 266),
        },
    }


def build_stage() -> Dict[str, Any]:
    bg = [
        {"type": "rect", "x": 0, "y": 600, "w": 1920, "h": 480, "fill": "paper_deep"},
        {"type": "rect", "x": 170, "y": 105, "w": 1580, "h": 565, "rx": 8, "fill": "accent", "opacity": 0.38, "stroke": True, "strokeW": 8},
        {"type": "line", "x1": 430, "y1": 115, "x2": 430, "y2": 660, "stroke": True, "strokeW": 5},
        {"type": "line", "x1": 740, "y1": 115, "x2": 740, "y2": 660, "stroke": True, "strokeW": 5},
        {"type": "line", "x1": 1180, "y1": 115, "x2": 1180, "y2": 660, "stroke": True, "strokeW": 5},
        {"type": "line", "x1": 1490, "y1": 115, "x2": 1490, "y2": 660, "stroke": True, "strokeW": 5},
        {"type": "polygon", "points": [690, 105, 540, 660, 840, 660], "fill": "yellow", "opacity": 0.2},
        {"type": "polygon", "points": [1230, 105, 1080, 660, 1380, 660], "fill": "yellow", "opacity": 0.2},
        {"type": "circle", "cx": 540, "cy": 152, "r": 34, "fill": "yellow", "stroke": True, "strokeW": 5},
        {"type": "circle", "cx": 1380, "cy": 152, "r": 34, "fill": "yellow", "stroke": True, "strokeW": 5},
        {"type": "line", "x1": 172, "y1": 300, "x2": 1748, "y2": 300, "stroke": True, "strokeW": 4, "opacity": 0.24},
    ]
    mid = [
        {"type": "rect", "x": 825, "y": 600, "w": 270, "h": 230, "rx": 8, "fill": "paper", "stroke": True, "strokeW": 9},
        {"type": "rect", "x": 300, "y": 740, "w": 1320, "h": 120, "rx": 8, "fill": "paper", "stroke": True, "strokeW": 10},
        {"type": "line", "x1": 340, "y1": 802, "x2": 1580, "y2": 802, "stroke": True, "strokeW": 5, "opacity": 0.38},
        {"type": "rect", "x": 470, "y": 675, "w": 130, "h": 74, "rx": 6, "fill": "blue", "stroke": True, "strokeW": 6},
        {"type": "rect", "x": 1320, "y": 675, "w": 130, "h": 74, "rx": 6, "fill": "accent", "stroke": True, "strokeW": 6},
    ]
    fg = [
        {"type": "polygon", "points": [0, 850, 1920, 850, 1920, 1080, 0, 1080], "fill": "paper_deep", "stroke": True, "strokeW": 10},
        {"type": "line", "x1": 0, "y1": 850, "x2": 1920, "y2": 850, "stroke": True, "strokeW": 14},
    ]
    return {
        "id": "stage",
        "backdrop": bg,
        "midground": mid,
        "foreground": fg,
        "text_zone": _text_zone(585, 18, 750, 80),
        "slots": {
            "speaker_podium": _slot(960, 586, 1.25, 260),
            "panelist_left": _slot(620, 715, 1.2, 245),
            "panelist_right": _slot(1300, 715, 1.2, 246),
        },
    }


def build_field() -> Dict[str, Any]:
    bg = [
        {"type": "rect", "x": 0, "y": 0, "w": 1920, "h": 455, "fill": "paper"},
        {"type": "rect", "x": 0, "y": 455, "w": 1920, "h": 625, "fill": "green", "opacity": 0.48},
        {"type": "rect", "x": 210, "y": 215, "w": 1500, "h": 190, "rx": 8, "fill": "paper_deep", "stroke": True, "strokeW": 8},
        {"type": "rect", "x": 330, "y": 96, "w": 190, "h": 70, "rx": 8, "fill": "yellow", "stroke": True, "strokeW": 6},
        {"type": "rect", "x": 1400, "y": 96, "w": 190, "h": 70, "rx": 8, "fill": "blue", "stroke": True, "strokeW": 6},
    ]
    for cx in range(290, 1640, 82):
        bg.append({"type": "circle", "cx": cx, "cy": 292, "r": 16, "fill": "muted", "opacity": 0.55})
        bg.append({"type": "circle", "cx": cx + 35, "cy": 350, "r": 14, "fill": "blue", "opacity": 0.42})
    mid = [
        {"type": "polygon", "points": [300, 625, 1620, 625, 1800, 940, 120, 940], "fill": "green", "stroke": True, "strokeW": 10},
        {"type": "line", "x1": 960, "y1": 625, "x2": 960, "y2": 940, "stroke": True, "strokeW": 6},
        {"type": "ellipse", "cx": 960, "cy": 770, "r": 185, "ry": 70, "fill": "none", "stroke": True, "strokeW": 6},
        {"type": "rect", "x": 1370, "y": 570, "w": 230, "h": 150, "rx": 4, "fill": "none", "stroke": True, "strokeW": 8},
        {"type": "line", "x1": 420, "y1": 682, "x2": 700, "y2": 682, "stroke": True, "strokeW": 5, "opacity": 0.46},
        {"type": "line", "x1": 1220, "y1": 842, "x2": 1510, "y2": 842, "stroke": True, "strokeW": 5, "opacity": 0.46},
        {"type": "circle", "cx": 910, "cy": 805, "r": 22, "fill": "white", "stroke": True, "strokeW": 5},
    ]
    fg = [
        {"type": "polygon", "points": [0, 900, 1920, 900, 1920, 1080, 0, 1080], "fill": "paper_deep", "stroke": True, "strokeW": 10},
        {"type": "line", "x1": 0, "y1": 900, "x2": 1920, "y2": 900, "stroke": True, "strokeW": 14},
    ]
    return {
        "id": "field",
        "backdrop": bg,
        "midground": mid,
        "foreground": fg,
        "text_zone": _text_zone(610, 42, 700, 122),
        "slots": {
            "player_left": _slot(690, 710, 1.35, 250),
            "player_right": _slot(1230, 710, 1.35, 251),
            "referee_center": _slot(960, 760, 1.45, 280),
            "goal": _slot(1485, 645, 0.75, 100),
        },
    }


def build_space() -> Dict[str, Any]:
    bg = [
        {"type": "rect", "x": 0, "y": 0, "w": 1920, "h": 625, "fill": "paper_deep"},
        {"type": "circle", "cx": 1380, "cy": 280, "r": 126, "fill": "lavender", "stroke": True, "strokeW": 8},
        {"type": "path", "d": "M1272 260 C1350 220 1428 220 1490 260", "fill": "none", "stroke": True, "strokeW": 5},
        {"type": "path", "d": "M1265 315 C1355 355 1430 350 1495 310", "fill": "none", "stroke": True, "strokeW": 5},
        {"type": "path", "d": "M120 520 C380 470 620 535 850 492 C1070 452 1300 520 1810 445", "fill": "none", "stroke": True, "strokeW": 5, "opacity": 0.26},
        {"type": "circle", "cx": 430, "cy": 462, "r": 42, "fill": "yellow", "stroke": True, "strokeW": 6},
    ]
    for i, (cx, cy) in enumerate(((240, 155), (410, 330), (620, 210), (850, 375), (1120, 170), (1610, 390), (1740, 180))):
        bg.append({"type": "circle", "cx": cx, "cy": cy, "r": 7 + (i % 3) * 2, "fill": "white", "stroke": True, "strokeW": 3})
    mid = [
        {"type": "polygon", "points": [0, 675, 1920, 560, 1920, 1080, 0, 1080], "fill": "paper", "stroke": True, "strokeW": 10},
        {"type": "path", "d": "M300 720 C620 640 980 660 1320 605 C1510 575 1690 590 1850 560", "fill": "none", "stroke": True, "strokeW": 5},
        {"type": "ellipse", "cx": 620, "cy": 760, "r": 135, "ry": 36, "fill": "paper_deep", "stroke": True, "strokeW": 5, "opacity": 0.75},
        {"type": "ellipse", "cx": 1240, "cy": 700, "r": 118, "ry": 30, "fill": "paper_deep", "stroke": True, "strokeW": 5, "opacity": 0.65},
    ]
    fg = [
        {"type": "polygon", "points": [0, 875, 1920, 800, 1920, 1080, 0, 1080], "fill": "paper_deep", "stroke": True, "strokeW": 10},
        {"type": "line", "x1": 0, "y1": 875, "x2": 1920, "y2": 800, "stroke": True, "strokeW": 14},
    ]
    return {
        "id": "space",
        "backdrop": bg,
        "midground": mid,
        "foreground": fg,
        "text_zone": _text_zone(565, 38, 700, 125),
        "slots": {
            "subject_center": _slot(960, 670, 1.35, 260),
            "planet": _slot(1380, 280, 0.85, 80),
            "object_left": _slot(560, 670, 0.9, 230),
        },
    }


def build_kitchen() -> Dict[str, Any]:
    bg = [
        {"type": "rect", "x": 0, "y": 620, "w": 1920, "h": 460, "fill": "paper_deep"},
        {"type": "rect", "x": 210, "y": 130, "w": 520, "h": 250, "rx": 8, "fill": "paper", "stroke": True, "strokeW": 8},
        {"type": "rect", "x": 1190, "y": 130, "w": 520, "h": 250, "rx": 8, "fill": "paper", "stroke": True, "strokeW": 8},
        {"type": "line", "x1": 470, "y1": 130, "x2": 470, "y2": 380, "stroke": True, "strokeW": 5},
        {"type": "line", "x1": 1450, "y1": 130, "x2": 1450, "y2": 380, "stroke": True, "strokeW": 5},
        {"type": "rect", "x": 280, "y": 520, "w": 1360, "h": 180, "rx": 8, "fill": "paper", "stroke": True, "strokeW": 10},
        {"type": "rect", "x": 815, "y": 425, "w": 290, "h": 120, "rx": 8, "fill": "paper_deep", "stroke": True, "strokeW": 7},
        {"type": "rect", "x": 330, "y": 190, "w": 86, "h": 92, "rx": 6, "fill": "yellow", "stroke": True, "strokeW": 5},
        {"type": "rect", "x": 1280, "y": 190, "w": 86, "h": 92, "rx": 6, "fill": "accent", "stroke": True, "strokeW": 5},
        {"type": "line", "x1": 300, "y1": 600, "x2": 1620, "y2": 600, "stroke": True, "strokeW": 5, "opacity": 0.35},
    ]
    mid = [
        {"type": "polygon", "points": [470, 680, 1450, 680, 1560, 855, 360, 855], "fill": "muted", "stroke": True, "strokeW": 10},
        {"type": "ellipse", "cx": 760, "cy": 695, "r": 95, "ry": 30, "fill": "paper_deep", "stroke": True, "strokeW": 6, "opacity": 0.55},
        {"type": "ellipse", "cx": 1160, "cy": 695, "r": 95, "ry": 30, "fill": "paper_deep", "stroke": True, "strokeW": 6, "opacity": 0.55},
        {"type": "rect", "x": 905, "y": 650, "w": 110, "h": 65, "rx": 7, "fill": "white", "stroke": True, "strokeW": 5},
        {"type": "circle", "cx": 1028, "cy": 685, "r": 18, "fill": "green", "stroke": True, "strokeW": 4},
    ]
    fg = [
        {"type": "polygon", "points": [170, 845, 1750, 845, 1920, 1080, 0, 1080], "fill": "paper_deep", "stroke": True, "strokeW": 10},
        {"type": "line", "x1": 170, "y1": 845, "x2": 1750, "y2": 845, "stroke": True, "strokeW": 14},
        {"type": "rect", "x": 82, "y": 788, "w": 145, "h": 292, "rx": 8, "fill": "paper", "stroke": True, "strokeW": 8},
    ]
    return {
        "id": "kitchen",
        "backdrop": bg,
        "midground": mid,
        "foreground": fg,
        "text_zone": _text_zone(760, 42, 400, 120),
        "slots": {
            "cook_center": _slot(960, 605, 1.38, 260),
            "item_left": _slot(760, 655, 0.62, 230),
            "item_right": _slot(1160, 655, 0.62, 231),
        },
    }


def _room_scene(
    env_id: str,
    backdrop: list,
    midground: list,
    foreground: list,
    slots: Dict[str, Dict[str, Any]],
    text_zone: Dict[str, float] | None = None,
) -> Dict[str, Any]:
    return {
        "id": env_id,
        "backdrop": backdrop,
        "midground": midground,
        "foreground": foreground,
        "text_zone": text_zone or _text_zone(610, 24, 700, 104),
        "slots": slots,
    }


def _interior_base() -> list:
    return [
        {"type": "rect", "x": 0, "y": 620, "w": 1920, "h": 460, "fill": "paper_deep"},
        {"type": "rect", "x": 180, "y": 130, "w": 1560, "h": 500, "rx": 8, "fill": "paper", "stroke": True, "strokeW": 8},
    ]


def _floor_occluder(y: int = 860) -> list:
    return [
        {"type": "polygon", "points": [180, y, 1740, y, 1920, 1080, 0, 1080], "fill": "paper_deep", "stroke": True, "strokeW": 10},
        {"type": "line", "x1": 180, "y1": y, "x2": 1740, "y2": y, "stroke": True, "strokeW": 14},
    ]


def _landscape_scene(env_id: str, backdrop: list, midground: list, slots: Dict[str, Dict[str, Any]], text_zone: Dict[str, float] | None = None) -> Dict[str, Any]:
    foreground = [
        {"type": "polygon", "points": [0, 890, 1920, 830, 1920, 1080, 0, 1080], "fill": "paper_deep", "stroke": True, "strokeW": 10},
        {"type": "line", "x1": 0, "y1": 890, "x2": 1920, "y2": 830, "stroke": True, "strokeW": 14},
    ]
    return _room_scene(env_id, backdrop, midground, foreground, slots, text_zone or _text_zone(610, 36, 700, 118))


def build_museum() -> Dict[str, Any]:
    bg = _interior_base()
    bg.extend(
        [
            {"type": "rect", "x": 235, "y": 205, "w": 230, "h": 220, "rx": 6, "fill": "white", "stroke": True, "strokeW": 7},
            {"type": "circle", "cx": 350, "cy": 315, "r": 54, "fill": "lavender", "stroke": True, "strokeW": 5},
            {"type": "rect", "x": 485, "y": 438, "w": 92, "h": 34, "rx": 4, "fill": "paper_deep", "stroke": True, "strokeW": 4},
            {"type": "rect", "x": 1345, "y": 205, "w": 250, "h": 220, "rx": 6, "fill": "white", "stroke": True, "strokeW": 7},
            {"type": "polygon", "points": [1470, 260, 1408, 375, 1532, 375], "fill": "muted", "stroke": True, "strokeW": 5},
            {"type": "rect", "x": 1278, "y": 438, "w": 92, "h": 34, "rx": 4, "fill": "paper_deep", "stroke": True, "strokeW": 4},
            {"type": "line", "x1": 270, "y1": 515, "x2": 1650, "y2": 515, "stroke": True, "strokeW": 5, "opacity": 0.32},
        ]
    )
    mid = [
        {"type": "rect", "x": 805, "y": 590, "w": 350, "h": 190, "rx": 8, "fill": "paper_deep", "stroke": True, "strokeW": 9},
        {"type": "rect", "x": 882, "y": 470, "w": 196, "h": 130, "rx": 8, "fill": "yellow", "stroke": True, "strokeW": 7},
        {"type": "ellipse", "cx": 980, "cy": 470, "r": 86, "ry": 28, "fill": "white", "stroke": True, "strokeW": 5},
        {"type": "line", "x1": 660, "y1": 760, "x2": 1260, "y2": 760, "stroke": True, "strokeW": 4, "opacity": 0.42},
    ]
    return _room_scene("museum", bg, mid, _floor_occluder(), {"visitor": _slot(960, 710, 1.32, 260), "exhibit": _slot(980, 535, 0.72, 180), "guide_left": _slot(630, 730, 1.2, 250), "visitor_right": _slot(1320, 730, 1.2, 251)}, _text_zone(700, 22, 520, 104))


def build_hospital() -> Dict[str, Any]:
    bg = _interior_base()
    bg.extend([
        {"type": "rect", "x": 270, "y": 232, "w": 360, "h": 235, "rx": 8, "fill": "white", "stroke": True, "strokeW": 7},
        {"type": "rect", "x": 415, "y": 270, "w": 72, "h": 160, "fill": "accent"},
        {"type": "rect", "x": 340, "y": 344, "w": 222, "h": 72, "fill": "accent"},
        {"type": "rect", "x": 1260, "y": 215, "w": 300, "h": 250, "rx": 8, "fill": "blue", "opacity": 0.28, "stroke": True, "strokeW": 7},
        {"type": "path", "d": "M1300 345 L1345 345 L1365 305 L1405 395 L1430 345 L1510 345", "fill": "none", "stroke": True, "strokeW": 7},
        {"type": "line", "x1": 720, "y1": 500, "x2": 1200, "y2": 500, "stroke": True, "strokeW": 5, "opacity": 0.35},
    ])
    mid = [
        {"type": "rect", "x": 640, "y": 648, "w": 720, "h": 150, "rx": 10, "fill": "white", "stroke": True, "strokeW": 9},
        {"type": "rect", "x": 730, "y": 604, "w": 245, "h": 68, "rx": 10, "fill": "paper_deep", "stroke": True, "strokeW": 6},
        {"type": "line", "x1": 700, "y1": 705, "x2": 1315, "y2": 705, "stroke": True, "strokeW": 5, "opacity": 0.4},
        {"type": "circle", "cx": 760, "cy": 800, "r": 28, "fill": "paper_deep", "stroke": True, "strokeW": 5},
        {"type": "circle", "cx": 1260, "cy": 800, "r": 28, "fill": "paper_deep", "stroke": True, "strokeW": 5},
        {"type": "rect", "x": 1415, "y": 560, "w": 85, "h": 165, "rx": 8, "fill": "paper", "stroke": True, "strokeW": 7},
        {"type": "circle", "cx": 1458, "cy": 610, "r": 22, "fill": "green", "stroke": True, "strokeW": 5},
    ]
    return _room_scene("hospital", bg, mid, _floor_occluder(), {"doctor": _slot(760, 675, 1.25, 260), "patient_bed": _slot(1030, 650, 0.92, 230), "nurse_right": _slot(1290, 710, 1.2, 270), "monitor": _slot(1410, 330, 0.62, 90)}, _text_zone(700, 22, 520, 104))


def build_factory_floor() -> Dict[str, Any]:
    bg = _interior_base()
    for x in (300, 585, 1320, 1580):
        bg.append({"type": "rect", "x": x, "y": 210, "w": 120, "h": 420, "fill": "muted", "stroke": True, "strokeW": 7})
    bg.extend(
        [
            {"type": "path", "d": "M280 330 L620 250 L940 330 L1260 250 L1600 330", "fill": "none", "stroke": True, "strokeW": 9},
            {"type": "rect", "x": 735, "y": 250, "w": 450, "h": 190, "rx": 8, "fill": "paper_deep", "stroke": True, "strokeW": 7},
            {"type": "circle", "cx": 820, "cy": 342, "r": 34, "fill": "green", "stroke": True, "strokeW": 5},
            {"type": "circle", "cx": 960, "cy": 342, "r": 34, "fill": "yellow", "stroke": True, "strokeW": 5},
            {"type": "circle", "cx": 1100, "cy": 342, "r": 34, "fill": "accent", "stroke": True, "strokeW": 5},
        ]
    )
    mid = [
        {"type": "rect", "x": 330, "y": 690, "w": 1260, "h": 105, "rx": 8, "fill": "paper", "stroke": True, "strokeW": 9},
        {"type": "line", "x1": 350, "y1": 742, "x2": 1570, "y2": 742, "stroke": True, "strokeW": 6},
        {"type": "circle", "cx": 510, "cy": 742, "r": 42, "fill": "blue", "stroke": True, "strokeW": 6},
        {"type": "circle", "cx": 960, "cy": 742, "r": 42, "fill": "yellow", "stroke": True, "strokeW": 6},
        {"type": "circle", "cx": 1410, "cy": 742, "r": 42, "fill": "green", "stroke": True, "strokeW": 6},
        {"type": "rect", "x": 455, "y": 575, "w": 140, "h": 115, "rx": 8, "fill": "blue", "stroke": True, "strokeW": 7},
        {"type": "rect", "x": 1340, "y": 575, "w": 140, "h": 115, "rx": 8, "fill": "green", "stroke": True, "strokeW": 7},
    ]
    return _room_scene("factory_floor", bg, mid, _floor_occluder(), {"worker_center": _slot(960, 650, 1.28, 260), "machine_left": _slot(520, 690, 0.82, 220), "machine_right": _slot(1410, 690, 0.82, 221), "supervisor": _slot(1260, 705, 1.18, 270)}, _text_zone(700, 22, 520, 104))


def build_beach() -> Dict[str, Any]:
    bg = [
        {"type": "rect", "x": 0, "y": 0, "w": 1920, "h": 560, "fill": "paper"},
        {"type": "rect", "x": 0, "y": 560, "w": 1920, "h": 520, "fill": "yellow", "opacity": 0.42},
        {"type": "circle", "cx": 1540, "cy": 170, "r": 82, "fill": "yellow", "stroke": True, "strokeW": 7},
        {"type": "path", "d": "M0 565 C360 515 650 620 960 565 C1260 515 1540 620 1920 565", "fill": "blue", "opacity": 0.18, "stroke": True, "strokeW": 8},
        {"type": "path", "d": "M120 420 C420 360 610 450 820 405", "fill": "none", "stroke": True, "strokeW": 5, "opacity": 0.38},
        {"type": "path", "d": "M1120 430 C1380 370 1550 455 1760 408", "fill": "none", "stroke": True, "strokeW": 5, "opacity": 0.38},
    ]
    mid = [
        {"type": "path", "d": "M0 680 C360 620 650 740 960 680 C1260 620 1540 740 1920 680", "fill": "none", "stroke": True, "strokeW": 8},
        {"type": "path", "d": "M0 760 C360 710 650 810 960 760 C1260 710 1540 810 1920 760", "fill": "none", "stroke": True, "strokeW": 5, "opacity": 0.42},
        {"type": "polygon", "points": [420, 625, 595, 625, 520, 492], "fill": "accent", "stroke": True, "strokeW": 7},
        {"type": "line", "x1": 520, "y1": 625, "x2": 520, "y2": 755, "stroke": True, "strokeW": 7},
        {"type": "rect", "x": 1180, "y": 745, "w": 120, "h": 52, "rx": 10, "fill": "blue", "stroke": True, "strokeW": 6},
        {"type": "circle", "cx": 700, "cy": 766, "r": 34, "fill": "green", "stroke": True, "strokeW": 5},
    ]
    return _landscape_scene("beach", bg, mid, {"beachgoer": _slot(960, 725, 1.3, 260), "umbrella": _slot(520, 610, 0.78, 170), "item_left": _slot(690, 760, 0.55, 240), "item_right": _slot(1240, 760, 0.55, 241)}, _text_zone(700, 22, 520, 104))


def build_forest() -> Dict[str, Any]:
    bg = [{"type": "rect", "x": 0, "y": 0, "w": 1920, "h": 1080, "fill": "paper"}]
    for x, h, role in ((180, 360, "green"), (360, 430, "muted"), (1420, 410, "green"), (1640, 350, "muted"), (1260, 300, "green")):
        bg.append({"type": "rect", "x": x, "y": 625 - h, "w": 54, "h": h + 180, "fill": "paper_deep", "stroke": True, "strokeW": 6})
        bg.append({"type": "circle", "cx": x + 27, "cy": 600 - h, "r": 120, "fill": role, "stroke": True, "strokeW": 7})
    mid = [{"type": "polygon", "points": [0, 690, 1920, 610, 1920, 930, 0, 930], "fill": "green", "opacity": 0.55, "stroke": True, "strokeW": 9}]
    return _landscape_scene("forest", bg, mid, {"hiker_center": _slot(960, 700, 1.28, 260), "tree_left": _slot(365, 575, 0.82, 150), "tree_right": _slot(1435, 570, 0.82, 151), "trail_item": _slot(1180, 745, 0.55, 240)})


def build_mountain() -> Dict[str, Any]:
    bg = [{"type": "rect", "x": 0, "y": 0, "w": 1920, "h": 1080, "fill": "paper"}, {"type": "polygon", "points": [80, 690, 520, 230, 920, 690], "fill": "muted", "stroke": True, "strokeW": 8}, {"type": "polygon", "points": [680, 690, 1140, 170, 1640, 690], "fill": "lavender", "stroke": True, "strokeW": 8}, {"type": "polygon", "points": [1130, 690, 1580, 280, 1900, 690], "fill": "muted", "stroke": True, "strokeW": 8}]
    mid = [{"type": "polygon", "points": [0, 720, 1920, 640, 1920, 940, 0, 940], "fill": "green", "opacity": 0.48, "stroke": True, "strokeW": 9}]
    return _landscape_scene("mountain", bg, mid, {"climber": _slot(960, 705, 1.25, 260), "peak": _slot(1140, 360, 0.7, 110), "guide_left": _slot(700, 740, 1.05, 245), "pack_right": _slot(1220, 760, 0.55, 240)})


def build_desert() -> Dict[str, Any]:
    bg = [{"type": "rect", "x": 0, "y": 0, "w": 1920, "h": 1080, "fill": "paper"}, {"type": "circle", "cx": 1450, "cy": 180, "r": 78, "fill": "yellow", "stroke": True, "strokeW": 7}]
    mid = [{"type": "path", "d": "M0 695 C380 575 700 760 980 655 C1270 550 1540 730 1920 625", "fill": "none", "stroke": True, "strokeW": 9}, {"type": "path", "d": "M520 725 L520 560 M520 610 C440 600 420 525 450 475 M520 625 C610 600 650 530 620 490", "fill": "none", "stroke": True, "strokeW": 11}]
    return _landscape_scene("desert", bg, mid, {"traveler": _slot(960, 720, 1.25, 260), "cactus": _slot(520, 625, 0.75, 170), "dune_left": _slot(650, 760, 0.55, 220), "dune_right": _slot(1280, 730, 0.55, 221)})


def build_restaurant() -> Dict[str, Any]:
    bg = _interior_base()
    bg.extend([{"type": "rect", "x": 360, "y": 210, "w": 310, "h": 180, "rx": 6, "fill": "paper_deep", "stroke": True, "strokeW": 7}, {"type": "rect", "x": 1260, "y": 210, "w": 310, "h": 180, "rx": 6, "fill": "paper_deep", "stroke": True, "strokeW": 7}])
    mid = [{"type": "ellipse", "cx": 960, "cy": 690, "r": 315, "ry": 90, "fill": "white", "stroke": True, "strokeW": 9}, {"type": "rect", "x": 880, "y": 685, "w": 160, "h": 100, "fill": "paper", "stroke": True, "strokeW": 6}]
    return _room_scene("restaurant", bg, mid, _floor_occluder(), {"server": _slot(960, 615, 1.25, 255), "diner_left": _slot(690, 725, 1.08, 270), "diner_right": _slot(1260, 725, 1.08, 271), "table_center": _slot(960, 690, 0.65, 230)})


def build_gym() -> Dict[str, Any]:
    bg = _interior_base()
    bg.extend([{"type": "rect", "x": 330, "y": 220, "w": 320, "h": 250, "rx": 8, "fill": "blue", "opacity": 0.32, "stroke": True, "strokeW": 7}, {"type": "line", "x1": 1180, "y1": 335, "x2": 1580, "y2": 335, "stroke": True, "strokeW": 13}, {"type": "circle", "cx": 1180, "cy": 335, "r": 46, "fill": "muted", "stroke": True, "strokeW": 7}, {"type": "circle", "cx": 1580, "cy": 335, "r": 46, "fill": "muted", "stroke": True, "strokeW": 7}])
    mid = [{"type": "rect", "x": 470, "y": 705, "w": 980, "h": 95, "rx": 8, "fill": "green", "opacity": 0.5, "stroke": True, "strokeW": 8}]
    return _room_scene("gym", bg, mid, _floor_occluder(), {"athlete_center": _slot(960, 675, 1.35, 260), "trainer_left": _slot(700, 725, 1.15, 250), "equipment_right": _slot(1340, 705, 0.78, 220), "mat": _slot(960, 730, 0.58, 210)})


def build_library() -> Dict[str, Any]:
    bg = _interior_base()
    mid = [{"type": "polygon", "points": [680, 660, 1240, 660, 1340, 820, 580, 820], "fill": "paper", "stroke": True, "strokeW": 9}]
    return _room_scene("library", bg, mid, _floor_occluder(), {"reader": _slot(960, 640, 1.22, 260), "shelf_left": _slot(450, 500, 0.7, 130), "shelf_right": _slot(1440, 500, 0.7, 131), "book_table": _slot(960, 700, 0.55, 230)})


def build_bank() -> Dict[str, Any]:
    bg = _interior_base()
    bg.extend([{"type": "rect", "x": 360, "y": 240, "w": 380, "h": 260, "rx": 8, "fill": "paper_deep", "stroke": True, "strokeW": 7}, {"type": "circle", "cx": 550, "cy": 370, "r": 70, "fill": "muted", "stroke": True, "strokeW": 7}, {"type": "rect", "x": 1230, "y": 230, "w": 320, "h": 240, "rx": 8, "fill": "white", "stroke": True, "strokeW": 7}])
    mid = [{"type": "rect", "x": 500, "y": 650, "w": 980, "h": 155, "rx": 8, "fill": "paper", "stroke": True, "strokeW": 9}, {"type": "line", "x1": 760, "y1": 650, "x2": 760, "y2": 805, "stroke": True, "strokeW": 6}]
    return _room_scene("bank", bg, mid, _floor_occluder(), {"teller": _slot(760, 625, 1.18, 250), "customer": _slot(1160, 720, 1.25, 270), "vault": _slot(550, 370, 0.68, 100), "counter": _slot(960, 690, 0.55, 230)})


def build_airport() -> Dict[str, Any]:
    bg = _interior_base()
    bg.extend([{"type": "rect", "x": 330, "y": 210, "w": 1180, "h": 240, "rx": 8, "fill": "blue", "opacity": 0.28, "stroke": True, "strokeW": 7}, {"type": "line", "x1": 625, "y1": 210, "x2": 625, "y2": 450, "stroke": True, "strokeW": 5}, {"type": "line", "x1": 920, "y1": 210, "x2": 920, "y2": 450, "stroke": True, "strokeW": 5}, {"type": "line", "x1": 1215, "y1": 210, "x2": 1215, "y2": 450, "stroke": True, "strokeW": 5}])
    mid = [{"type": "rect", "x": 380, "y": 700, "w": 1180, "h": 80, "rx": 8, "fill": "muted", "stroke": True, "strokeW": 8}, {"type": "polygon", "points": [1180, 560, 1500, 640, 1180, 720], "fill": "white", "stroke": True, "strokeW": 8}]
    return _room_scene("airport", bg, mid, _floor_occluder(), {"traveler": _slot(820, 700, 1.25, 260), "agent_right": _slot(1260, 700, 1.15, 261), "plane_window": _slot(1320, 625, 0.75, 170), "luggage": _slot(650, 780, 0.58, 245)})


def build_boardroom() -> Dict[str, Any]:
    bg = _interior_base()
    bg.extend([{"type": "rect", "x": 730, "y": 205, "w": 470, "h": 280, "rx": 8, "fill": "blue", "opacity": 0.34, "stroke": True, "strokeW": 7}, {"type": "path", "d": "M790 410 L900 330 L1020 375 L1160 275", "fill": "none", "stroke": True, "strokeW": 8}])
    mid = [{"type": "polygon", "points": [470, 665, 1450, 665, 1580, 870, 340, 870], "fill": "paper", "stroke": True, "strokeW": 10}]
    return _room_scene("boardroom", bg, mid, _floor_occluder(), {"presenter": _slot(960, 600, 1.2, 250), "executive_left": _slot(650, 740, 1.1, 270), "executive_right": _slot(1320, 740, 1.1, 271), "screen": _slot(965, 340, 0.82, 90)})


def build_theater() -> Dict[str, Any]:
    bg = _interior_base()
    bg.extend([{"type": "rect", "x": 440, "y": 190, "w": 1040, "h": 430, "rx": 8, "fill": "accent", "opacity": 0.4, "stroke": True, "strokeW": 8}, {"type": "polygon", "points": [800, 190, 680, 620, 920, 620], "fill": "yellow", "opacity": 0.22}, {"type": "polygon", "points": [1120, 190, 1000, 620, 1240, 620], "fill": "yellow", "opacity": 0.22}])
    mid = [{"type": "rect", "x": 520, "y": 690, "w": 880, "h": 115, "rx": 8, "fill": "paper", "stroke": True, "strokeW": 9}]
    return _room_scene("theater", bg, mid, _floor_occluder(), {"performer": _slot(960, 610, 1.35, 260), "audience_left": _slot(690, 760, 1.05, 240), "audience_right": _slot(1260, 760, 1.05, 241), "prop_center": _slot(960, 700, 0.55, 230)})


def build_news_studio() -> Dict[str, Any]:
    return build_newsroom() | {"id": "news_studio", "slots": {"host_center": _slot(960, 704, 1.45, 260), "guest_left": _slot(700, 740, 1.18, 250), "screen": _slot(960, 360, 0.95, 80), "desk_props": _slot(1060, 774, 0.55, 310)}}


def build_podcast_studio() -> Dict[str, Any]:
    bg = _interior_base()
    bg.extend([{"type": "rect", "x": 360, "y": 230, "w": 310, "h": 250, "rx": 8, "fill": "muted", "stroke": True, "strokeW": 7}, {"type": "rect", "x": 1260, "y": 230, "w": 310, "h": 250, "rx": 8, "fill": "muted", "stroke": True, "strokeW": 7}])
    mid = [{"type": "ellipse", "cx": 960, "cy": 690, "r": 355, "ry": 98, "fill": "paper", "stroke": True, "strokeW": 9}, {"type": "line", "x1": 815, "y1": 620, "x2": 890, "y2": 690, "stroke": True, "strokeW": 9}, {"type": "line", "x1": 1120, "y1": 620, "x2": 1045, "y2": 690, "stroke": True, "strokeW": 9}]
    return _room_scene("podcast_studio", bg, mid, _floor_occluder(), {"host_left": _slot(760, 660, 1.18, 260), "guest_right": _slot(1220, 660, 1.18, 261), "mic_left": _slot(850, 635, 0.5, 220), "mic_right": _slot(1080, 635, 0.5, 221)})


def build_voting_booth() -> Dict[str, Any]:
    bg = _interior_base()
    bg.extend([{"type": "rect", "x": 460, "y": 225, "w": 290, "h": 410, "rx": 8, "fill": "blue", "opacity": 0.35, "stroke": True, "strokeW": 8}, {"type": "rect", "x": 1210, "y": 225, "w": 290, "h": 410, "rx": 8, "fill": "accent", "opacity": 0.32, "stroke": True, "strokeW": 8}, {"type": "rect", "x": 850, "y": 300, "w": 220, "h": 150, "rx": 6, "fill": "white", "stroke": True, "strokeW": 7}])
    mid = [{"type": "rect", "x": 785, "y": 650, "w": 350, "h": 160, "rx": 8, "fill": "paper", "stroke": True, "strokeW": 9}, {"type": "rect", "x": 850, "y": 595, "w": 220, "h": 75, "rx": 5, "fill": "paper_deep", "stroke": True, "strokeW": 7}]
    return _room_scene("voting_booth", bg, mid, _floor_occluder(), {"voter": _slot(960, 650, 1.25, 260), "booth_left": _slot(605, 520, 0.72, 160), "booth_right": _slot(1355, 520, 0.72, 161), "ballot_box": _slot(960, 660, 0.62, 220)})


def build_farm() -> Dict[str, Any]:
    bg = [{"type": "rect", "x": 0, "y": 0, "w": 1920, "h": 1080, "fill": "paper"}, {"type": "rect", "x": 0, "y": 545, "w": 1920, "h": 535, "fill": "green", "opacity": 0.45}, {"type": "polygon", "points": [330, 610, 540, 430, 750, 610], "fill": "accent", "stroke": True, "strokeW": 8}, {"type": "rect", "x": 390, "y": 610, "w": 300, "h": 190, "fill": "paper_deep", "stroke": True, "strokeW": 8}]
    mid = [{"type": "line", "x1": 0, "y1": 720, "x2": 1920, "y2": 650, "stroke": True, "strokeW": 8}, {"type": "line", "x1": 0, "y1": 805, "x2": 1920, "y2": 735, "stroke": True, "strokeW": 8}]
    return _landscape_scene("farm", bg, mid, {"farmer": _slot(960, 720, 1.25, 260), "barn": _slot(540, 610, 0.8, 150), "crop_left": _slot(700, 775, 0.55, 220), "crop_right": _slot(1240, 745, 0.55, 221)})


def build_lab_clean() -> Dict[str, Any]:
    env = build_lab()
    env["id"] = "lab_clean"
    env["text_zone"] = _text_zone(700, 22, 520, 104)
    env["slots"] = {"scientist": _slot(920, 635, 1.35, 260), "clean_bench": _slot(960, 675, 0.62, 220), "sample_left": _slot(650, 635, 0.58, 221), "sample_right": _slot(1240, 635, 0.58, 222)}
    return env


def build_city_rooftop() -> Dict[str, Any]:
    bg = [{"type": "rect", "x": 0, "y": 0, "w": 1920, "h": 1080, "fill": "paper"}]
    for x, h, role in ((120, 380, "paper_deep"), (360, 480, "muted"), (1290, 430, "paper_deep"), (1540, 520, "muted")):
        bg.append({"type": "rect", "x": x, "y": 680 - h, "w": 210, "h": h, "fill": role, "stroke": True, "strokeW": 7})
        for y in range(720 - h, 650, 80):
            bg.append({"type": "rect", "x": x + 35, "y": y, "w": 48, "h": 42, "fill": "white", "stroke": True, "strokeW": 3})
    mid = [{"type": "rect", "x": 260, "y": 690, "w": 1400, "h": 150, "rx": 8, "fill": "paper", "stroke": True, "strokeW": 10}, {"type": "line", "x1": 260, "y1": 650, "x2": 1660, "y2": 650, "stroke": True, "strokeW": 10}]
    return _landscape_scene("city_rooftop", bg, mid, {"subject_center": _slot(960, 685, 1.3, 260), "city_left": _slot(465, 520, 0.72, 130), "city_right": _slot(1395, 520, 0.72, 131), "roof_prop": _slot(1210, 740, 0.55, 240)})


ENVIRONMENT_BUILDERS: Dict[str, Callable[[], Dict[str, Any]]] = {
    "arena": build_arena,
    "courtroom": build_courtroom,
    "newsroom": build_newsroom,
    "lab": build_lab,
    "street": build_street,
    "office": build_office,
    "classroom": build_classroom,
    "stage": build_stage,
    "field": build_field,
    "space": build_space,
    "kitchen": build_kitchen,
    "museum": build_museum,
    "hospital": build_hospital,
    "factory_floor": build_factory_floor,
    "beach": build_beach,
    "forest": build_forest,
    "mountain": build_mountain,
    "desert": build_desert,
    "restaurant": build_restaurant,
    "gym": build_gym,
    "library": build_library,
    "bank": build_bank,
    "airport": build_airport,
    "boardroom": build_boardroom,
    "theater": build_theater,
    "news_studio": build_news_studio,
    "podcast_studio": build_podcast_studio,
    "voting_booth": build_voting_booth,
    "farm": build_farm,
    "lab_clean": build_lab_clean,
    "city_rooftop": build_city_rooftop,
}

ENVIRONMENT_VARIANTS = frozenset(["day", "night", "crowded", "empty"])
PREFERRED_ENVIRONMENT_SLOTS = {
    "arena": ["red_corner", "blue_corner", "referee_center"],
    "courtroom": ["defendant_left", "lawyer_right", "witness_stand", "judge_bench"],
    "newsroom": ["anchor_center", "screen", "desk_props"],
    "lab": ["presenter", "board", "sample_left", "sample_right"],
    "street": ["pedestrian_center", "pedestrian_left", "pedestrian_right", "sign"],
    "office": ["person_behind_desk", "person_left", "person_right", "screen"],
    "classroom": ["teacher", "board", "student_left", "student_right"],
    "stage": ["speaker_podium", "panelist_left", "panelist_right"],
    "field": ["player_left", "player_right", "referee_center", "goal"],
    "space": ["subject_center", "planet", "object_left"],
    "kitchen": ["cook_center", "item_left", "item_right"],
    "museum": ["visitor", "exhibit", "guide_left", "visitor_right"],
    "hospital": ["doctor", "patient_bed", "nurse_right", "monitor"],
    "factory_floor": ["worker_center", "machine_left", "machine_right", "supervisor"],
    "beach": ["beachgoer", "umbrella", "item_left", "item_right"],
    "forest": ["hiker_center", "tree_left", "tree_right", "trail_item"],
    "mountain": ["climber", "peak", "guide_left", "pack_right"],
    "desert": ["traveler", "cactus", "dune_left", "dune_right"],
    "restaurant": ["server", "diner_left", "diner_right", "table_center"],
    "gym": ["athlete_center", "trainer_left", "equipment_right", "mat"],
    "library": ["reader", "shelf_left", "shelf_right", "book_table"],
    "bank": ["teller", "customer", "vault", "counter"],
    "airport": ["traveler", "agent_right", "plane_window", "luggage"],
    "boardroom": ["presenter", "executive_left", "executive_right", "screen"],
    "theater": ["performer", "audience_left", "audience_right", "prop_center"],
    "news_studio": ["host_center", "guest_left", "screen", "desk_props"],
    "podcast_studio": ["host_left", "guest_right", "mic_left", "mic_right"],
    "voting_booth": ["voter", "booth_left", "booth_right", "ballot_box"],
    "farm": ["farmer", "barn", "crop_left", "crop_right"],
    "lab_clean": ["scientist", "clean_bench", "sample_left", "sample_right"],
    "city_rooftop": ["subject_center", "city_left", "city_right", "roof_prop"],
}

ENVIRONMENT_SET_PROPS = {
    "lab": [
        {"asset": "microscope", "x": 430, "y": 672, "scale": 0.52, "z": 118},
        {"asset": "flask", "x": 660, "y": 696, "scale": 0.42, "z": 122},
        {"asset": "beaker", "x": 1450, "y": 696, "scale": 0.42, "z": 123},
    ],
    "lab_clean": [
        {"asset": "microscope", "x": 450, "y": 666, "scale": 0.5, "z": 118},
        {"asset": "flask", "x": 700, "y": 690, "scale": 0.4, "z": 122},
        {"asset": "beaker", "x": 1440, "y": 690, "scale": 0.4, "z": 123},
    ],
    "library": [
        {"asset": "bookshelf", "x": 320, "y": 610, "scale": 0.9, "z": 92},
        {"asset": "bookshelf", "x": 1600, "y": 610, "scale": 0.9, "z": 93},
        {"asset": "library_ladder", "x": 1365, "y": 685, "scale": 0.62, "z": 130},
    ],
    "classroom": [
        {"asset": "chalkboard", "x": 960, "y": 255, "scale": 0.82, "z": 88},
        {"asset": "globe", "x": 450, "y": 690, "scale": 0.52, "z": 124},
        {"asset": "school_desk", "x": 1470, "y": 760, "scale": 0.68, "z": 136},
    ],
    "hospital": [
        {"asset": "hospital_bed", "x": 1360, "y": 665, "scale": 0.78, "z": 132},
        {"asset": "iv_stand", "x": 560, "y": 625, "scale": 0.58, "z": 126},
    ],
    "office": [
        {"asset": "office_chair", "x": 470, "y": 730, "scale": 0.56, "z": 132},
        {"asset": "filing_cabinet", "x": 1490, "y": 660, "scale": 0.62, "z": 118},
    ],
    "boardroom": [
        {"asset": "framed_painting", "x": 960, "y": 250, "scale": 0.6, "z": 86},
        {"asset": "office_chair", "x": 410, "y": 735, "scale": 0.54, "z": 132},
    ],
    "bank": [
        {"asset": "vault_door", "x": 1480, "y": 535, "scale": 0.78, "z": 106},
        {"asset": "filing_cabinet", "x": 430, "y": 670, "scale": 0.58, "z": 118},
    ],
    "street": [
        {"asset": "traffic_light", "x": 360, "y": 450, "scale": 0.64, "z": 104},
        {"asset": "fire_hydrant", "x": 620, "y": 815, "scale": 0.42, "z": 148},
        {"asset": "park_bench", "x": 1460, "y": 790, "scale": 0.72, "z": 138},
    ],
    "city_rooftop": [
        {"asset": "park_bench", "x": 420, "y": 765, "scale": 0.68, "z": 132},
        {"asset": "street_sign", "x": 1500, "y": 620, "scale": 0.56, "z": 116},
    ],
    "space": [
        {"asset": "ringed_planet", "x": 1690, "y": 250, "scale": 0.68, "z": 88},
        {"asset": "rocket", "x": 430, "y": 610, "scale": 0.68, "z": 116},
        {"asset": "telescope", "x": 1450, "y": 760, "scale": 0.58, "z": 134},
    ],
    "desert": [
        {"asset": "cactus_tall", "x": 430, "y": 690, "scale": 0.8, "z": 118},
    ],
    "forest": [
        {"asset": "pine_tree", "x": 380, "y": 610, "scale": 0.9, "z": 96},
        {"asset": "tent", "x": 1470, "y": 780, "scale": 0.72, "z": 136},
    ],
    "beach": [
        {"asset": "beach_umbrella", "x": 440, "y": 640, "scale": 0.78, "z": 116},
        {"asset": "palm_tree", "x": 1510, "y": 600, "scale": 0.9, "z": 104},
    ],
    "farm": [
        {"asset": "barn", "x": 380, "y": 575, "scale": 0.86, "z": 96},
        {"asset": "tractor", "x": 1480, "y": 760, "scale": 0.72, "z": 136},
    ],
    "factory_floor": [
        {"asset": "robot_arm", "x": 410, "y": 660, "scale": 0.72, "z": 128},
    ],
    "theater": [
        {"asset": "theater_curtain", "x": 960, "y": 350, "scale": 0.92, "z": 84},
    ],
    "restaurant": [
        {"asset": "dining_table", "x": 420, "y": 745, "scale": 0.68, "z": 132},
    ],
    "gym": [
        {"asset": "dumbbell", "x": 1450, "y": 795, "scale": 0.52, "z": 142},
    ],
    "kitchen": [
        {"asset": "stove", "x": 430, "y": 705, "scale": 0.62, "z": 124},
        {"asset": "refrigerator", "x": 1490, "y": 610, "scale": 0.72, "z": 110},
    ],
    "museum": [
        {"asset": "framed_painting", "x": 1420, "y": 275, "scale": 0.62, "z": 86},
    ],
}


def load_generated_environments() -> Dict[str, Any]:
    global _GENERATED_ENVIRONMENTS_CACHE
    if _GENERATED_ENVIRONMENTS_CACHE is not None:
        return _GENERATED_ENVIRONMENTS_CACHE
    try:
        with open(GENERATED_ENVIRONMENTS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}
    _GENERATED_ENVIRONMENTS_CACHE = {
        str(env_id).strip(): env
        for env_id, env in data.items()
        if str(env_id).strip() and isinstance(env, dict)
    }
    return _GENERATED_ENVIRONMENTS_CACHE


def reset_generated_cache() -> None:
    global _GENERATED_ENVIRONMENTS_CACHE, ENVIRONMENTS
    _GENERATED_ENVIRONMENTS_CACHE = None
    ENVIRONMENTS = frozenset(ENVIRONMENT_BUILDERS.keys()) | _generated_environment_ids()


def _generated_environment_ids() -> frozenset[str]:
    return frozenset(load_generated_environments().keys())


def _generated_slot(slot: Dict[str, Any]) -> Dict[str, Any]:
    x = float(slot.get("x", 960))
    y = float(slot.get("y", 720))
    z = int(slot.get("z", 250))
    out = {
        "x": x,
        "y": y,
        "scale": float(slot.get("scale", 1.0)),
        "z": z,
        "depth": slot.get("depth") or _slot_depth(y, z),
    }
    if slot.get("role"):
        out["role"] = str(slot.get("role"))
    return out


def _build_generated_environment(env_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    slots = data.get("slots") if isinstance(data.get("slots"), dict) else {}
    backdrop = copy.deepcopy(data.get("backdrop") or [])
    env = {
        "id": env_id,
        "description": str(data.get("description") or "").strip(),
        "backdrop": backdrop,
        "midground": copy.deepcopy(data.get("midground") or []),
        "foreground": copy.deepcopy(data.get("foreground") or []),
        "set_props": copy.deepcopy(data.get("set_props") or []),
        "slots": {str(name): _generated_slot(slot) for name, slot in slots.items() if isinstance(slot, dict)},
        "text_zone": copy.deepcopy(data.get("text_zone") or _text_zone(120, 90, 760, 150)),
        "shapeSpace": "frame",
        "generated": True,
    }
    return _document_slots(env)


ENVIRONMENTS = frozenset(ENVIRONMENT_BUILDERS.keys()) | _generated_environment_ids()


def default_environment_slots(environment_id: str) -> list[str]:
    env_id, _ = _parse_environment_ref(environment_id)
    generated = load_generated_environments().get(env_id)
    if isinstance(generated, dict) and isinstance(generated.get("slots"), dict):
        return list(generated["slots"].keys())
    preferred = PREFERRED_ENVIRONMENT_SLOTS.get(env_id)
    if preferred:
        return list(preferred)
    builder = ENVIRONMENT_BUILDERS.get(env_id)
    if builder is None:
        return []
    return list((builder().get("slots") or {}).keys())


def all_environment_slot_ids() -> frozenset[str]:
    slots = set()
    for env_id in ENVIRONMENT_BUILDERS:
        slots.update(default_environment_slots(env_id))
        builder = ENVIRONMENT_BUILDERS.get(env_id)
        if builder:
            slots.update((builder().get("slots") or {}).keys())
    for env_id in load_generated_environments():
        slots.update(default_environment_slots(env_id))
    return frozenset(slots)


def _apply_set_props(env: Dict[str, Any]) -> None:
    env_id = str(env.get("id") or "")
    props = ENVIRONMENT_SET_PROPS.get(env_id)
    if props:
        env["set_props"] = copy.deepcopy(props)


def get_environment(environment_id: str, variant: str | None = None) -> Dict[str, Any]:
    env_id, env_variant = _parse_environment_ref(environment_id, variant)
    builder = ENVIRONMENT_BUILDERS.get(env_id)
    if builder is None:
        generated = load_generated_environments().get(env_id)
        if not isinstance(generated, dict):
            raise KeyError(environment_id)
        return _clamp_safe_area_centers(_build_generated_environment(env_id, generated))
    env = copy.deepcopy(builder())
    _apply_set_props(env)
    return _clamp_safe_area_centers(_document_slots(_apply_variant(_enrich_environment(env), env_variant)))


def has_environment(environment_id: str) -> bool:
    env_id, _ = _parse_environment_ref(environment_id)
    return env_id in ENVIRONMENT_BUILDERS or env_id in load_generated_environments()


def environment_slot_docs(environment_id: str, variant: str | None = None) -> Dict[str, Dict[str, Any]]:
    return get_environment(environment_id, variant=variant).get("slot_docs", {})


def get_vertical_environment(environment_id: str, variant: str | None = None) -> Dict[str, Any]:
    return _verticalize_environment(get_environment(environment_id, variant=variant))
