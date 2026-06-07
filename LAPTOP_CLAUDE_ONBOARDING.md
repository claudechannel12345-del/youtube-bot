# Onboarding brief for Claude Code (laptop) — "Second Glance" YouTube engine

**You are Claude Code, resuming an in-flight project on a second (laptop) machine.** Read this whole
file first, run the bootstrap, verify, then continue the pending work. The owner fed you this file on
purpose — it is your handoff. Everything you need to "hit the ground running" is here or in the repo.

---
## 0. What this project is (context)
An autonomous, CGP-Grey-style **clean-flat illustrated YouTube explainer channel** called
**"Second Glance"**. Videos are rendered programmatically (no stock footage) from a script:
- **Art style:** cream background `#F7F4EC` (PAPER), ink `#1E1E24`, coral accent `#FF5A3C` (CORAL),
  bold geometric flat-vector shapes, thick even outlines. Think CGP Grey / Kurzgesagt-lite.
- **Voice:** ElevenLabs voice clone of the owner (voice id `OOLdd0jihd5eCDYx6lL9`, "Caden Narrator"),
  model `eleven_multilingual_v2`. Energetic narrator with deliberate tonal shifts.
- **Render stack:** Remotion 4.0.370 (React) renders 1920x1080 @ 30fps via a blueprint engine. Each
  beat = a SceneBlueprint of primitive shapes (rect/circle/polygon/path) composed into environments
  (backdrop + set_props + actors + foreground + text).
- **First real video:** "Homework Was Invented as a Punishment" (bait-and-switch structure). A first
  render exists; the owner reviewed it and gave a detailed critique (see section 6). Visual fixes are
  DONE; **audio + script fixes are the main pending work.**

## 1. CRITICAL working constraints (do not violate)
- **Outsource bulk/heavy coding to Codex** (the `codex` CLI, gpt-5.5). Reserve yourself (Opus) for
  critical thinking, judgment, proofing, and rendering. The owner is near their Opus usage cap and wants
  minimal Opus token spend. Pattern: write a `CODEX_TASK*.md` spec, dispatch via a bash for-loop that
  re-invokes `codex exec --dangerously-bypass-approvals-and-sandbox -c model_reasoning_effort=high "..."`
  until the deliverable files exist AND a `DONE` line is appended to `.codex_batch_progress.txt`. A single
  `codex exec` ends after ~one step, so loop it. Detached/nohup loops report "completed" immediately but
  keep running — POLL the progress file, do not trust the notification.
