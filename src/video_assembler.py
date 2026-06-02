import os
import re
import subprocess
import textwrap

VIDEO_W = 1280
VIDEO_H = 720


def _sec_to_ass(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _build_ass(sections_data):
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
        text     = s["text"].strip()
        duration = s["duration"]
        sentences = [x.strip() for x in re.split(r"(?<=[.!?])\s+", text) if x.strip()]
        if not sentences:
            global_t += duration
            continue

        word_counts = [max(1, len(sent.split())) for sent in sentences]
        total_words = sum(word_counts)
        section_t   = 0.0

        for sent, words in zip(sentences, word_counts):
            sent_dur = (words / total_words) * duration
            display  = textwrap.fill(sent, width=52).replace("\n", r"\N")
            start    = _sec_to_ass(global_t + section_t)
            end      = _sec_to_ass(global_t + section_t + sent_dur)
            lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{display}")
            section_t += sent_dur

        global_t += duration

    return "\n".join(lines)


def create_section_clip(anim_path, audio_path, duration, output_path):
    """Merge Manim animation with narration audio into one clip."""
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", anim_path,
                "-i", audio_path,
                "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
                "-t", str(duration),
                output_path,
            ],
            check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg merge error:\n{e.stderr[-500:]}")


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
        raise RuntimeError(f"FFmpeg concat error:\n{e.stderr[-500:]}")


def assemble_video(sections, temp_dir, output_path):
    clips = []
    for i, s in enumerate(sections):
        clip_path = os.path.join(temp_dir, f"clip_{i:02d}.mp4")
        create_section_clip(s["anim_path"], s["audio_path"], s["duration"], clip_path)
        clips.append(clip_path)
        print(f"  Clip {i + 1}/{len(sections)} merged")

    no_subs = os.path.join(temp_dir, "no_subs.mp4")
    concatenate_clips(clips, no_subs, temp_dir)

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
        raise RuntimeError(f"FFmpeg subtitle error:\n{e.stderr[-500:]}")
