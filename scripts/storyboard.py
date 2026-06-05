"""Proof tool: render ONE still of EVERY scene (beat) in the video, so every scene can
be reviewed before anything is published. This is the manual half of the proof-checker;
proof_check.py adds the automated vision pass on top of the stills this produces.

  py -3 scripts/storyboard.py            # rebuild props, render, extract per-beat stills
  py -3 scripts/storyboard.py --skip-render   # reuse the existing storyboard mp4

Output: remotion/slice_stills/storyboard/NN_sSS_<family>.png  (+ index.txt)
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REMOTION = os.path.join(ROOT, "remotion")
PROPS = os.path.join(REMOTION, "props_gps_local.json")
MP4 = os.path.join(REMOTION, "slice_stills", "storyboard_full.mp4")
OUT = os.path.join(REMOTION, "slice_stills", "storyboard")
FPS = 30
NPX = "npx.cmd" if os.name == "nt" else "npx"


def _env():
    env = {**os.environ}
    if "--use-system-ca" not in env.get("NODE_OPTIONS", ""):
        env["NODE_OPTIONS"] = (env.get("NODE_OPTIONS", "") + " --use-system-ca").strip()
    return env


def _run(cmd):
    subprocess.run(cmd, cwd=REMOTION, env=_env(), check=True, capture_output=True, text=True)


def beat_frames(props):
    """Yield (label, global_midpoint_frame) for every beat."""
    offset = 0
    for s in props["sections"]:
        sec = s["section_index"] + 1
        for j, b in enumerate(s["beats"]):
            mid = offset + (b["startFrame"] + b["endFrame"]) // 2
            label = f"s{sec:02d}_{j}_{b['scene_family']}"
            yield label, mid
        offset += s["durationInFrames"]


def main():
    skip = "--skip-render" in sys.argv
    os.makedirs(OUT, exist_ok=True)

    if not skip:
        subprocess.run([sys.executable, os.path.join(HERE, "build_local_props.py")], check=True)
        print("rendering storyboard mp4 (one pass)...")
        _run([NPX, "remotion", "render", "src/index.ts", "Cutaway",
              os.path.relpath(MP4, REMOTION), "--props=props_gps_local.json"])

    with open(PROPS, "r", encoding="utf-8") as f:
        props = json.load(f)

    index_lines = []
    for i, (label, frame) in enumerate(beat_frames(props)):
        sec = frame / FPS
        out_rel = os.path.relpath(os.path.join(OUT, f"{i:02d}_{label}.png"), REMOTION)
        _run([NPX, "remotion", "ffmpeg", "-ss", f"{sec:.3f}", "-i",
              os.path.relpath(MP4, REMOTION), "-frames:v", "1", out_rel, "-y"])
        index_lines.append(f"{i:02d}_{label}.png  @ frame {frame} ({sec:.1f}s)")
        print("extracted", f"{i:02d}_{label}.png")

    with open(os.path.join(OUT, "index.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(index_lines) + "\n")
    print(f"\nstoryboard: {len(index_lines)} scenes -> {OUT}")


if __name__ == "__main__":
    main()
