"""Pluggable ElevenLabs text-to-speech (stdlib only, no extra deps).

Used for voice sampling and production narration. Runs in CI with normal TLS; set
ELEVENLABS_INSECURE_SSL=1 for local use behind a TLS-intercepting network (testing only).
"""

import base64
import json
import math
import os
import re
import ssl
import subprocess
import urllib.error
import urllib.request

# Production model = Eleven v3 (owner A/B 2026-06-10: v3 emotion was far better - indistinguishable
# from a real read). v3 IGNORES style/speaker_boost/speed; emotion comes from inline audio TAGS
# (see DELIVERY_TAG) plus a discrete stability MODE (0=Creative/0.5=Natural/1=Robust). Natural (0.5)
# won the A/B. Set ELEVENLABS_MODEL=eleven_multilingual_v2 to fall back to the (also-fixed) v2 path.
# The clone OOLdd0jihd5eCDYx6lL9 is an IVC ("cloned" category), which v3 handles well (PVCs don't).
DEFAULT_MODEL = os.environ.get("ELEVENLABS_MODEL", "eleven_v3")
V2_MODEL = "eleven_multilingual_v2"
# Production voice = the owner's ORIGINAL clone OOLdd0jihd5eCDYx6lL9 ("Caden Narrator") - made from a
# SCRIPT read, so it carries more emotion than the calmer brain-dump clone. Owner picked it over the
# RodeCaster clone WNhDx8wlTpzgEKtePF2W (kept as a fallback) for being livelier. Override via the
# ELEVENLABS_VOICE_ID env var (CI sets it as a secret); premade "Chris" iP95p4xoKVk53GoZ742B is a last resort.
CHRIS_VOICE_ID = "OOLdd0jihd5eCDYx6lL9"
DEFAULT_SETTINGS = {
    "stability": 0.48,       # lower = more expressive/dynamic, but too low => the clone hallucinates
                             # words. First homework render gibbered continuously from ~8:26 to the end
                             # plus scattered garble; root cause = style too high / stability too low.
                             # 0.48 is the new floor (was 0.42) - keeps life without the warble.
    "similarity_boost": 0.8,
    "style": 0.30,           # energy/inflection. Kept moderate; the per-delivery map below now CAPS
                             # style at 0.35 (was up to 0.6) - that ceiling is what killed the garble.
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


def _sanitize_settings(model_id, settings):
    """v3 rejects/ignores style, speed, and speaker_boost, and takes stability as a discrete MODE
    (0.0 Creative / 0.5 Natural / 1.0 Robust). Strip the v2-only knobs and snap stability to a mode."""
    if str(model_id).startswith("eleven_v3"):
        stab = settings.get("stability", 0.5)
        stab = min((0.0, 0.5, 1.0), key=lambda v: abs(v - stab))
        return {"stability": stab, "similarity_boost": settings.get("similarity_boost", 0.8)}
    return settings


def synthesize(text, out_path, voice_id, model_id=DEFAULT_MODEL, api_key=None, voice_settings=None,
               previous_text=None, next_text=None):
    """Synthesize `text` with `voice_id`/`model_id` and write an mp3 to `out_path`.

    `previous_text`/`next_text` give the model the surrounding narration as CONTEXT (not voiced) so
    short clips render stably - this is the fix for the gibberish/garble that short isolated
    sentences ("Back off.", "Gone.") produced.
    """
    api_key = api_key or os.environ["ELEVENLABS_API_KEY"]
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    settings = _sanitize_settings(model_id, dict(voice_settings or DEFAULT_SETTINGS))
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
# what gives the "shifts in tone" so it doesn't read flat.
# GARBLE FIX (homework v1 review): the old map pushed style up to 0.6 and stability down to 0.32 on the
# lively deliveries (curious/surprised/warm_cta) - that combo is what made the clone hallucinate words
# (continuous gibberish 8:26->end + scattered garble). New band: style ceiling 0.35, stability floor
# 0.48. Still carries spread for tonal shifts, just inside the clone's stable zone.
DELIVERY_STYLE = {
    "neutral": 0.28, "curious": 0.35, "question": 0.33, "brisk": 0.33,
    "weighty": 0.20, "surprised": 0.35, "skeptical": 0.30, "ominous": 0.16, "warm_cta": 0.34,
    "transition": 0.28, "punch": 0.34,
}
DELIVERY_STABILITY = {
    "neutral": 0.50, "curious": 0.48, "question": 0.50, "brisk": 0.50,
    "weighty": 0.54, "surprised": 0.48, "skeptical": 0.50, "ominous": 0.54, "warm_cta": 0.49,
    "transition": 0.50, "punch": 0.49,
}
# v3 ONLY: emotion comes from a natural-language audio TAG prepended to the sentence (not the style
# knob, which v3 ignores). neutral = no tag (reads plainly). Keep tags short/common - obscure tags can
# get read aloud. Stability stays Natural.
# TONED DOWN (owner feedback on the first v3 full render: "a bit too much on the emotional side,
# specifically the intro" + voice felt inconsistent clip-to-clip). The biggest offenders were the most
# COMMON deliveries: weighty (x28) on [dramatically] and brisk (x8) on [upbeat] made the read theatrical.
# Those now carry NO tag - the words do the work - leaving only the subtle, consistent tags. The intro
# (section 0) is forced fully plain via plain_until (see make_video). Result = calmer, more uniform.
DELIVERY_TAG = {
    "neutral": "", "curious": "[curious]", "question": "[curious]", "brisk": "",
    "weighty": "", "surprised": "[surprised]", "skeptical": "[dryly]",
    "ominous": "[serious]", "warm_cta": "[warmly]", "transition": "", "punch": "[emphatic]",
}
V3_STABILITY = 0.5  # Natural - the A/B winner. Creative(0.0) hallucinates; Robust(1.0) flattens emotion.
V3_MAX_CHARS = 4800   # v3 hard-caps a single request at 5000 chars; stay under it with room for tags.
V3_SEAM_PAUSE = 0.35  # silence inserted at each chunk seam (seams fall on section/topic boundaries).


def _silence(path, seconds):
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
         "-t", f"{max(0.05, seconds):.3f}", "-c:a", "libmp3lame", "-b:a", "192k", path],
        check=True, capture_output=True, text=True,
    )


