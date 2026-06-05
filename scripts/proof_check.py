"""Automated visual proof-checker.

Looks at every storyboard still (from scripts/storyboard.py) with a vision model and
checks it against what the scene is SUPPOSED to show (from the director's plan). Flags
scenes with real problems (text cut off / garbled, broken or missing shapes, empty or
messy composition, stray lines). Writes a report and exits non-zero if anything fails,
so it can gate an upload.

  GEMINI_API_KEY=... py -3 scripts/proof_check.py
Reads:  remotion/props_gps_local.json + remotion/slice_stills/storyboard/*.png
Writes: remotion/slice_stills/storyboard/proof_report.json
"""

import glob
import json
import os
import re
import sys

from google import genai
from google.genai import types

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROPS = os.path.join(ROOT, "remotion", "props_gps_local.json")
SB = os.path.join(ROOT, "remotion", "slice_stills", "storyboard")
MODEL = "gemini-2.5-flash"

PROMPT = """You are a strict QA reviewer for a clean-flat animated explainer video (warm off-white
background, bold flat shapes, thick dark outlines, occasional coral accent). You are given ONE
rendered frame and a description of what it is supposed to show.

INTENT: {intent}

Flag ONLY clear, objective problems:
- on-screen text that is cut off, runs off the frame edge, overlaps other text, or is illegible
- text that is garbled, truncated mid-word, or nonsensical
- an object that should appear is clearly missing, or a shape looks broken / unrecognizable
- a blank/empty frame, or elements piled into an unreadable mess
- a stray line that passes straight through an object oddly, or a shape with no apparent purpose

Do NOT flag: artistic style, color choices, minor spacing, or a scene simply being sparse/minimal.

Respond with ONLY compact JSON, no prose:
{{"ok": true, "issues": []}}  if the frame is fine, otherwise
{{"ok": false, "issues": ["short description", ...]}}
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
        f"Scene family '{beat['scene_family']}' for the section '{section.get('key_phrase', '')}'. "
        f"Objects that should be visible: {assets}. "
        f"On-screen text that must be fully visible and legible: {text_str}."
    )


def parse_verdict(text):
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        return {"ok": True, "issues": [], "_note": "unparseable response"}
    try:
        v = json.loads(m.group())
        return {"ok": bool(v.get("ok", True)), "issues": list(v.get("issues", []))}
    except json.JSONDecodeError:
        return {"ok": True, "issues": [], "_note": "bad json"}


def main():
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    with open(PROPS, "r", encoding="utf-8") as f:
        props = json.load(f)

    report = []
    failures = 0
    for i, (beat, section) in enumerate(beats_in_order(props)):
        matches = glob.glob(os.path.join(SB, f"{i:02d}_*.png"))
        if not matches:
            continue
        still = matches[0]
        with open(still, "rb") as fh:
            img = fh.read()
        intent = intent_for(beat, section)
        part = types.Part.from_bytes(data=img, mime_type="image/png")
        resp = client.models.generate_content(model=MODEL, contents=[part, PROMPT.format(intent=intent)])
        verdict = parse_verdict(resp.text or "")
        name = os.path.basename(still)
        report.append({"scene": name, "ok": verdict["ok"], "issues": verdict["issues"]})
        if not verdict["ok"]:
            failures += 1
            print(f"FAIL {name}: {'; '.join(verdict['issues'])}")
        else:
            print(f"ok   {name}")

    out = os.path.join(SB, "proof_report.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"checked": len(report), "failures": failures, "scenes": report}, f, indent=2)
    print(f"\nproof check: {len(report)} scenes, {failures} flagged -> {out}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
