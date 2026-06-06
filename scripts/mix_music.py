"""Mix a subtle background-music bed under a finished video's narration (CGP-Grey style).

The music is looped to the video length, dropped to a low volume that sits UNDER the voice, and
gently faded in/out. Voice stays at full level (amix normalize=0). Optional gentle ducking makes the
music dip while the narrator talks.

Usage:
  py -3 scripts/mix_music.py <video_in.mp4> <music.mp3> <video_out.mp4> [volume] [--duck]

Pick the music bed by dropping a file in data/music/ (see render_voiced.py), or pass MUSIC_PATH.
Needs ffmpeg + ffprobe on PATH.
"""
import json
import os
import subprocess
import sys


def _duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
        capture_output=True, text=True, check=True,
    )
    return float(json.loads(out.stdout)["format"]["duration"])


def mix_music(video_in, music, video_out, volume=0.10, duck=False, fade=2.5):
    """Loop `music` under `video_in`'s audio at `volume`, fade in/out, write `video_out`."""
    dur = _duration(video_in)
    fade_out_start = max(0.0, dur - fade - 0.2)
    if duck:
        # Music ducks under the narration (sidechain compressor keyed off the voice), then is mixed
        # back together. Subtle: only a few dB of dip.
        filt = (
            f"[1:a]volume={volume * 1.7:.3f},afade=t=in:st=0:d={fade},"
            f"afade=t=out:st={fade_out_start:.2f}:d={fade}[bg];"
            f"[bg][0:a]sidechaincompress=threshold=0.02:ratio=4:attack=15:release=350[bgd];"
            f"[0:a][bgd]amix=inputs=2:duration=first:normalize=0[mix];"
            f"[mix]loudnorm=I=-14:TP=-1.5:LRA=11[aout]"
        )
    else:
        filt = (
            f"[1:a]volume={volume:.3f},afade=t=in:st=0:d={fade},"
            f"afade=t=out:st={fade_out_start:.2f}:d={fade}[bg];"
            f"[0:a][bg]amix=inputs=2:duration=first:normalize=0[mix];"
            f"[mix]loudnorm=I=-14:TP=-1.5:LRA=11[aout]"
        )
    cmd = [
        "ffmpeg", "-y", "-i", video_in, "-stream_loop", "-1", "-i", music,
        "-filter_complex", filt,
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", video_out,
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return video_out


def find_music():
    """MUSIC_PATH env wins; else the first audio file in data/music/."""
    env = os.environ.get("MUSIC_PATH")
    if env and os.path.exists(env):
        return env
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    music_dir = os.path.join(root, "data", "music")
    if os.path.isdir(music_dir):
        for name in sorted(os.listdir(music_dir)):
            if name.lower().endswith((".mp3", ".m4a", ".wav", ".ogg")):
                return os.path.join(music_dir, name)
    return None


def main():
    args = [a for a in sys.argv[1:] if a != "--duck"]
    duck = "--duck" in sys.argv
    video_in, music, video_out = args[0], args[1], args[2]
    volume = float(args[3]) if len(args) > 3 else 0.10
    mix_music(video_in, music, video_out, volume=volume, duck=duck)
    print("wrote", video_out)


if __name__ == "__main__":
    main()
