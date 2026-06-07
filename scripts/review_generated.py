"""Build a Remotion contact-sheet props file for generated primitive assets.

This is a local curation helper. It reads data/generated_assets.json, validates a
minimal contact-sheet shape, and writes remotion/props_generated_assets_review.json.
Claude can then render a still from the Cutaway composition for visual review.
"""

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from generate_asset import validate_asset  # noqa: E402

IN_PATH = os.path.join(ROOT, "data", "generated_assets.json")
OUT_PATH = os.path.join(ROOT, "remotion", "props_generated_assets_review.json")

FPS = 30
W = 1920
H = 1080
MAX_ASSETS = 40


def _load_assets(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError:
        return {}
    if not isinstance(raw, dict):
        raise ValueError("%s must contain an object keyed by asset name" % path)
    assets = {}
    for name, item in sorted(raw.items()):
        candidate = dict(item) if isinstance(item, dict) else {}
        candidate.setdefault("name", name)
        candidate.setdefault("description", "")
        asset = validate_asset(candidate, name, candidate.get("description", ""))
        assets[asset["name"]] = asset
    return assets


def _label(text, x, y, w=250):
    return {
        "id": "label_%s_%s" % (int(x), int(y)),
        "kind": "tiny_note",
        "asset": "none",
        "position": {"mode": "point", "x": x, "y": y},
        "size": {"mode": "box", "w": w, "h": 56},
        "text": {"role": "tiny_note", "text": text[:42], "tone": "ink"},
        "z": 20,
    }


def _generated_element(name, asset, x, y):
    return {
        "id": "generated_%s" % name,
        "kind": "generated_image",
        "asset": "generated_image",
        "generatedAssetName": name,
        "position": {"mode": "point", "x": x, "y": y},
        "size": {"mode": "scale", "scale": 0.52},
        "shapes": asset["shapes"],
        "shapeSpace": "local",
        "z": 10,
    }


def _empty_elements():
    return [
        {
            "id": "empty_title",
            "kind": "headline",
            "asset": "none",
            "position": {"mode": "point", "x": W / 2, "y": 440},
            "size": {"mode": "box", "w": 1100, "h": 120},
            "text": {"role": "headline", "text": "NO GENERATED ASSETS", "tone": "ink"},
            "z": 10,
        },
        {
            "id": "empty_note",
            "kind": "caption",
            "asset": "none",
            "position": {"mode": "point", "x": W / 2, "y": 570},
            "size": {"mode": "box", "w": 980, "h": 120},
            "text": {"role": "caption", "text": "Run scripts/generate_asset.py --run first, then rebuild this review sheet.", "tone": "muted"},
            "z": 10,
        },
    ]


def build_contact_sheet(assets):
    elements = [
        {
            "id": "sheet_title",
            "kind": "title",
            "asset": "none",
            "position": {"mode": "point", "x": W / 2, "y": 120},
            "size": {"mode": "box", "w": 980, "h": 64},
            "text": {"role": "title", "text": "GENERATED ASSET REVIEW", "tone": "ink"},
            "z": 30,
        }
    ]

    items = list(assets.items())[:MAX_ASSETS]
    sheet_h = H
    if not items:
        elements.extend(_empty_elements())
    else:
        cols = 5
        cell_w = 328
        cell_h = 300
        start_x = 305
        start_y = 300
        pw, ph = 290, 250
        rows = (len(items) + cols - 1) // cols
        sheet_h = int(start_y + rows * cell_h + 40)
        for index, (name, asset) in enumerate(items):
            col = index % cols
            row = index // cols
            x = start_x + col * cell_w
            y = start_y + row * cell_h
            elements.append(
                {
                    "id": "panel_%s" % name,
                    "kind": "panel",
                    "asset": "none",
                    "position": {"mode": "point", "x": x, "y": y},
                    "size": {"mode": "box", "w": pw, "h": ph - 30},
                    "shapes": [
                        {"type": "rect", "x": x - pw / 2, "y": y - ph / 2, "w": pw, "h": ph, "rx": 8, "fill": "paper", "stroke": True, "strokeW": 5}
                    ],
                    "z": 0,
                }
            )
            elements.append(_generated_element(name, asset, x, y - 24))
            elements.append(_label(name.replace("_", " ").upper(), x, y + 96, w=270))
        if len(assets) > MAX_ASSETS:
            elements.append(_label("+%d MORE IN JSON" % (len(assets) - MAX_ASSETS), W / 2, sheet_h - 30, 420))

    beat = {
        "id": "generated_asset_contact_sheet",
        "type": "emphasize",
        "start": 0,
        "end": 4,
        "startFrame": 0,
        "endFrame": 120,
        "scene_family": "object_stage",
        "layout": "wide_scene",
        "camera": {"move": "static", "target": "center", "intensity": "none"},
        "transition_in": "hard_cut",
        "transition_out": "hard_cut",
        "background": {"treatment": "plain"},
        "assets": [],
        "text_overlays": [],
        "motion": [],
        "blueprint": {
            "version": 1,
            "preset": "object_stage",
            "intent": "generated asset contact sheet",
            "elements": elements,
            "connections": [],
            "camera": {"move": "static", "target": "center", "intensity": "none"},
            "background": {"treatment": "plain", "elements": []},
        },
    }
    return {
        "schema_version": 2,
        "fps": FPS,
        "width": W,
        "height": sheet_h,
        "style_version": "clean_flat_light_v1",
        "renderer": "blueprint",
        "sections": [
            {
                "section_index": 0,
                "durationInFrames": 120,
                "audioSrc": "",
                "key_phrase": "GENERATED ASSET REVIEW",
                "narration": "",
                "captions": [],
                "beats": [beat],
            }
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=IN_PATH)
    parser.add_argument("--out", default=OUT_PATH)
    args = parser.parse_args()

    in_path = args.input if os.path.isabs(args.input) else os.path.join(ROOT, args.input)
    out_path = args.out if os.path.isabs(args.out) else os.path.join(ROOT, args.out)
    assets = _load_assets(in_path)
    episode = build_contact_sheet(assets)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(episode, f, indent=2)
    print("wrote", out_path)
    print("generated assets:", len(assets))
    print("render still:")
    print("cd remotion && npx.cmd remotion still src/index.ts Cutaway out/generated_assets_review.png --props=props_generated_assets_review.json --frame=30")


if __name__ == "__main__":
    main()
