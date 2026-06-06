"""Transcribe an owner brain-dump audio file with Gemini (File API + PRO model).

Verbatim transcription that PRESERVES the owner's natural phrasing, filler words, and humor --
this transcript triple-duties as (1) raw video content, (2) voice/style learning for the writer,
and (3) a pointer into the voice-clone corpus. Light cleanup only (obvious false starts), never
paraphrase.

Usage:
  py -3 scripts/transcribe_braindump.py "C:\\path\\to\\audio.wav" [--topic "color performance"]

Key is read from GEMINI_API_KEY env, else from C:\\Users\\<user>\\.youtube_bot_gemini_key.txt
(out-of-repo, never committed).
"""
import os
import sys
import time
import argparse

# This network intercepts TLS; use the OS (Windows) cert store so cert verification succeeds
# instead of hitting CERTIFICATE_VERIFY_FAILED. Must run before httpx/genai build SSL contexts.
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
    "You are transcribing a personal audio brain-dump from the channel owner. Produce a faithful, "
    "VERBATIM transcript of everything spoken. Rules:\n"
    "- Preserve his actual words, phrasing, and natural tone. This is used to learn how he talks.\n"
    "- Keep meaningful filler and asides (they reveal his humor and emphasis), but you MAY silently "
    "drop pure stutters and repeated false starts (e.g. 'the the', 'I I mean').\n"
    "- Do NOT paraphrase, summarize, correct grammar, or add anything. No headings, no commentary.\n"
    "- Use sentence case and natural punctuation/paragraph breaks where he pauses.\n"
    "- Output ONLY the transcript text."
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("--topic", default="")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    audio = args.audio
    if not os.path.exists(audio):
        raise SystemExit(f"Audio not found: {audio}")

    from google import genai
    client = genai.Client(api_key=load_api_key())

    print(f"Uploading {audio} ...")
    f = client.files.upload(file=audio)
    # Wait for the file to finish processing (ACTIVE) before referencing it.
    for _ in range(60):
        info = client.files.get(name=f.name)
        state = getattr(info.state, "name", str(info.state))
        if state == "ACTIVE":
            break
        if state == "FAILED":
            raise SystemExit("Gemini file processing FAILED.")
        time.sleep(2)
    else:
        raise SystemExit("Timed out waiting for file to become ACTIVE.")
    print("File ACTIVE; transcribing with", PRO_MODELS[0], "...")

    resp = generate(client, [f, PROMPT], models=PRO_MODELS)
    text = (getattr(resp, "text", None) or "").strip()
    if not text:
        raise SystemExit("Empty transcript returned.")

    out = args.out or os.path.join(
        "data", "persona",
        "_braindump_" + (args.topic.replace(" ", "_").lower() or "raw") + ".txt",
    )
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(text + "\n")
    words = len(text.split())
    print(f"\nWrote {out} ({words} words)\n")
    print("=" * 70)
    print(text)
    print("=" * 70)


if __name__ == "__main__":
    main()
