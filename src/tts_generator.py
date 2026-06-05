import json
import os
import re
import subprocess

from openai import OpenAI

MODEL = "gpt-4o-mini-tts"
VOICE = "ash"  # natural American male; overridable per call via synthesize_section(voice=...)
# One consistent, real-person American narrator. The delivery tags are SUBTLE shadings of this
# same person (not different characters) so the voice never jumps or sounds robotic. Modeled on
# the closing-CTA delivery the owner liked: warm, grounded, easygoing.
BASE_PERSONA = ("You are a real American narrator talking to one curious friend, not reading a script. "
                "Relaxed, warm, naturally conversational, and grounded - never robotic, never an "
                "announcer. Light even energy with natural pauses at commas and periods. Keep the same "
                "voice and personality the whole way through.")
DELIVERY_INSTRUCTIONS = {
    "neutral": BASE_PERSONA + " Easy, natural pace.",
    "curious": BASE_PERSONA + " A genuine little spark of curiosity, a slight lift, like you enjoy the puzzle.",
    "question": BASE_PERSONA + " A real question - a small, honest upward turn, not flat or rhetorical.",
    "brisk": BASE_PERSONA + " A touch quicker and lighter through this connecting line; keep it moving.",
    "weighty": BASE_PERSONA + " Slow just slightly and let the key idea land, with a small beat after it. Still natural, not solemn.",
    "surprised": BASE_PERSONA + " A small, real beat of surprise - understated, not theatrical.",
    "skeptical": BASE_PERSONA + " A little wry doubt, like you are gently raising an eyebrow.",
    "ominous": BASE_PERSONA + " Drop the energy a little - slightly quieter and slower, still relaxed.",
    "warm_cta": BASE_PERSONA + " Warm, sincere, easygoing close, like recommending something to a friend.",
}
# Faster baseline and a NARROW range so pace changes never sound like a different person.
DELIVERY_SPEED = {
    "neutral": 1.12,
    "curious": 1.10,
    "question": 1.08,
    "brisk": 1.18,
    "weighty": 1.04,
    "surprised": 1.08,
    "skeptical": 1.08,
    "ominous": 1.02,
    "warm_cta": 1.06,
}
DEFAULT_DELIVERY = "neutral"
SENTENCE_SPLIT_RE = r"(?<=[.!?])\s+"

# Some steerable TTS models (gpt-4o-mini-tts) may reject the `speed` param and
# steer pacing via `instructions` instead. Probe once, then degrade gracefully.
_SPEED_SUPPORTED = True


def _speech_create(client, sentence, instructions, speed, voice=VOICE):
    global _SPEED_SUPPORTED
    if _SPEED_SUPPORTED and abs(speed - 1.0) > 1e-6:
        try:
            return client.audio.speech.create(
                model=MODEL,
                voice=voice,
                input=sentence,
                instructions=instructions,
                speed=speed,
                response_format="mp3",
            )
        except Exception as e:
            # Disable speed for the rest of the run; pacing still steered by instructions.
            _SPEED_SUPPORTED = False
            print(f"  NOTE: TTS 'speed' param rejected ({type(e).__name__}); "
                  f"falling back to instructions-only pacing.")
    return client.audio.speech.create(
        model=MODEL,
        voice=voice,
        input=sentence,
        instructions=instructions,
        response_format="mp3",
    )


def synthesize_section(text, output_path, temp_dir, sentences=None, voice=None) -> list[dict]:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    voice = voice or VOICE
    sentence_items = _sentence_items(text, sentences)

    os.makedirs(temp_dir, exist_ok=True)
    sent_paths = []
    timings = []
    current = 0.0

    try:
        for i, item in enumerate(sentence_items):
            sentence = item["text"]
            delivery = item["delivery"]
            sent_path = os.path.join(temp_dir, f"_sent_{i:03d}.mp3")
            response = _speech_create(
                client, sentence,
                DELIVERY_INSTRUCTIONS[delivery],
                DELIVERY_SPEED[delivery],
                voice=voice,
            )
            with open(sent_path, "wb") as f:
                f.write(response.content)

            duration = get_audio_duration(sent_path)
            timings.append({
                "text": sentence,
                "start": current,
                "end": current + duration,
                "delivery": delivery,
            })
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


def _sentence_items(text, sentences=None):
    items = []
    if isinstance(sentences, list) and sentences:
        for sentence in sentences:
            if not isinstance(sentence, dict):
                continue
            sentence_text = str(sentence.get("text") or "").strip()
            if not sentence_text:
                continue
            delivery = sentence.get("delivery")
            if delivery not in DELIVERY_INSTRUCTIONS:
                delivery = DEFAULT_DELIVERY
            items.append({"text": sentence_text, "delivery": delivery})

    if items:
        return items

    split_sentences = [s.strip() for s in re.split(SENTENCE_SPLIT_RE, text) if s.strip()]
    if not split_sentences:
        split_sentences = [text]
    return [
        {"text": sentence, "delivery": DEFAULT_DELIVERY}
        for sentence in split_sentences
    ]
