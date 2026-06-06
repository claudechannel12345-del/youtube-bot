# Background music beds

The render pipeline (scripts/render_voiced.py -> scripts/mix_music.py) automatically mixes a subtle
music bed UNDER the narration: looped to length, low volume, gentle fade in/out. The voice stays at
full level.

## How to add music (monetization-safe path)
1. Go to **YouTube Studio -> Audio Library** (studio.youtube.com -> Audio Library), signed in as the
   channel (claudechannel12345@gmail.com).
2. Filter to low-energy instrumental: genre **Ambient** or **Cinematic**, mood **Calm / Dramatic**,
   and prefer tracks marked "No attribution required."
3. Download 1-3 tracks you like and **drop the files into this folder** (`data/music/`).
   - Audio Library tracks carry **zero Content ID claims** - safe to monetize.
4. That's it. The pipeline auto-picks the first audio file here (`.mp3/.m4a/.wav/.ogg`, alphabetical).
   To force a specific one, set `MUSIC_PATH=...`.

## Tuning knobs (env vars)
- `MUSIC_VOLUME` - bed loudness, default `0.10` (try 0.06-0.14; CGP-Grey-ish is quiet).
- `MUSIC_DUCK=1` - dip the music slightly while the narrator talks (off by default; the bed is
  already quiet enough that constant usually sounds cleaner).

## Notes
- Audio files here are gitignored (large / per-channel). If you ever use a track that needs
  attribution, record it in `MUSIC_CREDITS.md` so it can be auto-added to the video description.
- One subtle track looped across the whole video is the CGP-Grey approach and the default here.
