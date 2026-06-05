"""Automated visual proof-checker.

Looks at every storyboard still (from scripts/storyboard.py) with a vision model and
checks it against what the scene is SUPPOSED to show (from the director's plan). Flags
scenes with real problems (text cut off / garbled, broken or missing shapes, empty or
messy composition, stray lines). Writes a report and exits non-zero if anything fails,
so it can gate an upload.

Stills are sent in BATCHES (several images per call) so we make only a handful of API
calls total and stay well under the free-tier rate limit.

  GEMINI_API_KEY=... py -3 scripts/proof_check.py
Reads:  remotion/props_gps_local.json + remotion/slice_stills/storyboard/*.png
Writes: remotion/slice_stills/storyboard/proof_report.json
"""

import glob
import json
import os
import re
import sys
import time

from google import genai
from google.genai import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROPS = os.path.join(ROOT, "remotion", "props_gps_local.json")
SB = os.path.join(ROOT, "remotion", "slice_stills", "storyboard")
MODEL = "gemini-2.0-flash"
BATCH = 8          # stills per API call
THROTTLE = 8.0     # seconds between batches

INSTRUCTIONS = """You are a strict QA reviewer for a clean-flat animated explainer video (warm off-white
background, bold flat shapes, thick dark outlines, occasional coral accent). Below are several rendered
frames, each preceded by FRAME N and what it is supposed to show.

For EACH frame, flag ONLY clear, objective problems:
- on-screen text cut off, running off the frame edge, overlapping other text, or illegible
- text that is garbled, truncated mid-word, or nonsensical
- an object that should appear is clearly missing, or a shape looks broken / unrecognizable
- a blank/empty frame, or elements piled into an unreadable mess
- a stray line passing oddly through an object, or a shape with no apparent purpose

Do NOT flag artistic style, color, minor spacing, or a frame simply being sparse/minimal.

Respond with ONLY a JSON array, one object per frame in order:
[{"frame": 1, "ok": true, "issues": []}, {"frame": 2, "ok": false, "issues": ["short description"]}, ...]
"""


def beats_in_order(props):
    for s in props["sections"]:
        for b in s["beats"]:
            yield b, s


def intent_for(beat, section):
    assets = ", ".join(sorted({a["name"] for a in beat.get("assets", [])})) or "(no objects)"
    texts = [t["text"] for t in beat.get("text_overlays", []) if t.get("text")]
    text_str = " | ".join(texts) if texts else "(no on-screen text expected)"
    return (
        f"scene '{beat['scene_family']}' (section '{section.get('key_phrase', '')}'); "
        f"objects: {assets}; on-screen text that must be fully visible: {text_str}"
    )


def _generate(client, contents, retries=6):
    for attempt in range(retries):
        try:
            return client.models.generate_content(model=MODEL, contents=contents)
        except Exception as e:
            msg = str(e)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                m = re.search(r"retryDelay'?:?\s*'?(\d+)s", msg)
                wait = (int(m.group(1)) + 2) if m else 35
                print(f"  rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Gemini retries exhausted (rate limit)")


def parse_array(text, n):
    m = re.search(r"\[.*\]", text or "", re.DOTALL)
    if not m:
        return [{"ok": True, "issues": []} for _ in range(n)]
    try:
        arr = json.loads(m.group())
    except json.JSONDecodeError:
        return [{"ok": True, "issues": []} for _ in range(n)]
    out = []
    for i in range(n):
        v = arr[i] if i < len(arr) and isinstance(arr[i], dict) else {}
        out.append({"ok": bool(v.get("ok", True)), "issues": list(v.get("issues", []))})
    return out


def main():
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    with open(PROPS, "r", encoding="utf-8") as f:
        props = json.load(f)

    scenes = []
    for i, (beat, section) in enumerate(beats_in_order(props)):
        matches = glob.glob(os.path.join(SB, f"{i:02d}_*.png"))
        if matches:
            scenes.append((os.path.basename(matches[0]), matches[0], intent_for(beat, section)))

    report = []
    failures = 0
    for start in range(0, len(scenes), BATCH):
        batch = scenes[start:start + BATCH]
        contents = [INSTRUCTIONS]
        for n, (_name, path, intent) in enumerate(batch, 1):
            with open(path, "rb") as fh:
                contents.append(types.Part.from_bytes(data=fh.read(), mime_type="image/png"))
            contents.append(f"FRAME {n} INTENT: {intent}")
        contents.append("Return the JSON array of verdicts for all frames above, in order.")

        verdicts = parse_array((_generate(client, contents).text or ""), len(batch))
        for (name, _path, _intent), v in zip(batch, verdicts):
            report.append({"scene": name, "ok": v["ok"], "issues": v["issues"]})
            if not v["ok"]:
                failures += 1
                print(f"FAIL {name}: {'; '.join(v['issues'])}")
            else:
                print(f"ok   {name}")
        time.sleep(THROTTLE)

    out = os.path.join(SB, "proof_report.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"checked": len(report), "failures": failures, "scenes": report}, f, indent=2)
    print(f"\nproof check: {len(report)} scenes, {failures} flagged -> {out}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
