"""Upload publish/short.mp4 as a YouTube Short (#Shorts, links to the full video)."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from uploader import upload_video
FULL = os.environ.get("FULL_VIDEO_URL", "")
meta = {
    "title": "Who really invented homework? #Shorts",
    "description": (
        "Everyone repeats the same story: an Italian teacher named Roberto Nevilis invented homework "
        "in 1905 as a punishment. It's the perfect origin story - but almost none of it is true, and "
        "the real reason you have homework is far stranger.\n\n"
        "Full story: " + FULL + "\n\n#Shorts #history #homework #education\n\n"
        'Music: "Wholesome" by Kevin MacLeod (incompetech.com) - CC BY 4.0 '
        "(http://creativecommons.org/licenses/by/4.0/)"
    ),
    "tags": ["shorts", "homework", "history", "education", "roberto nevilis",
             "who invented homework", "history of homework", "did you know", "second glance"],
}
vid = upload_video(os.path.join(ROOT, "publish", "short.mp4"),
                   os.path.join(ROOT, "publish", "nope.png"),  # no custom thumb for Shorts
                   meta, os.path.join(ROOT, "publish", "short_captions.srt"))
print("SHORT PUBLISHED: https://youtube.com/watch?v=" + vid)
