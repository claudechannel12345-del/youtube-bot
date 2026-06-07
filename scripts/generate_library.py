"""Grind out a library of brand-style signature props with Gemini, paced for the
free-tier 5 requests/minute cap (ALL models share it).

- Uses PRO_MODELS (quality) since RPM is identical across models.
- Spaces calls >=14s apart (GEMINI_MIN_INTERVAL) -> ~4/min, safely under 5/min.
- Skips props already in data/generated_assets.json (resumable).
- Logs every result to .gen_library_progress.txt (flushed) so progress is visible
  even if background stdout capture drops.

Run: py scripts/generate_library.py
"""
import os
import sys
import time

# Pace BEFORE importing gemini_utils (MIN_INTERVAL is read at import time).
os.environ.setdefault("GEMINI_MIN_INTERVAL", "14")

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
    # File is authoritative: overwrite any stale/conflicting env var (e.g. a Groq key
    # sitting in OPENAI_API_KEY) so we always use the project's real key.
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            os.environ[env] = f.read().strip()


_load_key(r"C:\Users\Caden\.youtube_bot_gemini_key.txt", "GEMINI_API_KEY")
_load_key(r"C:\Users\Caden\.youtube_bot_openai_key.txt", "OPENAI_API_KEY")

# Provider: "openai" (paid, no daily cap, gpt-5.5) is the default; "gemini" stays as a
# free fallback (20 req/day/model rotation).
PROVIDER = os.environ.get("GEN_PROVIDER", "openai").lower()
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5.5")
MAX_CALLS = int(os.environ.get("GEN_MAX_CALLS", "60"))  # runaway/cost guard per run

from generate_asset import (  # noqa: E402
    build_prompt, validate_asset, _parse_json, _response_text, _write_store, _safe_name, _load_store,
)

LOG = os.path.join(ROOT, ".gen_library_progress.txt")

# Free tier = 20 requests/day PER MODEL. Rotate across models so each contributes its
# daily allotment. Ordered best-quality-first. A model is dropped for the rest of the
# run once it returns a daily-quota 429.
MODEL_POOL = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
]

