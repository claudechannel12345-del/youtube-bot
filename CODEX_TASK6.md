# CODEX TASK 6 — director "match-or-create" environment orchestration (Phase 3)

Builds on TASK5 (self-extending env library is DONE: src/environments.py loads
data/generated_environments.json; scripts/generate_environment.py --run generates+persists envs and
auto-creates missing props; validators accept generated env ids). NOW wire the orchestration so the
PIPELINE reuses an existing scene when one fits, otherwise generates a new one BEFORE render. Goal
(user's words): "have the model choose what scene it needs and if it has already been created then use
that, otherwise allow it to create new scenes that fit the needs and they will be added to the library."

Compile-check after each step (py -X pycache_prefix=%TEMP%\pc -m compileall src scripts; py
tests/test_scene_contracts.py; npx.cmd tsc --noEmit in remotion ONLY if TS touched). ASCII only. Do NOT
break the 31 code envs, existing scenes, or the homework pipeline. Append "DONE CODEX_TASK6 STEP N ..."
to .codex_batch_progress.txt after each step. You cannot render; Claude proofs.

## STEP 1 — resolver module: src/env_resolver.py
- `resolve_environment(env_id, *, description=None, allow_create=True) -> str`:
  - If env_id is falsy/None -> return None (abstract beat, no env).
  - If has_environment(env_id) (code OR generated) -> return env_id unchanged (MATCH, no LLM call).
  - Else if allow_create and a key is configured (reuse generate_environment's key check) -> CALL
    scripts/generate_environment to generate+persist env_id using `description` (fallback to a description
    derived from env_id, e.g. env_id.replace("_"," ")). Reload the environments cache
    (environments.load_generated_environments has a module cache - add/raise a cache-reset hook, e.g.
    environments.reset_generated_cache(), and call it after a new env is written). Return env_id if it now
    exists, else fall through.
  - Else (no key, or create failed) -> return a SAFE FALLBACK code env id (pick a sensible generic, e.g.
    "office" or "classroom"; prefer one whose slots match the requested actor needs if known). NEVER crash.
- `ensure_environments(specs) -> dict`: specs = list of {id, description}. De-dupe by id, resolve each
  ONCE (so a scene reused across many sections generates at most once), return {requested_id: resolved_id}.
- Import generate_environment as a module (refactor scripts/generate_environment.py if needed so its
  generate+validate+persist logic is callable as a function, not only via __main__ / argparse). Keep the
  CLI working. NO network at import time.

## STEP 2 — wire into the script->video pipeline (scripts/make_video_from_script.py)
- Before building beats, collect every section's desired environment + a description hint built from that
  section's scene_label + visual (+ on_screen_text[0] if useful).
- Call env_resolver.ensure_environments(...) ONCE up front (so missing envs are created before any render
  and the cache is warm). Map each section's environment through the returned dict.
- Respect an env var gate: ENV_AUTOCREATE (default "1"); if "0", skip creation and use fallbacks only
  (so a pure-offline render never calls the network). Log each MATCH vs CREATE vs FALLBACK to stdout.
- Also extend ENV_ACTORS handling: for a newly created/generated env not in the ENV_ACTORS map, derive
  actors from the env's own slots (use the first 1-2 slot names) instead of the empty-slot default.

## STEP 3 — (optional but preferred) director path + tests
- src/director.py: when DIRECTOR_MODE=llm and the model returns an environment NOT in the catalog, route it
  through env_resolver.resolve_environment(env_id, description=<from beat subject/text>) instead of
  discarding it. If creation is off/fails, keep the existing safe behavior (null env or fallback). Do not
  change rules-mode behavior.
- Tests in tests/ (offline, NO network): resolve_environment returns a code env id unchanged (match);
  unknown env with allow_create=False returns a valid fallback code env id (never crashes); ensure_envi
  ronments de-dupes; make a fake/monkeypatched generate function to prove the create branch persists +
  cache-resets + returns the new id WITHOUT a real network call.

NOTE: generation is the only network step and must stay opt-in/offline-safe. When done, list for Claude:
which env ids to render-proof, and confirm ENV_AUTOCREATE=0 still renders the homework script with
fallbacks only (no network).
