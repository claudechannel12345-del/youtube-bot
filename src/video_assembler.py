import os
import random
import re
import subprocess
import textwrap

import requests
from PIL import Image

VIDEO_W = 1280
VIDEO_H = 720
FRAME_RATE = 25
IMAGES_PER_SECTION = 3


# ---------------------------------------------------------------------------
# Pexels helpers
# ---------------------------------------------------------------------------

def download_multiple_images(keyword, api_key, output_paths):
    """Download len(output_paths) distinct landscape images for a section."""
    headers = {"Authorization": api_key}
    needed = len(output_paths)

    for query in [keyword, keyword.split()[0], "nature landscape"]:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            headers=headers,
            params={"query": query, "per_page": 15, "orientation": "landscape"},
            timeout=30,
        )
        resp.raise_for_status()
        photos = resp.json().get("photos", [])
        if len(photos) >= needed:
            selected = random.sample(photos[:15], min(needed, len(photos)))
            for photo, path in zip(selected, output_paths):
                img_data = requests.get(photo["src"]["large"], timeout=60)
                img_data.raise_for_status()
                with open(path, "wb") as f:
                    f.write(img_data.content)
            return
        elif photos:
            # Fewer images than needed — use what we have, duplicate the rest
            for i, path in enumerate(output_paths):
                photo = photos[i % len(photos)]
                img_data = requests.get(photo["src"]["large"], timeout=60)
                img_data.raise_for_status()
                with open(path, "wb") as f:
                    f.write(img_data.content)
            return

    # Last resort: solid dark image
    for path in output_paths:
        Image.new("RGB", (VIDEO_W, VIDEO_H), (20, 20, 50)).save(path)


# ---------------------------------------------------------------------------
# Ken Burns pan filter
# ---------------------------------------------------------------------------

def _ken_burns_vf(sub_duration, effect_idx):
    """
    Scale image to 130% of output, then pan across it.
    Uses crop filter with 't' (presentation timestamp) so position moves
    smoothly from start to end over the clip duration.
    """
    sw = int(VIDEO_W * 1.3)   # 1664
    sh = int(VIDEO_H * 1.3)   # 936
    dx = sw - VIDEO_W          # 384  (horizontal travel range)
    dy = sh - VIDEO_H          # 216  (vertical travel range)
    d = max(0.1, float(sub_duration))

    # Scale to 130%, center-crop to exactly sw×sh (handles any input aspect ratio)
    normalize = (
        f"scale={sw}:{sh}:force_original_aspect_ratio=increase,"
        f"crop={sw}:{sh}"
    )

    # Four pan directions, cycling with section variety
    pans = [
        # pan right
        f"crop={VIDEO_W}:{VIDEO_H}:x='{dx}*min(t,{d:.4f})/{d:.4f}':y='{dy // 2}'",
        # pan left
        f"crop={VIDEO_W}:{VIDEO_H}:x='{dx}*(1-min(t,{d:.4f})/{d:.4f})':y='{dy // 2}'",
        # pan down
        f"crop={VIDEO_W}:{VIDEO_H}:x='{dx // 2}':y='{dy}*min(t,{d:.4f})/{d:.4f}'",
        # pan up
        f"crop={VIDEO_W}:{VIDEO_H}:x='{dx // 2}':y='{dy}*(1-min(t,{d:.4f})/{d:.4f})'",
    ]

    return f"{normalize},{pans[effect_idx % 4]}"


# ---------------------------------------------------------------------------
# Clip creation
# ---------------------------------------------------------------------------

def _create_image_clip(image_path, sub_duration, output_path, effect_idx):
    """Single image → video clip with Ken Burns pan, no audio."""
    vf = _ken_burns_vf(sub_duration, effect_idx)
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-loop", "1", "-i", image_path,
                "-t", str(sub_duration),
                "-vf", vf,
                "-r", str(FRAME_RATE),
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
                "-pix_fmt", "yuv420p",
                output_path,
            ],
            check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg image clip error:\n{e.stderr[-800:]}")