def _post_json(url, body, api_key):
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"xi-api-key": api_key, "Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, context=_ssl_context()) as resp:
        return json.loads(resp.read())


def _v3_with_timestamps(text, voice_id, model_id, api_key, stability, sim):
    """One v3 synthesis returning the mp3 bytes AND per-character alignment (start/end seconds).
    This is what lets us render a whole chunk as ONE continuous, consistent read and still recover
    per-line timings for captions/scenes - no per-sentence stitching (which is what made v3 drift)."""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"
    body = {"text": text, "model_id": model_id,
            "voice_settings": {"stability": stability, "similarity_boost": sim}}
    d = _post_json(url, body, api_key)
    audio = base64.b64decode(d["audio_base64"])
    al = d.get("alignment") or {}
    return audio, al.get("character_start_times_seconds", []), al.get("character_end_times_seconds", [])


def _v3_rendered_len(item):
    short = len(item["text"].split()) <= 3
    tag = "" if item.get("_plain") else DELIVERY_TAG.get(item["delivery"], "")
    n = len(item["text"])
    if tag and not short:
        n += len(tag) + 1
    return n + 1  # + a joining space


def _v3_chunk_ranges(items, section_starts, max_chars):
    """Group whole SECTIONS into chunks <= max_chars so every seam lands on a topic boundary.
    Returns [(start_idx, end_idx), ...] index ranges into items."""
    bounds = sorted(set(section_starts) | {0, len(items)})
    spans = list(zip(bounds, bounds[1:]))  # [start,end) per section
    chunks = []
    cs, cur = None, 0
    for a, b in spans:
        seglen = sum(_v3_rendered_len(items[k]) for k in range(a, b))
        if cs is None:
            cs, cur = a, seglen
        elif cur + seglen <= max_chars:
            cur += seglen
        else:
            chunks.append((cs, a))
            cs, cur = a, seglen
    if cs is not None:
        chunks.append((cs, len(items)))
    return chunks


def _v3_build_chunk_text(chunk_items):
    """Concatenate a chunk's lines into one string (tags inline) and record each line's TEXT char
    range [lo, hi) so we can pull its timing from the alignment without the tag chars polluting it."""
    parts, offsets, pos = "", [], 0
    for j, it in enumerate(chunk_items):
        if j > 0:
            parts += " "
            pos += 1
        short = len(it["text"].split()) <= 3
        tag = "" if it.get("_plain") else DELIVERY_TAG.get(it["delivery"], "")
        if tag and not short:
            parts += tag + " "
            pos += len(tag) + 1
        lo = pos
        parts += it["text"]
        pos += len(it["text"])
        offsets.append((lo, pos))
    return parts, offsets


