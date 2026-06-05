# Cutaway Engine - Build Log / RESUME HERE (updated 2026-06-05)

CGP-Grey-style clean-flat illustrated CUTAWAY explainer channel. Pivoted off the abandoned
cosmic-octopus direction. This doc is the resume point; architecture of record is
`.codex_cutaway_arch.txt`.

## >>> RESUME HERE (next session: 2026-06-06 / tomorrow) <<<
Everything non-voice is DONE and verified. The next session is the VOICE + polished upload:
1. Owner buys **ElevenLabs Creator** (~$11 first month, 100k credits). Free tier is exhausted
   (TTS for the test renders), which is why the current full render is SILENT.
2. **Clone the owner's voice**: owner records ~1-3 min of clean speech (dad's good mic) ->
   ElevenLabs Instant Voice Clone (Creator feature) -> get the new voice_id -> set it as the
   `ELEVENLABS_VOICE_ID` GitHub secret (CI) and/or in src/elevenlabs_tts.py (CHRIS_VOICE_ID is
   the current placeholder). Override is via the ELEVENLABS_VOICE_ID env var.
3. Trigger the full voiced render + unlisted upload:
   `gh workflow run cutaway_pilot.yml --ref cutaway-engine -f do_upload=true`
   (export GH_TOKEN=$(cat /c/Users/Caden/.youtube_bot_gh_token.txt) first). It uses ElevenLabs
   (TTS_PROVIDER=elevenlabs) + the owner's voice + all visual fixes -> watch -> report the link.
4. Validate the auto-checker on fresh Gemini quota:
   `gh workflow run proof_check.yml --ref cutaway-engine` -> review proof_report.json artifact.
   (It was BUILT + design-proven this session but the free Gemini daily quota was exhausted by
   repeated test runs; it resets daily.)
5. Build the owner's **re-check-only-flagged correction loop**: pass 1 = batch all scenes;
   then re-render + re-check ONLY the flagged scenes; repeat until clean. (Owner's idea, agreed.)
6. One-time: owner should phone-verify the channel at youtube.com/verify so custom thumbnails
   stop 403'ing (currently videos use an auto frame).

## State of things
- **Branch `cutaway-engine`** has ALL the work, pushed. `main` has only the workflow files
  (so they're dispatchable). Git push works via Git Credential Manager.
- Latest UNLISTED test videos: `XriRusTze4E` (v2 - old gpt-4o-mini-tts voice, pre visual fixes).
  Current best = **silent** local render on the owner's Desktop: `gps_v3_silent.mp4` (~8.6 min,
  all visual fixes). No voiced v3 yet (credits).
- Keys: GH PAT + ElevenLabs key stored OUTSIDE the repo in C:\Users\Caden\ (see the
  [[reference-gh-token]] memory). GH secrets set: ELEVENLABS_API_KEY, OPENAI_API_KEY,
  GEMINI_API_KEY, YOUTUBE_*.

## What's built (all done + verified this session)
- **Engine:** director (src/director.py, rules-first, cumulative/progressive builds) + closed
  vocab (src/cutaway_vocab.py) + Remotion cutaway engine (remotion/src/cutaway/: CutawayEpisode/
  Section/Beat, registry, 11 scene families) + clean-flat kit (remotion/src/flat/).
- **Script:** data/gps_script.json - deeper ~9-min mystery->reveal "Impossible Dot" journey
  (owner-approved voice). Invariant: concat(sentences)==narration (validated).
- **Voice:** ElevenLabs (eleven_multilingual_v2), default voice "Chris"
  (iP95p4xoKVk53GoZ742B) until the owner's clone exists. src/elevenlabs_tts.py is a drop-in for
  tts_generator (synthesize_section); render_voiced.py picks provider via TTS_PROVIDER (default
  elevenlabs). PACING: per-delivery speed + real silence pauses after each sentence (longer after
  weighty/question/reveal) so dramatic beats land. OpenAI TTS rejected (robotic).
- **Persona:** data/persona/STYLE_BIBLE.md (master style doc, GROWS over time) + voiceprint.json.
  Owner will feed in his own writing/transcripts + influences; comment-mining feedback loop planned.
- **Proof-checker:** scripts/storyboard.py (renders one still per scene) + scripts/proof_check.py
  (Gemini vision judges each scene vs its intent, BATCHED ~4 calls, fails-fast + partial report) +
  .github/workflows/proof_check.yml. The MANUAL proof pass (Claude reviews every scene) is now the
  gate before any upload - it caught real bugs spot-checking missed.

## Owner feedback addressed this session
voice robotic/electronic -> ElevenLabs. pacing too fast / no pauses -> per-delivery pauses.
Earth looked wrong (triangles/teal) -> real blue globe w/ rounded continents. trilateration
"never updated" -> cumulative build (1->2->3). lines through planet + mirrored circle ->
satellite->planet lines, no range circles. text truncated/off-center/filler -> fit-to-box +
centered + filler labels dropped. miniature-world "rectangle w/ curved top" floor -> removed.
clock/earth icon thick border ("wheel") -> scale-the-group fix. end line "ask a stranger for
directions" felt random -> retied to the blue dot.

## Local dev workflow
- Repo E:\youtube-bot; shell cwd defaults to C:\ -> use absolute paths.
- Python: `py -3`. ffmpeg/openai NOT installed locally (Remotion bundles ffmpeg for renders +
  `npx remotion ffmpeg` for extraction; full TTS pipeline can't run locally).
- Remotion: `cd remotion`; set `REMOTION_USE_SYSTEM_CA=1` (or NODE_OPTIONS=--use-system-ca) for
  the TLS-intercepting local net; `npx.cmd tsc --noEmit`, `npx.cmd remotion still/render`.
- Storyboard proof: `py -3 scripts/storyboard.py` (renders mp4 + extracts per-beat stills to
  remotion/slice_stills/storyboard/). build props first: `py -3 scripts/build_local_props.py`.
- Codex: `codex exec --skip-git-repo-check -C /e/youtube-bot -s workspace-write -o OUT.txt "..."`
  DIRECTLY in a backgrounded Bash call with `< /dev/null` (stdin redirect or it hangs). Specs in
  .codex_*_spec.txt. ASCII-only in Python.
- gh: `export GH_TOKEN=$(cat /c/Users/Caden/.youtube_bot_gh_token.txt)` then `gh workflow run` /
  `gh run watch <id>`.

## Workflows (.github/workflows/, all workflow_dispatch)
- cutaway_pilot.yml - full voiced render + UNLISTED upload (ElevenLabs + cutaway engine).
- proof_check.yml - storyboard render + vision proof check -> artifact.
- voice_sample.yml - OpenAI voice samples (legacy). (ElevenLabs samples = scripts/voice_sample_eleven.py, run locally.)
- daily_video.yml - the OLD template pipeline (untouched; still on its cron).

## Credit status (as of 2026-06-05)
- ElevenLabs: free tier ~exhausted (was 1663/10000 left, then more voice tests). Need Creator for
  the next voiced render.
- Gemini: free daily quota exhausted by proof-check test runs today; resets daily.
