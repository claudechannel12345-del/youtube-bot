"""Build a vertical (1080x1920) YouTube Short for the HOMEWORK video.

Kinetic-typography cut (NO environment scenes): big bold text cards on the brand
cream background. The VO tells the homework-origin story as if it's true, then
pivots ("but almost none of it is true") and sends viewers to the full video for
the real answer — cliffhanger, no payoff revealed.
Output: out/short_hw.mp4 (+ captions). Needs ELEVENLABS_API_KEY in env.
"""
import json
import os
import sys
import tempfile

# Avast intercepts HTTPS with a root not in certifi; route SSL through the Windows store.
import truststore

truststore.inject_into_ssl()

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, HERE)

from elevenlabs_tts import synthesize_section  # noqa: E402
from remotion_renderer import render_cutaway  # noqa: E402
from caption_generator import build_srt  # noqa: E402
from mix_music import find_music, mix_music  # noqa: E402

FPS = 30
VOICE_ID = "OOLdd0jihd5eCDYx6lL9"  # narrator clone, matches the full video
CX = 540  # horizontal center of a 1080-wide frame


def L(idx, text, y, tone="ink", role="headline", h=360, w=980):
    """A centered text element (label) for a text card."""
    return {
        "id": "l%d" % idx, "kind": "label", "asset": "none",
        "position": {"mode": "point", "x": CX, "y": y},
        "size": {"mode": "box", "w": w, "h": h}, "z": 60,
        "text": {"role": role, "text": text, "tone": tone, "maxChars": 90, "fit": "auto"},
    }


# Each card: spoken sentence + delivery + the on-screen text elements.
CARDS = [
    {
        "sentence": "In 1905, an Italian teacher got so fed up with his students that he snapped.",
        "delivery": "neutral",
        "elements": [L(0, "IN 1905\nA TEACHER\nSNAPPED", 900, "ink", h=640)],
    },
    {
        "sentence": "So he invented the ultimate punishment: homework.",
        "delivery": "weighty",
        "elements": [
            L(0, "HE INVENTED", 720, "ink", "label", h=200, w=900),
            L(1, "HOMEWORK", 960, "coral_stamp", "headline", h=320),
            L(2, "as a punishment", 1200, "ink", "label", h=140, w=820),
        ],
    },
    {
        "sentence": "His name was Roberto Nevilis, and his idea spread across the entire world.",
        "delivery": "brisk",
        "elements": [L(0, "ROBERTO\nNEVILIS", 900, "ink", h=540)],
    },
    {
        "sentence": "It's the perfect story.",
        "delivery": "neutral",
        "elements": [L(0, "THE PERFECT\nSTORY", 900, "ink", h=480)],
    },
    {
        "sentence": "But almost none of it is actually true.",
        "delivery": "ominous",
        "elements": [L(0, "BUT IT'S\nNOT TRUE", 900, "coral_stamp", h=480)],
    },
    {
        "sentence": "And the real reason you have homework is far stranger than any punishment.",
        "delivery": "weighty",
        "elements": [L(0, "THE TRUTH IS\nFAR STRANGER", 900, "ink", h=480)],
    },
    {
        "sentence": "The full story is on Second Glance.",
        "delivery": "warm_cta",
        "elements": [
            L(0, "SECOND\nGLANCE", 840, "ink", h=440),
            L(1, "full story →", 1200, "coral_stamp", "label", h=150, w=720),
        ],
    },
]


def _beat(i, start_s, end_s):
    sf = int(round(start_s * FPS))
    ef = int(round(end_s * FPS))
    return {
        "id": "card%d" % i, "type": "emphasize", "scene_family": "comparison_stage",
        "start": start_s, "end": ef / FPS, "startFrame": sf, "endFrame": ef,
        "layout": "caption_only", "camera": {"move": "static", "target": "center", "intensity": "none"},
        "transition_in": "hard_cut", "transition_out": "hard_cut", "background": "plain",
        "assets": [], "text_overlays": [], "motion": [],
        "blueprint": {
            "version": 1, "preset": "comparison_stage", "intent": "thumb",
            "background": {"treatment": "plain"},
            "camera": {"move": "static", "target": "center", "intensity": "none"},
            "elements": CARDS[i]["elements"], "connections": [],
        },
    }


def main():
    narration = " ".join(c["sentence"] for c in CARDS)
    sentences = [{"text": c["sentence"], "delivery": c["delivery"]} for c in CARDS]
    temp = tempfile.mkdtemp(prefix="short_hw_")
    audio = os.path.join(temp, "short_audio.mp3")
    timings = synthesize_section(narration, audio, temp, sentences=sentences, voice=VOICE_ID)

    total_end = timings[-1]["end"] + 0.4
    beats = []
    for i in range(len(CARDS)):
        start_s = timings[i]["start"]
        end_s = timings[i + 1]["start"] if i + 1 < len(timings) else total_end
        beats.append(_beat(i, start_s, end_s))

    dur_frames = int(round(total_end * FPS))
    episode = {
        "schema_version": 2, "fps": FPS, "width": 1080, "height": 1920,
        "style_version": "clean_flat_light_v1", "renderer": "blueprint",
        "sections": [{"section_index": 0, "durationInFrames": dur_frames, "audioSrc": "",
                      "key_phrase": "SHORT", "narration": narration, "captions": [], "beats": beats,
                      "orientation": "vertical", "vertical": True}],
    }
    raw = os.path.join(ROOT, "out", "short_hw_raw.mp4")
    render_cutaway(episode, [audio], raw)

    cues = [{"text": t["text"], "start": t["start"], "end": t["end"]} for t in timings]
    build_srt(cues, os.path.join(ROOT, "out", "short_hw_captions.srt"))

    out = os.path.join(ROOT, "out", "short_hw.mp4")
    music = find_music()
    if music:
        mix_music(raw, music, out, volume=float(os.environ.get("MUSIC_VOLUME", "0.08")))
    else:
        import shutil
        shutil.copyfile(raw, out)
    print("SHORT:", out, "| %.1fs" % total_end)


if __name__ == "__main__":
    main()
