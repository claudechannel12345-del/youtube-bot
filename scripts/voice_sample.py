"""Generate the same passage in several American voices so the owner can pick one.

CI entrypoint:  python scripts/voice_sample.py
Outputs labeled mp3s into voice_samples/ (uploaded as a workflow artifact).
"""

import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

from tts_generator import synthesize_section  # noqa: E402

# Candidate American male voices (gpt-4o-mini-tts).
VOICES = ["ash", "onyx", "echo"]

# A passage that exercises the range: curiosity, doubt, a weighty reveal, a dry line,
# and the warm CTA the owner liked - so each voice is judged on tone consistency too.
SENTENCES = [
    {"text": "Right now, a little blue dot on your phone knows where you are.", "delivery": "curious"},
    {"text": "Your phone isn't sending anything to space.", "delivery": "skeptical"},
    {"text": "Measure how late the signal is, multiply by the speed of light, and you've got the exact distance.", "delivery": "weighty"},
    {"text": "Ignore that, and the blue dot would be useless before lunch.", "delivery": "neutral"},
    {"text": "If you like the universe explained without the breathless hype, stick around - new deep-dives every week.", "delivery": "warm_cta"},
]
TEXT = " ".join(s["text"] for s in SENTENCES)


def main():
    out_dir = os.path.join(ROOT, "voice_samples")
    os.makedirs(out_dir, exist_ok=True)
    temp_dir = tempfile.mkdtemp(prefix="voice_sample_")
    try:
        for i, voice in enumerate(VOICES, start=1):
            out_path = os.path.join(out_dir, f"{i}_{voice}.mp3")
            print(f"Synthesizing voice '{voice}' -> {out_path}")
            synthesize_section(TEXT, out_path, temp_dir, sentences=SENTENCES, voice=voice)
        print("Done. Samples in", out_dir)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
