# Phase 5 spec — Shorts pipeline (vertical, burned captions)

Goal: repurpose each long-form episode into 1-3 vertical Shorts (1080x1920) as an acquisition layer.
Shorts use BURNED-IN captions (mobile, sound-off) - this is the ONE place we burn captions. Reuse the
per-section narration audio already generated in the main run (no new TTS calls = no extra cost).

Toggle: env `MAKE_SHORTS` (default `"1"` = on). Set to `"0"` to skip. ASCII source only.

## 0. Prereq wiring in main.py (small)
- In the per-section loop, store the section's LOCAL captions on its section_dict:
  `section_dict["captions"] = sent_timings` (the list of {text,start,end} relative to section start,
  already returned by synthesize_section). This lets shorts reuse exact timings.

## 1. Remotion `Short` composition (1080x1920)
- `remotion/src/Short.tsx`: vertical short renderer. Props:
  `{ fps:number, sections: Array<{durationInFrames, audioSrc, key_phrase, captions: Array<{text,start,end}>}> }`
  (start/end in SECONDS relative to that clip's own start; convert to frames with fps).
- Visual: reuse `Background` (Cosmos Dark, vertical), a top `key_phrase` header band, and LARGE
  centered captions that appear sentence-by-sentence in sync with the audio (burned in). Bold, high
  contrast, safe margins for mobile. Add subtle motion (spring pop on each caption).
- Sequence sections back-to-back like Episode; each section plays its `<Audio staticFile(audioSrc)>`.
- Register in `Root.tsx` as a SECOND `<Composition id="Short" component={Short} ...>` with
  `calculateMetadata` computing fps=30, width=1080, height=1920, durationInFrames = sum of sections.
  Keep the existing "Episode" composition unchanged.

## 2. `src/shorts_generator.py` (NEW)
- `select_short_segments(script_sections, sections_data) -> list[list[int]]`: choose up to 3 shorts;
  each short = 1-2 consecutive section indices whose COMBINED audio duration is ~20-50s. Always make
  the cold-open (section 0) one short; then pick 1-2 other high-impact sections (e.g. stat_reveal /
  quote / the longest). Skip a short if a single section already exceeds 60s. Return list of index
  groups; [] if fewer than 1 viable.
- `render_shorts(sections_data, temp_dir) -> list[dict]`: for each selected group, build a Short
  props file (copy the needed audio into remotion/public/ as short audio names; include per-section
  captions), run `npx remotion render src/index.ts Short <out> --props=<file>` (cwd=remotion, same
  env/NODE_OPTIONS + `--props=` bare-path pattern as remotion_renderer; reuse a shared helper if easy).
  Return `[{ "path": mp4, "section_indices": [...] }, ...]`. Clean copied public/ assets in finally.
- Reuse the `_npx_command()` + system-CA env approach from remotion_renderer.py (import or duplicate).

## 3. `src/uploader.py` — add Shorts upload
- `def upload_short(video_path, metadata) -> str`: same OAuth/insert as upload_video but no thumbnail
  and no SRT (captions are burned). Ensure the title/description include `#Shorts`. categoryId 27.
  Return video_id. (Factor shared upload logic if clean, else a small separate function is fine.)

## 4. `src/main.py` — generate + upload shorts after the main upload
- After `_append_topic_history(...)`, if `os.environ.get("MAKE_SHORTS","1") != "0"`:
  - `groups = select_short_segments(script["sections"], sections_data)`
  - `shorts = render_shorts([sections_data[i] for grp in groups for i ...])` — actually pass the full
    `sections_data` + `groups` so the generator can slice; design the signature to take
    `(sections_data, groups, TEMP_DIR)`.
  - For each short: build metadata from `script` (title like `"<short hook> #Shorts"`, a short
    description ending in a subscribe line + `#Shorts`, a few tags) and `upload_short(...)`.
  - Wrap the entire shorts block in try/except: a shorts failure must NOT fail the main run (the
    long-form is already uploaded). Print a non-fatal warning on error.
- Do shorts generation BEFORE the `finally` deletes TEMP_DIR (audio still present there).

## 5. Verify
- `cd remotion && npx tsc --noEmit` (PASS).
- `py -m py_compile src/shorts_generator.py src/uploader.py src/main.py` (AST ok).
- Report a per-file changelog. Do NOT run a full render.
