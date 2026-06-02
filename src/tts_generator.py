import asyncio
import json
import subprocess

import edge_tts

VOICE = "en-US-AndrewNeural"


async def _save_audio(text, output_path):
    communicate = edge_tts.Communicate(text, VOICE)
    with open(output_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])


def generate_section_audio(text, output_path):
    asyncio.run(_save_audio(text, output_path))


def get_audio_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])
