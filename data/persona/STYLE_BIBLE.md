# Channel Style Bible (master document)

The single source of truth for how this channel writes, sounds, and feels. The script
writer (a human, or Gemini/an LLM) reads this so every video is (1) consistent and
(2) actually what the owner wants. It GROWS over time - every personality decision,
example, joke, influence, and reference transcript gets added here.

Companion file: `voiceprint.json` = the machine-updatable layer (favored phrasings, jokes
that landed, owner-flagged lines) that evolves automatically from feedback. This doc is the
human-curated layer.

## How this is used (and how it scales)
- The script generator injects the **CORE** (sections 1-6) into its prompt as the style
  reference + a few-shot "write like this" block.
- Sections 7-9 are a growing **archive** (owner's own samples, full reference transcripts,
  per-video notes). They can get huge, so we do NOT inject all of it every time - instead we
  periodically **distill** new material from the archive up into the core exemplars/rules.
- Owner adds material freely; Claude keeps the core tight and the distillation honest.

---

## 1. The Narrator (persona)
Dry, witty, understated, curious. Smart but never smug. Explains genuinely fascinating things
in plain language and lets the absurd parts land on their own. Talks to "you" like a clever
friend, not a lecturer. (Full rules live in `persona.md` - this is the summary.)
- Sounds informed, not impressed with himself.
- One dry aside every few paragraphs, not every line. Scarcity keeps it funny.
- Drops the jokes for the genuine reveal and lets it be plain.
- Personality stays DRY for the first videos; deepens as the owner feeds in his own voice.

## 2. Influences - who we borrow from, and exactly WHAT we take
(Take a specific thing from each; we are not copying anyone wholesale.)
- **Veritasium** - tension, real stakes, the "but actually..." reveal, the slow turn of a screw.
- **Vsauce** - the destabilizing opening question; permission to wander into a tangent.
- **CGP Grey** - cutaway timing, visual economy, letting a clean visual carry a beat.
- **Kurzgesagt** - clarity and structure (but we are drier, less awe-struck).
- _[owner: add channels/people + the ONE thing we take from each]_

## 3. Voice exemplars - "write like THIS"
Lines that ARE the voice. (Seeded from the GPS pilot; add the best lines from every video.)
- "Which is a start, technically. It's also several thousand kilometers of start."
- "Your phone keeps time like a tired intern with a cheap watch."
- "...reduced to a background process so you can find a coffee shop."
- "The satellites have no idea it exists."
- _[owner: paste lines you wish you'd written / that sound like you]_

## 4. Humor / jokes
The kind of funny we want: deadpan, understatement, a grand mechanism contrasted with a
trivial payoff, taking something literally, the quiet contradiction. NOT meme-y, NOT hype.
- _[owner: drop jokes you'd make, things you find funny, your sense of humor in your words]_

## 5. Structure & pacing (the JOURNEY, not a textbook)
Every video is a journey: **hook a mystery -> dismantle the obvious assumption -> escalating
reveals -> a twist -> the big reveal -> a lingering reframe -> dry CTA.** Talk to "you." Plant
open loops and pay them off. Depth over brevity - go as long as the idea earns (10-20 min is
fine). Never "here's a fact, here's the explanation, done."

## 6. Banned / avoid
- Hype: "mind-blowing", "you won't believe", "this changes everything", "game changer".
- Filler openers: "let's dive in", "buckle up", "sit back and relax".
- Meme phrasing, internet-comment sarcasm, winking after every joke.
- Sounding like a digital textbook.

---

## 7. Owner's own voice (how HE actually talks)  _[GROWING]_
Transcripts of the owner talking, his writing, phrases he uses, things he's said he likes.
This is what makes the narrator sound like HIM over time.
- _[to be added - owner will paste voiceovers / writing / messages]_

## 8. Reference transcripts archive  _[GROWING]_
Full transcripts/excerpts of videos we want to emulate (tagged with what to learn from each).
- _[to be added]_

## 9. Per-video log - what worked / what didn't  _[GROWING]_
- _[updated after each video: lines that landed, jokes that flopped, pacing notes, comments]_
