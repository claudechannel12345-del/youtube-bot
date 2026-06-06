"""Author channel avatar + banner as one-beat blueprint episodes (clean-flat brand style).

Renders at 1920x1080; a post step crops/scales to avatar (800x800) and banner (2560x1440).
Usage: py -3 scripts/make_branding.py avatar|banner <out_props.json>
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _text(eid, text, x, y, w, h, role="headline", tone="ink", z=60):
    return {
        "id": eid, "kind": "label", "asset": "none",
        "position": {"mode": "point", "x": x, "y": y},
        "size": {"mode": "box", "w": w, "h": h},
        "z": z,
        "text": {"role": role, "text": text, "tone": tone, "maxChars": 80, "fit": "auto"},
    }


def _eye(x, y, scale, color="accent", z=30):
    return {
        "id": "eye", "kind": "prop", "asset": "eye",
        "position": {"mode": "point", "x": x, "y": y},
        "size": {"mode": "scale", "scale": scale}, "z": z, "colorRole": color,
    }


def _wrap(elements, bg="plain"):
    blueprint = {
        "version": 1, "preset": "comparison_stage", "intent": "brand",
        "background": {"treatment": bg},
        "camera": {"move": "static", "target": "center", "intensity": "none"},
        "elements": elements, "connections": [],
    }
    beat = {
        "id": "brand", "type": "compare", "start": 0.0, "end": 2.0,
        "startFrame": 0, "endFrame": 60, "scene_family": "comparison_stage",
        "layout": "left_right", "camera": {"move": "static", "target": "center", "intensity": "none"},
        "transition_in": "hard_cut", "transition_out": "hard_cut",
        "background": "plain", "assets": [], "text_overlays": [], "motion": [], "blueprint": blueprint,
    }
    return {
        "schema_version": 2, "fps": 30, "width": 1920, "height": 1080,
        "style_version": "clean_flat_light_v1", "renderer": "blueprint",
        "sections": [{
            "section_index": 0, "durationInFrames": 60, "audioSrc": "",
            "key_phrase": "BRAND", "narration": "", "captions": [], "beats": [beat],
        }],
    }


def avatar():
    # Big centered eye - reads as an icon at tiny avatar size. (Center 1080x1080 is cropped out.)
    return _wrap([_eye(960, 540, 2.6, color="accent", z=30)])


def banner():
    # Name + tagline + small eye, all in the CENTER safe area (center ~1546x423 of 2560x1440).
    return _wrap([
        _eye(960, 330, 1.05, color="accent", z=30),
        _text("name", "SECOND GLANCE", 960, 560, 1500, 200, role="headline", tone="ink", z=60),
        _text("tag", "ONE STRANGE, TRUE THING AT A TIME", 960, 720, 1400, 90, role="label", tone="coral_stamp", z=60),
    ])


def main():
    kind = sys.argv[1]
    out = sys.argv[2]
    if not os.path.isabs(out):
        out = os.path.join(ROOT, out)
    data = avatar() if kind == "avatar" else banner()
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f)
    print("wrote", out)


if __name__ == "__main__":
    main()
