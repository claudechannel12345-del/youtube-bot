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
    "stability": 0.42,       # lower = more expressive/dynamic. Safe now that context-passing is in.
    "similarity_boost": 0.8,
    "style": 0.30,           # owner wanted MORE ENERGY (dry deadpan didn't land). Earlier style 0.30
                             # garbled, but that was WITHOUT the previous/next_text context; with it +
                             # complete sentences, a moderate style is safe (verified by re-transcribing).
    "use_speaker_boost": True,
    "speed": 0.95,           # natural-but-deliberate; drama comes from the inter-sentence PAUSES below
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


def synthesize(text, out_path, voice_id, model_id=DEFAULT_MODEL, api_key=None, voice_settings=None,
               previous_text=None, next_text=None):
    """Synthesize `text` with `voice_id`/`model_id` and write an mp3 to `out_path`.

    `previous_text`/`next_text` give the model the surrounding narration as CONTEXT (not voiced) so
    short clips render stably - this is the fix for the gibberish/garble that short isolated
    sentences ("Back off.", "Gone.") produced.
    """
    api_key = api_key or os.environ["ELEVENLABS_API_KEY"]
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    settings = dict(voice_settings or DEFAULT_SETTINGS)
    body = {"text": text, "model_id": model_id, "voice_settings": settings}
    if previous_text:
        body["previous_text"] = previous_text
    if next_text:
        body["next_text"] = next_text
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
# Keep speeds in a SAFE band (>=0.92): the extreme-slow values (0.86) warbled on this clone. Drama
# comes from the pauses below, not from slowing the speech.
DELIVERY_SPEED = {
    "neutral": 0.95, "curious": 0.96, "question": 0.94, "brisk": 1.0,
    "weighty": 0.93, "surprised": 0.94, "skeptical": 0.94, "ominous": 0.93, "warm_cta": 0.94,
    "transition": 0.94, "punch": 0.97,
}
# v2 had "a lot of really weird pauses" (too big, and some landed mid-thought). Moderated here; the
# script also no longer splits mid-sentence, so pauses only fall at real sentence ends.
PAUSE_AFTER = {
    "neutral": 0.3, "curious": 0.38, "question": 0.5, "brisk": 0.2,
    "weighty": 0.5, "surprised": 0.45, "skeptical": 0.4, "ominous": 0.62, "warm_cta": 0.42,
    "transition": 0.8, "punch": 0.4,
}
# Per-delivery TONE: style = inflection/energy (higher = livelier), stability = consistency (lower =
# more dynamic). Enthusiastic/curious/punch lines swing UP; weighty/ominous stay grounded. This is
# what gives the "shifts in tone" so it doesn't read flat. Kept moderate to avoid re-introducing garble.
DELIVERY_STYLE = {
    "neutral": 0.32, "curious": 0.52, "question": 0.42, "brisk": 0.42,
    "weighty": 0.2, "surprised": 0.6, "skeptical": 0.36, "ominous": 0.16, "warm_cta": 0.56,
    "transition": 0.34, "punch": 0.46,
}
DELIVERY_STABILITY = {
    "neutral": 0.4, "curious": 0.34, "question": 0.38, "brisk": 0.38,
    "weighty": 0.5, "surprised": 0.32, "skeptical": 0.4, "ominous": 0.52, "warm_cta": 0.34,
    "transition": 0.4, "punch": 0.36,
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
            settings["style"] = DELIVERY_STYLE.get(delivery, settings["style"])
            settings["stability"] = DELIVERY_STABILITY.get(delivery, settings["stability"])
            # Very short clips (e.g. "Back off.") garble at high style even with context. Cap style and
            # firm up stability for them - this is what jibbered in the primate section.
            if len(item["text"].split()) <= 3:
                settings["style"] = min(settings["style"], 0.12)
                settings["stability"] = max(settings["stability"], 0.5)
            prev_text = items[i - 1]["text"] if i > 0 else None
            next_text = items[i + 1]["text"] if i < len(items) - 1 else None
            synthesize(item["text"], sent_path, voice_id, model_id=model_id, voice_settings=settings,
                       previous_text=prev_text, next_text=next_text)
            duration = _audio_duration(sent_path)
            timings.append({
                "text": item["text"], "start": current, "end": current + duration, "delivery": delivery,
            })
            clip_paths.append(sent_path)
            current += duration
            is_last = i == len(items) - 1
            # Section-ending "transition" lines get a closing BREATH so topic shifts (e.g. into the
            # twist) don't feel abrupt at the section boundary, which otherwise has no pause at all.
            if is_last:
                pause = PAUSE_AFTER.get("transition", 0.8) if delivery == "transition" else 0.0
            else:
                pause = PAUSE_AFTER.get(delivery, 0.34)
            if pause > 0:
                gap_path = os.path.join(temp_dir, f"_el_gap_{i:03d}.mp3")
                _silence(gap_path, pause)
                clip_paths.append(gap_path)
                current += pause
                if is_last:
                    timings[-1]["end"] = current  # include the closing breath in the section duration

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
