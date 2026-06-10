"""Render a full horizontal video from a Second Glance script JSON
(data/scripts/<name>_script.json produced by write_script.py).

Each script section becomes one held environment SCENE (still camera, micro-bobbing
actors, the new generated set_props carrying recognizability) with one short headline
overlay. Narration is TTS'd in your voice (ElevenLabs) with per-line delivery; music
is mixed under. Output: out/<name>.mp4 (+ captions).

Run with ELEVENLABS_API_KEY set (loaded from the key file below if present).
Usage: py scripts/make_video_from_script.py data/scripts/homework_script.json
"""
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, HERE)

# Bundled ffmpeg/ffprobe live in tools/ (gitignored, not on PATH). The TTS + mux steps
# shell out to "ffmpeg"/"ffprobe", so make sure they resolve.
os.environ["PATH"] = os.path.join(ROOT, "tools") + os.pathsep + os.environ.get("PATH", "")

# Keys + intercept-network SSL flags BEFORE importing the TTS/render modules.
for fname, env in ((".youtube_bot_elevenlabs_key.txt", "ELEVENLABS_API_KEY"),):
    p = os.path.join(r"C:\Users\Caden", fname)
    if not os.environ.get(env) and os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            os.environ[env] = f.read().strip()
os.environ.setdefault("ELEVENLABS_INSECURE_SSL", "1")
os.environ.setdefault("REMOTION_USE_SYSTEM_CA", "1")
os.environ.setdefault("NODE_OPTIONS", "--use-system-ca")

from elevenlabs_tts import synthesize_section  # noqa: E402
from remotion_renderer import render_cutaway  # noqa: E402
from caption_generator import build_srt  # noqa: E402
from mix_music import find_music, mix_music  # noqa: E402
from blueprint_presets import build_scene_stage  # noqa: E402
from env_resolver import ensure_environments, last_resolution_events  # noqa: E402
from environments import get_environment  # noqa: E402

FPS = 30
W, H = 1920, 1080

# 1-2 actors per environment, staged into valid slots (build_scene_stage falls back if a
# slot name is off). The generated set_props carry the "where am I" recognizability.
ENV_ACTORS = {
    "classroom": [("person", "teacher", "ink"), ("person", "student_left", "blue")],
    "courtroom": [("person", "judge_bench", "ink"), ("person", "witness_stand", "accent")],
    "newsroom": [("person", "anchor_center", "accent")],
    "news_studio": [("person", "host_center", "accent"), ("person", "guest_left", "blue")],
    "library": [("person", "reader", "accent")],
    "space": [("person", "subject_center", "accent")],
    "office": [("person", "person_left", "accent"), ("person", "person_right", "blue")],
    "street": [("person", "pedestrian_center", "accent")],
}


def actors_for(env):
    spec = ENV_ACTORS.get(env)
    if spec is None:
        spec = _actors_from_environment_slots(env) or [("person", "", "accent")]
    return [
        {"id": "a%d" % i, "asset": a, "slot": s, "colorRole": c, "motion": "micro_bob"}
        for i, (a, s, c) in enumerate(spec)
    ]


def _actors_from_environment_slots(env):
    try:
        environment = get_environment(env)
    except Exception:
        return []
    if not environment.get("generated"):
        return []
    slots = list((environment.get("slots") or {}).keys())[:2]
    colors = ["accent", "blue"]
    return [("person", slot, colors[i % len(colors)]) for i, slot in enumerate(slots)]


def _section_environment(sec):
    return str(sec.get("environment") or "classroom").strip() or "classroom"


def _section_environment_description(sec):
    parts = [
        sec.get("scene_label"),
        sec.get("visual"),
    ]
    ost = [str(t).strip() for t in (sec.get("on_screen_text") or []) if str(t).strip()]
    if ost:
        parts.append(ost[0])
    text = " ".join(str(part).strip() for part in parts if str(part or "").strip())
    return text[:500]


