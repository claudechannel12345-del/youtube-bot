"""Post a finished vertical short (out/short.mp4) to TikTok and Instagram Reels.

Stdlib only (urllib) so it matches the rest of the pipeline - no new deps. Tokens load from the
same C:\\Users\\Caden\\.youtube_bot_*.txt convention used for the other keys (kept OUTSIDE the repo).

BOTH platforms require a developer app + OAuth token that the OWNER must create once (their accounts):
  - TikTok  : open.tiktokapis.com Content Posting API. Token file .youtube_bot_tiktok_token.txt.
              UNAUDITED apps can only post privacy_level=SELF_ONLY (private). Public direct-post needs
              TikTok app audit. Scope needed: video.publish (direct) or video.upload (-> drafts/inbox).
  - Instagram: graph.facebook.com Reels publishing. Needs an IG Business/Creator acct linked to a FB
              Page. Token file .youtube_bot_ig_token.txt + IG user id .youtube_bot_ig_user_id.txt.
              IG PULLS the video from a public URL (no raw-byte upload) - _upload_public() hosts it.

See data/SOCIAL_SETUP.md for the one-time token setup.
"""

import json
import os
import ssl
import time
import urllib.error
import urllib.request

KEY_DIR = r"C:\Users\Caden"
TIKTOK_API = "https://open.tiktokapis.com/v2"
GRAPH_API = "https://graph.facebook.com/v21.0"


def _ssl_context():
    ctx = ssl.create_default_context()
    if os.environ.get("ELEVENLABS_INSECURE_SSL") or os.environ.get("SOCIAL_INSECURE_SSL"):
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _load(env, fname, required=True):
    val = os.environ.get(env)
    if val:
        return val.strip()
    p = os.path.join(KEY_DIR, fname)
    if os.path.exists(p):
        with open(p, "r", encoding="utf-8") as f:
            return f.read().strip()
    if required:
        raise RuntimeError(f"Missing {env}: set the env var or create {p}")
    return None


def _req(url, method="GET", headers=None, data=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, context=_ssl_context()) as resp:
            body = resp.read()
            return resp.status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def _json(url, method="GET", token=None, body=None, headers=None):
    h = dict(headers or {})
    if token:
        h["Authorization"] = f"Bearer {token}"
    payload = None
    if body is not None:
        h["Content-Type"] = "application/json; charset=utf-8"
        payload = json.dumps(body).encode("utf-8")
    status, raw = _req(url, method=method, headers=h, data=payload)
    try:
        parsed = json.loads(raw) if raw else {}
    except ValueError:
        parsed = {"raw": raw.decode("utf-8", "replace")}
    return status, parsed


# ----------------------------------------------------------------------------- public hosting (for IG)
def _upload_public(video_path):
    """Host the mp4 at a public URL (catbox.moe, free, no auth) so Instagram can pull it.
    Override by passing video_url to post_instagram_reel, or set SOCIAL_PUBLIC_URL."""
    if os.environ.get("SOCIAL_PUBLIC_URL"):
        return os.environ["SOCIAL_PUBLIC_URL"].strip()
    boundary = "----sgflatboundary7c2a"
    with open(video_path, "rb") as f:
        filedata = f.read()
    parts = []
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(b'Content-Disposition: form-data; name="reqtype"\r\n\r\nfileupload\r\n')
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(
        ('Content-Disposition: form-data; name="fileToUpload"; filename="%s"\r\n'
         % os.path.basename(video_path)).encode()
    )
    parts.append(b"Content-Type: video/mp4\r\n\r\n")
    parts.append(filedata)
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    payload = b"".join(parts)
    status, raw = _req(
        "https://catbox.moe/user/api.php", method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, data=payload,
    )
    url = raw.decode("utf-8", "replace").strip()
    if status != 200 or not url.startswith("http"):
        raise RuntimeError(f"public host failed ({status}): {url[:200]}")
    print("  hosted:", url, flush=True)
    return url


