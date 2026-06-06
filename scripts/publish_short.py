"""Upload publish/short.mp4 as a YouTube Short (#Shorts, links to the full video)."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from uploader import upload_video
FULL = os.environ.get("FULL_VIDEO_URL", "")
meta = {
    "title": "Wearing red is basically cheating #Shorts",
    "description": (
        "Across the Olympics, athletes in red won more often - and when researchers swapped the colors "
        "on the same footage, referees STILL scored red higher. The advantage was never in the fighter.\n\n"
        "Full video: " + FULL + "\n\n#Shorts #psychology #science\n\n"
        'Music: "Wholesome" by Kevin MacLeod (incompetech.com) - CC BY 4.0 '
        "(http://creativecommons.org/licenses/by/4.0/)"
    ),
    "tags": ["shorts", "psychology", "color", "red", "science", "sports"],
}
vid = upload_video(os.path.join(ROOT, "publish", "short.mp4"),
                   os.path.join(ROOT, "publish", "nope.png"),  # no custom thumb for Shorts
                   meta, os.path.join(ROOT, "publish", "short_captions.srt"))
print("SHORT PUBLISHED: https://youtube.com/watch?v=" + vid)
