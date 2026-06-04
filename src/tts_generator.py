import json
import os
import re
import subprocess

from openai import OpenAI

MODEL = "gpt-4o-mini-tts"
VOICE = "fable"
BASE_PERSONA = ("Curious, intimate documentary narrator. Conversational and human, never robotic. "
                "Natural pauses at commas and full stops.")
DELIVERY_INSTRUCTIONS = {
    "neutral": BASE_PERSONA + " Warm and clear, even pacing.",
    "curious": BASE_PERSONA + " Sound genuinely curious, inviting the listener into a puzzle; slight lift in intonation.",
    "question": BASE_PERSONA + " Pose this as a real question with a clear inquisitive upward shift; do not sound flat or rhetorical.",
    "brisk": BASE_PERSONA + " Move briskly and lightly through this connective line; keep momentum.",
    "weighty": BASE_PERSONA + " Slow down. Give the key words real weight. Leave a small beat after the central idea.",
    "surprised": BASE_PERSONA + " Sound quietly surprised, not theatrical; let the reveal feel real.",
    "skeptical": BASE_PERSONA + " Sound doubtful and analytical, like testing an assumption.",
    "ominous": BASE_PERSONA + " Lower the energy; slower, tense, restrained, still documentary.",
    "warm_cta": BASE_PERSONA + " Relaxed, warm, sincere closing delivery; not salesy.",
}
DELIVERY_SPEED = {
    "neutral": 1.08,
    "curious": 1.06,
    "question": 1.03,
    "brisk": 1.15,
    "weighty": 0.94,
    "surprised": 1.04,
    "skeptical": 1.02,
    "ominous": 0.92,
    "warm_cta": 1.00,
}
DEFAULT_DELIVERY = "neutral"
SENTENCE_SPLIT_RE = r"(?<=[.!?])\s+"

# Some steerable TTS models (gpt-4o-mini-tts) may reject the `speed` param and
# steer pacing via `instructions` instead. Probe once, then degrade gracefully.
_SPEED_SUPPORTED = True


def _speech_create(client, sentence, instructions, speed):
    global _SPEED_SUPPORTED
    if _SPEED_SUPPORTED and abs(speed - 1.0) > 1e-6:
        try:
            return client.audio.speech.create(
                model=MODEL,
                voice=VOICE,
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
        voice=VOICE,
        input=sentence,
        instructions=instructions,
        response_format="mp3",
    )


def synthesize_section(text, output_path, temp_dir, sentences=None) -> list[dict]:
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
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
