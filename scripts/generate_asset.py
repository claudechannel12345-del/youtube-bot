"""Generate one brand-style primitive shape-list asset with an LLM.

Default mode is dry-run: it prints the prompt and does not call the network.
Use --run to call the configured LLM, validate the JSON, and write
data/generated_assets.json. Set LLM_PROVIDER=gemini for the Gemini fallback.
"""
import argparse
import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

OUT_PATH = os.path.join(ROOT, "data", "generated_assets.json")
SHAPE_TYPES = frozenset(["rect", "circle", "ellipse", "polygon", "line", "path"])
COLOR_ROLES = frozenset(["ink", "accent", "blue", "green", "yellow", "lavender", "muted", "white", "paper", "paper_deep", "none"])
BOX_LIMIT = 512.0
MAX_SHAPES = 38

FEW_SHOTS = [
    {
        "name": "heart",
        "description": "single coral heart with thick ink outline",
        "shapes": [
            {
                "type": "path",
                "d": "M 0 118 L -112 8 Q -166 -52 -120 -104 Q -76 -150 0 -86 Q 76 -150 120 -104 Q 166 -52 112 8 Z",
                "fill": "accent",
                "stroke": True,
                "strokeW": 11,
            }
        ],
    },
    {
        "name": "eye",
        "description": "flat almond eye brand mark",
        "shapes": [
            {"type": "path", "d": "M -176 0 Q 0 -132 176 0 Q 0 132 -176 0 Z", "fill": "paper", "stroke": True, "strokeW": 11},
            {"type": "circle", "cx": 0, "cy": 0, "r": 72, "fill": "accent", "stroke": True, "strokeW": 11},
            {"type": "circle", "cx": 0, "cy": 0, "r": 31, "fill": "ink"},
            {"type": "circle", "cx": 24, "cy": -24, "r": 12, "fill": "paper"},
        ],
    },
    {
        "name": "gavel",
        "description": "upright judge gavel and sound block",
        "shapes": [
            {"type": "rect", "x": -78, "y": 104, "w": 156, "h": 30, "rx": 10, "fill": "paper_deep", "stroke": True, "strokeW": 11},
            {"type": "rect", "x": -12, "y": -6, "w": 24, "h": 108, "rx": 11, "fill": "paper", "stroke": True, "strokeW": 11},
            {"type": "rect", "x": -92, "y": -66, "w": 184, "h": 64, "rx": 14, "fill": "paper_deep", "stroke": True, "strokeW": 11},
            {"type": "line", "x1": -58, "y1": -66, "x2": -58, "y2": -2, "stroke": True, "strokeW": 7},
            {"type": "line", "x1": 58, "y1": -66, "x2": 58, "y2": -2, "stroke": True, "strokeW": 7},
        ],
    },
    {
        "name": "document",
        "description": "plain paper sheet with a few text lines",
        "shapes": [
            {"type": "rect", "x": -86, "y": -118, "w": 172, "h": 236, "rx": 10, "fill": "paper", "stroke": True, "strokeW": 11},
            {"type": "line", "x1": -56, "y1": -70, "x2": 56, "y2": -70, "stroke": True, "strokeW": 4},
            {"type": "line", "x1": -56, "y1": -30, "x2": 56, "y2": -30, "stroke": True, "strokeW": 4},
            {"type": "line", "x1": -56, "y1": 10, "x2": 56, "y2": 10, "stroke": True, "strokeW": 4},
            {"type": "line", "x1": -56, "y1": 50, "x2": 18, "y2": 50, "stroke": True, "strokeW": 4},
        ],
    },
]


def _safe_name(raw):
    name = re.sub(r"[^a-z0-9_]+", "_", str(raw or "").strip().lower().replace("-", "_"))
    name = re.sub(r"_+", "_", name).strip("_")
    if not name:
        raise ValueError("asset name is empty after normalization")
    return name[:64]


