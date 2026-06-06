"""Upload an ALREADY-RENDERED video (publish/video.mp4) + thumbnail + captions to YouTube.

Uploads the exact verified file - no re-render, no TTS. Title/description/tags come from
data/color_script.json. Privacy from UPLOAD_PRIVACY env. Runs in CI where the YouTube creds live.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from uploader import upload_video  # noqa: E402


def main():
    with open(os.path.join(ROOT, "data", "color_script.json"), "r", encoding="utf-8") as f:
        script = json.load(f)
    meta = {
        "title": script["title"],
        "description": script["description"],
        "tags": script.get("tags", []),
    }
    video = os.path.join(ROOT, "publish", "video.mp4")
    thumb = os.path.join(ROOT, "publish", "thumbnail.png")
    srt = os.path.join(ROOT, "publish", "captions.srt")
    for p in (video, thumb, srt):
        if not os.path.exists(p):
            raise SystemExit("missing publish asset: %s" % p)
    print("Publishing '%s' (%s)..." % (meta["title"], os.environ.get("UPLOAD_PRIVACY", "public")))
    video_id = upload_video(video, thumb, meta, srt)
    print("PUBLISHED: https://youtube.com/watch?v=" + video_id)


if __name__ == "__main__":
    main()
