import os
import shutil
import sys

from google import genai

from research import get_trending_topics, pick_topic
from script_generator import generate_script
from tts_generator import generate_section_audio, get_audio_duration
from video_assembler import assemble_video, download_pexels_video, extract_video_frame
from thumbnail_generator import generate_thumbnail
from uploader import upload_video

TEMP_DIR = "/tmp/yt_bot"

REQUIRED_ENV = [
    "GEMINI_API_KEY",
    "PEXELS_API_KEY",
    "YOUTUBE_API_KEY",
    "YOUTUBE_CLIENT_ID",
    "YOUTUBE_CLIENT_SECRET",
    "YOUTUBE_REFRESH_TOKEN",
]


def main():
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        sys.exit(1)

    os.makedirs(TEMP_DIR, exist_ok=True)

    try:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

        # 1 — Research
        print("[1/6] Researching trending topics...")
        topics = get_trending_topics(os.environ["YOUTUBE_API_KEY"])
        topic_data = pick_topic(topics, client)
        print(f"  Topic : {topic_data['topic']}")
        print(f"  Angle : {topic_data['angle']}")

        # 2 — Script
        print("\n[2/6] Generating script...")
        script = generate_script(topic_data, client)
        print(f"  Title    : {script['title']}")
        print(f"  Sections : {len(script['sections'])}")

        # 3 — Audio + images per section
        print("\n[3/6] Generating audio and fetching images...")
        sections_data = []
        fallback_keywords = topic_data["visual_keywords"]

        for i, section in enumerate(script["sections"]):
            audio_path = os.path.join(TEMP_DIR, f"audio_{i:02d}.mp3")
            generate_section_audio(section["narration"], audio_path)
            duration = get_audio_duration(audio_path)

            bg_video_path = os.path.join(TEMP_DIR, f"bg_{i:02d}.mp4")
            fallback = fallback_keywords[i % len(fallback_keywords)]
            try:
                download_pexels_video(section["visual"], os.environ["PEXELS_API_KEY"], bg_video_path)
            except Exception as e:
                print(f"  Video fallback section {i + 1} ({section['visual']}): {e}")
                download_pexels_video(fallback, os.environ["PEXELS_API_KEY"], bg_video_path)

            sections_data.append({
                "bg_video_path": bg_video_path,
                "audio_path": audio_path,
                "duration": duration,
            })
            print(f"  Section {i + 1}/{len(script['sections'])}: {section['visual']} ({duration:.1f}s)")

        # 4 — Assemble video
        print("\n[4/6] Assembling video...")
        video_path = os.path.join(TEMP_DIR, "output.mp4")
        assemble_video(sections_data, TEMP_DIR, video_path)

        # 5 — Thumbnail (extract first frame of first section's video)
        print("\n[5/6] Generating thumbnail...")
        thumbnail_path = os.path.join(TEMP_DIR, "thumbnail.jpg")
        thumb_bg = os.path.join(TEMP_DIR, "thumb_bg.jpg")
        extract_video_frame(sections_data[0]["bg_video_path"], thumb_bg)
        generate_thumbnail(script["title"], thumbnail_path, background_image_path=thumb_bg)

        # 6 — Upload
        print("\n[6/6] Uploading to YouTube...")
        video_id = upload_video(video_path, thumbnail_path, {
            "title": script["title"],
            "description": script["description"],
            "tags": script["tags"],
        })

        print(f"\nDone! https://youtube.com/watch?v={video_id}")

    finally:
        shutil.rmtree(TEMP_DIR, ignore_errors=True)


if __name__ == "__main__":
    main()
