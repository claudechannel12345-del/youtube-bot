# YouTube Bot — Build Progress (RESUME FILE)

**If you are an AI resuming this project: read this file first, then `RESEARCH.md` (the
★ FINAL PLAN section), then continue from the phase marked 👉 RESUME HERE.**

Last updated: 2026-06-02 (session start of build)

---

## How this build works
- **Claude (Opus)** specs each phase + reviews/verifies the code.
- **Codex** (`gpt-5.5`) does the heavy coding. Invoke headless:
  ```
  codex exec --skip-git-repo-check -C /e/youtube-bot -s workspace-write "<task or 'implement specs/phaseN.md'>"
  ```
  - Codex auth: re-login via `codex login` if you see `refresh_token_reused` / 401.
  - Windows sandbox is set to `unelevated` in `~/.codex/config.toml` (REQUIRED — `elevated`
    breaks headless shell). Don't revert it.
  - Capture Codex's final message with `-o <file>` if needed.

## Key approved decisions (from RESEARCH.md ★ FINAL PLAN)
- Engine: **Remotion-first** (free for solo individual). Stay solo or it's $100/mo.
- Voice: **gpt-4o-mini-tts**, steered + script-written-for-speech.
- Captions: **upload SRT**, NO burned-in subtitles (burn only on Shorts).
- AI video clips: **OFF by default**, pluggable shot provider, only 2-4 hero shots when justified.
  Use Veo Lite ($0.05/s)/Fast ($0.10/s) — **NEVER Sora 2 (deprecated, dies Sept 24 2026)**.
- Thumbnails: **free**, composed from the video's own frames + text; generate ~3, user picks.
- Title + hook: auto-generate a couple, user picks.
- Cadence: ~2-3×/week (not daily). Upload ~16:00 UTC, Mon-Wed.
- Monetisation: must show authorship — original angles, narrative/editing variance, cited
  sources, + a per-episode **production log**. Human picks title/thumb/hook before publish.

---

## ⚠️ ACTION ITEMS FOR USER (one-time, manual)
- **Re-auth YouTube for captions.** Caption upload needs the `youtube.force-ssl` scope. The code
  now uses it, but the stored refresh token was made with the old `youtube` scope. Regenerate:
  `python auth/get_refresh_token.py` → update the `YOUTUBE_REFRESH_TOKEN` GitHub secret.
  Until then, SRT upload fails (non-fatal) and videos ship with no captions.

## Phase checklist

- [x] **Phase 1 — Voice + captions** ✅ DONE (reviewed by Claude)
  - [x] `tts_generator.py`: gpt-4o-mini-tts + `instructions` steering + per-sentence render w/ timing
  - [x] `caption_generator.py` (new): accurate global SRT from sentence timings
  - [x] `video_assembler.py`: removed burned ASS subtitles
  - [x] `uploader.py`: SRT via `captions().insert()` + scope bumped to `youtube.force-ssl`
  - [x] `auth/get_refresh_token.py`: scope bumped to `youtube.force-ssl`
  - [x] `main.py`: wired timing → SRT → uploader
  - Note: fixed mojibake Codex wrote into the INSTRUCTIONS string (watch for non-ASCII in Codex writes).
- [x] **Phase 2 — Script + ideation** ✅ DONE (reviewed by Claude)
  - [x] `research.py`: brainstorm-6-then-select, recent-topic avoidance, `why_original` + `key_facts`
  - [x] `script_generator.py`: retention structure, template vocab, title/hook/thumbnail options, validation
  - [x] `main.py`: append `script["title"]` to `data/topic_history.json` after upload (keep latest 50)
  - ⚠️ Phase 6 TODO: `data/topic_history.json` won't persist across GitHub Actions runs (ephemeral
    checkout). Must commit it back in the workflow OR use actions/cache, or topic variance resets each run.
