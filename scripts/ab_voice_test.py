"""A/B the owner's clone: eleven_multilingual_v2 (current fixed settings) vs eleven_v3 (audio tags).

Synthesizes the same emotional lines both ways so the owner can listen and pick. v2 uses the real
production path (per-sentence + context + the fixed delivery maps). v3 uses model_id=eleven_v3 with
inline audio tags for emotion and Natural stability (0.5) - v3 does NOT support style/speaker_boost.

Output: out/ab_test/NN_<label>_v2.mp3 and NN_<label>_v3.mp3

Usage:  py -3 scripts/ab_voice_test.py
"""
import json
import os
import ssl
import sys
import tempfile
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

# ffmpeg for the v2 per-sentence concat path
os.environ["PATH"] = os.path.join(ROOT, "tools") + os.pathsep + os.environ.get("PATH", "")
os.environ.setdefault("ELEVENLABS_INSECURE_SSL", "1")

from elevenlabs_tts import synthesize_section, CHRIS_VOICE_ID  # noqa: E402

VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID") or CHRIS_VOICE_ID


def _load_key():
    key = os.environ.get("ELEVENLABS_API_KEY")
    if key:
        return key.strip()
    p = os.path.join(r"C:\Users\Caden", ".youtube_bot_elevenlabs_key.txt")
    with open(p, "r", encoding="utf-8") as f:
        return f.read().strip()


def _ctx():
    c = ssl.create_default_context()
    if os.environ.get("ELEVENLABS_INSECURE_SSL"):
        c.check_hostname = False
        c.verify_mode = ssl.CERT_NONE
    return c


def synth_v3(text, out_path, api_key):
    """v3: no style/speaker_boost. Natural stability (0.5). Emotion via inline [tags] in text."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    body = {
        "text": text,
        "model_id": "eleven_v3",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.8},
    }
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"),
        headers={"xi-api-key": api_key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
        method="POST",
    )
    with urllib.request.urlopen(req, context=_ctx()) as resp:
        audio = resp.read()
    with open(out_path, "wb") as f:
        f.write(audio)
    return out_path


# (label, v2 sentence list with deliveries, v3 text with audio tags)
TESTS = [
    (
        "opener",
        [{"text": "Okay, you're going to love this one.", "delivery": "brisk"},
         {"text": "Homework was invented as a punishment.", "delivery": "weighty"}],
        "[cheerfully] Okay, you're going to love this one. [dramatically] Homework was invented as a punishment.",
    ),
    (
        "surprised",
        [{"text": "It was small. It was shiny. It beeped. And it scared the United States out of its chair.",
          "delivery": "surprised"}],
        "It was small. It was shiny. It beeped. [surprised] And it scared the United States out of its chair.",
    ),
    (
        "ominous",
        [{"text": "But the real origin of homework isn't one cranky teacher. It's an education system built to shape obedient citizens.",
          "delivery": "ominous"}],
        "[serious] But the real origin of homework isn't one cranky teacher. It's an education system built to shape obedient citizens.",
    ),
    (
        "warm_cta",
        [{"text": "So take a Second Glance.", "delivery": "warm_cta"},
         {"text": "Subscribe, and I'll see you in the next one.", "delivery": "warm_cta"}],
        "[warmly] So take a Second Glance. [smiling] Subscribe, and I'll see you in the next one.",
    ),
]


def main():
    api_key = _load_key()
    os.environ["ELEVENLABS_API_KEY"] = api_key
    out_dir = os.path.join(ROOT, "out", "ab_test")
    os.makedirs(out_dir, exist_ok=True)
    temp = tempfile.mkdtemp(prefix="ab_")
    for i, (label, v2_sents, v3_text) in enumerate(TESTS):
        v2_text = " ".join(s["text"] for s in v2_sents)
        v2_path = os.path.join(out_dir, f"{i:02d}_{label}_v2.mp3")
        v3_path = os.path.join(out_dir, f"{i:02d}_{label}_v3.mp3")
        print(f"[{i}] {label}: v2 (multilingual_v2, fixed settings)...", flush=True)
        synthesize_section(v2_text, v2_path, temp, sentences=v2_sents)
        print(f"[{i}] {label}: v3 (eleven_v3, audio tags)...", flush=True)
        try:
            synth_v3(v3_text, v3_path, api_key)
        except urllib.error.HTTPError as e:
            print(f"    v3 HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:300]}", flush=True)
    print("\nDONE. A/B files in:", out_dir, flush=True)
    for fn in sorted(os.listdir(out_dir)):
        print("  ", fn)


if __name__ == "__main__":
    import urllib.error
    main()
