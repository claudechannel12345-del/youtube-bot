# RESUME — Second Glance / youtube-bot

Read this first to pick up where we left off. Repo: E:\youtube-bot, default branch **cutaway-engine**.

## >>> WHERE WE ARE (2026-06-06)

The channel + first video are LIVE. We are **mid channel-migration** to a Brand Account.

### Published (on the OLD personal channel, claudechannel12345@gmail.com)
- **Main video** (public, loud -14 LUFS, custom thumbnail, captions): https://youtube.com/watch?v=p-VRCQ4JLX8
  - Title: "Wearing Red Is Basically Cheating"
- **Short** (public, vertical, links to full video): https://youtube.com/watch?v=2gDdnd9Od0k
- Old quiet first upload `bIoV9d9R_dU` was DELETED.

### >>> PENDING: finish moving to the Brand Account "Second Glance"
Personal->Brand *move* is impossible (Google removed it). Owner instead **created a NEW Brand Account
channel** by making a channel with a custom name — handle had to be suffixed (e.g. "...TV") because
`@secondglance` was taken. DISPLAY NAME can still be exactly "Second Glance" (handle just needs to be
unique). The new Brand channel is the intended real home.

REMAINING STEPS (in order):
1. **Owner**: switch to the new channel (YouTube avatar -> Switch account -> Second Glance) and set
   Customization -> Basic info: Name = "Second Glance", handle, upload avatar + banner -> Publish.
   Branding files on Desktop: `SecondGlance_avatar.png` (800x800), `SecondGlance_banner.png` (2560x1440).
2. **RE-AUTHORIZE uploads for the new Brand channel** (CRITICAL — current creds point at the old
   personal channel). The publish workflows use `YOUTUBE_CLIENT_ID/SECRET/REFRESH_TOKEN` (GH secrets).
   Need a NEW `YOUTUBE_REFRESH_TOKEN` generated via an OAuth consent where the owner SELECTS the
   "Second Glance" Brand channel. Then update the GH secret. (Claude can guide the OAuth flow; scope =
   https://www.googleapis.com/auth/youtube.force-ssl.)
3. **Re-publish** to the new channel: assets are already staged in `publish/` (video.mp4 = loud main,
   thumbnail.png, captions.srt, short.mp4, short_captions.srt). Dispatch `publish.yml` (privacy=public)
   then `publish_short.yml` (full_video_url = the new main URL). Then `set_thumbnail.yml` if needed.
4. **Delete** the 2 videos on the OLD personal channel via `delete_video.yml` (ids p-VRCQ4JLX8 and
   2gDdnd9Od0k) once the new ones are confirmed live.
5. (Optional, later) Create `secondglance@gmail.com`, add as Owner of the Brand Account, transfer
   primary ownership. (Can't rename an existing Gmail; viewers never see the login email anyway.)

## THE PRODUCTION PIPELINE (all working, committed)
- Brain-dump (audio) -> `scripts/transcribe_braindump.py` (Gemini File API, verbatim) -> research ->
  script. The first video's script lives in `data/color_script.json`, authored by
  `scripts/build_color_script.py` (11 sections; edit there + rebuild).
- `scripts/build_local_props.py <script.json> <out.json>` -> director -> blueprints (silent draft props).
- `scripts/render_voiced.py` = TTS (ElevenLabs) + render + music. Key envs: SCRIPT_PATH,
  CUTAWAY_RENDERER=blueprint, MUSIC_VOLUME, **REUSE_AUDIO=1** (skips TTS for visual-only re-renders,
  uses the audio cache at `out/voiced_cache/`). `scripts/resynth_section.py <script> <idx>` re-rolls ONE
  section's audio into the cache (used to fix jibberish in a single section cheaply).
- `scripts/mix_music.py` mixes a music bed + **loudnorm to -14 LUFS** (YouTube loudness). Music tracks in
  `data/music/` (active: Wholesome by Kevin MacLeod, CC-BY -> credit is in the description; alternates in
  data/music/_alternates/). Owner prefers YouTube Audio Library long-term (zero Content ID claims).
- `scripts/make_thumbnail.py` (16:9 thumbnail: dominant red vs small blue + hook headline).
- `scripts/make_short.py` (true vertical 9:16 Short; the renderer's SVG viewBox is now dynamic so 1080x1920
  works). `scripts/make_branding.py` (avatar + banner, eye brand mark).

## JIBBERISH / VOICE NOTES (hard-won)
- Voice = owner's clone `OOLdd0jihd5eCDYx6lL9` (script-read, more emotional). Settings in
  `src/elevenlabs_tts.py`: style 0.30 baseline + per-delivery DELIVERY_STYLE/STABILITY for tone swings;
  short clips (<=3 words) auto-cap style (they garble at high style).
- Causes of ElevenLabs garble we fixed: high `style` on SHORT clips; **mid-sentence dashes/colons**
  (now stripped to commas in `_tts_norm`); `'d` contractions ("you'd") can stutter (spell out).
- QA trick: extract the rendered audio and run `transcribe_braindump.py` on it — if it transcribes
  clean and matches the script, there's no jibberish (Gemini may smooth mild stutters, so also trust the
  owner's ear). Re-roll a bad section with `resynth_section.py`, then re-render with REUSE_AUDIO=1.

## WORKFLOWS (dispatch via `gh workflow run <name> --repo claudechannel12345-del/youtube-bot`)
On default branch cutaway-engine: `publish.yml` (prebuilt upload, no re-render), `publish_short.yml`,
`set_thumbnail.yml`, `delete_video.yml`, `cutaway_pilot.yml` (full re-render+upload). `daily_video.yml`
cron is DISABLED (old slideshow engine). GH token: `export GH_TOKEN=$(cat /c/Users/Caden/.youtube_bot_gh_token.txt)`.

## KEYS / TOOLS (all outside the repo, see [[reference-gh-token]] memory)
- GH PAT, ElevenLabs key, Gemini key: `C:\Users\Caden\.youtube_bot_{gh_token,elevenlabs_key,gemini_key}.txt`.
- ffmpeg/ffprobe static build: `E:\youtube-bot\tools\` (gitignored). Network intercepts TLS -> use
  `truststore` in Python, `ELEVENLABS_INSECURE_SSL=1`, `NODE_OPTIONS=--use-system-ca` / REMOTION_USE_SYSTEM_CA=1.
- YouTube OAuth secrets are GH Actions secrets (client id/secret/refresh token).

## NEXT CONTENT
Owner records a brain-dump (RODECaster) for the next topic -> transcribe -> research -> script ->
render -> publish (+ Short). Voice corpus accrues toward a Professional Voice Clone (~30 min of clean
audio needed; have ~3 min). See data/persona/ (STYLE_BIBLE, BRAIN_DUMPS, RESEARCH/SCRIPT/FIXLIST_color).
