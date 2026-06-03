# Phase 6 spec — Production log, alerting, CI workflow, finalize

Goal: make the new pipeline run on GitHub Actions end-to-end, on a 2-3x/week schedule, with an
authorship "production log" (monetisation evidence) and failure visibility. ASCII source only.

## 1. `requirements.txt` — drop Manim
- Remove the `manim>=0.18.0` line (Manim is retired). Keep the rest. (Remotion is a Node dep, not pip.)

## 2. Production log — `src/main.py` (+ helper)
- Add `src/production_log.py` with `write_log(entry: dict, logs_dir="production_logs") -> str`:
  creates the dir, writes `production_logs/<UTC-date>-<slug-of-title>.json` (slug = lowercase, hyphens,
  alnum only, trimmed to ~60 chars), returns the path. Use `datetime.datetime.now(datetime.timezone.utc)`.
- In `main.py`, after a successful main upload (and after shorts), write a log entry capturing
  authorship evidence:
  `{ "utc": <iso8601>, "video_id": ..., "topic": topic_data["topic"], "angle": topic_data["angle"],
    "why_original": topic_data.get("why_original"), "key_facts": topic_data.get("key_facts"),
    "title": script["title"], "title_options": script.get("title_options"),
    "hook_options": script.get("hook_options"), "thumbnail_text_options": script.get("thumbnail_text_options"),
    "section_count": len(script["sections"]), "templates": [s.get("template") for s in script["sections"]],
    "shorts": [<short video ids if any>] }`
  Wrap in try/except (non-fatal: a logging failure must not fail the run).

## 3. CI workflow — rewrite `.github/workflows/daily_video.yml`
Keep the job name. Requirements:
- `on:` ENABLE schedule `cron: '0 16 * * 1,3,5'` (16:00 UTC Mon/Wed/Fri ~= noon ET, the 2-3x/week
  cadence) AND keep `workflow_dispatch:`.
- `permissions: { contents: write, issues: write }` (needed to commit history/logs back + open an
  issue on failure).
- runs-on ubuntu-latest, timeout-minutes: 90.
- Steps:
  1. `actions/checkout@v4`.
  2. `actions/setup-node@v4` with node-version '20'.
  3. `actions/setup-python@v5` with python 3.11.
  4. System deps: `sudo apt-get update` then install `ffmpeg fonts-liberation` PLUS the Chrome headless
     shell libs Remotion needs: `libnss3 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2
     libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 libpango-1.0-0
     libcairo2 libatspi2.0-0`. (Drop the old Manim libs: libcairo2-dev, libpango1.0-dev, pkg-config,
     python3-dev.)
  5. `pip install --no-cache-dir -r requirements.txt` (keep the `pip uninstall google-generativeai -y || true`).
  6. Remotion deps: `cd remotion && npm install` (working-directory or explicit cd).
  7. Run pipeline from REPO ROOT so `data/` resolves to repo-root/data:
     `python src/main.py` (NOT `cd src`). Pass env: GEMINI_API_KEY, OPENAI_API_KEY, YOUTUBE_CLIENT_ID,
     YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN (from secrets). (SHOT_PROVIDER/MAX_AI_CLIPS/MAKE_SHORTS
     left default => free, shorts on.)
  8. Commit back state (so topic variance + logs persist): `if: success()` step that
     `git config user.name/email`, `git add data/topic_history.json production_logs`, and commits
     `"chore: episode <date> [skip ci]"` then pushes — GUARD with `git diff --cached --quiet || git commit ...`
     so it does not fail when nothing changed.
  9. Failure visibility: `if: failure()` step using `actions/github-script@v7` (or `gh issue create`)
     to open an issue titled "Pipeline failed: <run id>" with a link to the run. Keep it short.

## 4. Verify
- `py -m py_compile src/production_log.py src/main.py` (AST ok if pycache write denied).
- Sanity: the YAML is valid (you may `python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/daily_video.yml'))"`
  only if pyyaml present; otherwise just ensure correct indentation).
- Report a per-file changelog. Do NOT attempt to run the workflow.
- IMPORTANT: do not commit/push anything yourself; only edit files.
