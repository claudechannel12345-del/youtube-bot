"""
Manim animation generator — channel visual style: Cosmos Dark.
Deep space background, cycling accent colors, geometric reveals.
"""
import glob
import json
import os
import shutil
import subprocess

ACCENT_CYCLE = ["#FFD166", "#06D6A0", "#EF476F", "#9B5DE5"]

# Scene template written to a temp file and executed via manim CLI.
# Parameters passed safely via MANIM_PARAMS env var (JSON).
_SCENE_TEMPLATE = r'''
import os, json, numpy as np
from manim import (
    Scene, Text, Line, Circle, Dot, VGroup,
    FadeIn, Create, Write, GrowFromCenter,
    ORIGIN, UP, DOWN,
)

_p        = json.loads(os.environ["MANIM_PARAMS"])
PHRASE    = _p["phrase"]
ACCENT    = _p["accent"]
DURATION  = float(_p["duration"])
FLIP      = bool(_p["flip"])
BG        = "#0D0D1A"
WHT       = "#FFFFFF"

class SectionScene(Scene):
    def construct(self):
        self.camera.background_color = BG

        cx1 = -5.2 if not FLIP else 5.2
        cx2 =  5.0 if not FLIP else -5.0
        dx  = -5.5 if not FLIP else 5.5

        c1 = Circle(radius=3.0, color=ACCENT, stroke_width=1.5, fill_opacity=0.05)
        c1.move_to(np.array([cx1, 3.2, 0]))
        c2 = Circle(radius=1.6, color=ACCENT, stroke_width=1.0, fill_opacity=0.07)
        c2.move_to(np.array([cx2, -2.2, 0]))
        dot  = Dot(point=np.array([dx, -3.2, 0]), radius=0.12, color=ACCENT)
        line = Line(np.array([-3.2, -0.35, 0]), np.array([3.2, -0.35, 0]),
                    color=ACCENT, stroke_width=2.5)

        words = PHRASE.upper().split()
        if len(words) > 4:
            mid   = len(words) // 2
            title = VGroup(
                Text(" ".join(words[:mid]), color=WHT, weight="BOLD"),
                Text(" ".join(words[mid:]), color=WHT, weight="BOLD"),
            ).arrange(DOWN, buff=0.2)
        else:
            fs    = 0.85 if len(PHRASE) > 22 else (1.0 if len(PHRASE) > 15 else 1.15)
            title = Text(PHRASE.upper(), color=WHT, weight="BOLD").scale(fs)

        title.move_to(ORIGIN + UP * 0.45)

        ANIM = 2.5
        self.play(FadeIn(c1, scale=0.92), FadeIn(c2, scale=0.92),
                  GrowFromCenter(dot), run_time=0.5)
        self.play(Write(title), run_time=1.5)
        self.play(Create(line), run_time=0.5)
        self.wait(max(0.5, DURATION - ANIM))
'''


def render_section_animation(key_phrase: str, section_idx: int, duration: float,
                              output_path: str, temp_dir: str):
    accent = ACCENT_CYCLE[section_idx % len(ACCENT_CYCLE)]
    params = json.dumps({
        "phrase":   key_phrase,
        "accent":   accent,
        "duration": duration,
        "flip":     bool(section_idx % 2),
    })

    scene_file = os.path.join(temp_dir, f"scene_{section_idx:03d}.py")
    out_name   = f"anim_{section_idx:03d}"

    with open(scene_file, "w") as f:
        f.write(_SCENE_TEMPLATE)

    env = {**os.environ, "MANIM_PARAMS": params}
    result = subprocess.run(
        [
            "manim", "-qm",
            "--verbosity", "WARNING",
            "--media_dir", temp_dir,
            "--output_file", out_name,
            "--disable_caching",
            scene_file, "SectionScene",
        ],
        capture_output=True, text=True, env=env,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Manim failed (section {section_idx}):\n{result.stderr[-600:]}"
        )

    found = glob.glob(os.path.join(temp_dir, "**", f"{out_name}.mp4"), recursive=True)
    if not found:
        raise RuntimeError(f"Manim output not found for section {section_idx}")
    shutil.move(found[0], output_path)


def create_fallback_clip(duration: float, output_path: str):
    """Solid dark background clip used when Manim fails."""
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=0x0D0D1A:s=1280x720:d={duration}:r=30",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-pix_fmt", "yuv420p",
            output_path,
        ],
        check=True, capture_output=True,
    )