def main():
    script_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "scripts", "homework_script.json")
    name = os.path.splitext(os.path.basename(script_path))[0].replace("_script", "")
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)
    sections = script["sections"]
    allow_create = os.environ.get("ENV_AUTOCREATE", "1").strip() != "0"
    env_specs = [
        {"id": _section_environment(sec), "description": _section_environment_description(sec)}
        for sec in sections
    ]
    env_map = ensure_environments(env_specs, allow_create=allow_create)
    for info in last_resolution_events().values():
        print(
            "ENV_RESOLVE %s requested=%s resolved=%s"
            % (str(info.get("status", "")).upper(), info.get("requested"), info.get("resolved")),
            flush=True,
        )

    # Flatten all narration lines (in order); remember section boundaries by sentence index.
    sentences, sec_ranges = [], []
    for sec in sections:
        start_idx = len(sentences)
        for line in sec["narration"]:
            sentences.append({"text": line["text"], "delivery": line.get("delivery", "neutral")})
        sec_ranges.append((start_idx, len(sentences)))  # [start, end) sentence indices

    narration = " ".join(s["text"] for s in sentences)
    temp = tempfile.mkdtemp(prefix="vid_")
    audio = os.path.join(temp, "narration.mp3")
    print("TTS: %d lines..." % len(sentences), flush=True)
    # section_starts = where each section begins (v3 chunks on these so seams land on topic boundaries).
    # plain_until = end of section 0 so the cold-open intro reads fully plain (owner: less intro emotion).
    section_starts = [r[0] for r in sec_ranges]
    plain_until = sec_ranges[0][1] if sec_ranges else 0
    timings = synthesize_section(narration, audio, temp, sentences=sentences,
                                 section_starts=section_starts, plain_until=plain_until)
    total_end = timings[-1]["end"] + 0.4
    # Persist the narration audio so it can be transcribe-verified (gibberish check) independent of the
    # video render. Saved BEFORE render so a render failure still leaves the audio to inspect.
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    saved_audio = os.path.join(ROOT, "out", name + "_audio.mp3")
    import shutil as _shutil
    _shutil.copyfile(audio, saved_audio)
    print("AUDIO:", saved_audio, flush=True)
    if os.environ.get("AUDIO_ONLY", "").strip() == "1":
        print("AUDIO_ONLY=1 -> skipping video render", flush=True)
        return

    beats = []
    for si, sec in enumerate(sections):
        s_start, s_end = sec_ranges[si]
        if s_start >= len(timings):
            continue
        start_t = timings[s_start]["start"]
        end_t = timings[min(s_end, len(timings)) - 1]["end"]
        requested_env = _section_environment(sec)
        env = env_map.get(requested_env) or "classroom"
        ost = [t for t in (sec.get("on_screen_text") or []) if t]
        overlay = [{"role": "headline", "text": ost[0][:48], "tone": "ink"}] if ost else []
        beat = {
            "id": "sec%d" % si, "type": "emphasize", "scene_family": "scene_stage",
            "layout": "wide_scene", "start": start_t, "end": end_t,
            "startFrame": int(round(start_t * FPS)), "endFrame": int(round(end_t * FPS)),
            "camera": {"move": "static", "target": "center", "intensity": "none"},
            "transition_in": "hard_cut", "transition_out": "hard_cut", "background": "plain",
            "environment": env, "actors": actors_for(env), "assets": [],
            "text_overlays": overlay, "motion": [],
        }
        beat["blueprint"] = build_scene_stage(beat, [], {"environment": env, "section_index": 0})
        beats.append(beat)

    dur_frames = int(round(total_end * FPS))
    episode = {
        "schema_version": 2, "fps": FPS, "width": W, "height": H,
        "style_version": "clean_flat_light_v1", "renderer": "blueprint",
        "sections": [{
            "section_index": 0, "durationInFrames": dur_frames, "audioSrc": "",
            "key_phrase": script.get("title", "VIDEO"), "narration": narration,
            "captions": [], "beats": beats,
        }],
    }
    raw = os.path.join(ROOT, "out", name + "_raw.mp4")
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    print("rendering %d scenes, %.1fs..." % (len(beats), total_end), flush=True)
    render_cutaway(episode, [audio], raw)

    cues = [{"text": t["text"], "start": t["start"], "end": t["end"]} for t in timings]
    build_srt(cues, os.path.join(ROOT, "out", name + "_captions.srt"))

    out = os.path.join(ROOT, "out", name + ".mp4")
    music = find_music()
    if music:
        mix_music(raw, music, out, volume=float(os.environ.get("MUSIC_VOLUME", "0.08")))
    else:
        import shutil
        shutil.copyfile(raw, out)
    print("VIDEO:", out, "| %.1fs | %d scenes" % (total_end, len(beats)), flush=True)


if __name__ == "__main__":
    main()
