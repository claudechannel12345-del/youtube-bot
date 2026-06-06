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

### 2026-06-05 - Color & performance (red advantage)   (audio: voice_corpus/ColorPerformance.wav, full-quality original in C:\Users\Caden\Documents\Audacity\)
Okay, the idea I have for this first video is something I saw on an SAT I took a couple years ago. The
premise should be about - first of all, the study I learned was that the color of the uniform you're
wearing in sports can actually affect your performance and how you're being judged. So the study I found
(you should fact check this for me, you can probably find past SAT tests to find this) essentially said
there's two reasons for this and the red person has the advantage in like a red and blue color scheme.
For wrestling specifically - I think it was wrestling - they showed two possible solutions. One is that
the person in blue had a reaction to the red and it gave the red person an advantage. Or that when people
are judging it, they judge the person in red better than the person in blue. So these were both checked.
I don't remember how they checked the one about the people actually wrestling, but the one with the judge:
they took wrestling film that ended in a draw and then color-swapped the red and the blue and had people
judge those matches. Even though they'd usually end in a draw, people would give the edge to the person in
red the majority of the time. It's a really interesting study I'd never heard of before. So I want to look
into that and then look into what else the color you wear can impact - like a job application, or if you're
getting charged for a crime, or if you're meeting new people. Check all kinds of studies. You can use
quotes from studies. I've never heard of a video like that - check if there are videos out there that have
done well with this same premise. And if you can, pull the exact study from the SAT. I took it my junior
year, three years ago, right before they switched to the online thing. So that's my idea. Give me a
framework - I want you to do a lot of research first to figure out all the info and the different studies,
then come back and talk to me about the idea and where we can go with it.

**Style notes Claude pulled:** Leads with a personal hook ("something I saw on an SAT I took"). Thinks in
mechanisms - the "two reasons / two possible solutions" framing is core to how he finds things interesting
(he wants the WHY, and more than one candidate explanation). Strong rigor instinct: repeatedly says "fact
check this for me," "check all kinds of studies," "check if videos exist" - he wants honesty and is wary of
overclaiming. Curiosity is broad and outward-spreading: from one finding he immediately asks "what else
could this impact" (jobs, crime, dating). Casual, understated, hedging delivery ("I guess," "I think it was
wrestling," "I don't remember how," lots of "um/like"). Not hypey - collaborative and low-key ("let me know
what you think," "where we can go with it"). Distilled into [[../persona/STYLE_BIBLE.md]]: open on a
concrete personal/relatable hook, structure around competing explanations, earn trust by showing the
checking, then widen the lens. Research write-up: see RESEARCH_color_performance.md.

<!--
Template per entry:
### YYYY-MM-DD - <topic>   (audio: voice_corpus/<file>)
<transcript>
**Style notes Claude pulled:** <recurring phrasings / humor / what he found interesting>
-->
