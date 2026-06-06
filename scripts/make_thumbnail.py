"""Author a thumbnail as a one-beat blueprint episode and render it as a still (clean-flat style).

Usage: py -3 scripts/make_thumbnail.py "WHY DOES RED WIN?" props_thumb_a.json
Then:  npx.cmd remotion still Cutaway out.png --props=props_thumb_a.json --frame=20
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _text_el(eid, text, x, y, w, h, role="headline", tone="ink", z=60):
    return {
        "id": eid, "kind": "label", "asset": "none",
        "position": {"mode": "point", "x": x, "y": y},
        "size": {"mode": "box", "w": w, "h": h},
        "z": z,
        "text": {"role": role, "text": text, "tone": tone, "maxChars": 60, "fit": "auto"},
    }


def _person(eid, x, color, z, scale=0.92, y=560):
    return {
        "id": eid, "kind": "prop", "asset": "person",
        "position": {"mode": "point", "x": x, "y": y},
        "size": {"mode": "scale", "scale": scale},
        "z": z, "colorRole": color,
    }


def build(headline, subtext=None):
    # Red is BIGGER (dominant = winning) so the "cheating" claim reads instantly; blue is smaller.
    elements = [
        _person("p_red", 540, "accent", 21, scale=1.7, y=560),
        _person("p_blue", 1380, "blue", 20, scale=1.05, y=590),
        _text_el("headline", headline, 960, 150, 1700, 210, role="headline", tone="ink", z=60),
    ]
    if subtext:
        elements.append(_text_el("sub", subtext, 960, 960, 1500, 110, role="label", tone="coral_stamp", z=60))
    blueprint = {
        "version": 1, "preset": "comparison_stage", "intent": "thumb",
        "background": {"treatment": "comparison_panels"},
        "camera": {"move": "static", "target": "center", "intensity": "none"},
        "elements": elements, "connections": [],
    }
    beat = {
        "id": "thumb", "type": "compare", "start": 0.0, "end": 2.0,
        "startFrame": 0, "endFrame": 60, "scene_family": "comparison_stage",
        "layout": "left_right", "camera": {"move": "static", "target": "center", "intensity": "none"},
        "transition_in": "hard_cut", "transition_out": "hard_cut",
        "background": "panel", "assets": [], "text_overlays": [], "motion": [],
        "blueprint": blueprint,
    }
    return {
        "schema_version": 2, "fps": 30, "width": 1920, "height": 1080,
        "style_version": "clean_flat_light_v1", "renderer": "blueprint",
        "sections": [{
            "section_index": 0, "durationInFrames": 60, "audioSrc": "",
            "key_phrase": "THUMB", "narration": "", "captions": [], "beats": [beat],
        }],
    }


def main():
    headline = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "remotion/props_thumb.json"
    subtext = sys.argv[3] if len(sys.argv) > 3 else None
    if not os.path.isabs(out):
        out = os.path.join(ROOT, out)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(build(headline, subtext), f)
    print("wrote", out)


if __name__ == "__main__":
    main()
