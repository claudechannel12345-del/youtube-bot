import os
import random
import subprocess

import requests
from PIL import Image

VIDEO_W = 1280
VIDEO_H = 720
FRAME_RATE = 25


def download_pexels_image(keyword, api_key, output_path):
    headers = {"Authorization": api_key}
    # Try the given keyword, then first word of it, then a safe fallback
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
            img_url = photo["src"]["large"]
            img_data = requests.get(img_url, timeout=60)
            img_data.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(img_data.content)
            return

    # Last resort: solid dark background
    Image.new("RGB", (VIDEO_W, VIDEO_H), (20, 20, 50)).save(output_path)


def _scale_pad_filter():
    return (
        f"scale={VIDEO_W}:{VIDEO_H}:force_original_aspect_ratio=decrease,"
        f"pad={VIDEO_W}:{VIDEO_H}:(ow-iw)/2:(oh-ih)/2:black"
    )


def create_section_clip(image_path, audio_path, output_path, duration):
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-loop", "1", "-i", image_path,
                "-i", audio_path,
                "-vf", _scale_pad_filter(),
                "-r", str(FRAME_RATE),
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                "-t", str(duration),
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
        create_section_clip(s["image_path"], s["audio_path"], clip_path, s["duration"])
        clips.append(clip_path)
        print(f"  Clip {i + 1}/{len(sections)} assembled")
    concatenate_clips(clips, output_path, temp_dir)
