"""Real generator test: ask Gemini to compose several recognizable props as
brand-style primitive shape-lists, validate, and write to data/generated_assets.json.

Run: py scripts/gen_batch_test.py
Loads the Gemini key from C:/Users/Caden/.youtube_bot_gemini_key.txt and injects
the OS trust store so it works on the TLS-intercept network.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
SCRIPTS = os.path.join(ROOT, "scripts")
for p in (SRC, SCRIPTS):
    if p not in sys.path:
        sys.path.insert(0, p)

# OS trust store for the intercept proxy.
try:
    import truststore
    truststore.inject_into_ssl()
except Exception as e:
    print("truststore not active:", e)

KEY_FILE = r"C:\Users\Caden\.youtube_bot_gemini_key.txt"
if not os.environ.get("GEMINI_API_KEY") and os.path.exists(KEY_FILE):
    with open(KEY_FILE, "r", encoding="utf-8") as f:
        os.environ["GEMINI_API_KEY"] = f.read().strip()

from google import genai  # noqa: E402
from gemini_utils import MODELS, PRO_MODELS, generate  # noqa: E402

USE_MODELS = MODELS if os.environ.get("GEN_MODEL", "pro") == "flash" else PRO_MODELS
from generate_asset import (  # noqa: E402
    build_prompt, validate_asset, _parse_json, _response_text, _write_store, _safe_name,
)

TARGETS = [
    ("streetlamp", "city street lamp post: a tall thin vertical pole, and at the TOP of the pole a lantern head (a small box or cap) with a glowing yellow light; small square base at the bottom"),
    ("telescope", "telescope on a tripod: a long cylindrical tube angled diagonally upward, mounted on three splayed tripod legs, with a small eyepiece"),
    ("potted_cactus", "a potted cactus: a tall green saguaro cactus body with two short arms, sitting in a terracotta pot at the bottom"),
    ("microscope", "a lab microscope: a heavy base, an angled eyepiece tube at the top, an objective lens pointing down at a flat stage, on the side an adjustment knob"),
]


def main():
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    ok, fail = [], []
    for name, desc in TARGETS:
        name = _safe_name(name)
        prompt = build_prompt(name, desc)
        try:
            resp = generate(client, prompt, models=USE_MODELS)
            asset = validate_asset(_parse_json(_response_text(resp)), name, desc)
            _write_store(asset["name"], asset)
            ok.append("%s (%d shapes)" % (asset["name"], len(asset["shapes"])))
            print("OK  ", asset["name"], len(asset["shapes"]), "shapes")
        except Exception as e:
            fail.append("%s: %s" % (name, e))
            print("FAIL", name, "->", repr(e))
    print("\n=== DONE ===")
    print("ok:", ok)
    print("fail:", fail)


if __name__ == "__main__":
    main()
