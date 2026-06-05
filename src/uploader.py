import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]


def _get_youtube():
    creds = Credentials(
        token=None,
        refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
        client_id=os.environ["YOUTUBE_CLIENT_ID"],
        client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return build("youtube", "v3", credentials=creds)


def upload_video(video_path, thumbnail_path, metadata, srt_path=None):
    video_id, youtube = _upload_media(video_path, metadata, "  Upload")

    if os.path.exists(thumbnail_path):
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path),
            ).execute()
            print("  Thumbnail set.")
        except Exception as e:
            print(f"  Thumbnail warning (non-fatal): {e}")

    if srt_path and os.path.exists(srt_path):
        try:
            youtube.captions().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "language": "en",
                        "name": "English",
                        "isDraft": False,
                    }
                },
                media_body=MediaFileUpload(srt_path),
            ).execute()
            print("  Captions uploaded.")
        except Exception as e:
            print(f"  Captions warning (non-fatal): {e}")

    return video_id


def upload_short(video_path, metadata):
    short_metadata = dict(metadata)
    short_metadata["title"] = _ensure_shorts(short_metadata.get("title") or "")
    short_metadata["description"] = _ensure_shorts(short_metadata.get("description") or "")
    video_id, _ = _upload_media(video_path, short_metadata, "  Shorts upload")
    return video_id


def _upload_media(video_path, metadata, progress_label):
    youtube = _get_youtube()
    privacy_status = os.environ.get("UPLOAD_PRIVACY", "public")

    body = {
        "snippet": {
            "title": metadata["title"],
            "description": metadata["description"],
            "tags": metadata["tags"],
            "categoryId": "27",  # Education
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True, chunksize=1024 * 1024)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"{progress_label}: {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"  Live: https://youtube.com/watch?v={video_id}")

    return video_id, youtube


def _ensure_shorts(value):
    text = str(value).strip()
    if "#shorts" in text.lower():
        return text
    return f"{text} #Shorts".strip()
