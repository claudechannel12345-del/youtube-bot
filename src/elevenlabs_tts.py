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
# Production voice = the owner's ORIGINAL clone OOLdd0jihd5eCDYx6lL9 ("Caden Narrator") - made from a
# SCRIPT read, so it carries more emotion than the calmer brain-dump clone. Owner picked it over the
# RodeCaster clone WNhDx8wlTpzgEKtePF2W (kept as a fallback) for being livelier. Override via the
# ELEVENLABS_VOICE_ID env var (CI sets it as a secret); premade "Chris" iP95p4xoKVk53GoZ742B is a last resort.
CHRIS_VOICE_ID = "OOLdd0jihd5eCDYx6lL9"
DEFAULT_SETTINGS = {
    "stability": 0.45,       # low enough to stay expressive, high enough not to rush/warble
    "similarity_boost": 0.8,
    "style": 0.30,           # owner wanted it more UPBEAT/emotional, not flat - style adds inflection
    "use_speaker_boost": True,
    "speed": 0.94,           # natural-but-deliberate; drama comes from the inter-sentence PAUSES below
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


# Per-delivery pacing. Slower baseline + a real beat of silence after each sentence
# (longer after the dramatic ones) so lines land, reveals breathe, and sentences never
# run together. Owner feedback: it sped through and skipped the dramatic pauses.
DELIVERY_SPEED = {
    "neutral": 0.94, "curious": 0.95, "question": 0.93, "brisk": 1.0,
    "weighty": 0.9, "surprised": 0.93, "skeptical": 0.93, "ominous": 0.88, "warm_cta": 0.93,
    "transition": 0.93, "punch": 0.95,
}
# Owner critique: lots of spots "need a pause" - especially major section transitions and the short
# punch lines (which also had weird exhales). Bigger dramatic gaps; a dedicated long "transition" gap.
PAUSE_AFTER = {
    "neutral": 0.34, "curious": 0.42, "question": 0.7, "brisk": 0.22,
    "weighty": 0.95, "surprised": 0.65, "skeptical": 0.5, "ominous": 1.05, "warm_cta": 0.5,
    "transition": 1.25, "punch": 0.85,
}


def _silence(path, seconds):
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
         "-t", f"{max(0.05, seconds):.3f}", "-c:a", "libmp3lame", "-b:a", "192k", path],
        check=True, capture_output=True, text=True,
    )


def synthesize_section(text, output_path, temp_dir, sentences=None, voice=None, model_id=DEFAULT_MODEL):
    """Drop-in replacement for tts_generator.synthesize_section using ElevenLabs.

    Renders each sentence with per-delivery speed, inserts a silence gap after each so the
    pacing breathes, concatenates, and returns per-sentence timings for the director. The
    pause sits BETWEEN sentences (dead air the held visual covers).
    """
    voice_id = voice or os.environ.get("ELEVENLABS_VOICE_ID") or CHRIS_VOICE_ID
    os.makedirs(temp_dir, exist_ok=True)
    items = _sentence_items(text, sentences)
    clip_paths = []
    timings = []
    current = 0.0
    try:
        for i, item in enumerate(items):
            delivery = item["delivery"]
            sent_path = os.path.join(temp_dir, f"_el_sent_{i:03d}.mp3")
            settings = dict(DEFAULT_SETTINGS)
            settings["speed"] = DELIVERY_SPEED.get(delivery, 1.0)
            synthesize(item["text"], sent_path, voice_id, model_id=model_id, voice_settings=settings)
            duration = _audio_duration(sent_path)
            timings.append({
                "text": item["text"], "start": current, "end": current + duration, "delivery": delivery,
            })
            clip_paths.append(sent_path)
            current += duration
            pause = PAUSE_AFTER.get(delivery, 0.34) if i < len(items) - 1 else 0.0
            if pause > 0:
                gap_path = os.path.join(temp_dir, f"_el_gap_{i:03d}.mp3")
                _silence(gap_path, pause)
                clip_paths.append(gap_path)
                current += pause

        concat_txt = os.path.join(temp_dir, "_el_concat.txt")
        with open(concat_txt, "w", encoding="utf-8") as f:
            for p in clip_paths:
                safe = os.path.abspath(p).replace("\\", "/").replace("'", r"'\''")
                f.write(f"file '{safe}'\n")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt,
             "-c:a", "libmp3lame", "-b:a", "192k", output_path],
            check=True, capture_output=True, text=True,
        )
        return timings
    finally:
        for p in clip_paths:
            try:
                os.remove(p)
            except OSError:
                pass
