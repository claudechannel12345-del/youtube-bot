# Phase 4 spec — Pluggable AI hero-clip layer (OFF by default)

Goal: allow 0-N short AI-generated video clips per episode as "hero shots", WITHOUT making them a
dependency. Default behaviour = completely free, pure motion graphics, zero API calls, zero cost,
no change to current output. The clip layer only activates when explicitly enabled via env vars.

Constraints: as-free-as-possible. Never exceed the per-episode cap. Never use Sora 2 (deprecated).
ASCII source only. No new REQUIRED pip deps (Veo uses the already-present `google-genai`).

## 1. `src/shot_provider.py` (NEW) — provider interface + selection
- Env config:
  - `SHOT_PROVIDER` (default `"none"`): one of `none`, `veo`.
  - `MAX_AI_CLIPS` (default `"0"`): hard per-episode cap (int). Even if a provider is set, 0 = no clips.
  - `VEO_MODEL` (default `"veo-3.1-fast"`); `VEO_MAX_SECONDS` (default `"6"`).
- Interface: `class ShotProvider` with `def generate_clip(self, prompt: str, seconds: float, out_path: str) -> bool`
  (returns True on success and writes an mp4 to out_path; False if it declined/failed).
- `class NoneProvider(ShotProvider)`: always returns False (the default; no network).
- `class VeoProvider(ShotProvider)`: uses `google-genai` to call Google's Veo video generation
  (model = VEO_MODEL) with `os.environ["GEMINI_API_KEY"]`; clamp seconds to VEO_MAX_SECONDS; download
  the result mp4 to out_path; return True. Wrap all network/errors in try/except -> return False
  (never raise; a failed clip must degrade gracefully to motion graphics). Add a short module
  docstring noting this path costs money and is UNTESTED until real keys + enabling.
- `def get_provider() -> ShotProvider`: returns NoneProvider unless `SHOT_PROVIDER=veo` AND
  `MAX_AI_CLIPS > 0`.
- `def select_hero_indices(sections, max_clips) -> list[int]`: choose up to `max_clips` section
  indices best suited to a hero shot. Heuristic: prefer sections whose template is `image_focus`,
  then the cold-open (index 0); never more than max_clips. Return [] if max_clips <= 0.

## 2. Remotion `image_focus` template — support an optional real video clip
- Extend the `ImageFocus` template: if `section.on_screen.video` is set (a filename in public/),
  render it full-bleed via Remotion `<OffthreadVideo src={staticFile(on_screen.video)} />` with the
  `key_phrase`/`overlay_text` as a kinetic text overlay on top (so it still looks branded).
  If `on_screen.video` is absent, keep the current stylized-gradient behaviour (unchanged).
- types.ts `on_screen` is already `Record<string, unknown>`; no type change needed. Read defensively.

## 3. `src/remotion_renderer.py` — copy hero clips into public/
- `render_video(sections, output_path)`: in addition to audio, if a section dict has a truthy
  `video_path`, copy it to `public/clip_{i:03d}.mp4` and set that section's prop
  `on_screen["video"] = "clip_{i:03d}.mp4"`. Track copied clips and remove them in the finally block
  (same pattern as audio). Do NOT mutate the caller's on_screen dict in place destructively — build
  the prop copy.

## 4. `src/main.py` — wire the optional layer (no-op when disabled)
- After the script is generated and BEFORE/at audio generation, compute:
  `provider = get_provider()`, `hero_idx = set(select_hero_indices(script["sections"], int(os.environ.get("MAX_AI_CLIPS","0")))) if not isinstance(provider, NoneProvider) else set()`.
- When building each section dict for `render_video`, if `i in hero_idx`, call
  `provider.generate_clip(prompt, seconds, clip_path)` where prompt is built from the section
  `key_phrase` + `broll_keywords`, seconds = min(section duration, VEO_MAX_SECONDS), clip_path in
  TEMP_DIR. If it returns True, set `section_dict["video_path"] = clip_path` and print a note +
  increment a counter (stop at cap). On False, do nothing (motion graphics used).
- With defaults (`SHOT_PROVIDER=none`, `MAX_AI_CLIPS=0`) this path is entirely skipped: identical
  free output as Phase 3.
- Print a one-line summary, e.g. `AI hero clips: 0 (provider=none)`.

## 5. Verify
- `cd remotion && npx tsc --noEmit` (PASS).
- `py -m py_compile src/shot_provider.py src/remotion_renderer.py src/main.py` (AST ok).
- Confirm defaults => NoneProvider and select_hero_indices(..., 0) => []. Report a per-file changelog.
