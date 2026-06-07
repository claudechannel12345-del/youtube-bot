"""Build data/color_script_scenes.json with authored scene environments.

This leaves the live data/color_script.json path untouched. Narration sentences are
identical to build_color_script.py so the existing audio cache can still match.
"""
import copy
import json
import os

import build_color_script

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ARENA_SECTIONS = frozenset([0, 2, 3, 4])
COURTROOM_SECTION = 6


def _actor(actor_id, asset, slot, color_role, motion="micro_bob"):
    return {
        "id": actor_id,
        "asset": asset,
        "slot": slot,
        "colorRole": color_role,
        "motion": motion,
    }


def _arena_actors(swapped=False):
    red_slot = "blue_corner" if swapped else "red_corner"
    blue_slot = "red_corner" if swapped else "blue_corner"
    red_color = "blue" if swapped else "accent"
    blue_color = "accent" if swapped else "blue"
    return [
        _actor("red_fighter", "person", red_slot, red_color),
        _actor("blue_fighter", "person", blue_slot, blue_color),
        _actor("referee", "person", "referee_center", "ink"),
    ]


def _courtroom_actors():
    return [
        _actor("defendant", "person", "defendant_left", "muted"),
        _actor("lawyer", "person", "lawyer_right", "ink"),
        _actor("judge", "person", "judge_bench", "paper_deep", motion="none"),
    ]


def _scene_beat(beat, section_index):
    out = copy.deepcopy(beat)
    if section_index in ARENA_SECTIONS:
        out["actors"] = _arena_actors(swapped=(section_index == 4 and "swapped" in str(beat.get("text", "")).lower()))
        out["subjects"] = []
    elif section_index == COURTROOM_SECTION:
        out["actors"] = _courtroom_actors()
        out["subjects"] = []
    return out


def build():
    data = copy.deepcopy(build_color_script.build())
    for index, section in enumerate(data.get("sections", [])):
        if index in ARENA_SECTIONS:
            section["environment"] = "arena"
        elif index == COURTROOM_SECTION:
            section["environment"] = "courtroom"
        else:
            section.pop("environment", None)
        section["beats"] = [_scene_beat(beat, index) for beat in section.get("beats", [])]
    return data


def _check_invariant(data):
    bad = []
    for index, section in enumerate(data.get("sections", [])):
        expected = " ".join(sentence["text"] for sentence in section.get("sentences", []))
        if expected != section.get("narration"):
            bad.append(index)
    return bad


def main():
    data = build()
    bad = _check_invariant(data)
    out = os.path.join(ROOT, "data", "color_script_scenes.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    scene_sections = [i + 1 for i, section in enumerate(data["sections"]) if section.get("environment")]
    print("wrote", out)
    print(
        "sections:",
        len(data["sections"]),
        "| scene_sections:",
        scene_sections,
        "| beats:",
        sum(len(section["beats"]) for section in data["sections"]),
        "| invariant_violations:",
        len(bad),
    )
    if bad:
        raise SystemExit("narration invariant failed for sections: %s" % bad)


if __name__ == "__main__":
    main()
