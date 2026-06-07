# CODEX TASK 4 — unify LLM calls behind one provider switch (default OpenAI)

Today LLM calls are split: generate_library.py and write_script.py use OpenAI (gpt-5.5); director.py,
script_generator.py, research.py, shot_provider.py, generate_asset.py use Gemini (gemini_utils).
Unify them behind ONE abstraction defaulting to OpenAI, Gemini kept as fallback.

## STEP 1 — shared LLM helper
Create src/llm.py with:
- `llm_generate(prompt, *, tier="quality", json_mode=False, provider=None) -> str` (returns text).
- provider from env LLM_PROVIDER (default "openai"); "gemini" supported as fallback.
- Tiers map to models (env-overridable):
  - openai: quality = OPENAI_MODEL or "gpt-5.5"; cheap = OPENAI_MODEL_CHEAP or "gpt-5-mini".
  - gemini: quality = PRO_MODELS; cheap = MODELS (reuse gemini_utils).
- Loads keys from C:\Users\Caden\.youtube_bot_openai_key.txt / .youtube_bot_gemini_key.txt if env unset
  (file is AUTHORITATIVE -> overwrite any stale env var, e.g. a Groq key in OPENAI_API_KEY).
- truststore.inject_into_ssl() for the intercept network.
- openai path: client.chat.completions.create(model, messages=[{role:user,...}], response_format=
  {"type":"json_object"} when json_mode). Retry on 429/5xx/timeout (see generate_library.openai_generate).
- gemini path: delegate to gemini_utils.generate.
- Return the response TEXT (callers parse JSON themselves with generate_asset._parse_json).

## STEP 2 — repoint call sites to llm_generate
- generate_asset.py (--run): use llm_generate(tier="quality", json_mode=True). (quality: prop art matters)
- script_generator.py: use llm_generate(tier="quality", json_mode where it expects JSON).
- director.py (DIRECTOR_MODE=llm): use llm_generate(tier="cheap"). (mechanical: pick env/actors)
- research.py, shot_provider.py: use llm_generate(tier="cheap").
- Keep behavior equivalent; do not change prompt contents or output parsing beyond the client swap.
- LEAVE scripts/transcribe_braindump.py on Gemini (multimodal audio input - provider-specific).
- generate_library.py and write_script.py already on OpenAI; OPTIONAL: route them through llm.py too
  for consistency, but do NOT regress their working behavior.

## STEP 3 — notes
- script_generator.py (old) and scripts/write_script.py (new) overlap. Do NOT delete either. Just make
  both work. Leave a TODO note that write_script.py is the current entry point.
- Compile-check: npx.cmd tsc --noEmit in remotion (if TS touched - probably none); py -X
  pycache_prefix=%TEMP%\pc -m compileall src scripts; py tests/test_scene_contracts.py.
- Add a tiny offline smoke that imports src.llm and confirms llm_generate is callable with a fake/mock
  (do NOT make a real network call in tests).
Append DONE notes to .codex_batch_progress.txt with files touched + any call site you could not safely
convert (flag for Claude).
