import json
import os
import re
import subprocess

from openai import OpenAI

MODEL = "gpt-4o-mini-tts"
VOICE = "fable"
INSTRUCTIONS = "Warm, curious documentary narrator. Natural pauses at commas and full stops. Slight emphasis on surprising words. Unhurried, clear, conversational - not robotic."


def synthesize_section(text, output_path, temp_dir) -> list[dict]:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if not sentences:
        sentences = [text]

    os.makedirs(temp_dir, exist_ok=True)
    sent_paths = []
    timings = []
    current = 0.0

    try:
        for i, sentence in enumerate(sentences):
            sent_path = os.path.join(temp_dir, f"_sent_{i:03d}.mp3")
            response = client.audio.speech.create(
                model=MODEL,
                voice=VOICE,
                input=sentence,
                instructions=INSTRUCTIONS,
                response_format="mp3",
            )
            with open(sent_path, "wb") as f:
                f.write(response.content)

            duration = get_audio_duration(sent_path)
            timings.append({"text": sentence, "start": current, "end": current + duration})
            current += duration
            sent_paths.append(sent_path)

        concat_txt = os.path.join(temp_dir, "_sent_concat.txt")
        with open(concat_txt, "w", encoding="utf-8") as f:
            for sent_path in sent_paths:
                safe_path = os.path.abspath(sent_path).replace("\\", "/").replace("'", r"'\''")
                f.write(f"file '{safe_path}'\n")

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", concat_txt,
                "-c:a", "libmp3lame", "-b:a", "192k",
                output_path,
            ],
            check=True, capture_output=True, text=True,
        )

        return timings
    finally:
        for sent_path in sent_paths:
            try:
                os.remove(sent_path)
            except FileNotFoundError:
                pass


def get_audio_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
        capture_output=True, text=True, check=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])
