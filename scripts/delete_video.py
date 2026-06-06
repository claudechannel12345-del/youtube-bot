import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from uploader import _get_youtube
vid = os.environ.get("VIDEO_ID") or (sys.argv[1] if len(sys.argv) > 1 else "")
if not vid:
    raise SystemExit("provide VIDEO_ID")
_get_youtube().videos().delete(id=vid).execute()
print("DELETED", vid)
