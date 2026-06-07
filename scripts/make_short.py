"""Build a true vertical (1080x1920) YouTube Short for the color/red video.

Hand-authors vertical environment scenes timed to a short TTS narration, renders via
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
from blueprint_presets import build_scene_stage  # noqa: E402

FPS = 30


def A(actor_id, asset, slot, color, pose="idle", motion="micro_bob"):
    return {"id": actor_id, "asset": asset, "slot": slot, "colorRole": color, "pose": pose, "motion": motion}


def O(text, role="headline", tone="ink"):
    return {"role": role, "text": text, "tone": tone}


SCENE_CARDS = [
    {
        "sentence": "Two fighters. Same skill. One in red, one in blue.",
        "delivery": "neutral",
        "environment": "arena",
        "actors": [
            A("red_fighter", "person", "red_corner", "accent", "walking"),
            A("blue_fighter", "person", "blue_corner", "blue", "walking"),
            A("referee", "person", "referee_center", "ink", "idle"),
        ],
        "overlay": O("SAME FIGHT\nDIFFERENT COLOR"),
    },
    {
        "sentence": "At the Olympics, the one in red wins more often.",
        "delivery": "weighty",
        "environment": "arena",
        "actors": [
            A("red_fighter", "person", "red_corner", "accent", "arms_up", "idle"),
            A("blue_fighter", "person", "blue_corner", "blue", "sitting", "none"),
            A("referee", "person", "referee_center", "ink", "pointing", "point"),
        ],
        "overlay": O("RED WINS\nMORE OFTEN"),
    },
    {
        "sentence": "So researchers took the same fights and just swapped the colors.",
        "delivery": "neutral",
        "environment": "arena",
        "actors": [
            A("red_fighter", "person", "blue_corner", "accent", "left"),
            A("blue_fighter", "person", "red_corner", "blue", "right"),
            A("referee", "person", "referee_center", "ink", "pointing", "point"),
        ],
        "overlay": O("SAME FOOTAGE\nSWAP COLORS"),
    },
    {
        "sentence": "The red fighter still scored thirteen percent higher.",
        "delivery": "weighty",
        "environment": "arena",
        "actors": [
            A("red_fighter", "person", "red_corner", "accent", "arms_up", "idle"),
            A("blue_fighter", "person", "blue_corner", "blue", "idle"),
            A("referee", "person", "referee_center", "ink", "pointing", "point"),
        ],
        "overlay": O("+13%", role="stat", tone="coral_stamp"),
    },
    {
        "sentence": "Same kick. Same human. Just a different color.",
        "delivery": "weighty",
        "environment": "arena",
        "actors": [
            A("red_fighter", "person", "blue_corner", "accent", "walking"),
            A("blue_fighter", "person", "red_corner", "blue", "walking"),
            A("referee", "person", "referee_center", "ink", "idle"),
        ],
        "overlay": O("SAME KICK\nSAME HUMAN"),
    },
    {
        "sentence": "It was never the fighter. It was the referee.",
        "delivery": "ominous",
        "environment": "courtroom",
        "actors": [
            A("judge", "judge", "judge_bench", "ink", "idle"),
            A("witness", "person", "witness_stand", "blue", "pointing", "point"),
            A("lawyer", "suit", "lawyer_right", "accent", "lean", "lean"),
        ],
        "overlay": O("IT WAS THE\nREFEREE"),
    },
    {
        "sentence": "Full story on Second Glance.",
        "delivery": "warm_cta",
        "environment": "news_studio",
        "actors": [
            A("host", "suit", "host_center", "accent", "pointing", "point"),
            A("guest", "person", "guest_left", "blue", "idle"),
            A("screen", "eye", "screen", "accent", "idle", "none"),
        ],
        "overlay": O("SECOND GLANCE\nFULL STORY"),
    },
]


def main():
    narration = " ".join(c["sentence"] for c in SCENE_CARDS)
    sentences = [{"text": c["sentence"], "delivery": c["delivery"]} for c in SCENE_CARDS]
    temp = tempfile.mkdtemp(prefix="short_")
    audio = os.path.join(temp, "short_audio.mp3")
    timings = synthesize_section(narration, audio, temp, sentences=sentences)

    total_end = timings[-1]["end"] + 0.4
    beats = []
    section = {"section_index": 0, "key_phrase": "SHORT", "environment": "arena", "orientation": "vertical", "vertical": True}
    for i, card in enumerate(SCENE_CARDS):
        start_f = int(round(timings[i]["start"] * FPS))
        end_f = int(round((timings[i + 1]["start"] if i + 1 < len(timings) else total_end) * FPS))
        beat = {
            "id": "card%d" % i, "type": "emphasize", "scene_family": "caption_punch",
            "start": timings[i]["start"], "end": end_f / FPS,
            "startFrame": start_f, "endFrame": end_f,
            "layout": "caption_only", "camera": {"move": "static", "target": "center", "intensity": "none"},
            "transition_in": "hard_cut", "transition_out": "hard_cut", "background": "plain",
            "environment": card["environment"], "vertical": True,
            "actors": card["actors"], "assets": [], "text_overlays": [card["overlay"]], "motion": [],
        }
        beat["blueprint"] = build_scene_stage(beat, [], section)
        beats.append(beat)
    dur_frames = int(round(total_end * FPS))
    episode = {
        "schema_version": 2, "fps": FPS, "width": 1080, "height": 1920,
        "style_version": "clean_flat_light_v1", "renderer": "blueprint",
        "sections": [{"section_index": 0, "durationInFrames": dur_frames, "audioSrc": "",
                      "key_phrase": "SHORT", "narration": narration, "captions": [], "beats": beats,
                      "environment": "arena", "orientation": "vertical", "vertical": True}],
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