def create_section_clip(image_paths, audio_path, duration, output_path, temp_dir, section_idx):
    """
    Combine multiple Ken Burns image sub-clips with section audio into one clip.
    """
    n = len(image_paths)
    sub_dur = duration / n

    # Build a Ken Burns clip for each image
    sub_clips = []
    for i, img_path in enumerate(image_paths):
        sub_path = os.path.join(temp_dir, f"sub_{section_idx:02d}_{i}.mp4")
        effect_idx = (section_idx * n + i) % 4
        _create_image_clip(img_path, sub_dur, sub_path, effect_idx)
        sub_clips.append(sub_path)

    # Concatenate sub-clips into a silent visual track
    visual_path = os.path.join(temp_dir, f"visual_{section_idx:02d}.mp4")
    concat_txt = os.path.join(temp_dir, f"concat_{section_idx:02d}.txt")
    with open(concat_txt, "w") as f:
        for p in sub_clips:
            f.write(f"file '{os.path.abspath(p)}'\n")
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", concat_txt,
                "-c:v", "copy",
                visual_path,
            ],
            check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg visual concat error:\n{e.stderr[-800:]}")

    # Merge audio onto visual track
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", visual_path,
                "-i", audio_path,
                "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                "-t", str(duration),
                output_path,
            ],
            check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg audio merge error:\n{e.stderr[-800:]}")


# ---------------------------------------------------------------------------
# ASS subtitle generation
# ---------------------------------------------------------------------------

def _sec_to_ass(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _build_ass(sections_data):
    """Generate ASS subtitle content timed across the entire video."""
    header = (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        f"PlayResX: {VIDEO_W}\n"
        f"PlayResY: {VIDEO_H}\n\n"
        "[V4+ Styles]\n"
        "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,"
        "OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,"
        "ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,"
        "Alignment,MarginL,MarginR,MarginV,Encoding\n"
        "Style: Default,Arial,52,&H00FFFFFF,&H000000FF,&H00000000,"
        "&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,20,20,50,1\n\n"
        "[Events]\n"
        "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n"
    )

    lines = [header]
    global_t = 0.0

    for s in sections_data:
        text = s["text"].strip()
        duration = s["duration"]

        # Split into sentences
        sentences = [x.strip() for x in re.split(r"(?<=[.!?])\s+", text) if x.strip()]
        if not sentences:
            global_t += duration
            continue

        word_counts = [max(1, len(sent.split())) for sent in sentences]
        total_words = sum(word_counts)

        section_t = 0.0
        for sent, words in zip(sentences, word_counts):
            sent_dur = (words / total_words) * duration
            # Wrap long sentences to two lines
            display = textwrap.fill(sent, width=52).replace("\n", r"\N")
            start = _sec_to_ass(global_t + section_t)
            end = _sec_to_ass(global_t + section_t + sent_dur)
            lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{display}")
            section_t += sent_dur

        global_t += duration

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Final assembly
# ---------------------------------------------------------------------------

def concatenate_clips(clip_paths, output_path, temp_dir):
    concat_txt = os.path.join(temp_dir, "final_concat.txt")
    with open(concat_txt, "w") as f:
        for p in clip_paths:
            f.write(f"file '{os.path.abspath(p)}'\n")
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", concat_txt,
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                "-pix_fmt", "yuv420p",
                output_path,
            ],
            check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg concat error:\n{e.stderr[-800:]}")


def assemble_video(sections, temp_dir, output_path):
    # 1 — Create section clips
    clips = []
    for i, s in enumerate(sections):
        clip_path = os.path.join(temp_dir, f"clip_{i:02d}.mp4")
        create_section_clip(
            s["image_paths"], s["audio_path"], s["duration"],
            clip_path, temp_dir, i,
        )
        clips.append(clip_path)
        print(f"  Clip {i + 1}/{len(sections)} assembled")

    # 2 — Concatenate all clips (no subtitles yet)
    no_subs = os.path.join(temp_dir, "no_subs.mp4")
    concatenate_clips(clips, no_subs, temp_dir)

    # 3 — Generate and burn subtitles
    ass_path = os.path.join(temp_dir, "subs.ass")
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(_build_ass(sections))

    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", no_subs,
                "-vf", f"ass={ass_path}",
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "copy",
                output_path,
            ],
            check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg subtitle burn error:\n{e.stderr[-800:]}")
