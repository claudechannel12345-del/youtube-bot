"""Build Remotion props for the Cutaway composition from a hand-written script,
using ESTIMATED timings (no TTS/API). For silent local full-length renders.

Usage:  py -3 scripts/build_local_props.py
Writes: remotion/props_gps_local.json
Then:   cd remotion; npx.cmd remotion render src/index.ts Cutaway out.mp4 --props=props_gps_local.json
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

from director import build_episode  # noqa: E402

FPS = 30
WPS = 2.5  # words per second, measured dry pace
LEAD = 0.35  # silence before a section's first sentence
EXTRA_PAUSE = {"weighty": 0.45, "ominous": 0.5, "question": 0.25, "surprised": 0.3, "warm_cta": 0.2}


def estimate_section_timings(section):
    timings = []
    t = LEAD
    for sent in section.get("sentences", []):
        words = max(1, len(str(sent.get("text", "")).split()))
        dur = max(1.1, words / WPS)
        end = t + dur
        timings.append(
            {
                "text": sent.get("text", ""),
                "start": round(t, 3),
                "end": round(end, 3),
                "delivery": sent.get("delivery", "neutral"),
            }
        )
        t = end + 0.32 + EXTRA_PAUSE.get(sent.get("delivery", "neutral"), 0.0)
    return timings


def main():
    script_path = os.path.join(ROOT, "data", "gps_script.json")
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    per_section = [estimate_section_timings(s) for s in script["sections"]]
    episode = build_episode(script, per_section, fps=FPS)

    total_frames = sum(s["durationInFrames"] for s in episode["sections"])
    out_path = os.path.join(ROOT, "remotion", "props_gps_local.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(episode, f, indent=2)

    print("wrote", out_path)
    print("sections:", len(episode["sections"]))
    print("total frames:", total_frames, "(~%.1f s)" % (total_frames / FPS))
    beats = sum(len(s["beats"]) for s in episode["sections"])
    print("beats:", beats)


if __name__ == "__main__":
    main()
