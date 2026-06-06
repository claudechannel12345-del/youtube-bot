"""PROOF: one composed arena SCENE (still, 1920x1080) to test the scenes-not-slideshow approach.

Layers: background environment (stands+crowd, lights, scoreboard, floor), midground (mat + corners),
foreground actors (red/blue fighters + referee, staged with depth), foreground occluder (ropes).
Text is optional/minimal. Renders a still via the Cutaway comp.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def shapes_el(eid, shapes, z):
    return {"id": eid, "kind": "texture", "asset": "none",
            "position": {"mode": "point", "x": 960, "y": 540}, "size": {"mode": "scale", "scale": 1.0},
            "z": z, "shapes": shapes}


def person(eid, x, y, scale, color, z, bob=True):
    el = {"id": eid, "kind": "prop", "asset": "person",
          "position": {"mode": "point", "x": x, "y": y}, "size": {"mode": "scale", "scale": scale},
          "z": z, "colorRole": color}
    if bob:
        el["motion"] = [{"kind": "micro_bob", "start": 0.0, "duration": 6.0}]
    return el


def build():
    bg = []
    # floor band (subtle) + horizon
    bg.append({"type": "rect", "x": 0, "y": 600, "w": 1920, "h": 480, "fill": "paper_deep"})
    # tiered stand behind the crowd
    bg.append({"type": "rect", "x": 120, "y": 150, "w": 1680, "h": 250, "rx": 8, "fill": "paper_deep"})
    # crowd: rows of small heads, receding tones
    tones = ["muted", "ink", "blue", "accent"]
    for r, cy in enumerate((205, 268, 331)):
        for i, cx in enumerate(range(190, 1760, 66)):
            bg.append({"type": "circle", "cx": cx + (r % 2) * 14, "cy": cy, "r": 17,
                       "fill": tones[(i + r) % 4], "opacity": 0.5})
    # arena lights (cones from the top)
    for lx in (840, 1080):
        bg.append({"type": "polygon", "points": [lx, 0, lx - 90, 170, lx + 90, 170], "fill": "yellow", "opacity": 0.22})
    # scoreboard, high center, mostly blank
    bg.append({"type": "rect", "x": 808, "y": 56, "w": 304, "h": 132, "rx": 12, "fill": "paper", "stroke": True, "strokeW": 8})
    bg.append({"type": "line", "x1": 960, "y1": 70, "x2": 960, "y2": 174, "stroke": True, "strokeW": 5})

    mid = []
    # the mat (perspective-lite trapezoid) + inner boundary
    mid.append({"type": "polygon", "points": [620, 652, 1300, 652, 1500, 958, 420, 958], "fill": "muted", "stroke": True, "strokeW": 10})
    mid.append({"type": "polygon", "points": [684, 694, 1236, 694, 1404, 922, 516, 922], "fill": "none", "stroke": True, "strokeW": 5})
    # corner pads
    mid.append({"type": "rect", "x": 430, "y": 922, "w": 120, "h": 46, "rx": 6, "fill": "accent", "stroke": True, "strokeW": 6})
    mid.append({"type": "rect", "x": 1370, "y": 922, "w": 120, "h": 46, "rx": 6, "fill": "blue", "stroke": True, "strokeW": 6})

    fg_ropes = []
    for ry in (986, 1046):
        fg_ropes.append({"type": "line", "x1": 40, "y1": ry, "x2": 1880, "y2": ry, "stroke": True, "strokeW": 14})
    for px in (62, 1818):
        fg_ropes.append({"type": "rect", "x": px, "y": 940, "w": 40, "h": 140, "rx": 6, "fill": "paper_deep", "stroke": True, "strokeW": 8})

    elements = [
        shapes_el("env_bg", bg, z=5),
        shapes_el("env_mid", mid, z=100),
        person("fighter_red", 770, 706, 1.45, "accent", z=210),
        person("fighter_blue", 1150, 706, 1.45, "blue", z=211),
        person("referee", 965, 812, 1.9, "ink", z=300),
        shapes_el("fg_ropes", fg_ropes, z=500),
    ]
    blueprint = {"version": 1, "preset": "scene_stage", "intent": "arena",
                 "background": {"treatment": "plain"},
                 "camera": {"move": "static", "target": "center", "intensity": "none"},
                 "elements": elements, "connections": []}
    beat = {"id": "scene", "type": "establish", "start": 0.0, "end": 4.0, "startFrame": 0, "endFrame": 120,
            "scene_family": "object_stage", "layout": "center_subject",
            "camera": {"move": "static", "target": "center", "intensity": "none"},
            "transition_in": "hard_cut", "transition_out": "hard_cut", "background": "plain",
            "assets": [], "text_overlays": [], "motion": [], "blueprint": blueprint}
    return {"schema_version": 2, "fps": 30, "width": 1920, "height": 1080,
            "style_version": "clean_flat_light_v1", "renderer": "blueprint",
            "sections": [{"section_index": 0, "durationInFrames": 120, "audioSrc": "",
                          "key_phrase": "SCENE", "narration": "", "captions": [], "beats": [beat]}]}


def main():
    out = os.path.join(ROOT, "remotion", "props_scene.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(build(), f)
    print("wrote", out)


if __name__ == "__main__":
    main()
