# YouTube Bot — AI Continuation Context

This file exists so a future AI session can pick up this project without losing context.
Read it fully before touching any code.

---

## What This Project Is

An autonomous YouTube channel that runs entirely on GitHub Actions — no computer needs
to stay on. The goal is a **revenue-generating channel** that posts daily without any
manual intervention. The channel is at:

- **Google account**: claudechannel12345@gmail.com
- **GitHub repo**: github.com/claudechannel12345-del/youtube-bot
- **Local project path**: E:\youtube-bot

---

## User Preferences

- **Fully hands-off**: The user wants zero manual steps per video. Everything must be automated.
- **Revenue is the goal**: Not a hobby project. Decisions should optimise for monetisation eligibility and watch time.
- **No budget constraints stated** but prefers free where reasonable. Has accepted OpenAI TTS at ~$4/month.
- **Style reference**: Kurzgesagt — animated, dark background, bold text, polished educational feel.
- **Niche**: Science, psychology, history, and human behaviour. Fascinating/counterintuitive facts.
- **Voice**: OpenAI TTS `fable` (British accent, tts-1-hd). Chosen for naturalness and documentary feel.
- **Do not suggest reverting to stock footage or static images** — the user explicitly moved away from those.

---

## Current Architecture

### Pipeline (runs on GitHub Actions, Ubuntu, Python 3.11)

```
Gemini 2.5-flash  →  pick topic (science/psychology/history niche)
                  →  generate 20-22 section script with key_phrase per section

Per section (loop):
  OpenAI TTS (fable, tts-1-hd)  →  narration MP3
  Manim (medium quality, 720p)   →  animated visual MP4
  FFmpeg                         →  merge audio + video into section clip

FFmpeg concat  →  join all section clips
FFmpeg         →  burn ASS subtitles onto final video
Pillow         →  generate thumbnail (channel aesthetic, no external images)
YouTube API    →  upload video + thumbnail
```

### File Structure

```
E:\youtube-bot\
├── .github/workflows/daily_video.yml   # GitHub Actions workflow (CRON DISABLED)
├── requirements.txt
├── src/
│   ├── main.py                 # Orchestrator — runs all 6 steps
│   ├── research.py             # Gemini picks topic within niche
│   ├── script_generator.py     # Gemini writes 20-22 section script
│   ├── gemini_utils.py         # Retry wrapper for Gemini 503 errors
│   ├── tts_generator.py        # OpenAI TTS (fable voice)
│   ├── animation_generator.py  # Manim scene renderer (Cosmos Dark style)
│   ├── video_assembler.py      # FFmpeg merge, concat, subtitle burn
│   ├── thumbnail_generator.py  # Pillow thumbnail (channel aesthetic)
│   └── uploader.py             # YouTube OAuth upload
└── auth/
    └── get_refresh_token.py    # One-time local OAuth script (already done)
```

### Required GitHub Secrets

| Secret | Purpose | Status |
|--------|---------|--------|
| GEMINI_API_KEY | Gemini API for research + scripting | ✅ Set |
| OPENAI_API_KEY | TTS narration (fable voice) | ✅ Set |
| YOUTUBE_CLIENT_ID | OAuth for upload | ✅ Set |
| YOUTUBE_CLIENT_SECRET | OAuth for upload | ✅ Set |
| YOUTUBE_REFRESH_TOKEN | OAuth headless auth | ✅ Set |

PEXELS_API_KEY and YOUTUBE_API_KEY are no longer used and can be deleted.

---

## Channel Visual Style — "Cosmos Dark"

Defined in `animation_generator.py` and `thumbnail_generator.py`.

- **Background**: #0D0D1A (deep space navy-black)
- **Accent colours** (cycling per section): Gold #FFD166 → Teal #06D6A0 → Coral #EF476F → Purple #9B5DE5
- **Text**: White, bold, Liberation Sans font
- **Animation**: Floating circles fade in → title writes in → accent line draws across → scene holds
- **Layout alternates** left/right on odd/even sections for variety
- **key_phrase**: Each section has a 2-5 word chapter title (e.g. "THE HIDDEN TRUTH") that becomes the animated headline
- **Subtitles**: Sentence-level ASS subtitles burned in, white with black outline

This style is intentional and consistent. Do not change it without user approval.

---

## What Has Been Done

1. ✅ Google account created (claudechannel12345@gmail.com)
2. ✅ GitHub repo created and connected
3. ✅ All API credentials obtained and stored as GitHub secrets
4. ✅ OAuth refresh token obtained for headless YouTube upload
5. ✅ Full pipeline built and successfully uploaded at least one video to YouTube
6. ✅ Switched from stock footage to Manim animation (Kurzgesagt-inspired)
7. ✅ Switched voice from edge-tts to OpenAI TTS fable
8. ✅ Gemini retry logic added (handles 503 overload errors with fallback to gemini-2.0-flash)
9. ✅ Cron schedule disabled pending further work

