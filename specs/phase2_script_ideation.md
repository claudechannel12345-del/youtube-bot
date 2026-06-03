# Phase 2 spec — Original-angle ideation + YouTube retention script

Goal: (a) pick genuinely ORIGINAL, non-repeating topics/angles (monetisation requires materially
different topics + variance); (b) generate scripts structured like a real YouTube video (retention
beats, cold-open hook) with narration written FOR SPEECH; (c) emit a Remotion-ready per-section
schema using the fixed visual-template vocabulary below; (d) auto-generate a few title/hook/thumbnail
options for a later human-pick gate.

Keep the pipeline runnable: the existing Manim path reads `section["key_phrase"]` and
`section["narration"]`, and `main.py` reads `script["title"]`, `["description"]`, `["tags"]`. Do NOT
break those field names. ADD new fields alongside them.

No new pip deps. Gemini access is via `from gemini_utils import generate` (already retry-wrapped).

## Visual-template vocabulary (Phase 3 Remotion will implement exactly these)
Each section's `template` MUST be one of:
- `title_card` — big headline + short subtitle
- `stat_reveal` — one big number/statistic + label
- `comparison` — A vs B, two sides
- `timeline` — ordered events along a line
- `process` — sequential steps with arrows/flow
- `quote` — a quotation + attribution
- `list` — 2-5 short bullet points revealed in sequence
- `map` — a place/region being highlighted
- `diagram` — labeled parts of one thing
- `image_focus` — a sourced b-roll image with kinetic text overlay

## 1. `src/research.py` — rewrite for original, non-repeating ideation
- Keep `CHANNEL_NICHE` but REMOVE the "illustratable with stock photography" line (we use motion
  graphics now). Replace with "illustratable with motion graphics, data, diagrams, maps, or timelines."
- New behaviour in `pick_topic(client)`:
  1. Read recent topics from `data/topic_history.json` (a JSON list of strings; missing file = `[]`).
  2. Prompt Gemini to brainstorm 6 candidate topics, then SELECT the single most original + specific
     one, explicitly AVOIDING anything similar to the recent topics passed in, and avoiding generic
     well-worn faceless-channel topics. Demand a non-obvious angle ("the thing most videos on this
     get wrong / never mention").
  3. Return JSON: `{"topic","angle","why_original","visual_keywords":[...4],"key_facts":[...3-5]}`
     where `key_facts` are concrete, checkable facts (for the production log later).
- Keep the JSON-extraction + error handling pattern already used.

## 2. `src/script_generator.py` — rewrite for retention + Remotion schema
`generate_script(topic_data, client)` returns JSON:
```
{
  "title": "primary title (<=70 chars, curiosity gap, specific, no all-caps words)",
  "title_options": ["alt 1", "alt 2"],            // 2 alternates for human pick
  "hook_options": ["spoken hook v1", "spoken hook v2"],  // first ~5s opening lines
  "thumbnail_text_options": ["3-5 WORD TEXT A", "3-5 WORD TEXT B", "3-5 WORD TEXT C"],
  "description": "3 paragraphs; first sentence = strong hook; ends with a subscribe line",
  "tags": [10 tags],
  "sections": [
    {
      "narration": "what the narrator SAYS. Written for the EAR: contractions, short sentences, ellipses for breath, vivid, no list-y fragments. ~50-90 words.",
      "key_phrase": "ON-SCREEN HEADLINE (2-5 words)",   // keep this name (Manim + Remotion use it)
      "template": "one of the vocabulary values",
      "on_screen": { template-specific fields, see below },
      "broll_keywords": ["1-3 search keywords for optional b-roll"]
    }
  ]
}
```
`on_screen` fields by template (include only what the template needs; keep values SHORT, display text):
- title_card: `{"subtitle": "..."}`
- stat_reveal: `{"stat": "70%", "label": "short label"}`
- comparison: `{"left": "...", "right": "...", "left_label": "...", "right_label": "..."}`
- timeline: `{"events": ["1969: ...", "1972: ...", ...]}` (2-5)
- process: `{"steps": ["...", "...", ...]}` (2-5)
- quote: `{"quote": "...", "attribution": "..."}`
- list: `{"items": ["...", "...", ...]}` (2-5)
- map: `{"place": "Region/Country"}`
- diagram: `{"parts": ["label1","label2",...]}`
- image_focus: `{"overlay_text": "short phrase"}`

Script structure requirements (NOT uniform sections):
- The FIRST section is the cold-open hook: open on the single most surprising moment/fact, no slow
  build. Its narration should match one of `hook_options`.
- Then: stakes/context → escalating reveals → climax/big reveal → payoff/meaning → CTA close.
- Vary template choice across sections (don't repeat the same template back-to-back); pick the
  template that actually fits each beat. ~10-16 sections, length driven by the story, not a fixed count.
- Final section ends with a natural subscribe CTA (not the old "every single day" line — cadence is
  now 2-3x/week; say something like "new deep-dives every week").
- Validate: must have >= 8 sections and a non-empty title; each section has narration, key_phrase,
  and a `template` from the vocabulary (default invalid/missing template to `title_card`).

## 3. `src/main.py` — minimal wiring
- After a SUCCESSFUL upload, append `script["title"]` to `data/topic_history.json` (create dir/file
  if missing; keep only the most recent ~50 entries). Do this inside the try, after the Done print.
- No other changes required (it already reads title/description/tags and section key_phrase/narration).

## 4. Verify
- `py -m py_compile` (note: `python` is a Store alias here; use `py`) on changed files. Report PASS/FAIL
  and a concise per-file changelog. Do not run the full pipeline (needs API keys).
- IMPORTANT: write all files as plain ASCII where possible; do NOT introduce smart quotes/em-dashes
  into source strings (they get mojibake-corrupted). Use straight quotes and hyphens.
