"""Generate one data-driven scene environment with an LLM.

Default mode is dry-run: it prints the prompt and does not call the network.
Use --run to call the configured LLM, validate JSON, resolve missing props via
scripts/generate_asset.py, and write data/generated_environments.json.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import os
import re
import sys
from typing import Any, Dict, Iterable, List, Optional, Set

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import generate_asset  # noqa: E402
from cutaway_vocab import REGISTRY_ASSETS  # noqa: E402

OUT_PATH = os.path.join(ROOT, "data", "generated_environments.json")
GENERATED_ASSETS_PATH = os.path.join(ROOT, "data", "generated_assets.json")
FRAME_W = 1920.0
FRAME_H = 1080.0
MIN_SLOTS = 2
MAX_SLOTS = 4
MIN_SET_PROPS = 2
MAX_SET_PROPS = 4


DATA_MODEL = {
    "id": "bakery",
    "description": "simple readable environment description",
    "backdrop": [
        {"type": "rect", "x": 0, "y": 0, "w": 1920, "h": 620, "fill": "paper"},
        {"type": "rect", "x": 0, "y": 620, "w": 1920, "h": 460, "fill": "paper_deep"},
    ],
    "set_props": [{"asset": "oven", "x": 480, "y": 720, "scale": 0.9, "z": 120}],
    "slots": {
        "baker": {"x": 960, "y": 760, "scale": 1.4, "z": 250, "role": "foreground"},
        "customer": {"x": 1260, "y": 760, "scale": 1.2, "z": 260, "role": "foreground"},
    },
    "text_zone": {"x": 120, "y": 90, "w": 760, "h": 150},
}


FEW_SHOTS = [
    {
        "id": "plain_room",
        "description": "quiet generic room with a wall, floor, and one framed panel",
        "backdrop": [
            {"type": "rect", "x": 0, "y": 0, "w": 1920, "h": 620, "fill": "paper"},
            {"type": "rect", "x": 0, "y": 620, "w": 1920, "h": 460, "fill": "paper_deep"},
            {"type": "rect", "x": 720, "y": 180, "w": 480, "h": 250, "rx": 8, "fill": "white", "stroke": True, "strokeW": 7},
        ],
        "set_props": [
            {"asset": "office_chair", "x": 500, "y": 760, "scale": 0.58, "z": 122},
            {"asset": "framed_painting", "x": 1420, "y": 310, "scale": 0.6, "z": 92},
        ],
        "slots": {
            "speaker": {"x": 880, "y": 700, "scale": 1.25, "z": 250, "role": "actor"},
            "listener": {"x": 1160, "y": 720, "scale": 1.15, "z": 260, "role": "actor"},
        },
        "text_zone": {"x": 120, "y": 70, "w": 650, "h": 135},
    },
    {
        "id": "lab_simple",
        "description": "clean lab with bench, whiteboard, and small science props",
        "backdrop": [
            {"type": "rect", "x": 0, "y": 0, "w": 1920, "h": 620, "fill": "paper"},
            {"type": "rect", "x": 0, "y": 620, "w": 1920, "h": 460, "fill": "paper_deep"},
            {"type": "rect", "x": 660, "y": 170, "w": 600, "h": 300, "rx": 8, "fill": "white", "stroke": True, "strokeW": 7},
        ],
        "set_props": [
            {"asset": "microscope", "x": 530, "y": 675, "scale": 0.52, "z": 118},
            {"asset": "flask", "x": 690, "y": 705, "scale": 0.42, "z": 122},
            {"asset": "beaker", "x": 1400, "y": 705, "scale": 0.42, "z": 123},
        ],
        "slots": {
            "scientist": {"x": 940, "y": 665, "scale": 1.35, "z": 260, "role": "actor"},
            "assistant": {"x": 1200, "y": 690, "scale": 1.15, "z": 270, "role": "actor"},
            "sample_table": {"x": 960, "y": 735, "scale": 0.62, "z": 220, "role": "set_prop"},
        },
        "text_zone": {"x": 120, "y": 70, "w": 650, "h": 135},
    },
]


def _safe_id(raw: Any) -> str:
    env_id = re.sub(r"[^a-z0-9_]+", "_", str(raw or "").strip().lower().replace("-", "_"))
    env_id = re.sub(r"_+", "_", env_id).strip("_")
    if not env_id:
        raise ValueError("environment id is empty after normalization")
    return env_id[:64]


def _load_json(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _write_json(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def _generated_asset_names() -> Set[str]:
    data = _load_json(GENERATED_ASSETS_PATH)
    return {str(name).strip() for name, asset in data.items() if str(name).strip() and isinstance(asset, dict) and isinstance(asset.get("shapes"), list)}


# Registry names that are UI/diagram glyphs or number widgets, not physical scene
# set-dressing. The env generator must not offer these (e.g. "counter"/"number" both
# map to a numeric Counter component, so an LLM picking "counter" for a shop surface
# rendered a stray digit). Keep this list to clearly non-physical assets only.
NON_PHYSICAL_PROPS = frozenset({
    "counter", "number", "dot", "arrow", "arrow_up", "arrow_down",
    "checkmark", "cross", "question_mark", "label", "subscribe",
    "chart_bar", "chart_line", "pie_chart",
})


def available_prop_names() -> List[str]:
    names = (set(REGISTRY_ASSETS) | _generated_asset_names()) - NON_PHYSICAL_PROPS
    return sorted(names)


def build_env_prompt(name: str, description: str) -> str:
    payload = {
        "task": "Return exactly one reusable scene environment JSON object.",
        "environment": {"id": name, "description": description},
        "brand_rules": [
            "clean flat vector explainer style",
            "warm paper background compatibility",
            "few big readable shapes, not decorative clutter",
            "use only palette role names for fills",
            "do not include text, raster images, gradients, shadows, or SVG markup",
            "leave the text_zone visibly clear of props and actor slot centers",
            "prefer existing available prop names for set_props",
        ],
        "frame_coordinate_system": {
            "shapeSpace": "frame",
            "width": 1920,
            "height": 1080,
            "origin": "top-left",
            "x_range": "0..1920",
            "y_range": "0..1080",
            "set_prop_z_band": "80..160",
            "actor_slot_z_band": "200..399",
        },
        "data_model": DATA_MODEL,
        "primitive_shape_vocabulary": {
            "types": sorted(generate_asset.SHAPE_TYPES),
            "palette_roles": sorted(generate_asset.COLOR_ROLES),
            "rect": ["type", "x", "y", "w", "h", "rx", "fill", "stroke", "strokeW", "opacity"],
            "circle": ["type", "cx", "cy", "r", "fill", "stroke", "strokeW", "opacity"],
            "ellipse": ["type", "cx", "cy", "r", "ry", "fill", "stroke", "strokeW", "opacity"],
            "polygon": ["type", "points", "fill", "stroke", "strokeW", "opacity"],
            "line": ["type", "x1", "y1", "x2", "y2", "stroke", "strokeW", "opacity"],
            "path": ["type", "d", "fill", "stroke", "strokeW", "opacity"],
        },
        "requirements": [
            "Use 1 to 3 backdrop shapes in frame coordinates.",
            "Use 2 to 4 set_props. Each set_prop has asset, x, y, scale, z.",
            "Use 2 to 4 actor slots. Each slot has x, y, scale, z, role.",
            "Use exactly one text_zone fully inside the frame.",
            "No set_prop position or slot center may be inside text_zone.",
        ],
        "available_prop_names": available_prop_names(),
        "few_shot_examples": FEW_SHOTS,
        "output_schema": {
            "id": name,
            "description": description,
            "backdrop": ["1 to 3 PrimitiveShape objects in frame coordinates"],
            "set_props": ["2 to 4 placed props"],
            "slots": {"slot_id": {"x": 960, "y": 760, "scale": 1.2, "z": 250, "role": "actor"}},
            "text_zone": {"x": 120, "y": 90, "w": 760, "h": 150},
        },
    }
    return "Return ONLY valid JSON. No markdown, comments, or explanation.\n" + json.dumps(payload, indent=2, sort_keys=True)


def _finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _num(value: Any, path: str) -> float:
    if not _finite(value):
        raise ValueError("%s must be a finite number" % path)
    return float(value)


def _positive(value: Any, path: str) -> float:
    number = _num(value, path)
    if number <= 0:
        raise ValueError("%s must be positive" % path)
    return number


def _frame_point(x: Any, y: Any, path: str) -> tuple[float, float]:
    nx = _num(x, path + ".x")
    ny = _num(y, path + ".y")
    if nx < 0 or nx > FRAME_W or ny < 0 or ny > FRAME_H:
        raise ValueError("%s point outside 1920x1080 frame" % path)
    return nx, ny


def _check_fill(shape: Dict[str, Any], index: int) -> None:
    fill = shape.get("fill")
    if fill is not None and fill not in generate_asset.COLOR_ROLES:
        raise ValueError("shape %d has invalid fill %r" % (index, fill))
    for key in ("strokeW", "opacity", "rx", "r", "ry", "w", "h"):
        if key in shape and not _finite(shape[key]):
            raise ValueError("shape %d key %s must be finite" % (index, key))


def _check_rect_bounds(x: float, y: float, w: float, h: float, path: str) -> None:
    if x < 0 or y < 0 or x + w > FRAME_W or y + h > FRAME_H:
        raise ValueError("%s outside 1920x1080 frame" % path)


def _validate_frame_shape(shape: Any, index: int) -> Dict[str, Any]:
    if not isinstance(shape, dict):
        raise ValueError("shape %d is not an object" % index)
    item = copy.deepcopy(shape)
    old_limit = generate_asset.BOX_LIMIT
    try:
        generate_asset.BOX_LIMIT = FRAME_W
        item = generate_asset._validate_shape(item, index)
    finally:
        generate_asset.BOX_LIMIT = old_limit
    stype = item.get("type")
    if stype not in generate_asset.SHAPE_TYPES:
        raise ValueError("shape %d has invalid type %r" % (index, stype))
    _check_fill(item, index)
    if stype == "rect":
        x = _num(item.get("x"), "shape %d.x" % index)
        y = _num(item.get("y"), "shape %d.y" % index)
        w = _positive(item.get("w"), "shape %d.w" % index)
        h = _positive(item.get("h"), "shape %d.h" % index)
        _check_rect_bounds(x, y, w, h, "shape %d" % index)
    elif stype == "circle":
        cx, cy = _frame_point(item.get("cx"), item.get("cy"), "shape %d" % index)
        r = _positive(item.get("r"), "shape %d.r" % index)
        _check_rect_bounds(cx - r, cy - r, r * 2, r * 2, "shape %d" % index)
    elif stype == "ellipse":
        cx, cy = _frame_point(item.get("cx"), item.get("cy"), "shape %d" % index)
        r = _positive(item.get("r"), "shape %d.r" % index)
        ry = _positive(item.get("ry"), "shape %d.ry" % index)
        _check_rect_bounds(cx - r, cy - ry, r * 2, ry * 2, "shape %d" % index)
    elif stype == "line":
        _frame_point(item.get("x1"), item.get("y1"), "shape %d.start" % index)
        _frame_point(item.get("x2"), item.get("y2"), "shape %d.end" % index)
    elif stype == "polygon":
        points = item.get("points")
        if isinstance(points, list) and points and all(isinstance(p, (list, tuple)) and len(p) == 2 for p in points):
            points = [coord for pair in points for coord in pair]
            item["points"] = points
        if isinstance(points, list) and len(points) % 2 and len(points) >= 7:
            points = points[:-1]
            item["points"] = points
        if not isinstance(points, list) or len(points) < 6 or len(points) % 2:
            raise ValueError("shape %d polygon needs a flat even points list" % index)
        for point_index in range(0, len(points), 2):
            _frame_point(points[point_index], points[point_index + 1], "shape %d.points[%d]" % (index, point_index))
    elif stype == "path":
        if not str(item.get("d") or "").strip():
            raise ValueError("shape %d path needs d" % index)
        numbers = generate_asset._numbers_from_path(item.get("d"))
        for number_index in range(0, len(numbers), 2):
            x = numbers[number_index]
            y = numbers[number_index + 1] if number_index + 1 < len(numbers) else 0
            _frame_point(x, y, "shape %d.path[%d]" % (index, number_index))
    return item


def _point_in_zone(x: float, y: float, zone: Dict[str, float]) -> bool:
    return zone["x"] <= x <= zone["x"] + zone["w"] and zone["y"] <= y <= zone["y"] + zone["h"]


def _normalize_set_prop(prop: Any, index: int, available_assets: Set[str], allow_missing_props: bool) -> Dict[str, Any]:
    if not isinstance(prop, dict):
        raise ValueError("set_props[%d] must be an object" % index)
    asset = _safe_id(prop.get("asset") or prop.get("name"))
    if not allow_missing_props and asset not in available_assets:
        raise ValueError("set_props[%d].asset %r is not resolvable" % (index, asset))
    return {
        "asset": asset,
        "x": _num(prop.get("x"), "set_props[%d].x" % index),
        "y": _num(prop.get("y"), "set_props[%d].y" % index),
        "scale": _positive(prop.get("scale", 1.0), "set_props[%d].scale" % index),
        "z": int(_num(prop.get("z", 120), "set_props[%d].z" % index)),
    }


def _normalize_slots(slots: Any) -> Dict[str, Dict[str, Any]]:
    if not isinstance(slots, dict):
        raise ValueError("slots must be an object")
    if len(slots) < MIN_SLOTS or len(slots) > MAX_SLOTS:
        raise ValueError("environment must include %d to %d slots" % (MIN_SLOTS, MAX_SLOTS))
    fixed: Dict[str, Dict[str, Any]] = {}
    for raw_name, slot in slots.items():
        if not isinstance(slot, dict):
            raise ValueError("slot %r must be an object" % raw_name)
        name = _safe_id(raw_name)
        x, y = _frame_point(slot.get("x"), slot.get("y"), "slots.%s" % name)
        fixed_slot = {
            "x": x,
            "y": y,
            "scale": _positive(slot.get("scale", 1.0), "slots.%s.scale" % name),
            "z": int(_num(slot.get("z", 250), "slots.%s.z" % name)),
        }
        role = str(slot.get("role") or "").strip()
        if role:
            fixed_slot["role"] = role
        fixed[name] = fixed_slot
    return fixed


def _normalize_text_zone(text_zone: Any) -> Dict[str, float]:
    if not isinstance(text_zone, dict):
        raise ValueError("text_zone must be an object")
    zone = {
        "x": _num(text_zone.get("x"), "text_zone.x"),
        "y": _num(text_zone.get("y"), "text_zone.y"),
        "w": _positive(text_zone.get("w"), "text_zone.w"),
        "h": _positive(text_zone.get("h"), "text_zone.h"),
    }
    _check_rect_bounds(zone["x"], zone["y"], zone["w"], zone["h"], "text_zone")
    return zone


def validate_environment(env: Any, fallback_name: str = "", fallback_description: str = "", available_assets: Optional[Iterable[str]] = None, allow_missing_props: bool = False) -> Dict[str, Any]:
    if not isinstance(env, dict):
        raise ValueError("LLM JSON root must be an object")
    if "backdrop" not in env:
        for key in ("environment", "output", "result", "data"):
            inner = env.get(key)
            if isinstance(inner, dict) and "backdrop" in inner:
                env = inner
                break
    available = set(available_assets or available_prop_names())
    env_id = _safe_id(env.get("id") or fallback_name)
    description = " ".join(str(env.get("description") or fallback_description).split())
    backdrop = env.get("backdrop")
    if not isinstance(backdrop, list) or not backdrop:
        raise ValueError("environment must include at least one backdrop shape")
    set_props_raw = env.get("set_props")
    if not isinstance(set_props_raw, list):
        raise ValueError("set_props must be a list")
    if len(set_props_raw) < MIN_SET_PROPS or len(set_props_raw) > MAX_SET_PROPS:
        raise ValueError("environment must include %d to %d set_props" % (MIN_SET_PROPS, MAX_SET_PROPS))
    set_props = [_normalize_set_prop(prop, i, available, allow_missing_props) for i, prop in enumerate(set_props_raw)]
    slots = _normalize_slots(env.get("slots"))
    text_zone = _normalize_text_zone(env.get("text_zone"))
    for name, slot in slots.items():
        if _point_in_zone(slot["x"], slot["y"], text_zone):
            raise ValueError("text_zone overlaps slot center %s; slot center overlaps text_zone" % name)
    for index, prop in enumerate(set_props):
        _frame_point(prop["x"], prop["y"], "set_props[%d]" % index)
        if _point_in_zone(prop["x"], prop["y"], text_zone):
            raise ValueError("text_zone overlaps set_props[%d] position; set_prop position overlaps text_zone" % index)
    return {
        "id": env_id,
        "description": description,
        "backdrop": [_validate_frame_shape(shape, i) for i, shape in enumerate(backdrop)],
        "set_props": set_props,
        "slots": slots,
        "text_zone": text_zone,
    }


def _asset_description(asset_name: str, env: Dict[str, Any]) -> str:
    readable = asset_name.replace("_", " ")
    return "%s prop for %s environment: %s" % (readable, env.get("id", "scene"), env.get("description", "simple scene prop"))


def _generate_asset(asset_name: str, env: Dict[str, Any]) -> Optional[str]:
    from llm import llm_generate

    description = _asset_description(asset_name, env)
    prompt = generate_asset.build_prompt(asset_name, description)
    text = llm_generate(prompt, tier="quality", json_mode=True)
    asset = generate_asset.validate_asset(generate_asset._parse_json(text), asset_name, description)
    generate_asset._write_store(asset["name"], asset)
    return asset["name"]


def resolve_missing_props(env: Dict[str, Any]) -> Dict[str, Any]:
    available = set(REGISTRY_ASSETS) | _generated_asset_names()
    fixed_props = []
    for prop in env.get("set_props") or []:
        asset = _safe_id(prop.get("asset"))
        if asset not in available:
            try:
                generated_name = _generate_asset(asset, env)
                if generated_name:
                    asset = generated_name
                    available.add(asset)
            except Exception as exc:
                print("warning: dropped set_prop %r because generation failed: %s" % (asset, exc), file=sys.stderr)
                continue
        fixed = copy.deepcopy(prop)
        fixed["asset"] = asset
        fixed_props.append(fixed)
    out = copy.deepcopy(env)
    out["set_props"] = fixed_props
    return out


def _has_llm_key() -> bool:
    provider = str(os.environ.get("LLM_PROVIDER", "openai")).strip().lower()
    openai_key_file = r"C:\Users\Caden\.youtube_bot_openai_key.txt"
    gemini_key_file = r"C:\Users\Caden\.youtube_bot_gemini_key.txt"
    if provider == "gemini":
        return bool(os.environ.get("GEMINI_API_KEY")) or os.path.exists(gemini_key_file)
    if provider == "openai":
        return bool(os.environ.get("OPENAI_API_KEY")) or os.path.exists(openai_key_file)
    return bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("GEMINI_API_KEY") or os.path.exists(openai_key_file) or os.path.exists(gemini_key_file))


def has_configured_llm_key() -> bool:
    return _has_llm_key()


def _write_environment(env: Dict[str, Any], force: bool = False) -> bool:
    data = _load_json(OUT_PATH)
    env_id = env["id"]
    if env_id in data and not force:
        print("skipped existing environment %s; pass --force to overwrite" % env_id)
        return False
    data[env_id] = env
    _write_json(OUT_PATH, data)
    return True


def generate_and_persist_environment(name: str, description: str, force: bool = False) -> Optional[Dict[str, Any]]:
    env_id = _safe_id(name)
    clean_description = " ".join(str(description or "").split())
    if not clean_description:
        clean_description = env_id.replace("_", " ")
    store = _load_json(OUT_PATH)
    if env_id in store and not force:
        print("skipped existing environment %s; pass --force to overwrite" % env_id)
        existing = validate_environment(store[env_id], env_id, clean_description)
        return existing
    if not _has_llm_key():
        return None

    from llm import llm_generate

    prompt = build_env_prompt(env_id, clean_description)
    text = llm_generate(prompt, tier="quality", json_mode=True)
    env = validate_environment(generate_asset._parse_json(text), env_id, clean_description, allow_missing_props=True)
    env = resolve_missing_props(env)
    env = validate_environment(env, env_id, clean_description)
    wrote = _write_environment(env, force=force)
    if wrote:
        print("wrote", OUT_PATH, "environment", env["id"], "backdrop_shapes", len(env["backdrop"]), "set_props", len(env["set_props"]))
    return env


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("description", nargs="+")
    parser.add_argument("--run", action="store_true", help="call the configured LLM and write data/generated_environments.json")
    parser.add_argument("--force", action="store_true", help="overwrite an existing generated environment id")
    args = parser.parse_args()

    name = _safe_id(args.name)
    description = " ".join(" ".join(args.description).split())
    prompt = build_env_prompt(name, description)

    if not args.run or not _has_llm_key():
        print(prompt)
        print("\nDRY RUN: no LLM call made. Pass --run with a configured key to generate and write the environment.")
        return

    env = generate_and_persist_environment(name, description, force=args.force)
    if env is None:
        print("\nDRY RUN: no LLM call made. Pass --run with a configured key to generate and write the environment.")


if __name__ == "__main__":
    main()
