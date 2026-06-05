# Brain Dumps (owner's raw input, per video)

The owner records an audio brain-dump for each video idea (whatever he's curious about that day).
Each one does TRIPLE duty:
1. **Content** - the raw info/angle for that video's script.
2. **Voice/style learning** - transcribed here so the writer can see how the owner actually talks,
   what he finds interesting, his humor and phrasing. Distill recurring patterns up into
   [[../persona/STYLE_BIBLE.md]] sections 3/4/7 and into voiceprint.json over time.
3. **Voice-clone corpus** - the audio files accumulate as clean training data toward a higher-
   fidelity Professional Voice Clone later (the current voice is a 3-min instant clone).

## How it flows
- Owner records audio (RODECaster, clean) -> saves the file.
- Claude transcribes it (Gemini handles audio transcription; keep OpenAI out of it for cost) ->
  appends the transcript below with a date + topic + the audio filename.
- Audio files are kept in **data/persona/voice_corpus/** (gitignored if large) for the future clone.
- Claude reads the accumulated dumps to keep the writing sounding like the owner.

## Dumps
_(none yet - first one drops here once the owner records it)_

<!--
Template per entry:
### YYYY-MM-DD - <topic>   (audio: voice_corpus/<file>)
<transcript>
**Style notes Claude pulled:** <recurring phrasings / humor / what he found interesting>
-->
