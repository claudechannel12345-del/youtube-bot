"""LLM script writer for Second Glance. Reads a brief (markdown) and has the model
write the full narration script as structured JSON, so script-writing runs on cheap
API tokens (not the operator's Opus budget). Claude/owner acts as showrunner: brief
it, fact-check, direct.

Usage: py scripts/write_script.py data/briefs/homework_brief.md [out_name]
Default provider OpenAI gpt-5.5 (GEN_PROVIDER/OPENAI_MODEL env to override).
Writes data/scripts/<name>.json and prints a readable version.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(ROOT, "src"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    import truststore
    truststore.inject_into_ssl()
except Exception as e:
    print("truststore not active:", e)


def _load_key(path, env):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            os.environ[env] = f.read().strip()


_load_key(r"C:\Users\Caden\.youtube_bot_openai_key.txt", "OPENAI_API_KEY")
_load_key(r"C:\Users\Caden\.youtube_bot_gemini_key.txt", "GEMINI_API_KEY")

from generate_asset import _parse_json  # noqa: E402

PROVIDER = os.environ.get("GEN_PROVIDER", "openai").lower()
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.5")
DELIVERIES = {"neutral", "curious", "question", "brisk", "weighty", "surprised", "skeptical", "ominous", "warm_cta"}

SYSTEM = (
    "You are the head writer for the YouTube channel Second Glance. Follow the brief exactly, "
    "including its voice, structure, accuracy rules, and TTS rules. Return ONLY valid JSON in the "
    "schema the brief specifies. No markdown, no commentary."
)


def _call_openai(prompt):
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    r = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    return r.choices[0].message.content, r.usage.completion_tokens


def _validate(script):
    if not isinstance(script, dict) or not isinstance(script.get("sections"), list) or not script["sections"]:
        raise ValueError("script must have a non-empty sections list")
    words = 0
    for i, s in enumerate(script["sections"]):
        nar = s.get("narration")
        if not isinstance(nar, list) or not nar:
            raise ValueError("section %d missing narration" % i)
        for line in nar:
            d = line.get("delivery")
            if d not in DELIVERIES:
                line["delivery"] = "neutral"
            words += len(str(line.get("text") or "").split())
    return words


def readable(script):
    out = ["# %s\n" % script.get("title", "UNTITLED")]
    for s in script["sections"]:
        out.append("\n## %s  [%s]" % (s.get("scene_label", "SCENE"), s.get("environment", "")))
        if s.get("on_screen_text"):
            out.append("ON-SCREEN: %s" % " / ".join(t for t in s["on_screen_text"] if t))
        if s.get("visual"):
            out.append("VISUAL: %s" % s["visual"])
        for line in s["narration"]:
            out.append("  [%s] %s" % (line.get("delivery", "neutral"), line.get("text", "")))
    return "\n".join(out)


def main():
    brief_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "briefs", "homework_brief.md")
    out_name = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(os.path.basename(brief_path))[0].replace("_brief", "")
    with open(brief_path, "r", encoding="utf-8") as f:
        brief = f.read()

    text, ctoks = _call_openai(brief)
    script = _parse_json(text)
    words = _validate(script)

    out_dir = os.path.join(ROOT, "data", "scripts")
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, out_name + "_script.json")
    md_path = os.path.join(out_dir, out_name + "_script.md")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(script, f, indent=2)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(readable(script))
    est_min = words / 150.0
    print("wrote", json_path)
    print("wrote", md_path)
    print("sections: %d | words: %d | ~%.1f min | out_tokens: %d" % (
        len(script["sections"]), words, est_min, ctoks))


if __name__ == "__main__":
    main()