# Signature props that make environments instantly readable. (name, description, env)
LIBRARY = [
    # library / classroom
    ("library_ladder", "a wooden step ladder seen from the side: two slanted side rails joined by four or five evenly spaced horizontal rungs forming a tall narrow A-frame, with feet at the bottom", "library"),
    ("globe", "a classroom globe: a sphere with simple continent shapes on a small tilted stand with a curved meridian arc", "classroom"),
    ("chalkboard", "a classroom chalkboard on a wooden frame stand, dark board surface with a couple of faint chalk lines and a tray at the bottom", "classroom"),
    ("school_desk", "a single school desk: a flat slanted desktop on legs with an attached chair seat", "classroom"),
    # hospital / lab
    ("hospital_bed", "a hospital bed seen from the side: a raised mattress on a frame with wheels, a pillow at the head, and a slightly raised backrest", "hospital"),
    ("wheelchair", "a wheelchair seen from the side: a large rear wheel with spokes, a small front caster, a seat and a backrest, with armrest and footrest", "hospital"),
    ("microscope", "a lab microscope: a heavy base, an angled eyepiece tube at the top, an objective lens pointing down at a flat stage, and an adjustment knob on the side", "lab"),
    ("beaker", "a chemistry beaker: a wide flat-bottomed glass with a pour spout, partly filled with colored liquid, with measurement ticks on the side", "lab"),
    ("flask", "a conical Erlenmeyer flask: a triangular glass body with a narrow neck, partly filled with colored liquid", "lab"),
    # street / city
    ("traffic_light", "a traffic light: a tall pole topped by a vertical dark box housing three stacked round lights, red on top, yellow middle, green bottom", "street"),
    ("fire_hydrant", "a red fire hydrant: a short fat vertical body, a rounded dome cap on top with a small bolt, a chain, and a short nozzle sticking out of each side near the top", "street"),
    ("street_sign", "a street sign: a tall thin pole with a small rectangular sign panel near the top", "street"),
    # space
    ("telescope", "a telescope on a tripod: a long cylindrical tube angled diagonally upward on three splayed tripod legs, with a small eyepiece", "space"),
    ("ringed_planet", "a ringed planet like Saturn: a large sphere with a flat elliptical ring band tilted around its middle, plus a couple of small stars", "space"),
    ("rocket", "a cartoon rocket standing upright: a tube body with a pointed nose cone, two fins at the base, a round window, and a small flame underneath", "space"),
    # desert / nature
    ("cactus_tall", "a tall saguaro cactus: a thick green vertical trunk with two upward-curving arms, with a few spine ticks", "desert"),
    ("pine_tree", "a pine tree: a tall triangular evergreen made of stacked tiers of foliage on a short brown trunk", "forest"),
    ("tent", "a camping tent: a simple triangular ridge tent with a front triangular opening flap", "forest"),
    # office / bank
    ("office_chair", "an office swivel chair seen from the side: a padded seat and tall backrest on a single post with a five-star wheeled base", "office"),
    ("filing_cabinet", "a tall filing cabinet: an upright rectangular cabinet with three or four stacked drawers, each with a small handle", "office"),
    ("vault_door", "a bank vault door: a thick round metal door set in a square frame, with a central spoked wheel handle and bolts around the edge", "bank"),
    # restaurant / kitchen
    ("dining_table", "a restaurant dining table seen from the front: a wide flat round tabletop on a single central pedestal column with a round base, with two round plates and a thin vase sitting on top", "restaurant"),
    ("stove", "a kitchen stove/oven: a boxy appliance with four round burners on the flat top and an oven door with a handle below", "kitchen"),
    ("refrigerator", "a tall kitchen refrigerator: an upright rectangular appliance with two doors (a taller bottom and shorter top) and vertical handles", "kitchen"),
    # gym / farm
    ("dumbbell", "a dumbbell: a short horizontal bar with a large round weight plate on each end", "gym"),
    ("barn", "a red farm barn: a building with a peaked gambrel roof, a tall central door with an X plank pattern, and a small hayloft window", "farm"),
    ("tractor", "a farm tractor seen from the side: a large rear wheel and a smaller front wheel, a body with an exhaust pipe and a driver seat", "farm"),
    # museum / factory / theater / beach
    ("framed_painting", "a framed painting on a wall: a thick rectangular ornate frame around a simple landscape with a hill and sun", "museum"),
    ("robot_arm", "an industrial robot arm: a heavy base, two jointed arm segments, and a gripper claw at the end", "factory_floor"),
    ("theater_curtain", "stage theater curtains: two heavy draped red curtain panels pulled to the sides with tie-backs, and a valance across the top", "theater"),
    ("beach_umbrella", "a beach umbrella: an open canopy with alternating colored panels on a pole tilted slightly, planted in a small mound of sand", "beach"),
    ("palm_tree", "a palm tree: a curved tall trunk topped with several long arching palm fronds, with a couple of coconuts", "beach"),
]


def log(msg):
    line = "%s\n" % msg
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line)
        f.flush()
    print(msg, flush=True)


MIN_INTERVAL = float(os.environ.get("GEMINI_MIN_INTERVAL", "14"))  # 5 RPM cap is shared; pace globally.
_last_call = [0.0]


def _throttle():
    gap = MIN_INTERVAL - (time.time() - _last_call[0])
    if gap > 0:
        time.sleep(gap)
    _last_call[0] = time.time()


def _is_daily_quota(msg):
    return "PerDay" in msg or "RequestsPerDay" in msg


def _is_rate_limit(msg):
    return "429" in msg or "RESOURCE_EXHAUSTED" in msg


