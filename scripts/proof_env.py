"""Render-proof helper: emit Cutaway props for ANY environment id (+ optional variant).

Usage: py scripts/proof_env.py <env_id> [variant]
Writes remotion/props_envproof.json with 3 generic actors staged into the
environment's first three slots + one text-zone label.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from blueprint_presets import build_scene_stage  # noqa: E402
from environments import get_environment  # noqa: E402


def build(env_id, variant=None):
    env = get_environment(env_id, variant) if variant else get_environment(env_id)
    slot_names = list(env["slots"].keys())[:3]
    colors = ["accent", "blue", "ink"]
    actors = [
        {"id": "a%d" % i, "asset": "person", "slot": s, "colorRole": colors[i % 3], "motion": "micro_bob"}
        for i, s in enumerate(slot_names)
    ]
    beat = {
        "id": "scene", "type": "emphasize", "start": 0.0, "end": 4.0,
        "startFrame": 0, "endFrame": 120, "scene_family": "scene_stage",
        "layout": "wide_scene", "environment": env_id,
        "camera": {"move": "static", "target": "center", "intensity": "none"},
        "transition_in": "hard_cut", "transition_out": "hard_cut", "background": "plain",
        "assets": [], "actors": actors,
        "text_overlays": [{"role": "label", "text": env_id.upper().replace("_", " "), "tone": "ink"}],
        "motion": [],
    }
    section = {"section_index": 0, "durationInFrames": 120, "audioSrc": "", "key_phrase": "SCENE",
               "narration": "", "captions": [], "environment": env_id}
    if variant:
        beat["environment_variant"] = variant
        section["environment_variant"] = variant
    beat["blueprint"] = build_scene_stage(beat, [], section)
    section["beats"] = [beat]
    return {"schema_version": 2, "fps": 30, "width": 1920, "height": 1080,
            "style_version": "clean_flat_light_v1", "renderer": "blueprint", "sections": [section]}


def main():
    env_id = sys.argv[1] if len(sys.argv) > 1 else "courtroom"
    variant = sys.argv[2] if len(sys.argv) > 2 else None
    out = os.path.join(ROOT, "remotion", "props_envproof.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(build(env_id, variant), f)
    print("wrote", out, "for", env_id, variant or "")


if __name__ == "__main__":
    main()