- **Self-extending library directive (owner's words):** "have the model choose what scene it needs and if
  it has already been created then use that, otherwise allow it to create new scenes that fit the needs and
  they will be added to the library, same with any assets." This is BUILT (see section 4) — use it.
- **Autonomy directive:** "keep going with whatever that doesn't include me" / "All in sequence,
  autonomously." Grind through the pending list; only ping the owner when there's a fresh cut to review.
- **Windows machine:** use `py` (NOT `python` — it isn't on PATH). PowerShell is the default shell;
  Bash tool is available for POSIX scripts.

## 2. Bootstrap (one-time on the laptop)
Prereqs (winget): `Git.Git`, `Python.Python.3.12` (add to PATH), `OpenJS.NodeJS.LTS`. CLIs:
`npm i -g @anthropic-ai/claude-code` and `npm i -g @openai/codex` (run each once to log in).

```
cd %USERPROFILE%
git clone https://github.com/claudechannel12345-del/youtube-bot.git
cd youtube-bot
git checkout cutaway-engine        # <-- ALL the work is on this branch, not main
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
cd remotion && npm install         # ~680MB, downloads Chromium for rendering. Do on good wifi.
```

**Three things are deliberately NOT in git** — the owner brings them via USB (see section 3):
the API keys, the ffmpeg/ffprobe binaries, and the music beds. `LAPTOP_SETUP.md` (in the repo root)
has the full human-facing version of this with verification steps — read it too.

## 3. Secrets & binaries the owner must hand-carry (NEVER in git, NEVER email these)
Four key files live in the owner's home dir `C:\Users\<username>\` (loaders read from `%USERPROFILE%`,
so the laptop username can differ):
- `.youtube_bot_openai_key.txt`     — OpenAI (LLM: script, director, asset/env generation)
- `.youtube_bot_elevenlabs_key.txt` — ElevenLabs (voice)
- `.youtube_bot_gemini_key.txt`     — Gemini (free fallback; LLM_PROVIDER=gemini)
- `.youtube_bot_gh_token.txt`       — GitHub PAT (classic `ghp_`, for push)

Also copy (USB): `tools\ffmpeg.exe` + `tools\ffprobe.exe` into the laptop's `youtube-bot\tools\`
(the pipeline auto-prepends `tools\` to PATH), and `data\music\*.mp3` for background beds.

If any key file is missing, STOP and tell the owner — generation/voice/push won't work without them.

## 4. The engine, as currently built (so you know what exists before writing anything)
- **Environments are data.** `src/environments.py` has 31 code envs (classroom, library, space, office,
  lab, courtroom, etc.) AND loads generated ones from `data/generated_environments.json`. Each env =
  backdrop frame shapes + midground + set_props + named actor slots + a text_zone.
- **Self-extending env library:** `scripts/generate_environment.py <name> "<description>" --run` generates,
  validates, and persists a new scene, auto-creating any missing props via the asset generator. Dry-run by
  default; `--run` makes the (OpenAI) network call. A `NON_PHYSICAL_PROPS` blocklist stops the model from
  offering widgets/glyphs (counter/number/arrow/etc.) as physical props.
- **Match-or-create orchestration:** `src/env_resolver.py` — `resolve_environment(env_id, description=,
  allow_create=)` returns an existing env unchanged (MATCH, no LLM), else generates+persists it (CREATE),
  else safe FALLBACK to "classroom" (never crashes). `ensure_environments(specs)` de-dupes.
  `scripts/make_video_from_script.py` resolves every section's env up front, gated by env var
  `ENV_AUTOCREATE` (default `1`; set `0` for pure-offline render with fallbacks only).
- **Asset generator:** `scripts/generate_asset.py <name> "<description>" --run` writes shape-list props to
  `data/generated_assets.json` (currently 37 props). Render-proof new assets before trusting them.
- **Shared LLM:** `src/llm.py` `llm_generate(prompt, tier="quality"|"cheap", json_mode=, provider=)` —
  OpenAI default (gpt-5.5 quality / gpt-5-mini cheap), Gemini fallback. Loads the project key files.
- **TTS:** `src/elevenlabs_tts.py` synthesizes EACH sentence as a separate request (with prev/next text
  context) then concatenates with silence gaps. Per-delivery `DELIVERY_STYLE` / `DELIVERY_STABILITY` /
  `DELIVERY_SPEED` / `PAUSE_AFTER` maps.
- **Proofing:** `py scripts/proof_env.py <env_id>` writes `remotion/props_envproof.json`; render a still
  with the command in section 5. `scripts/review_generated.py` builds an all-assets contact sheet.

## 5. Render / proof commands (verify the setup works)
```
py tests\test_scene_contracts.py                 # should print OK
py scripts\proof_env.py library                  # writes remotion\props_envproof.json
cd remotion
set REMOTION_USE_SYSTEM_CA=1
set NODE_OPTIONS=--use-system-ca
npx.cmd remotion still src/index.ts Cutaway ..\out\test.png --props=props_envproof.json --frame=30
```
If `out\test.png` is a clean library scene, you're fully set up. Full video render goes through
`scripts\make_video_from_script.py` (resolves envs, builds beats, renders, mixes audio+music).

## 6. Owner's homework.mp4 critique — what still needs fixing (THE PENDING WORK)
Visual fixes (safe-area clamps so text/feet/props stay in frame; classroom declutter; space planet
spacing; library shelf cleanup) are **DONE** (Codex TASK7, committed). The globe was regenerated with a
clean outline and `library_ladder` regenerated as a proper tall **rolling** library ladder — both
render-proofed and committed. **Still pending, in priority order:**

**A. Audio / TTS settings** (`src/elevenlabs_tts.py`) — first render had continuous gibberish from ~8:26
to the end plus scattered garble (timestamps the owner flagged: 2:04, 2:12-2:13 stutter, 2:33, 3:42,
3:49, 4:04, 4:13, 4:23, 4:47, 6:26). Root cause is voice-model instability from too-aggressive delivery:
`DELIVERY_STYLE` values up to 0.6 and `DELIVERY_STABILITY` floors as low as 0.32 on the clone. FIX: cap
the `DELIVERY_STYLE` ceiling ~0.35 and raise the `DELIVERY_STABILITY` floor ~0.48. Consider `eleven_v3`.
Quota is NOT the cause (checked: plenty of characters remaining). After changing, re-synthesize and
re-transcribe (e.g. whisper) to CONFIRM the gibberish is gone before declaring it fixed.

**B. Script rewrite** (regenerate via `scripts/write_script.py` with an updated brief, or hand-edit the
homework script JSON). Owner's notes:
- Tone DOWN at sentence ends, not up (kill the uptalk/uptone). Intro is robotic/monotone — add emotion.
- More contractions, less formal — "that's the key difference" not "that is"; "you can't blame" not "you
  cannot blame". Should sound like a person, not an AI.
- Add deliberate pauses for emphasis: "kids worked around the house, kids farmed" (pause on "kids");
  "Absolutely not." (pause); "it was not military, it was economic" (pause).
- Rephrase the line "never cross oceans without changing clothes" — sounds wrong.
- Cut or properly tie in the "funniest phrase about a national crime" line — currently makes no sense.
- Roberto Nevilis (the "inventor"): his existence is historically uncertain — owner says **commit**:
  just say he existed (or didn't), don't hedge.
- Disregard the headphone-bleed section near the very beginning (recording artifact, not the script).

**C. Re-render homework, re-transcribe to verify audio, then surface the new cut to the owner for review.**

## 7. How to push (the auth gotcha)
A plain `git push` fails with "invalid credentials" on a fresh machine. The classic `ghp_` PAT works via
basic-auth in the URL:
```
set /p TOK=<%USERPROFILE%\.youtube_bot_gh_token.txt
git push https://x-access-token:%TOK%@github.com/claudechannel12345-del/youtube-bot.git cutaway-engine
```
Or cache once: `git config --global credential.helper manager`, push, paste the PAT as the password
(username can be anything). **Daily workflow:** `git pull` before working, commit + push after. Only ONE
machine active at a time to avoid merge conflicts — pull first, always. Renders (`out\`, `.mp3`, `.mp4`)
are gitignored and do NOT sync; re-render on the laptop, or copy a specific file by hand to review.

## 8. State at handoff (HEAD on `cutaway-engine`)
Latest commits pushed to origin/cutaway-engine:
- self-extending env library + match-or-create orchestration + TASK7 homework VISUAL fixes
- globe + library_ladder regen, PAT push auth documented
All code/data is on the remote. The repo carries code + data (generated assets, environments, scripts,
briefs, the homework brief in `data/briefs/`). The pending work is section 6 (audio + script + re-render).

## 9. Memory / preferences
On the owner's main PC there's a persistent memory at `~/.claude/projects/.../memory/` (MEMORY.md index)
with notes on the project, voice, strategy, asset generator, and a standing note that the PC crashes
mid-session so state is checkpointed to memory frequently. The laptop won't have that memory dir — THIS
file is your substitute context. If you set up memory on the laptop, mirror the key facts here.

---
**TL;DR for the first 10 minutes on the laptop:** clone + checkout `cutaway-engine`, confirm the 4 key
files + ffmpeg + music are present (owner brought them on USB), `pip install`, `npm install` in remotion/,
run the section-5 verify render. Then start on section 6A (TTS stability fix) — that's the biggest owner
pain point. Outsource bulk code to Codex; keep your own (Opus) cycles for judgment, proofing, and renders.