---

## What Still Needs Work

The user paused here because the pipeline "still needs a lot of work." Key areas to address:

### 1. Animation Quality
The Manim scenes are functional but basic — one template (dark bg + circles + text reveal).
Kurzgesagt uses varied scene compositions, multiple object types, cause-effect diagrams,
character-like icons, and richer motion. Improvements to consider:
- Add more Manim scene templates (stat reveal, comparison, flow diagram, timeline)
- Have Gemini choose the template per section based on content
- Add more geometric variety (hexagons, arrows, animated paths)
- Consider animated background elements (slowly drifting particles/shapes)

### 2. Script Quality
Scripts are 20-22 sections of narration. They may feel generic or lack the specific
storytelling arc that makes people watch to the end. Consider:
- Stronger hook structure (open with the most surprising moment, then explain how we got there)
- More specific facts and named sources
- Better pacing prompts in script_generator.py

### 3. Monetisation Risk
The strategy doc (D:\Downloads\Automating a YouTube Channel With AI.docx) is clear:
fully automated faceless channels with AI narration + programmatic visuals are borderline
under YouTube's "inauthentic content" rule. The Manim animations are more original than
stock footage loops, but the channel may still struggle to pass YPP review without:
- More visual variety per video
- More substantive, factually specific scripts
- Consistent upload history before applying for monetisation

### 4. Shorts Pipeline
The strategy doc recommends using Shorts as an acquisition layer (repurpose 3-4 clips
from each long-form video). This hasn't been built yet. High impact for channel growth.

### 5. Upload Timing
The cron was set to 3 PM UTC. This may not be optimal for the target audience.
Best time for educational content: typically 2-4 PM local time in the US East Coast.
Consider changing to 17:00 UTC (1 PM ET / 10 AM PT).

### 6. Thumbnail Testing
YouTube's native A/B thumbnail testing exists. The current thumbnail is purely
programmatic (channel aesthetic). No testing loop has been set up.

### 7. Error Handling
If any section's Manim render fails, it falls back to a solid dark clip. This is
silent — the user won't know a section fell back. Add logging/alerting.

---

## Key Technical Notes

### Manim Rendering
- Uses `manim -qm` (medium quality = 720p30)
- Each section writes a temp Python scene file, passes params via MANIM_PARAMS env var (JSON)
- Output found via glob pattern after render
- System deps required: libcairo2-dev libpango1.0-dev pkg-config python3-dev
- Font: Liberation Sans (installed via fonts-liberation apt package)
- Render time: ~8-15 minutes for 20 sections on GitHub Actions 2-core CPU

### Gemini API
- Model: gemini-2.5-flash (falls back to gemini-2.0-flash on 503)
- gemini-2.0-flash-lite was deprecated June 1, 2026 — do not use it
- Uses new google-genai SDK: `from google import genai; client = genai.Client(api_key=...)`
- NOT the old google-generativeai package (deprecated, uninstalled in CI)

### YouTube Upload
- Uses OAuth refresh token (no browser needed in CI)
- Credentials: google.oauth2.credentials.Credentials with refresh_token
- Upload via googleapiclient MediaFileUpload with resumable=True
- Thumbnail upload requires channel verification — may fail silently on new channels

### GitHub Actions
- Runner: ubuntu-latest
- Python: 3.11
- Timeout: 75 minutes
- Cron: DISABLED (commented out) — re-enable by uncommenting in daily_video.yml
- To re-enable: uncomment the schedule block and push

---

## How to Re-enable Automatic Uploads

Edit `.github/workflows/daily_video.yml` and uncomment:
```yaml
on:
  schedule:
    - cron: '0 15 * * *'  # 3 PM UTC daily
  workflow_dispatch:
```

Then push. The bot will run daily at 3 PM UTC.

---

## How to Test Manually

Go to: github.com/claudechannel12345-del/youtube-bot
→ Actions → Daily YouTube Video → Run workflow → Run workflow

Check logs under the run for any errors.

---

## Strategy Document

There is a detailed strategy document at:
D:\Downloads\Automating a YouTube Channel With AI.docx

It covers niche rankings, monetisation risk, recommended toolchain, and a 6-month growth
plan. Read it before making major strategic decisions. Key takeaway: the best fully-automated
niche is educational explainers (science/psychology/history) IF the scripts are genuinely
original and substantive, not generic AI filler.