def build_prompt(name, description):
    payload = {
        "task": "Return exactly one local-coordinate primitive shape-list asset as JSON.",
        "asset": {"name": name, "description": description},
        "style_rules": [
            "clean flat vector explainer style",
            "warm paper background compatibility",
            "thick ink strokes on important silhouettes",
            "use only palette role names for fills",
            "local coordinate box centered near 0,0; keep all coordinates inside -512..512",
            "do not include text, raster images, gradients, shadows, or SVG markup",
            # Recognizability rules (the asset MUST be guessable at a glance):
            "FIRST build the object's recognizable silhouette, THEN add 2-5 identifying details",
            "use enough shapes to be clearly recognizable (typically 8-22); too few shapes reads as an abstract blob, not the object",
            "place the single most identifying feature prominently and in its real-world position (e.g. a lamp's light sits at the TOP of the post; a tree's leaves sit above the trunk)",
            "fill the local box: the object should span most of the -512..512 area, not float small in the middle",
            "use the coral 'accent' role sparingly, only where the real object has a pop of color; default large surfaces to paper/paper_deep/white/muted with ink outline",
        ],
        "primitive_shape_vocabulary": {
            "types": sorted(SHAPE_TYPES),
            "palette_roles": sorted(COLOR_ROLES),
            "rect": ["type", "x", "y", "w", "h", "rx", "fill", "stroke", "strokeW", "opacity"],
            "circle": ["type", "cx", "cy", "r", "fill", "stroke", "strokeW", "opacity"],
            "ellipse": ["type", "cx", "cy", "r", "ry", "fill", "stroke", "strokeW", "opacity"],
            "polygon": ["type", "points", "fill", "stroke", "strokeW", "opacity"],
            "line": ["type", "x1", "y1", "x2", "y2", "stroke", "strokeW", "opacity"],
            "path": ["type", "d", "fill", "stroke", "strokeW", "opacity"],
        },
        "output_schema": {
            "name": name,
            "description": description,
            "shapes": ["1 to %d PrimitiveShape objects" % MAX_SHAPES],
        },
        "few_shot_examples": FEW_SHOTS,
    }
    return (
        "Return ONLY valid JSON. No markdown, comments, or explanation.\n"
        + json.dumps(payload, indent=2, sort_keys=True)
    )


def _numbers_from_path(path_data):
    return [float(x) for x in re.findall(r"[-+]?(?:\d*\.\d+|\d+)", str(path_data or ""))]


def _finite(value):
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def _check_num(value, path):
    if not _finite(value):
        raise ValueError("%s must be a finite number" % path)
    if abs(float(value)) > BOX_LIMIT:
        raise ValueError("%s out of local coordinate box" % path)


def _positive(value, path):
    if not _finite(value) or float(value) <= 0:
        raise ValueError("%s must be a positive finite number" % path)


