"""Authored hero environments for section-level scene staging.

Each environment is a deterministic 1920x1080 composition made from primitive
shape lists plus named actor slots. The renderer already understands
BlueprintElement.shapes, so callers wrap these layers as texture elements.
"""

from __future__ import annotations

import copy
from typing import Any, Callable, Dict


def _slot(x: float, y: float, scale: float, z: int) -> Dict[str, Any]:
    return {"x": x, "y": y, "scale": scale, "z": z}


def build_arena() -> Dict[str, Any]:
    bg = []
    bg.append({"type": "rect", "x": 0, "y": 600, "w": 1920, "h": 480, "fill": "paper_deep"})
    bg.append({"type": "rect", "x": 120, "y": 150, "w": 1680, "h": 250, "rx": 8, "fill": "paper_deep"})
    tones = ["muted", "ink", "blue", "accent"]
    for r, cy in enumerate((205, 268, 331)):
        for i, cx in enumerate(range(190, 1760, 66)):
            bg.append(
                {
                    "type": "circle",
                    "cx": cx + (r % 2) * 14,
                    "cy": cy,
                    "r": 17,
                    "fill": tones[(i + r) % 4],
                    "opacity": 0.5,
                }
            )
    for lx in (840, 1080):
        bg.append({"type": "polygon", "points": [lx, 0, lx - 90, 170, lx + 90, 170], "fill": "yellow", "opacity": 0.22})
    bg.append({"type": "rect", "x": 808, "y": 56, "w": 304, "h": 132, "rx": 12, "fill": "paper", "stroke": True, "strokeW": 8})
    bg.append({"type": "line", "x1": 960, "y1": 70, "x2": 960, "y2": 174, "stroke": True, "strokeW": 5})

    mid = []
    mid.append({"type": "polygon", "points": [620, 652, 1300, 652, 1500, 958, 420, 958], "fill": "muted", "stroke": True, "strokeW": 10})
    mid.append({"type": "polygon", "points": [684, 694, 1236, 694, 1404, 922, 516, 922], "fill": "none", "stroke": True, "strokeW": 5})
    mid.append({"type": "rect", "x": 430, "y": 922, "w": 120, "h": 46, "rx": 6, "fill": "accent", "stroke": True, "strokeW": 6})
    mid.append({"type": "rect", "x": 1370, "y": 922, "w": 120, "h": 46, "rx": 6, "fill": "blue", "stroke": True, "strokeW": 6})

    fg = []
    for ry in (986, 1046):
        fg.append({"type": "line", "x1": 40, "y1": ry, "x2": 1880, "y2": ry, "stroke": True, "strokeW": 14})
    for px in (62, 1818):
        fg.append({"type": "rect", "x": px, "y": 940, "w": 40, "h": 140, "rx": 6, "fill": "paper_deep", "stroke": True, "strokeW": 8})

    return {
        "id": "arena",
        "backdrop": bg,
        "midground": mid,
        "foreground": fg,
        "slots": {
            "red_corner": _slot(770, 706, 1.45, 210),
            "blue_corner": _slot(1150, 706, 1.45, 211),
            "referee_center": _slot(965, 812, 1.9, 300),
        },
    }


def build_courtroom() -> Dict[str, Any]:
    bg = [
        {"type": "rect", "x": 0, "y": 610, "w": 1920, "h": 470, "fill": "paper_deep"},
        {"type": "rect", "x": 180, "y": 110, "w": 1560, "h": 520, "rx": 10, "fill": "paper", "stroke": True, "strokeW": 8},
        {"type": "line", "x1": 180, "y1": 352, "x2": 1740, "y2": 352, "stroke": True, "strokeW": 5},
        {"type": "rect", "x": 300, "y": 175, "w": 164, "h": 260, "rx": 4, "fill": "blue", "stroke": True, "strokeW": 6},
        {"type": "rect", "x": 300, "y": 175, "w": 164, "h": 44, "fill": "accent"},
        {"type": "rect", "x": 300, "y": 263, "w": 164, "h": 44, "fill": "white"},
        {"type": "line", "x1": 482, "y1": 160, "x2": 482, "y2": 470, "stroke": True, "strokeW": 5},
        {"type": "rect", "x": 1220, "y": 220, "w": 340, "h": 220, "rx": 8, "fill": "paper_deep", "stroke": True, "strokeW": 6},
    ]
    mid = [
        {"type": "polygon", "points": [620, 420, 1320, 420, 1430, 650, 510, 650], "fill": "paper_deep", "stroke": True, "strokeW": 10},
        {"type": "rect", "x": 545, "y": 560, "w": 870, "h": 120, "rx": 8, "fill": "ink", "opacity": 0.88},
        {"type": "rect", "x": 1170, "y": 635, "w": 250, "h": 210, "rx": 8, "fill": "paper", "stroke": True, "strokeW": 8},
        {"type": "rect", "x": 430, "y": 705, "w": 330, "h": 125, "rx": 8, "fill": "paper", "stroke": True, "strokeW": 8},
        {"type": "rect", "x": 1460, "y": 705, "w": 250, "h": 120, "rx": 8, "fill": "paper_deep", "stroke": True, "strokeW": 7},
    ]
    fg = [
        {"type": "rect", "x": 145, "y": 875, "w": 1630, "h": 54, "rx": 8, "fill": "paper_deep", "stroke": True, "strokeW": 8},
        {"type": "line", "x1": 160, "y1": 825, "x2": 1760, "y2": 825, "stroke": True, "strokeW": 10},
        {"type": "line", "x1": 160, "y1": 930, "x2": 1760, "y2": 930, "stroke": True, "strokeW": 10},
    ]
    return {
        "id": "courtroom",
        "backdrop": bg,
        "midground": mid,
        "foreground": fg,
        "slots": {
            "judge_bench": _slot(960, 468, 1.0, 205),
            "witness_stand": _slot(1300, 720, 1.25, 260),
            "defendant_left": _slot(590, 745, 1.35, 275),
            "lawyer_right": _slot(1515, 755, 1.35, 285),
            "gallery": _slot(960, 842, 1.15, 235),
        },
    }


