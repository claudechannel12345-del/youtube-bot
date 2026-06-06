"""Re-synthesize ONE section's narration and patch it into the voiced-audio cache.

Use when a single section came out wrong (e.g. a gibberish clip) and you don't want to re-TTS the
whole video. Costs only that section's sentences. Then re-render with REUSE_AUDIO=1.

Usage:
  py -3 scripts/resynth_section.py data/color_script.json <section_index>
"""
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, HERE)

from elevenlabs_tts import synthesize_section  # noqa: E402
from render_voiced import _audio_cache_key  # noqa: E402


def main():
    script_path = sys.argv[1]
    if not os.path.isabs(script_path):
        script_path = os.path.join(ROOT, script_path)
    idx = int(sys.argv[2])
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    cache_dir = os.path.join(ROOT, "out", "voiced_cache")
    cache_meta = os.path.join(cache_dir, "meta.json")
    with open(cache_meta, "r", encoding="utf-8") as f:
        meta = json.load(f)

    section = script["sections"][idx]
    temp_dir = tempfile.mkdtemp(prefix="resynth_")
    try:
        out_mp3 = os.path.join(cache_dir, "cut_audio_%03d.mp3" % idx)
        print("re-synthesizing section %d (%s)..." % (idx, section.get("key_phrase", "")))
        timings = synthesize_section(
            section["narration"], out_mp3, temp_dir, sentences=section["sentences"],
        )
        meta["timings"][idx] = timings
        # Refresh the key so a REUSE_AUDIO render accepts the (now updated) cache under current settings.
        meta["key"] = _audio_cache_key(script)
        with open(cache_meta, "w", encoding="utf-8") as f:
            json.dump(meta, f)
        print("patched cache: %s (%d clips)" % (os.path.basename(out_mp3), len(timings)))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
