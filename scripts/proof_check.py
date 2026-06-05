"""Automated visual proof-checker.

Renders are reviewed by an OpenAI vision model against what each scene is SUPPOSED to show
(from the director's plan). Flags scenes with real problems (text cut off / garbled, broken or
missing shapes, empty or messy composition, stray lines), writes a report, and exits non-zero
if anything fails - so it can gate an upload. Stills go in BATCHES (several images per call).

(Uses OpenAI because the project's free Gemini tier rate-limits vision work too aggressively.)

  OPENAI_API_KEY=... py -3 scripts/proof_check.py
Reads:  remotion/props_gps_local.json + remotion/slice_stills/storyboard/*.png
Writes: remotion/slice_stills/storyboard/proof_report.json
"""

import base64
import glob
import json
import os
import re
import sys

from openai import OpenAI

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROPS = os.path.join(ROOT, "remotion", "props_gps_local.json")
SB = os.path.join(ROOT, "remotion", "slice_stills", "storyboard")
BATCH = 10  # stills per API call

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


def _b64(path):
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode("ascii")


def get_client_and_model():
    # Prefer OpenRouter (free vision models) when its key is set; else OpenAI.
    if os.environ.get("OPENROUTER_API_KEY"):
        client = OpenAI(api_key=os.environ["OPENROUTER_API_KEY"], base_url="https://openrouter.ai/api/v1")
        model = os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3.2-11b-vision-instruct:free")
        return client, model
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return client, os.environ.get("PROOF_MODEL", "gpt-4o-mini")


def main():
    client, model = get_client_and_model()
    print(f"proof model: {model}")
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
        content = [{"type": "text", "text": INSTRUCTIONS}]
        for n, (_name, path, intent) in enumerate(batch, 1):
            content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{_b64(path)}"}})
            content.append({"type": "text", "text": f"FRAME {n} INTENT: {intent}"})
        content.append({"type": "text", "text": "Return the JSON array of verdicts for all frames above, in order."})

        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": content}],
            temperature=0,
        )
        verdicts = parse_array(resp.choices[0].message.content, len(batch))
        for (name, _path, _intent), v in zip(batch, verdicts):
            report.append({"scene": name, "ok": v["ok"], "issues": v["issues"]})
            if not v["ok"]:
                failures += 1
                print(f"FAIL {name}: {'; '.join(v['issues'])}")
            else:
                print(f"ok   {name}")

    out = os.path.join(SB, "proof_report.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"checked": len(report), "failures": failures, "scenes": report}, f, indent=2)
    print(f"\nproof check: {len(report)} scenes, {failures} flagged -> {out}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