# ------------------------------------------------------------------------------------------- TikTok
def post_tiktok(video_path, caption, privacy=None):
    """Direct-post a video to TikTok via FILE_UPLOAD. Returns the publish_id.
    privacy: SELF_ONLY (default, only legal option for unaudited apps), PUBLIC_TO_EVERYONE,
    MUTUAL_FOLLOW_FRIENDS, FOLLOWER_OF_CREATOR."""
    token = _load("TIKTOK_ACCESS_TOKEN", ".youtube_bot_tiktok_token.txt")
    privacy = privacy or os.environ.get("TIKTOK_PRIVACY", "SELF_ONLY")
    size = os.path.getsize(video_path)
    init_body = {
        "post_info": {
            "title": caption[:2200],
            "privacy_level": privacy,
            "disable_comment": False,
            "disable_duet": False,
            "disable_stitch": False,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": size,
            "chunk_size": size,
            "total_chunk_count": 1,
        },
    }
    status, d = _json(f"{TIKTOK_API}/post/publish/video/init/", method="POST", token=token, body=init_body)
    if status != 200 or d.get("error", {}).get("code", "ok") not in ("ok", None):
        raise RuntimeError(f"TikTok init failed ({status}): {json.dumps(d)[:300]}")
    publish_id = d["data"]["publish_id"]
    upload_url = d["data"]["upload_url"]

    with open(video_path, "rb") as f:
        blob = f.read()
    put_status, _ = _req(
        upload_url, method="PUT",
        headers={
            "Content-Type": "video/mp4",
            "Content-Length": str(size),
            "Content-Range": f"bytes 0-{size - 1}/{size}",
        },
        data=blob,
    )
    if put_status not in (200, 201, 206):
        raise RuntimeError(f"TikTok upload PUT failed ({put_status})")

    # Poll status until it leaves PROCESSING.
    for _ in range(30):
        s, st = _json(f"{TIKTOK_API}/post/publish/status/fetch/", method="POST", token=token,
                      body={"publish_id": publish_id})
        state = st.get("data", {}).get("status")
        print("  tiktok status:", state, flush=True)
        if state in ("PUBLISH_COMPLETE", "SEND_TO_USER_INBOX"):
            break
        if state in ("FAILED",):
            raise RuntimeError(f"TikTok publish failed: {json.dumps(st)[:300]}")
        time.sleep(3)
    print("  TikTok publish_id:", publish_id, flush=True)
    return publish_id


# ------------------------------------------------------------------------------------------ Instagram
def post_instagram_reel(video_path, caption, video_url=None):
    """Publish a Reel. IG pulls the file from a public URL (auto-hosted if not given). Returns media id."""
    token = _load("IG_ACCESS_TOKEN", ".youtube_bot_ig_token.txt")
    ig_user = _load("IG_USER_ID", ".youtube_bot_ig_user_id.txt")
    video_url = video_url or _upload_public(video_path)

    create_url = (
        f"{GRAPH_API}/{ig_user}/media"
        f"?media_type=REELS&video_url={urllib.request.quote(video_url, safe='')}"
        f"&caption={urllib.request.quote(caption)}&access_token={token}"
    )
    status, d = _json(create_url, method="POST")
    if status != 200 or "id" not in d:
        raise RuntimeError(f"IG create container failed ({status}): {json.dumps(d)[:300]}")
    creation_id = d["id"]

    # Reels need transcoding before publish - poll the container until FINISHED.
    for _ in range(40):
        s, st = _json(f"{GRAPH_API}/{creation_id}?fields=status_code,status&access_token={token}")
        code = st.get("status_code")
        print("  ig container:", code, flush=True)
        if code == "FINISHED":
            break
        if code in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"IG container failed: {json.dumps(st)[:300]}")
        time.sleep(5)

    pub_url = f"{GRAPH_API}/{ig_user}/media_publish?creation_id={creation_id}&access_token={token}"
    status, d = _json(pub_url, method="POST")
    if status != 200 or "id" not in d:
        raise RuntimeError(f"IG publish failed ({status}): {json.dumps(d)[:300]}")
    print("  Instagram media id:", d["id"], flush=True)
    return d["id"]