def build_newsroom() -> Dict[str, Any]:
    bg = [
        {"type": "rect", "x": 0, "y": 620, "w": 1920, "h": 460, "fill": "paper_deep"},
        {"type": "rect", "x": 170, "y": 112, "w": 1580, "h": 510, "rx": 10, "fill": "paper", "stroke": True, "strokeW": 8},
        {"type": "rect", "x": 615, "y": 170, "w": 690, "h": 350, "rx": 12, "fill": "blue", "stroke": True, "strokeW": 8},
        {"type": "path", "d": "M720 330 C820 250 890 395 980 305 C1070 215 1160 385 1230 280", "stroke": True, "strokeW": 8, "fill": "none"},
        {"type": "circle", "cx": 838, "cy": 308, "r": 18, "fill": "accent", "stroke": True, "strokeW": 5},
        {"type": "circle", "cx": 1108, "cy": 305, "r": 18, "fill": "yellow", "stroke": True, "strokeW": 5},
        {"type": "rect", "x": 210, "y": 250, "w": 260, "h": 170, "rx": 8, "fill": "paper_deep", "stroke": True, "strokeW": 6},
        {"type": "rect", "x": 1430, "y": 245, "w": 270, "h": 178, "rx": 8, "fill": "paper_deep", "stroke": True, "strokeW": 6},
    ]
    mid = [
        {"type": "polygon", "points": [545, 695, 1375, 695, 1510, 900, 410, 900], "fill": "paper", "stroke": True, "strokeW": 10},
        {"type": "line", "x1": 620, "y1": 755, "x2": 1300, "y2": 755, "stroke": True, "strokeW": 5},
        {"type": "rect", "x": 815, "y": 735, "w": 350, "h": 95, "rx": 8, "fill": "paper_deep", "stroke": True, "strokeW": 6},
    ]
    fg = [
        {"type": "polygon", "points": [430, 850, 1490, 850, 1580, 1008, 340, 1008], "fill": "paper_deep", "stroke": True, "strokeW": 10},
        {"type": "line", "x1": 430, "y1": 850, "x2": 1490, "y2": 850, "stroke": True, "strokeW": 14},
    ]
    return {
        "id": "newsroom",
        "backdrop": bg,
        "midground": mid,
        "foreground": fg,
        "slots": {
            "anchor_center": _slot(960, 704, 1.45, 260),
            "screen": _slot(960, 360, 0.95, 80),
            "desk_props": _slot(1060, 774, 0.55, 310),
        },
    }


ENVIRONMENT_BUILDERS: Dict[str, Callable[[], Dict[str, Any]]] = {
    "arena": build_arena,
    "courtroom": build_courtroom,
    "newsroom": build_newsroom,
}

ENVIRONMENTS = frozenset(ENVIRONMENT_BUILDERS.keys())


def get_environment(environment_id: str) -> Dict[str, Any]:
    builder = ENVIRONMENT_BUILDERS.get(str(environment_id or "").strip())
    if builder is None:
        raise KeyError(environment_id)
    return copy.deepcopy(builder())


def has_environment(environment_id: str) -> bool:
    return str(environment_id or "").strip() in ENVIRONMENT_BUILDERS