def _synthesize_v3_longform(items, output_path, temp_dir, voice_id, model_id, section_starts, plain_until):
    """v3 path: a few LONG continuous reads (one per section-grouped chunk) instead of 109 isolated
    sentences. Kills the clip-to-clip voice/accent drift; seams fall only on topic boundaries."""
    api_key = os.environ["ELEVENLABS_API_KEY"]
    sim = DEFAULT_SETTINGS["similarity_boost"]
    for k, it in enumerate(items):
        if k < plain_until:
            it["_plain"] = True  # intro reads fully plain (owner: pull the intro emotion back)
    ranges = _v3_chunk_ranges(items, section_starts or [0], V3_MAX_CHARS)
    clip_paths, timings, offset = [], [], 0.0
    try:
        for ci, (a, b) in enumerate(ranges):
            chunk_items = items[a:b]
            text, offs = _v3_build_chunk_text(chunk_items)
            audio, starts, ends = _v3_with_timestamps(text, voice_id, model_id, api_key, V3_STABILITY, sim)
            cpath = os.path.join(temp_dir, f"_v3_chunk_{ci:02d}.mp3")
            with open(cpath, "wb") as f:
                f.write(audio)
            clip_paths.append(cpath)
            for (lo, hi), it in zip(offs, chunk_items):
                st = starts[lo] if lo < len(starts) else (ends[-1] if ends else 0.0)
                en = ends[hi - 1] if 0 < hi <= len(ends) else st
                timings.append({"text": it["text"], "start": offset + st,
                                "end": offset + en, "delivery": it["delivery"]})
            offset += _audio_duration(cpath)
            if ci != len(ranges) - 1:
                gap = os.path.join(temp_dir, f"_v3_seam_{ci:02d}.mp3")
                _silence(gap, V3_SEAM_PAUSE)
                clip_paths.append(gap)
                offset += V3_SEAM_PAUSE
        print("V3 longform: %d chars -> %d chunks (%d lines)"
              % (sum(len(it["text"]) for it in items), len(ranges), len(items)), flush=True)
        concat_txt = os.path.join(temp_dir, "_v3_concat.txt")
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


def synthesize_section(text, output_path, temp_dir, sentences=None, voice=None, model_id=DEFAULT_MODEL,
                       section_starts=None, plain_until=0):
    """Drop-in replacement for tts_generator.synthesize_section using ElevenLabs.

    v3 (default): synthesizes the whole script as a few LONG continuous reads (chunked on section
    boundaries, <=5000 chars each) via the with-timestamps endpoint - consistent voice, no per-clip
    drift. v2: renders each sentence with per-delivery speed + context-passing + silence gaps.
    Returns per-sentence timings for the director either way.
    """
    voice_id = voice or os.environ.get("ELEVENLABS_VOICE_ID") or CHRIS_VOICE_ID
    os.makedirs(temp_dir, exist_ok=True)
    items = _sentence_items(text, sentences)
    if str(model_id).startswith("eleven_v3"):
        return _synthesize_v3_longform(items, output_path, temp_dir, voice_id, model_id,
                                       section_starts, plain_until)
    clip_paths = []
    timings = []
    current = 0.0
    try:
        for i, item in enumerate(items):
            delivery = item["delivery"]
            sent_path = os.path.join(temp_dir, f"_el_sent_{i:03d}.mp3")
            short = len(item["text"].split()) <= 3
            send_text = item["text"]
            is_v3 = str(model_id).startswith("eleven_v3")
            if is_v3:
                # v3: emotion via an inline audio TAG; stability is the Natural mode. No style/speed.
                settings = {"stability": V3_STABILITY, "similarity_boost": DEFAULT_SETTINGS["similarity_boost"]}
                tag = DELIVERY_TAG.get(delivery, "")
                if tag and not short:  # a tag can swamp a 1-3 word clip; leave those untagged
                    send_text = f"{tag} {item['text']}"
            else:
                settings = dict(DEFAULT_SETTINGS)
                settings["speed"] = DELIVERY_SPEED.get(delivery, 1.0)
                settings["style"] = DELIVERY_STYLE.get(delivery, settings["style"])
                settings["stability"] = DELIVERY_STABILITY.get(delivery, settings["stability"])
                # Very short clips (e.g. "Back off.") garble at high style even with context. Cap style
                # and firm up stability for them - this is what jibbered in the primate section.
                if short:
                    settings["style"] = min(settings["style"], 0.12)
                    settings["stability"] = max(settings["stability"], 0.5)
            # v3 does NOT support previous_text/next_text (400 unsupported_model); only v2 gets context.
            prev_text = None if is_v3 else (items[i - 1]["text"] if i > 0 else None)
            next_text = None if is_v3 else (items[i + 1]["text"] if i < len(items) - 1 else None)
            synthesize(send_text, sent_path, voice_id, model_id=model_id, voice_settings=settings,
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
