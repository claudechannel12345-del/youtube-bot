import json
import os
import shutil
import sys
import datetime

from google import genai

from research import pick_topic
from script_generator import generate_script
from tts_generator import synthesize_section, get_audio_duration
from caption_generator import build_srt
from remotion_renderer import render_video
from shorts_generator import render_shorts, select_short_segments
from shot_provider import NoneProvider, get_provider, select_hero_indices
from thumbnail_generator import generate_thumbnail
from uploader import upload_short, upload_video
from production_log import write_log

TEMP_DIR = "/tmp/yt_bot"
CUES = []
TOPIC_HISTORY_PATH = os.path.join("data", "topic_history.json")

REQUIRED_ENV = [
    "GEMINI_API_KEY",
    "OPENAI_API_KEY",
    "YOUTUBE_CLIENT_ID",
    "YOUTUBE_CLIENT_SECRET",
    "YOUTUBE_REFRESH_TOKEN",
]


def _append_topic_history(title):
    os.makedirs(os.path.dirname(TOPIC_HISTORY_PATH), exist_ok=True)
    try:
        with open(TOPIC_HISTORY_PATH, "r", encoding="utf-8") as f:
            history = json.load(f)
    except (OSError, json.JSONDecodeError):
        history = []
    if not isinstance(history, list):
        history = []

    history.append(title)
    history = [item for item in history if isinstance(item, str)][-50:]

    with open(TOPIC_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=True)


