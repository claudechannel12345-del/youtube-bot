# Phase 2.5A - Voice delivery (per-sentence steering)

Goal: kill the "slow / monotone" narrator. Faster baseline, genuinely inquisitive on questions,
slow + weighty on the important lines, brisk on connective tissue. We ALREADY render each sentence
separately (tts_generator.synthesize_section), so per-sentence `instructions` + `speed` is ~free.

ASCII ONLY in all code/strings (past runs produced mojibake). Do not break existing callers.

## 1. src/script_generator.py
- Add a delivery vocabulary constant:
  ```py
  VALID_DELIVERY = {
      "neutral", "curious", "question", "brisk",
      "weighty", "surprised", "skeptical", "ominous", "warm_cta",
  }
  ```
- Change the JSON the model returns so EACH section also includes a `sentences` array, in addition to
  the existing `narration` string (keep `narration` - lots of code reads it: key_phrase fallback,
  shorts, etc.). Each sentence: `{"text": "...", "delivery": "<enum>"}`.
  - The concatenation of `sentences[].text` (joined with a space) MUST equal `narration`. Tell the model
    this explicitly so they stay in sync.
- Add to the prompt (ASCII):
  - "Split each section's narration into sentences. For each sentence add a `delivery` tag from this
    exact set: neutral, curious, question, brisk, weighty, surprised, skeptical, ominous, warm_cta."
  - Guidance: rhetorical/real questions -> `question`; the key reveal / most important line -> `weighty`;
    fast connective transitions -> `brisk`; a genuine twist -> `surprised`; testing an assumption ->
    `skeptical`; tense foreboding setup -> `ominous`; the closing CTA line -> `warm_cta`; default
    `neutral`. Use weighty/ominous sparingly (1-2 per section max) so they keep impact.
  - Update the example section object in the prompt to include `"sentences": [{"text":"...","delivery":"curious"}]`.
- Validation in generate_script():
  - For each section: if `sentences` missing/empty/malformed, synthesize a fallback by regex-splitting
    `narration` into sentences with delivery `neutral` (reuse the same split regex as tts). 
  - Coerce any delivery not in VALID_DELIVERY to `neutral`.
  - Ensure each sentence dict has non-empty `text`.

## 2. src/tts_generator.py
- Add maps (ASCII strings; keep the shared documentary persona voice consistent across all):
  ```py
  BASE_PERSONA = ("Curious, intimate documentary narrator. Conversational and human, never robotic. "
                  "Natural pauses at commas and full stops.")
  DELIVERY_INSTRUCTIONS = {
      "neutral":   BASE_PERSONA + " Warm and clear, even pacing.",
      "curious":   BASE_PERSONA + " Sound genuinely curious, inviting the listener into a puzzle; slight lift in intonation.",
      "question":  BASE_PERSONA + " Pose this as a real question with a clear inquisitive upward shift; do not sound flat or rhetorical.",
      "brisk":     BASE_PERSONA + " Move briskly and lightly through this connective line; keep momentum.",
      "weighty":   BASE_PERSONA + " Slow down. Give the key words real weight. Leave a small beat after the central idea.",
      "surprised": BASE_PERSONA + " Sound quietly surprised, not theatrical; let the reveal feel real.",
      "skeptical": BASE_PERSONA + " Sound doubtful and analytical, like testing an assumption.",
      "ominous":   BASE_PERSONA + " Lower the energy; slower, tense, restrained, still documentary.",
      "warm_cta":  BASE_PERSONA + " Relaxed, warm, sincere closing delivery; not salesy.",
  }
  DELIVERY_SPEED = {
      "neutral": 1.08, "curious": 1.06, "question": 1.03, "brisk": 1.15,
      "weighty": 0.94, "surprised": 1.04, "skeptical": 1.02, "ominous": 0.92, "warm_cta": 1.00,
  }
  DEFAULT_DELIVERY = "neutral"
  ```
- Change `synthesize_section(text, output_path, temp_dir)` -> add optional param:
  `synthesize_section(text, output_path, temp_dir, sentences=None)`.
  - If `sentences` is a non-empty list of dicts, use it: each item -> (item["text"], delivery).
    Coerce delivery not in DELIVERY_INSTRUCTIONS to DEFAULT_DELIVERY.
  - Else (backward compatible): regex-split `text` as today, delivery = DEFAULT_DELIVERY for all.
- In the per-sentence loop, pass BOTH:
  - `instructions=DELIVERY_INSTRUCTIONS[delivery]`
  - `speed=DELIVERY_SPEED[delivery]`   (OpenAI audio.speech.create supports speed 0.25-4.0)
- Timings unchanged in shape ({text,start,end}); keep returning the flat list. (Optional: also include
  "delivery" in each timing dict - harmless, but not required by callers.)
- Remove the now-unused module-level INSTRUCTIONS constant (or keep as BASE_PERSONA). No other behavior
  change to concat/ffmpeg.

## 3. src/main.py
- One-line change at the synth call (line ~89):
  `sent_timings = synthesize_section(section["narration"], audio_path, TEMP_DIR, sentences=section.get("sentences"))`

## 4. (optional) production log
- In the log dict in main.py, add `"deliveries": [s.get("delivery") for sec in script["sections"] for s in (sec.get("sentences") or [])]`
  OR a per-section delivery summary, for QA of how often each style is used. Non-essential.

## Acceptance / verification (Claude will run)
- `python -c "import ast; ast.parse(open('src/tts_generator.py').read())"` etc. compile clean for the 3 files.
- Dry check: a stubbed sentences list routes the right instructions+speed (inspect by adding a temporary
  print or a tiny unit harness; no real API call needed for the routing logic).
- Confirm fallback path still works when `sentences` is None (old behavior).
- caption_generator.py and SRT flow unchanged.
