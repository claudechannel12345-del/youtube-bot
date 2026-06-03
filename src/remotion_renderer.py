import json
import os
import shutil
import subprocess

FPS = 30
WIDTH = 1920
HEIGHT = 1080
REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REMOTION_DIR = os.path.join(REPO_DIR, "remotion")


def _npx_command():
    found = shutil.which("npx.cmd") or shutil.which("npx")
    return found or ("npx.cmd" if os.name == "nt" else "npx")


def render_video(sections, output_path):
    public_dir = os.path.join(REMOTION_DIR, "public")
    os.makedirs(public_dir, exist_ok=True)

    copied_audio = []
    copied_clips = []
    props_sections = []
    try:
        for i, section in enumerate(sections):
            audio_src = f"audio_{i:03d}.mp3"
            dest = os.path.join(public_dir, audio_src)
            shutil.copyfile(section["audio_path"], dest)
            copied_audio.append(dest)

            duration = float(section.get("duration") or 0)
            on_screen = section.get("on_screen") or {}
            if not isinstance(on_screen, dict):
                on_screen = {}
            on_screen = dict(on_screen)

            video_path = section.get("video_path")
            if video_path:
                clip_src = f"clip_{i:03d}.mp4"
                clip_dest = os.path.join(public_dir, clip_src)
                shutil.copyfile(video_path, clip_dest)
                copied_clips.append(clip_dest)
                on_screen["video"] = clip_src

            props_sections.append({
                "durationInFrames": max(1, round(duration * FPS)),
                "audioSrc": audio_src,
                "template": section.get("template") or "title_card",
                "key_phrase": section.get("key_phrase") or "",
                "on_screen": on_screen,
                "accentIndex": i,
            })

        props = {
            "fps": FPS,
            "width": WIDTH,
            "height": HEIGHT,
            "sections": props_sections,
        }
        props_path = os.path.join(REMOTION_DIR, "props.json")
        with open(props_path, "w", encoding="utf-8") as f:
            json.dump(props, f, indent=2, ensure_ascii=True)

        abs_output = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(abs_output), exist_ok=True)
        # Use the system CA store so chromium/font downloads work behind TLS-intercepting
        # networks (no-op on standard CI runners).
        env = {**os.environ}
        node_opts = env.get("NODE_OPTIONS", "")
        if "--use-system-ca" not in node_opts:
            env["NODE_OPTIONS"] = (node_opts + " --use-system-ca").strip()
        result = subprocess.run(
            [
                _npx_command(),
                "remotion",
                "render",
                "src/index.ts",
                "Episode",
                abs_output,
                "--props=props.json",
            ],
            cwd=REMOTION_DIR,
            shell=False,
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        if result.returncode != 0:
            tail = (result.stderr or result.stdout)[-1000:]
            raise RuntimeError(f"Remotion render failed:\n{tail}")
    finally:
        for path in copied_audio:
            try:
                os.remove(path)
            except OSError:
                pass
        for path in copied_clips:
            try:
                os.remove(path)
            except OSError:
                pass