def _validate_shape(shape, index):
    if not isinstance(shape, dict):
        raise ValueError("shape %d is not an object" % index)
    stype = shape.get("type")
    if stype not in SHAPE_TYPES:
        raise ValueError("shape %d has invalid type %r" % (index, stype))
    fill = shape.get("fill")
    if fill is not None and fill not in COLOR_ROLES:
        raise ValueError("shape %d has invalid fill %r" % (index, fill))
    for key in ("strokeW", "opacity", "rx", "r", "ry", "w", "h"):
        if key in shape and not _finite(shape[key]):
            raise ValueError("shape %d key %s must be finite" % (index, key))
    if stype == "rect":
        for key in ("x", "y"):
            _check_num(shape.get(key), "shape %d.%s" % (index, key))
        _positive(shape.get("w"), "shape %d.w" % index)
        _positive(shape.get("h"), "shape %d.h" % index)
    elif stype == "circle":
        for key in ("cx", "cy"):
            _check_num(shape.get(key), "shape %d.%s" % (index, key))
        _positive(shape.get("r"), "shape %d.r" % index)
    elif stype == "ellipse":
        for key in ("cx", "cy"):
            _check_num(shape.get(key), "shape %d.%s" % (index, key))
        _positive(shape.get("r"), "shape %d.r" % index)
        _positive(shape.get("ry"), "shape %d.ry" % index)
    elif stype == "line":
        for key in ("x1", "y1", "x2", "y2"):
            _check_num(shape.get(key), "shape %d.%s" % (index, key))
    elif stype == "polygon":
        points = shape.get("points")
        # Some models emit nested [[x,y],...] pairs; flatten to [x1,y1,x2,y2,...].
        if isinstance(points, list) and points and all(
            isinstance(p, (list, tuple)) and len(p) == 2 for p in points
        ):
            points = [coord for pair in points for coord in pair]
            shape["points"] = points
        # Tolerate a stray trailing odd coordinate (drop it) rather than failing the asset.
        if isinstance(points, list) and len(points) % 2 and len(points) >= 7:
            points = points[:-1]
            shape["points"] = points
        if not isinstance(points, list) or len(points) < 6 or len(points) % 2:
            raise ValueError("shape %d polygon needs a flat even points list" % index)
        for point_index, point in enumerate(points):
            _check_num(point, "shape %d.points[%d]" % (index, point_index))
    elif stype == "path":
        if not str(shape.get("d") or "").strip():
            raise ValueError("shape %d path needs d" % index)
        for number in _numbers_from_path(shape.get("d")):
            _check_num(number, "shape %d.path" % index)
    return shape


def validate_asset(asset, fallback_name, fallback_description):
    if not isinstance(asset, dict):
        raise ValueError("Gemini JSON root must be an object")
    # Some models echo the prompt schema and wrap the result in an outer key
    # (e.g. {"asset": {...}} or {"output": {...}}). Unwrap to the dict that has shapes.
    if "shapes" not in asset:
        for key in ("asset", "output", "result", "data"):
            inner = asset.get(key)
            if isinstance(inner, dict) and "shapes" in inner:
                asset = inner
                break
    shapes = asset.get("shapes")
    if not isinstance(shapes, list) or not shapes:
        raise ValueError("asset must include non-empty shapes list")
    if len(shapes) > MAX_SHAPES:
        raise ValueError("asset has too many shapes: %d" % len(shapes))
    return {
        "name": _safe_name(asset.get("name") or fallback_name),
        "description": str(asset.get("description") or fallback_description).strip(),
        "shapes": [_validate_shape(shape, i) for i, shape in enumerate(shapes)],
    }


def _response_text(response):
    text = getattr(response, "text", None)
    if text:
        return text
    try:
        parts = response.candidates[0].content.parts
        return "".join(str(getattr(part, "text", "") or "") for part in parts)
    except Exception:
        return str(response)


def _parse_json(text):
    raw = str(text or "").strip()
    try:
        return json.loads(raw)
    except Exception:
        decoder = json.JSONDecoder()
        start = raw.find("{")
        while start >= 0:
            try:
                obj, _ = decoder.raw_decode(raw[start:])
                return obj
            except ValueError:
                start = raw.find("{", start + 1)
    raise ValueError("No JSON object found in Gemini response")


def _load_store():
    try:
        with open(OUT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    return data if isinstance(data, dict) else {}


def _write_store(name, asset):
    data = _load_store()
    data[name] = {
        "description": asset["description"],
        "shapes": asset["shapes"],
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("description")
    parser.add_argument("--run", action="store_true", help="call the configured LLM and write data/generated_assets.json")
    args = parser.parse_args()

    name = _safe_name(args.name)
    description = " ".join(str(args.description).split())
    prompt = build_prompt(name, description)

    if not args.run:
        print(prompt)
        print("\nDRY RUN: no LLM call made. Pass --run to generate and write the asset.")
        return

    from llm import llm_generate

    text = llm_generate(prompt, tier="quality", json_mode=True)
    asset = validate_asset(_parse_json(text), name, description)
    _write_store(asset["name"], asset)
    print("wrote", OUT_PATH, "asset", asset["name"], "shapes", len(asset["shapes"]))


if __name__ == "__main__":
    main()