- [x] **Phase 3 — Remotion engine** ✅ DONE (reviewed + render-tested by Claude)
  - [x] Full `remotion/` project: Root/Episode/Background/theme/types + all 10 templates with real motion
  - [x] `src/remotion_renderer.py` bridge (copy audio -> props.json -> `npx remotion render` -> cleanup)
  - [x] `main.py` switched to Remotion; deleted `animation_generator.py` + `video_assembler.py`
  - [x] `npm install` OK, `tsc --noEmit` clean, **real render of 4 templates verified** (stills looked great)
  - [x] Fixed: font loading limited to latin subset (was 28 net reqs/render); renderer uses
        `--props=props.json` + `NODE_OPTIONS=--use-system-ca`
  - **CI notes for Phase 6 / final:**
    - Workflow must: setup Node, `cd remotion && npm install`, AND `apt-get install ffmpeg`
      (Python tts/concat calls system ffmpeg/ffprobe; they are NOT on this Windows box but ARE in CI).
    - First render downloads Chromium headless shell (network needed once).
    - Local testing on this machine needs `NODE_OPTIONS=--use-system-ca` (TLS-intercepting network);
      no-op on CI. ffmpeg is not on local PATH, so full local end-to-end (with audio) can't run here —
      visual render path is proven; audio path will first run in CI.
- [x] **Phase 4 — AI hero-clip layer** ✅ DONE (reviewed by Claude)
  - [x] `src/shot_provider.py`: ShotProvider/NoneProvider/VeoProvider + get_provider + select_hero_indices
  - [x] `main.py` wires it; default (SHOT_PROVIDER=none, MAX_AI_CLIPS=0) = free no-op, identical output
  - [x] `ImageFocus.tsx` renders optional `<OffthreadVideo>` when a clip is provided; renderer copies clips
  - Note: VeoProvider is opt-in + UNTESTED (no keys/never enabled); fails gracefully to motion graphics.
- [x] **Phase 5 — Shorts pipeline** ✅ DONE (reviewed + still-rendered by Claude)
  - [x] `remotion/src/Short.tsx` vertical 1080x1920 composition (registered as 2nd comp "Short")
  - [x] `src/shorts_generator.py`: select 1-3 segments + render via Remotion Short
  - [x] `src/uploader.py`: `upload_short` (+#Shorts, no thumb/SRT) via shared `_upload_media`
  - [x] `main.py`: stores per-section captions, generates+uploads shorts after main (non-fatal), toggle MAKE_SHORTS
  - [x] Verified: Short still rendered clean (vertical, header band, big caption, progress bar)
- [x] **Phase 6 — Timing + alerting + production log + CI** ✅ DONE (reviewed by Claude)
  - [x] `requirements.txt`: removed Manim
  - [x] `src/production_log.py` + main.py writes per-episode authorship log (topic, angle, why_original,
        key_facts, title/hook/thumbnail options, templates, shorts ids)
  - [x] `.github/workflows/daily_video.yml`: cron Mon/Wed/Fri 16:00 UTC + dispatch; Node+Python; ffmpeg +
        best-effort chromium libs (24.04 libasound2t64 fallback); npm install; runs `python src/main.py`
        from root; commits topic_history + production_logs back; opens an issue on failure
  - [x] Final integration check: full `tsc --noEmit` clean + all 12 python modules compile

## ✅ BUILD COMPLETE — remaining MANUAL deploy steps (user)
1. **Re-auth YouTube for force-ssl** (captions): `python auth/get_refresh_token.py` -> update the
   `YOUTUBE_REFRESH_TOKEN` GitHub secret. Without this, caption upload fails (non-fatal).
2. **Commit + push** all changes to GitHub (NOT done automatically).
3. **Test run**: GitHub -> Actions -> Daily YouTube Video -> Run workflow. Watch the logs.
4. Optional later: enable AI hero clips via `SHOT_PROVIDER=veo` + `MAX_AI_CLIPS=2` (costs money).

## Session log
- 2026-06-02: Research done (RESEARCH.md), Codex cross-check done (CODEX_REVIEW.md), plan
  approved. Fixed Codex Windows sandbox (elevated→unelevated). Starting Phase 1.
</content>
