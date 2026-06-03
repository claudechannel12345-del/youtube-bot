"""Optional AI shot providers.

The Veo path can cost money and is untested until real keys and opt-in env
vars are provided. Defaults use NoneProvider, which performs no network work.
"""

import os
import time


class ShotProvider:
    def generate_clip(self, prompt: str, seconds: float, out_path: str) -> bool:
        raise NotImplementedError


class NoneProvider(ShotProvider):
    def generate_clip(self, prompt: str, seconds: float, out_path: str) -> bool:
        return False


class VeoProvider(ShotProvider):
    def __init__(self):
        self.model = os.environ.get("VEO_MODEL", "veo-3.1-fast")
        self.max_seconds = _env_float("VEO_MAX_SECONDS", 6.0)

    def generate_clip(self, prompt: str, seconds: float, out_path: str) -> bool:
        try:
            from google import genai
            from google.genai import types

            api_key = os.environ["GEMINI_API_KEY"]
            duration = max(1, int(round(min(float(seconds), self.max_seconds))))
            client = genai.Client(api_key=api_key)
            operation = client.models.generate_videos(
                model=self.model,
                prompt=prompt,
                config=types.GenerateVideosConfig(duration_seconds=duration),
            )

            while not getattr(operation, "done", False):
                time.sleep(10)
                operation = client.operations.get(operation)

            response = getattr(operation, "response", None)
            generated = getattr(response, "generated_videos", None) or []
            if not generated:
                return False

            video = getattr(generated[0], "video", None)
            if video is None:
                return False

            os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
            downloaded = client.files.download(file=video)
            if hasattr(downloaded, "save"):
                downloaded.save(out_path)
            elif hasattr(video, "save"):
                video.save(out_path)
            else:
                return False
            return os.path.exists(out_path) and os.path.getsize(out_path) > 0
        except Exception:
            return False


def get_provider() -> ShotProvider:
    if os.environ.get("SHOT_PROVIDER", "none").lower() == "veo":
        if _env_int("MAX_AI_CLIPS", 0) > 0:
            return VeoProvider()
    return NoneProvider()


def select_hero_indices(sections, max_clips) -> list[int]:
    limit = int(max_clips)
    if limit <= 0:
        return []

    selected = []
    for i, section in enumerate(sections):
        if len(selected) >= limit:
            break
        if isinstance(section, dict) and section.get("template") == "image_focus":
            selected.append(i)

    if len(selected) < limit and sections and 0 not in selected:
        selected.append(0)

    return selected[:limit]


def _env_int(name, default):
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


def _env_float(name, default):
    try:
        return float(os.environ.get(name, str(default)))
    except ValueError:
        return default
