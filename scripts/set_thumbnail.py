"""Set the custom thumbnail on an EXISTING YouTube video (publish/thumbnail.png).

Usage (CI, where the YouTube creds live):  VIDEO_ID=xxxx python scripts/set_thumbnail.py
Requires the channel to be phone-verified (youtube.com/verify) or YouTube returns 403.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from googleapiclient.http import MediaFileUpload  # noqa: E402
from uploader import _get_youtube  # noqa: E402


def main():
    video_id = os.environ.get("VIDEO_ID") or (sys.argv[1] if len(sys.argv) > 1 else "")
    if not video_id:
        raise SystemExit("provide VIDEO_ID env or arg")
    thumb = os.path.join(ROOT, "publish", "thumbnail.png")
    if not os.path.exists(thumb):
        raise SystemExit("missing publish/thumbnail.png")
    youtube = _get_youtube()
    youtube.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumb)).execute()
    print("THUMBNAIL SET on https://youtube.com/watch?v=" + video_id)


if __name__ == "__main__":
    main()
