"""Transcribe a finished narration mp3 VERBATIM (Gemini) to verify TTS quality.

Used to confirm a render's audio has no gibberish/garble: transcribe what the clone ACTUALLY said,
then eyeball it against the script. If the clone hallucinated words, the transcript shows nonsense.

Usage:
  py -3 scripts/verify_audio_transcript.py out/homework_audio.mp3 [--out out/homework_transcript.txt]
"""
import os
import sys
import time
import argparse

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from gemini_utils import generate, PRO_MODELS  # noqa: E402


def load_api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key.strip()
    path = os.path.join(os.path.expanduser("~"), ".youtube_bot_gemini_key.txt")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    raise SystemExit("No GEMINI_API_KEY env and no ~/.youtube_bot_gemini_key.txt found.")


PROMPT = (
    "Transcribe this audio VERBATIM - exactly the sounds you hear, word for word. This is a "
    "QUALITY CHECK on a text-to-speech render, so it is critical that you do NOT correct, guess, "
    "or clean up anything. Rules:\n"
    "- If a stretch is garbled, slurred, or sounds like nonsense syllables, transcribe it "
    "phonetically as best you can and wrap it in [GARBLED: ...]. Do NOT silently fix it into real words.\n"
    "- Do NOT paraphrase, summarize, or add commentary.\n"
    "- Output ONLY the transcript text, with natural punctuation."
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    audio = args.audio
    if not os.path.isabs(audio):
        audio = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), audio)
    if not os.path.exists(audio):
        raise SystemExit(f"Audio not found: {audio}")

    from google import genai
    client = genai.Client(api_key=load_api_key())

    print(f"Uploading {audio} ...", flush=True)
    f = client.files.upload(file=audio)
    for _ in range(120):
        info = client.files.get(name=f.name)
        state = getattr(info.state, "name", str(info.state))
        if state == "ACTIVE":
            break
        if state == "FAILED":
            raise SystemExit("Gemini file processing FAILED.")
        time.sleep(2)
    else:
        raise SystemExit("Timed out waiting for file to become ACTIVE.")
    print("File ACTIVE; transcribing with", PRO_MODELS[0], "...", flush=True)

    resp = generate(client, [f, PROMPT], models=PRO_MODELS)
    text = (getattr(resp, "text", None) or "").strip()
    if not text:
        raise SystemExit("Empty transcript returned.")

    out = args.out or os.path.join("out", "verify_transcript.txt")
    if not os.path.isabs(out):
        out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(text + "\n")
    garbled = text.upper().count("[GARBLED")
    print(f"\nWrote {out} ({len(text.split())} words) | [GARBLED] markers: {garbled}\n", flush=True)
    print("=" * 70)
    print(text)
    print("=" * 70)


if __name__ == "__main__":
    main()
