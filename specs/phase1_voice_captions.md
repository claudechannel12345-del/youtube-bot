# Phase 1 spec — Voice upgrade + accurate SRT captions (no burn-in)

Goal: fix the robotic voice and replace burned-in subtitles with an accurate uploaded SRT.
Keep the pipeline runnable (Manim animation stays for now; it is replaced in Phase 3).
Do NOT introduce new pip dependencies (ffmpeg/ffprobe and the `openai` SDK are already available).

## 1. `src/tts_generator.py` — rewrite
- Constants: `MODEL = "gpt-4o-mini-tts"`, `VOICE = "fable"`,
  `INSTRUCTIONS = "Warm, curious documentary narrator. Natural pauses at commas and full stops. Slight emphasis on surprising words. Unhurried, clear, conversational — not robotic."`
- Keep `get_audio_duration(path)` exactly as is (ffprobe).
- New function `synthesize_section(text, output_path, temp_dir) -> list[dict]`:
  - Split `text` into sentences (regex on `(?<=[.!?])\s+`, drop empties).
  - For each sentence i: call OpenAI `client.audio.speech.create(model=MODEL, voice=VOICE, input=sentence, instructions=INSTRUCTIONS, response_format="mp3")`, write to `temp_dir/_sent_{i:03d}.mp3`, measure its duration with `get_audio_duration`.
  - Concatenate the per-sentence mp3s into `output_path` using ffmpeg concat demuxer (re-encode to a uniform mp3 to avoid concat artifacts).
  - Return a list of `{"text": sentence, "start": float, "end": float}` with times **relative to the start of this section** (cumulative).
  - If `text` has no sentences, synthesize the whole text as one chunk and return a single entry.
  - Clean up the temp per-sentence files.
- Create the OpenAI client once per call: `client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])`.

## 2. `src/caption_generator.py` — NEW file
- `def _ts(seconds: float) -> str`: format as SRT timestamp `HH:MM:SS,mmm`.
- `def build_srt(cues, output_path)`: `cues` is a flat list of `{"text","start","end"}` with
  GLOBAL times (seconds). Write a valid UTF-8 SRT file (index, `start --> end`, text, blank line).
  Skip cues where end <= start.

## 3. `src/video_assembler.py` — remove burned subtitles
- Delete `_build_ass`, `_sec_to_ass`, and the final ffmpeg subtitle-burn step.
- `assemble_video(sections, temp_dir, output_path)` now: merge each section clip
  (`create_section_clip`) then `concatenate_clips(...)` directly into `output_path`. No ASS burn.
- Keep `create_section_clip` and `concatenate_clips` unchanged.

## 4. `src/uploader.py` — upload the SRT caption track
- Change signature to `upload_video(video_path, thumbnail_path, metadata, srt_path=None)`.
- After the video upload and thumbnail set, if `srt_path` and `os.path.exists(srt_path)`:
  call `youtube.captions().insert(part="snippet", body={"snippet": {"videoId": video_id, "language": "en", "name": "English", "isDraft": False}}, media_body=MediaFileUpload(srt_path))`.execute().
  Wrap in try/except; print a non-fatal warning on failure. Print success otherwise.

## 5. `src/main.py` — wire it together
- Replace `generate_section_audio` import/use with `synthesize_section`.
- For each section: `sent_timings = synthesize_section(section["narration"], audio_path, TEMP_DIR)`;
  `duration = get_audio_duration(audio_path)`. Maintain a running `global_offset`; for each entry in
  `sent_timings`, append to a module-level `cues` list `{"text", "start": global_offset+entry["start"], "end": global_offset+entry["end"]}`; then `global_offset += duration`.
- After step 4 (assemble) and before/after upload: build the SRT to `TEMP_DIR/captions.srt` via
  `build_srt(cues, srt_path)`.
- Pass `srt_path` to `upload_video(...)`.
- Keep the existing Manim animation step and all prints; just renumber/adjust as needed.

## 6. Verify
- After editing, run a syntax check on all changed/new files (e.g. `python -m py_compile src/*.py`)
  and report the result. Do not run the full pipeline (needs API keys).
</content>
