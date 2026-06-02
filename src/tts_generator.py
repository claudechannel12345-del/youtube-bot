import json
import os
import subprocess

from openai import OpenAI

VOICE = "fable"   # British accent — documentary, authoritative, less robotic
MODEL = "tts-1-hd"


def generate_section_audio(text, output_path):
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.audio.speech.create(
        model=MODEL,
        voice=VOICE,
        input=text,
        response_format="mp3",
    )
    with open(output_path, "wb") as f:
        f.write(response.content)


def get_audio_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
        capture_output=True, text=True, check=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])
