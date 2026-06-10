"""Post a finished vertical short to TikTok and/or Instagram Reels (and optionally YouTube Shorts).

The vertical asset is produced by make_short.py (out/short.mp4). This just distributes it.

Usage:
  py scripts/publish_social.py --video out/short.mp4 --caption "..." --to tiktok,instagram
  py scripts/publish_social.py --to tiktok            # defaults video=out/short.mp4, caption from sidecar

Caption resolution: --caption  >  <video>.caption.txt sidecar  >  SOCIAL_CAPTION env  >  filename.
TikTok stays private (SELF_ONLY) until the app is audited; override with TIKTOK_PRIVACY=PUBLIC_TO_EVERYONE.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

# Load social tokens from the key files (kept outside the repo) if not already in the env.
for fname, env in (
    (".youtube_bot_tiktok_token.txt", "TIKTOK_ACCESS_TOKEN"),
    (".youtube_bot_ig_token.txt", "IG_ACCESS_TOKEN"),
    (".youtube_bot_ig_user_id.txt", "IG_USER_ID"),
):
    p = os.path.join(r"C:\Users\Caden", fname)
    if not os.environ.get(env) and os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            os.environ[env] = f.read().strip()
os.environ.setdefault("SOCIAL_INSECURE_SSL", "1")

from social_publisher import post_tiktok, post_instagram_reel  # noqa: E402


def _resolve_caption(video, explicit):
    if explicit:
        return explicit
    sidecar = os.path.splitext(video)[0] + ".caption.txt"
    if os.path.exists(sidecar):
        with open(sidecar, "r", encoding="utf-8") as f:
            return f.read().strip()
    if os.environ.get("SOCIAL_CAPTION"):
        return os.environ["SOCIAL_CAPTION"].strip()
    return os.path.splitext(os.path.basename(video))[0].replace("_", " ")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", default=os.path.join(ROOT, "out", "short.mp4"))
    ap.add_argument("--caption", default=None)
    ap.add_argument("--to", default="tiktok,instagram", help="comma list: tiktok,instagram")
    ap.add_argument("--video-url", default=None, help="public URL for IG (skips auto-host)")
    args = ap.parse_args()

    if not os.path.exists(args.video):
        sys.exit(f"video not found: {args.video} (run make_short.py first)")
    caption = _resolve_caption(args.video, args.caption)
    targets = [t.strip().lower() for t in args.to.split(",") if t.strip()]
    print(f"Publishing {args.video} to {targets}")
    print(f"Caption: {caption[:120]}")

    results = {}
    if "tiktok" in targets:
        try:
            results["tiktok"] = post_tiktok(args.video, caption)
        except Exception as e:
            results["tiktok"] = f"ERROR: {e}"
    if "instagram" in targets or "ig" in targets:
        try:
            results["instagram"] = post_instagram_reel(args.video, caption, video_url=args.video_url)
        except Exception as e:
            results["instagram"] = f"ERROR: {e}"

    print("\n=== RESULTS ===")
    for k, v in results.items():
        print(f"  {k}: {v}")
    if any(str(v).startswith("ERROR") for v in results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
