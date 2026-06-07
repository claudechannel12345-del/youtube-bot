# Laptop setup — work on youtube-bot from a second Windows machine

Goal: clone this repo on the laptop and have a FULL render-capable environment, then sync via git.
Repo: https://github.com/claudechannel12345-del/youtube-bot.git  (branch: `cutaway-engine`)

The repo carries all the CODE + DATA (generated assets, environments, scripts, briefs). Three things are
deliberately NOT in git and must be brought over by hand: (1) the API KEYS, (2) ffmpeg/ffprobe, (3) the
music beds. Everything below is one-time setup; after that it's just `git pull` / `git push`.

---
## 0. Install prerequisites (one time)
Install these on the laptop (use the official installers / winget):
- Git:           `winget install Git.Git`
- Python 3.11+:  `winget install Python.Python.3.12`  (tick "Add to PATH")
- Node.js LTS:   `winget install OpenJS.NodeJS.LTS`     (needed for Remotion 4.x rendering)
- Claude Code:   `npm install -g @anthropic-ai/claude-code`   then run `claude` once and log in
- Codex CLI:     `npm install -g @openai/codex`              then `codex` once and log in
Verify: `git --version`, `py --version`, `node --version`, `npm --version`.

## 1. Clone the repo
```
cd %USERPROFILE%
git clone https://github.com/claudechannel12345-del/youtube-bot.git
cd youtube-bot
git checkout cutaway-engine
```
(If git asks to authenticate the push later, use the GitHub PAT from the key file in step 2.)

## 2. Bring over the API KEYS (NEVER in git)
On THIS PC they live in `C:\Users\Caden\`. Copy these 4 files to `C:\Users\<your-laptop-username>\`
(same filenames, repo loaders read them from your user home):
- `.youtube_bot_openai_key.txt`      (OpenAI - script/LLM/generators)
- `.youtube_bot_elevenlabs_key.txt`  (ElevenLabs - voice)
- `.youtube_bot_gemini_key.txt`      (Gemini - free fallback)
- `.youtube_bot_gh_token.txt`        (GitHub PAT - upload/push)
Move them on a USB stick or a password manager. Do NOT email them or put them in the repo.

## 3. Python dependencies
```
cd %USERPROFILE%\youtube-bot
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

## 4. Node / Remotion dependencies
```
cd %USERPROFILE%\youtube-bot\remotion
npm install
```
(~680MB, downloads a Chromium for rendering. Needs decent wifi - do this before the trip.)

## 5. ffmpeg / ffprobe (NOT in git)
Two options:
- EASIEST: copy `tools\ffmpeg.exe` and `tools\ffprobe.exe` from this PC's `youtube-bot\tools\` onto the
  laptop's `youtube-bot\tools\` (USB). Those two .exe are all the pipeline needs.
- OR download: https://www.gyan.dev/ffmpeg/builds/ (ffmpeg-release-essentials.zip), unzip, and put
  `ffmpeg.exe` + `ffprobe.exe` into `youtube-bot\tools\`.
The pipeline auto-prepends `tools\` to PATH, so no system install needed.

## 6. Music beds (NOT in git, only needed to render finished videos)
Copy `data\music\*.mp3` from this PC's `youtube-bot\data\music\` to the laptop (USB). Without them a
render still works but has no background music (mix_music just copies the raw audio).

## 7. Verify it works
```
cd %USERPROFILE%\youtube-bot
py tests\test_scene_contracts.py            # should print "OK scene contract tests (N)"
py scripts\proof_env.py library             # writes remotion\props_envproof.json
cd remotion
set REMOTION_USE_SYSTEM_CA=1
set NODE_OPTIONS=--use-system-ca
npx.cmd remotion still src/index.ts Cutaway ..\out\test.png --props=props_envproof.json --frame=30
```
If `out\test.png` looks like a library scene, you're fully set up.

---
## Daily sync workflow (both machines)
- BEFORE working:  `git pull`
- AFTER working:   `git add -A && git commit -m "..." && git push`
- AUTH NOTE: a plain `git push` may fail with "invalid credentials" on a fresh machine. The PAT in
  `.youtube_bot_gh_token.txt` (a classic `ghp_` token) authenticates via basic-auth in the URL:
  ```
  set /p TOK=<%USERPROFILE%\.youtube_bot_gh_token.txt
  git push https://x-access-token:%TOK%@github.com/claudechannel12345-del/youtube-bot.git cutaway-engine
  ```
  Or once, cache it: `git config --global credential.helper manager` then push and paste the PAT as the
  password (username can be anything). After that, plain `git pull` / `git push` just work.
- Only ONE machine should be the "active" one at a time to avoid merge conflicts. Pull first, always.
- Renders in `out\` and audio `.mp3`/`.mp4` are gitignored (they regenerate) - they do NOT sync. If you
  want to review a specific render on the other machine, copy the file by hand or have Claude re-render.
- The keys, ffmpeg, and music (steps 2/5/6) are one-time - they don't change, no need to re-sync.

## Notes
- Keys are loaded from `%USERPROFILE%\.youtube_bot_*.txt` by src/llm.py + the TTS module - laptop username
  can differ from "Caden", the loaders use your home dir.
- This is a TLS-intercept-friendly setup; the env flags in step 7 (REMOTION_USE_SYSTEM_CA, NODE_OPTIONS)
  may be unnecessary on a normal home network but are harmless.