def generate_rotating(client, prompt, exhausted):
    """Try MODEL_POOL in order, skipping exhausted models. A daily-quota 429 marks the
    model exhausted (dropped for the rest of the run); a per-minute 429 waits and retries
    the same model once. Returns (response, model) or raises if all models are exhausted."""
    last_err = None
    for model in MODEL_POOL:
        if model in exhausted:
            continue
        for attempt in range(3):
            _throttle()
            try:
                return client.models.generate_content(model=model, contents=prompt), model
            except Exception as e:
                msg = str(e)
                last_err = e
                if _is_rate_limit(msg) and _is_daily_quota(msg):
                    exhausted.add(model)
                    log("  quota exhausted for %s; rotating to next model" % model)
                    break
                if _is_rate_limit(msg):
                    log("  per-minute limit on %s; waiting 20s" % model)
                    time.sleep(20)
                    continue
                if "504" in msg or "DEADLINE" in msg or "503" in msg or "UNAVAILABLE" in msg:
                    log("  transient %s error on %s (attempt %d); retrying" % (
                        msg[:3], model, attempt + 1))
                    continue
                raise
    raise last_err if last_err else RuntimeError("all models exhausted")


def openai_generate(client, prompt):
    """Call OpenAI (gpt-5.5) for one asset; retry transient errors. Returns response text."""
    last_err = None
    for attempt in range(4):
        try:
            r = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
            )
            return r.choices[0].message.content, r.usage.completion_tokens
        except Exception as e:
            msg = str(e)
            last_err = e
            if "429" in msg or "rate" in msg.lower():
                log("  openai rate-limited (attempt %d); waiting 20s" % (attempt + 1))
                time.sleep(20)
                continue
            if any(s in msg for s in ("500", "502", "503", "504", "timeout", "Timeout", "APIConnection")):
                log("  openai transient error (attempt %d); retrying in 8s" % (attempt + 1))
                time.sleep(8)
                continue
            raise
    raise last_err


def main():
    store = _load_store()
    todo = [(n, d) for (n, d, _env) in LIBRARY if _safe_name(n) not in store]
    log("=== LIBRARY RUN START (provider=%s model=%s): %d total, %d done, %d to generate ===" % (
        PROVIDER, OPENAI_MODEL if PROVIDER == "openai" else "rotation",
        len(LIBRARY), len(LIBRARY) - len(todo), len(todo)))

    if PROVIDER == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    else:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"],
                              http_options=types.HttpOptions(timeout=75000))

    exhausted = set()
    ok, fail, calls, out_tokens = 0, 0, 0, 0
    for i, (name, desc) in enumerate(todo, 1):
        sname = _safe_name(name)
        if calls >= MAX_CALLS:
            log("=== HIT MAX_CALLS=%d guard; stopping with %d remaining ===" % (MAX_CALLS, len(todo) - i + 1))
            break
        if PROVIDER == "gemini" and len(exhausted) >= len(MODEL_POOL):
            log("=== ALL MODELS EXHAUSTED for today; stopping with %d remaining ===" % (len(todo) - i + 1))
            break
        try:
            t = time.time()
            calls += 1
            if PROVIDER == "openai":
                txt, ctoks = openai_generate(client, build_prompt(sname, desc))
                out_tokens += ctoks or 0
                model = OPENAI_MODEL
            else:
                resp, model = generate_rotating(client, build_prompt(sname, desc), exhausted)
                txt = _response_text(resp)
            asset = validate_asset(_parse_json(txt), sname, desc)
            _write_store(asset["name"], asset)
            ok += 1
            log("OK  [%d/%d] %s -> %d shapes via %s (%.1fs)" % (
                i, len(todo), asset["name"], len(asset["shapes"]), model, time.time() - t))
        except Exception as e:
            fail += 1
            log("FAIL[%d/%d] %s -> %r" % (i, len(todo), sname, str(e)[:120]))
    cost = out_tokens / 1e6 * 10.0  # rough: ~$10/1M output tokens; input is negligible here
    log("=== LIBRARY RUN DONE: ok=%d fail=%d calls=%d out_tokens=%d (~$%.2f est) ===" % (
        ok, fail, calls, out_tokens, cost))


if __name__ == "__main__":
    main()