def main():
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        sys.exit(1)

    os.makedirs(TEMP_DIR, exist_ok=True)
    CUES.clear()

    try:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

        # 1 - Research
        print("[1/6] Picking today's topic...")
        topic_data = pick_topic(client)
        print(f"  Topic : {topic_data['topic']}")
        print(f"  Angle : {topic_data['angle']}")

        # 2 - Script
        print("\n[2/6] Generating script...")
        script = generate_script(topic_data, client)
        print(f"  Title    : {script['title']}")
        print(f"  Sections : {len(script['sections'])}")

        provider = get_provider()
        max_ai_clips = _env_int("MAX_AI_CLIPS", 0)
        if isinstance(provider, NoneProvider):
            hero_idx = set()
        else:
            hero_idx = set(select_hero_indices(script["sections"], max_ai_clips))
        ai_clip_count = 0

        # 3 - Audio per section
        print("\n[3/6] Generating section audio...")
        sections_data = []
        global_offset = 0.0

        for i, section in enumerate(script["sections"]):
            audio_path = os.path.join(TEMP_DIR, f"audio_{i:02d}.mp3")
            sent_timings = synthesize_section(
                section["narration"], audio_path, TEMP_DIR, sentences=section.get("sentences")
            )
            duration = get_audio_duration(audio_path)
            for entry in sent_timings:
                CUES.append({
                    "text": entry["text"],
                    "start": global_offset + entry["start"],
                    "end": global_offset + entry["end"],
                })
            global_offset += duration

            key_phrase = (section.get("key_phrase") or
                          " ".join(section["narration"].split()[:4]))

            section_dict = {
                "audio_path": audio_path,
                "duration": duration,
                "template": section.get("template") or "title_card",
                "key_phrase": key_phrase,
                "on_screen": section.get("on_screen") or {},
                "captions": sent_timings,
            }

            if i in hero_idx and ai_clip_count < max_ai_clips:
                clip_path = os.path.join(TEMP_DIR, f"clip_{i:02d}.mp4")
                prompt = _hero_prompt(section, key_phrase)
                seconds = min(duration, _env_float("VEO_MAX_SECONDS", 6.0))
                if provider.generate_clip(prompt, seconds, clip_path):
                    section_dict["video_path"] = clip_path
                    ai_clip_count += 1
                    print(f"  AI hero clip generated for section {i + 1}")

            sections_data.append(section_dict)
            print(f"  Section {i + 1}/{len(script['sections'])}: "
                  f"{key_phrase[:35]} ({duration:.1f}s)")

        provider_name = os.environ.get("SHOT_PROVIDER", "none").lower()
        if isinstance(provider, NoneProvider):
            provider_name = "none"
        print(f"  AI hero clips: {ai_clip_count} (provider={provider_name})")

        # 4 - Render video with Remotion
        print("\n[4/6] Rendering video with Remotion...")
        video_path = os.path.join(TEMP_DIR, "output.mp4")
        render_video(sections_data, video_path)
        srt_path = os.path.join(TEMP_DIR, "captions.srt")
        build_srt(CUES, srt_path)

        # 5 - Thumbnail
        print("\n[5/6] Generating thumbnail...")
        thumbnail_path = os.path.join(TEMP_DIR, "thumbnail.jpg")
        generate_thumbnail(script["title"], thumbnail_path)

        # 6 - Upload
        print("\n[6/6] Uploading to YouTube...")
        video_id = upload_video(video_path, thumbnail_path, {
            "title": script["title"],
            "description": script["description"],
            "tags": script["tags"],
        }, srt_path)

        print(f"\nDone! https://youtube.com/watch?v={video_id}")
        _append_topic_history(script["title"])
        short_video_ids = []
        if os.environ.get("MAKE_SHORTS", "1") != "0":
            try:
                print("\n[Shorts] Rendering and uploading Shorts...")
                groups = select_short_segments(script["sections"], sections_data)
                shorts = render_shorts(sections_data, groups, TEMP_DIR)
                for index, short in enumerate(shorts, start=1):
                    metadata = _short_metadata(script, sections_data, short["section_indices"])
                    short_id = upload_short(short["path"], metadata)
                    short_video_ids.append(short_id)
                    print(f"  Short {index}: https://youtube.com/watch?v={short_id}")
                if not shorts:
                    print("  No viable Shorts selected.")
            except Exception as e:
                print(f"WARNING: Shorts generation/upload failed (non-fatal): {e}")
        try:
            log_path = write_log({
                "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "video_id": video_id,
                "topic": topic_data["topic"],
                "angle": topic_data["angle"],
                "why_original": topic_data.get("why_original"),
                "key_facts": topic_data.get("key_facts"),
                "title": script["title"],
                "title_options": script.get("title_options"),
                "hook_options": script.get("hook_options"),
                "thumbnail_text_options": script.get("thumbnail_text_options"),
                "section_count": len(script["sections"]),
                "templates": [s.get("template") for s in script["sections"]],
                "deliveries": [
                    s.get("delivery")
                    for sec in script["sections"]
                    for s in (sec.get("sentences") or [])
                ],
                "shorts": short_video_ids,
            })
            print(f"Production log written: {log_path}")
        except Exception as e:
            print(f"WARNING: Production log write failed (non-fatal): {e}")

    finally:
        shutil.rmtree(TEMP_DIR, ignore_errors=True)


def _hero_prompt(section, key_phrase):
    keywords = section.get("broll_keywords") or []
    if isinstance(keywords, (list, tuple)):
        keyword_text = ", ".join(str(item) for item in keywords)
    else:
        keyword_text = str(keywords)
    parts = [str(key_phrase)]
    if keyword_text:
        parts.append(keyword_text)
    return ". ".join(parts)


def _env_int(name, default):
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


def _env_float(name, default):
    try:
        return float(os.environ.get(name, str(default)))
    except ValueError:
        return default


def _short_metadata(script, sections_data, section_indices):
    first = sections_data[section_indices[0]] if section_indices else {}
    hook = str(first.get("key_phrase") or script.get("title") or "Cosmic short").strip()
    title = hook[:80].rstrip()
    if "#shorts" not in title.lower():
        title = f"{title} #Shorts"
    description = (
        f"{hook}\n\n"
        f"From: {script.get('title', '')}\n"
        "Subscribe for the full cosmic story.\n"
        "#Shorts"
    )
    tags = list(script.get("tags") or [])
    for tag in ["Shorts", "space", "science"]:
        if tag not in tags:
            tags.append(tag)
    return {
        "title": title,
        "description": description,
        "tags": tags[:15],
    }


if __name__ == "__main__":
    main()
