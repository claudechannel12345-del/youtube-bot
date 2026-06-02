import os
import random
import subprocess

import requests

VIDEO_W = 1280
VIDEO_H = 720
FRAME_RATE = 25


def download_pexels_image(keyword, api_key, output_path):
    headers = {"Authorization": api_key}
    for query in [keyword, keyword.split()[0], "nature landscape"]:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            headers=headers,
            params={"query": query, "per_page": 5, "orientation": "landscape"},
            timeout=30,
        )
        resp.raise_for_status()
        photos = resp.json().get("photos", [])
        if photos:
            photo = random.choice(photos[:5])
            img_data = requests.get(photo["src"]["large"], timeout=60)
            img_data.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(img_data.content)
            return


def download_pexels_video(keyword, api_key, output_path):
    headers = {"Authorization": api_key}
    for query in [keyword, keyword.split()[0], "nature landscape"]:
        resp = requests.get(
            "https://api.pexels.com/videos/search",
            headers=headers,
            params={"query": query, "per_page": 5, "orientation": "landscape", "size": "medium"},
            timeout=30,
        )
        resp.raise_for_status()
        videos = resp.json().get("videos", [])
        if not videos:
            continue
        video = random.choice(videos[:5])
        files = video.get("video_files", [])
        hd = [f for f in files if f.get("width", 0) >= 1280 and f.get("height", 0) >= 720]
        best = sorted(hd or files, key=lambda f: f.get("width", 0), reverse=True)
        if not best:
            continue
        r = requests.get(best[0]["link"], timeout=120, stream=True)
        r.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                f.write(chunk)
        return

    raise RuntimeError(f"No Pexels video found for: {keyword}")


def extract_video_frame(video_path, output_path, time=1.0):
    subprocess.run(
        ["ffmpeg", "-y", "-ss", str(time), "-i", video_path, "-vframes", "1", "-q:v", "2", output_path],
        check=True, capture_output=True, text=True,
    )


def _scale_pad_filter():
    return (
        f"scale={VIDEO_W}:{VIDEO_H}:force_original_aspect_ratio=decrease,"
        f"pad={VIDEO_W}:{VIDEO_H}:(ow-iw)/2:(oh-ih)/2:black,setsar=1"
    )


def create_section_clip(bg_video_path, audio_path, output_path, duration):
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-stream_loop", "-1", "-i", bg_video_path,
                "-i", audio_path,
                "-t", str(duration),
                "-vf", _scale_pad_filter(),
                "-r", str(FRAME_RATE),
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                "-pix_fmt", "yuv420p",
                output_path,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg clip error:\n{e.stderr[-800:]}")


def concatenate_clips(clip_paths, output_path, temp_dir):
    concat_file = os.path.join(temp_dir, "concat.txt")
    with open(concat_file, "w") as f:
        for p in clip_paths:
            f.write(f"file '{os.path.abspath(p)}'\n")
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", concat_file,
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                "-pix_fmt", "yuv420p",
                output_path,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg concat error:\n{e.stderr[-800:]}")


def assemble_video(sections, temp_dir, output_path):
    clips = []
    for i, s in enumerate(sections):
        clip_path = os.path.join(temp_dir, f"clip_{i:02d}.mp4")
        create_section_clip(s["bg_video_path"], s["audio_path"], clip_path, s["duration"])
        clips.append(clip_path)
        print(f"  Clip {i + 1}/{len(sections)} assembled")
    concatenate_clips(clips, output_path, temp_dir)
