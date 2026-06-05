"""Pluggable ElevenLabs text-to-speech (stdlib only, no extra deps).

Used for voice sampling and production narration. Runs in CI with normal TLS; set
ELEVENLABS_INSECURE_SSL=1 for local use behind a TLS-intercepting network (testing only).
"""

import json
import os
import re
import ssl
import subprocess
import urllib.error
import urllib.request

DEFAULT_MODEL = "eleven_multilingual_v2"
# Locked production voice (for now). The owner will swap in a clone of his own voice at
# upload time; override with the ELEVENLABS_VOICE_ID env var.
CHRIS_VOICE_ID = "iP95p4xoKVk53GoZ742B"
DEFAULT_SETTINGS = {
    "stability": 0.45,
    "similarity_boost": 0.8,
    "style": 0.0,
    "use_speaker_boost": True,
    "speed": 1.05,
}
_SENTENCE_SPLIT_RE = r"(?<=[.!?])\s+"


def _ssl_context():
    ctx = ssl.create_default_context()
    if os.environ.get("ELEVENLABS_INSECURE_SSL"):
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _post(url, body, api_key):
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, context=_ssl_context()) as resp:
        return resp.read()


def synthesize(text, out_path, voice_id, model_id=DEFAULT_MODEL, api_key=None, voice_settings=None):
    """Synthesize `text` with `voice_id`/`model_id` and write an mp3 to `out_path`."""
    api_key = api_key or os.environ["ELEVENLABS_API_KEY"]
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    settings = dict(voice_settings or DEFAULT_SETTINGS)
    body = {"text": text, "model_id": model_id, "voice_settings": settings}
    try:
        audio = _post(url, body, api_key)
    except urllib.error.HTTPError as e:
        # Some models reject the `speed` setting; retry once without it.
        if e.code == 422 and "speed" in settings:
            settings.pop("speed", None)
            body["voice_settings"] = settings
            audio = _post(url, body, api_key)
        else:
            raise
    with open(out_path, "wb") as f:
        f.write(audio)
    return out_path


def _audio_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
        capture_output=True, text=True, check=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def _sentence_items(text, sentences):
    if isinstance(sentences, list) and sentences:
        items = []
        for s in sentences:
            if isinstance(s, dict):
                t = str(s.get("text") or "").strip()
                if t:
                    items.append({"text": t, "delivery": s.get("delivery", "neutral")})
        if items:
            return items
    parts = [p.strip() for p in re.split(_SENTENCE_SPLIT_RE, text) if p.strip()] or [text]
    return [{"text": p, "delivery": "neutral"} for p in parts]


def synthesize_section(text, output_path, temp_dir, sentences=None, voice=None, model_id=DEFAULT_MODEL):
    """Drop-in replacement for tts_generator.synthesize_section using ElevenLabs.

    Renders each sentence separately (so we get real per-sentence timings for the
    director), concatenates them, and returns the timing list. `delivery` is carried
    through for the director even though ElevenLabs handles prosody naturally.
    """
    voice_id = voice or os.environ.get("ELEVENLABS_VOICE_ID") or CHRIS_VOICE_ID
    os.makedirs(temp_dir, exist_ok=True)
    items = _sentence_items(text, sentences)
    sent_paths = []
    timings = []
    current = 0.0
    try:
        for i, item in enumerate(items):
            sent_path = os.path.join(temp_dir, f"_el_sent_{i:03d}.mp3")
            synthesize(item["text"], sent_path, voice_id, model_id=model_id)
            duration = _audio_duration(sent_path)
            timings.append({
                "text": item["text"],
                "start": current,
                "end": current + duration,
                "delivery": item["delivery"],
            })
            current += duration
            sent_paths.append(sent_path)

        concat_txt = os.path.join(temp_dir, "_el_concat.txt")
        with open(concat_txt, "w", encoding="utf-8") as f:
            for sent_path in sent_paths:
                safe = os.path.abspath(sent_path).replace("\\", "/").replace("'", r"'\''")
                f.write(f"file '{safe}'\n")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt,
             "-c:a", "libmp3lame", "-b:a", "192k", output_path],
            check=True, capture_output=True, text=True,
        )
        return timings
    finally:
        for sent_path in sent_paths:
            try:
                os.remove(sent_path)
            except OSError:
                pass
