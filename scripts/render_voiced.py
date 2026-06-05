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
from tts_generator import get_audio_duration, synthesize_section  # noqa: E402
from uploader import upload_video  # noqa: E402

FPS = 30


def main():
    script_path = os.path.join(ROOT, "data", "gps_script.json")
    with open(script_path, "r", encoding="utf-8") as f:
        script = json.load(f)

    temp_dir = tempfile.mkdtemp(prefix="cutaway_voiced_")
    try:
        per_section_timings = []
        audio_paths = []
        global_cues = []
        offset = 0.0

        for i, section in enumerate(script["sections"]):
            audio_path = os.path.join(temp_dir, f"cut_audio_{i:03d}.mp3")
            timings = synthesize_section(
                section["narration"],
                audio_path,
                temp_dir,
                sentences=section["sentences"],
            )
            per_section_timings.append(timings)
            audio_paths.append(audio_path)

            for cue in timings:
                global_cues.append(
                    {
                        "text": cue["text"],
                        "start": cue["start"] + offset,
                        "end": cue["end"] + offset,
                    }
                )
            offset += get_audio_duration(audio_path)

        episode = build_episode(script, per_section_timings, fps=FPS)

        out_mp4 = os.path.join(ROOT, "remotion", "slice_stills", "gps_voiced.mp4")
        render_cutaway(episode, audio_paths, out_mp4)

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
