"""PROOF: one composed arena SCENE still, 1920x1080.

This exercises the shared environment path: authored backdrop/midground,
foreground actors staged into named slots, foreground occluder, and text placed
inside the environment text_zone without an extra label backdrop.
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from blueprint_presets import build_scene_stage  # noqa: E402


def build():
    beat = {
        "id": "scene",
        "type": "emphasize",
        "start": 0.0,
        "end": 4.0,
        "startFrame": 0,
        "endFrame": 120,
        "scene_family": "scene_stage",
        "layout": "wide_scene",
        "environment": "arena",
        "environment_variant": "night",
        "camera": {"move": "static", "target": "center", "intensity": "none"},
        "transition_in": "hard_cut",
        "transition_out": "hard_cut",
        "background": "plain",
        "assets": [],
        "actors": [
            {"id": "fighter_red", "asset": "person", "slot": "red_corner", "colorRole": "accent", "motion": "micro_bob"},
            {"id": "fighter_blue", "asset": "person", "slot": "blue_corner", "colorRole": "blue", "motion": "micro_bob"},
            {"id": "referee", "asset": "person", "slot": "referee_center", "colorRole": "ink", "motion": "micro_bob"},
        ],
        "text_overlays": [{"role": "label", "text": "SCENE TEXT ZONE", "tone": "ink"}],
        "motion": [],
    }
    section = {
        "section_index": 0,
        "durationInFrames": 120,
        "audioSrc": "",
        "key_phrase": "SCENE",
        "narration": "",
        "captions": [],
        "environment": "arena",
        "environment_variant": "night",
    }
    beat["blueprint"] = build_scene_stage(beat, [], section)
    section["beats"] = [beat]
    return {
        "schema_version": 2,
        "fps": 30,
        "width": 1920,
        "height": 1080,
        "style_version": "clean_flat_light_v1",
        "renderer": "blueprint",
        "sections": [section],
    }


def main():
    out = os.path.join(ROOT, "remotion", "props_scene.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(build(), f)
    print("wrote", out)


if __name__ == "__main__":
    main()
