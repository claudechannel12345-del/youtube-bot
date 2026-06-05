"""Generate ElevenLabs voice samples (same passage as the OpenAI sampler) so the
owner can A/B them. Writes mp3s to ~/Desktop/voice_samples.

  ELEVENLABS_API_KEY=... ELEVENLABS_INSECURE_SSL=1 py -3 scripts/voice_sample_eleven.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

from elevenlabs_tts import synthesize  # noqa: E402

# Natural "real-guy" American male voices (not the character ones).
VOICES = [
    ("Chris", "iP95p4xoKVk53GoZ742B"),
    ("Will", "bIHbv24MWmeRgasZH58o"),
    ("Brian", "nPczCjzI2devNBz1zQrb"),
    ("Liam", "TX3LPaxmHKxFdv7VOQHJ"),
]

TEXT = (
    "Right now, a little blue dot on your phone knows where you are. "
    "Your phone isn't sending anything to space. "
    "Measure how late the signal is, multiply by the speed of light, and you've got the exact distance. "
    "Ignore that, and the blue dot would be useless before lunch. "
    "If you like the universe explained without the breathless hype, stick around - new deep-dives every week."
)


def main():
    out = os.path.join(os.path.expanduser("~"), "Desktop", "voice_samples")
    os.makedirs(out, exist_ok=True)

    for i, (name, vid) in enumerate(VOICES, start=1):
        path = os.path.join(out, f"el_{i}_{name}_v2.mp3")
        print("generating", path)
        synthesize(TEXT, path, vid, model_id="eleven_multilingual_v2")

    # Model comparison: same voice (Chris) in the cheaper Flash model.
    path = os.path.join(out, "el_5_Chris_flash.mp3")
    print("generating", path)
    synthesize(TEXT, path, "iP95p4xoKVk53GoZ742B", model_id="eleven_flash_v2_5")

    print("done ->", out)


if __name__ == "__main__":
    main()
