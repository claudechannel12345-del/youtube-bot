"""Render the hand-written GPS cutaway with generated narration.

CI entrypoint:
  python scripts/render_voiced.py
"""

import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

from caption_generator import build_srt  # noqa: E402
from director import build_episode  # noqa: E402
from remotion_renderer import render_cutaway  # noqa: E402
from thumbnail_generator import generate_thumbnail  # noqa: E402
from uploader import upload_video  # noqa: E402

# Pluggable narration voice. Default = ElevenLabs (Chris, then owner's clone later);
# set TTS_PROVIDER=openai to fall back to gpt-4o-mini-tts.
TTS_PROVIDER = os.environ.get("TTS_PROVIDER", "elevenlabs").lower()
if TTS_PROVIDER == "openai":
    from tts_generator import synthesize_section  # noqa: E402
else:
    from elevenlabs_tts import synthesize_section  # noqa: E402

FPS = 30


def _audio_cache_key(script):
    """Hash everything that affects the rendered audio (text + delivery + voice + TTS settings) so a
    cache can be safely reused for VISUAL-only changes but is invalidated when the audio would differ."""
    import hashlib
    import elevenlabs_tts as el

    h = hashlib.sha256()
    for s in script["sections"]:
        for x in s["sentences"]:
            h.update(("%s\x1f%s\x1e" % (x.get("text", ""), x.get("delivery", ""))).encode("utf-8"))
    sig = {
        "voice": os.environ.get("ELEVENLABS_VOICE_ID") or el.CHRIS_VOICE_ID,
        "provider": TTS_PROVIDER,
        "defaults": el.DEFAULT_SETTINGS,
        "style": el.DELIVERY_STYLE, "stability": el.DELIVERY_STABILITY,
        "speed": el.DELIVERY_SPEED, "pause": el.PAUSE_AFTER,
    }
    h.update(json.dumps(sig, sort_keys=True).encode("utf-8"))
    return h.hexdigest()


def main():
    # Which script to voice. Default GPS for back-compat; set SCRIPT_PATH=data/color_script.json
    # (or any path) to render a different video.
    script_path = os.environ.get("SCRIPT_PATH") or os.path.join(ROOT, "data", "gps_script.json")
    if not os.path.isabs(script_path):
        script_path = os.path.join(ROOT, script_path)
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    # Audio cache: lets a VISUAL-only re-render skip TTS entirely. Set REUSE_AUDIO=1 to reuse the
    # cached audio when text/delivery/voice/settings are unchanged (key match); otherwise re-synth.
    cache_dir = os.path.join(ROOT, "out", "voiced_cache")
    os.makedirs(cache_dir, exist_ok=True)
    cache_meta = os.path.join(cache_dir, "meta.json")
    cache_key = _audio_cache_key(script) if TTS_PROVIDER == "elevenlabs" else None

    temp_dir = tempfile.mkdtemp(prefix="cutaway_voiced_")
    try:
        per_section_timings = None
        audio_paths = None
        if os.environ.get("REUSE_AUDIO") == "1" and cache_key and os.path.exists(cache_meta):
            with open(cache_meta, "r", encoding="utf-8") as f:
                meta = json.load(f)
            files = [os.path.join(cache_dir, p) for p in meta.get("audio", [])]
            if meta.get("key") == cache_key and files and all(os.path.exists(p) for p in files):
                per_section_timings = meta["timings"]
                audio_paths = files
                print("REUSING cached audio - %d sections, NO TTS" % len(files))
            else:
                print("REUSE_AUDIO set but cache stale/missing; re-synthesizing.")

        if per_section_timings is None:
            per_section_timings = []
            audio_paths = []
            for i, section in enumerate(script["sections"]):
                audio_path = os.path.join(temp_dir, f"cut_audio_{i:03d}.mp3")
                timings = synthesize_section(
                    section["narration"], audio_path, temp_dir, sentences=section["sentences"],
                )
                per_section_timings.append(timings)
                audio_paths.append(audio_path)
            # Save to cache for future visual-only re-renders.
            if cache_key:
                cached = []
                for i, p in enumerate(audio_paths):
                    name = "cut_audio_%03d.mp3" % i
                    shutil.copy(p, os.path.join(cache_dir, name))
                    cached.append(name)
                with open(cache_meta, "w", encoding="utf-8") as f:
                    json.dump({"key": cache_key, "timings": per_section_timings, "audio": cached}, f)

        global_cues = []
        offset = 0.0
        for timings in per_section_timings:
            for cue in timings:
                global_cues.append({"text": cue["text"], "start": cue["start"] + offset, "end": cue["end"] + offset})
            offset += timings[-1]["end"] if timings else 0.0

        episode = build_episode(script, per_section_timings, fps=FPS)
        # Use the faithful blueprint renderer by default (the engine's current path); override with
        # CUTAWAY_RENDERER=legacy to fall back to the old family renderer.
        episode["renderer"] = os.environ.get("CUTAWAY_RENDERER", "blueprint")

        out_mp4 = os.path.join(ROOT, "remotion", "slice_stills", "gps_voiced.mp4")
        render_cutaway(episode, audio_paths, out_mp4)

        # Subtle background-music bed (CGP-Grey style), if a track is available. Looped under the
        # narration at low volume with fades. Drop a file in data/music/ or set MUSIC_PATH; set
        # MUSIC_VOLUME to tune (default 0.10), MUSIC_DUCK=1 to dip music under the voice.
        from mix_music import find_music, mix_music  # noqa: E402
        music = find_music()
        if music:
            mixed = os.path.join(ROOT, "remotion", "slice_stills", "gps_voiced_music.mp4")
            try:
                mix_music(
                    out_mp4, music, mixed,
                    volume=float(os.environ.get("MUSIC_VOLUME", "0.10")),
                    duck=os.environ.get("MUSIC_DUCK") == "1",
                )
                out_mp4 = mixed
                print("mixed background music:", os.path.basename(music))
            except Exception as e:
                print("music mix skipped (", e, ")")

        srt_path = os.path.join(temp_dir, "gps_voiced.srt")
        build_srt(global_cues, srt_path)

        if os.environ.get("DO_UPLOAD") == "1":
            os.environ.setdefault("UPLOAD_PRIVACY", "unlisted")
            thumb = os.path.join(temp_dir, "thumb.jpg")
            generate_thumbnail(script["title"], thumb)
            video_id = upload_video(
                out_mp4,
                thumb,
                {
                    "title": script["title"],
                    "description": script["description"],
                    "tags": script["tags"],
                },
                srt_path,
            )
            print("https://youtube.com/watch?v=" + video_id)
        else:
            print(out_mp4)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
