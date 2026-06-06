"""Build a true vertical (1080x1920) YouTube Short for the color/red video.

Hand-authors vertical blueprint 'cards' (explicit coords) timed to a short TTS narration, renders via
the Cutaway comp at vertical dims, mixes music. Output: out/short.mp4 (+ captions).
Run with the ElevenLabs env (see render_voiced).
"""
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, HERE)

from elevenlabs_tts import synthesize_section  # noqa: E402
from remotion_renderer import render_cutaway  # noqa: E402
from caption_generator import build_srt  # noqa: E402
from mix_music import find_music, mix_music  # noqa: E402

FPS = 30
CX = 540  # vertical-frame center x


def T(text, y, w, h, role="headline", tone="ink", z=60):
    return {"id": "t_%d" % y, "kind": "label", "asset": "none",
            "position": {"mode": "point", "x": CX, "y": y}, "size": {"mode": "box", "w": w, "h": h},
            "z": z, "text": {"role": role, "text": text, "tone": tone, "maxChars": 90, "fit": "auto"}}


def P(asset, y, scale, color, z=30, eid=None):
    return {"id": eid or ("a_%d" % y), "kind": "prop", "asset": asset,
            "position": {"mode": "point", "x": CX, "y": y}, "size": {"mode": "scale", "scale": scale},
            "z": z, "colorRole": color}


# Each card: (sentence text, delivery, [blueprint elements]) - explicit VERTICAL coords.
CARDS = [
    ("Two fighters. Same skill. One in red, one in blue.", "neutral", [
        T("SAME FIGHT,\nDIFFERENT COLOR", 300, 960, 360, role="headline", tone="ink"),
        P("person", 820, 2.0, "accent"), P("person", 1380, 2.0, "blue"),
    ]),
    ("At the Olympics, the one in red wins more often.", "weighty", [
        T("THE ONE IN RED\nWINS MORE OFTEN", 960, 1000, 600, role="headline", tone="ink"),
    ]),
    ("So researchers took the same fights and just swapped the colors.", "neutral", [
        T("SAME FOOTAGE.\nSWAP THE COLORS.", 960, 1000, 600, role="headline", tone="ink"),
    ]),
    ("The red fighter still scored thirteen percent higher.", "weighty", [
        T("+13%", 820, 900, 460, role="stat", tone="coral_stamp"),
        T("MORE POINTS FOR RED", 1240, 1000, 200, role="label", tone="ink"),
    ]),
    ("Same kick. Same human. Just a different color.", "weighty", [
        T("SAME KICK.\nSAME HUMAN.", 960, 1000, 600, role="headline", tone="ink"),
    ]),
    ("It was never the fighter. It was the referee.", "ominous", [
        T("IT WAS THE\nREFEREE", 960, 1000, 600, role="headline", tone="ink"),
    ]),
    ("Full story on Second Glance.", "warm_cta", [
        P("eye", 760, 2.2, "accent"),
        T("SECOND GLANCE", 1180, 1000, 200, role="headline", tone="ink"),
        T("FULL VIDEO IN THE DESCRIPTION", 1380, 1000, 150, role="label", tone="coral_stamp"),
    ]),
]


def main():
    narration = " ".join(c[0] for c in CARDS)
    sentences = [{"text": c[0], "delivery": c[1]} for c in CARDS]
    temp = tempfile.mkdtemp(prefix="short_")
    audio = os.path.join(temp, "short_audio.mp3")
    timings = synthesize_section(narration, audio, temp, sentences=sentences)

    total_end = timings[-1]["end"] + 0.4
    beats = []
    for i, (text, delivery, elements) in enumerate(CARDS):
        start_f = int(round(timings[i]["start"] * FPS))
        end_f = int(round((timings[i + 1]["start"] if i + 1 < len(timings) else total_end) * FPS))
        beats.append({
            "id": "card%d" % i, "type": "emphasize", "scene_family": "caption_punch",
            "start": timings[i]["start"], "end": end_f / FPS,
            "startFrame": start_f, "endFrame": end_f,
            "layout": "caption_only", "camera": {"move": "static", "target": "center", "intensity": "none"},
            "transition_in": "hard_cut", "transition_out": "hard_cut", "background": "plain",
            "assets": [], "text_overlays": [], "motion": [],
            "blueprint": {"version": 1, "preset": "caption_punch", "intent": "short",
                          "background": {"treatment": "plain"},
                          "camera": {"move": "static", "target": "center", "intensity": "none"},
                          "elements": elements, "connections": []},
        })
    dur_frames = int(round(total_end * FPS))
    episode = {
        "schema_version": 2, "fps": FPS, "width": 1080, "height": 1920,
        "style_version": "clean_flat_light_v1", "renderer": "blueprint",
        "sections": [{"section_index": 0, "durationInFrames": dur_frames, "audioSrc": "",
                      "key_phrase": "SHORT", "narration": narration, "captions": [], "beats": beats}],
    }
    raw = os.path.join(ROOT, "out", "short_raw.mp4")
    render_cutaway(episode, [audio], raw)

    # captions
    cues = [{"text": t["text"], "start": t["start"], "end": t["end"]} for t in timings]
    build_srt(cues, os.path.join(ROOT, "out", "short_captions.srt"))

    out = os.path.join(ROOT, "out", "short.mp4")
    music = find_music()
    if music:
        mix_music(raw, music, out, volume=float(os.environ.get("MUSIC_VOLUME", "0.08")))
    else:
        import shutil
        shutil.copyfile(raw, out)
    print("SHORT:", out, "| %.1fs" % total_end)


if __name__ == "__main__":
    main()
