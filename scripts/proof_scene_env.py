"""PROOF: one composed SCENE still for a given environment, with the SAME actors
the full video uses (ENV_ACTORS), so actor<->furniture interactions (e.g. a student
seated at a desk) render exactly as in make_video_from_script.

Usage: py scripts/proof_scene_env.py <env> ["HEADLINE TEXT"]
Writes remotion/props_scene_env.json
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
SCRIPTS = os.path.join(ROOT, "scripts")
for p in (SRC, SCRIPTS):
    if p not in sys.path:
        sys.path.insert(0, p)

from blueprint_presets import build_scene_stage  # noqa: E402
from make_video_from_script import actors_for  # noqa: E402


def build(env, headline):
    beat = {
        "id": "sec0",
        "type": "emphasize",
        "start": 0.0,
        "end": 4.0,
        "startFrame": 0,
        "endFrame": 120,
        "scene_family": "scene_stage",
        "layout": "wide_scene",
        "environment": env,
        "camera": {"move": "static", "target": "center", "intensity": "none"},
        "transition_in": "hard_cut",
        "transition_out": "hard_cut",
        "background": "plain",
        "assets": [],
        "actors": actors_for(env),
        "text_overlays": [{"role": "label", "text": headline, "tone": "ink"}],
        "motion": [],
    }
    section = {
        "section_index": 0,
        "durationInFrames": 120,
        "audioSrc": "",
        "key_phrase": headline,
        "narration": "",
        "captions": [],
        "environment": env,
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
    env = sys.argv[1] if len(sys.argv) > 1 else "classroom"
    headline = sys.argv[2] if len(sys.argv) > 2 else "TRUE STORY"
    out = os.path.join(ROOT, "remotion", "props_scene_env.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(build(env, headline), f)
    print("wrote", out, "env=", env)


if __name__ == "__main__":
    main()
