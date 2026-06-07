# SCRIPT BRIEF — "Homework Was Invented as a Punishment" (Second Glance)

You are the head writer for **Second Glance**, a CGP-Grey-style clean-flat illustrated explainer
channel. Write the FULL narration script for one video, improving and EXPANDING the v1 draft below.

## VOICE
- Energetic and conversational, with deliberate tonal SHIFTS (build up, then drop flat on a twist).
- Smart but never smug. Light humor that lands through timing, not zaniness.
- First person, talking straight to one viewer ("you").
- This is the owner's own cloned voice, so it should sound like a sharp friend telling you something wild.

## HARD STRUCTURE (do not change the shape)
Bait-and-switch: STATE THE MYTH AS IF IT IS TRUE and sell it hard in the open. Then reveal it is false.
Then deliver the real, wilder history: Prussian obedience tool -> brought to America -> attacked as a
"national crime" and BANNED -> revived by Sputnik -> the panic-revival pattern repeats -> today. End on
a funny payoff that calls back the fake inventor, then a warm subscribe CTA.

## EXPAND WITH THESE VERIFIED FACTS (only where they genuinely add meat; do NOT pad)
- The myth survives mostly because SEO/essay-mill websites needed a tidy answer to "who invented
  homework," so a fake inventor (Roberto Nevilis) spread across clickbait blogs. It feels true, so it stuck.
- The pendulum keeps swinging: Sputnik (1957) was not the only panic. A 1960s-70s backlash softened
  homework again, then the 1983 "A Nation at Risk" report (fear the US was losing economically, esp. to
  Japan) triggered ANOTHER homework surge. Pattern: national panic -> homework spikes. It has repeated.
- (Optional, one line) Modern research on homework's benefit is lukewarm, especially for young kids
  (the "ten-minute rule"); we largely keep it out of habit and that Cold War reflex.

## ACCURACY (must hold)
- Nevilis = fabricated; present as "true" only as the deliberate bait, then bust it clearly.
- Real, solid beats: Prussian Volksschule/obedience framing; Horace Mann brings it to the US in the
  1840s; Ladies' Home Journal 1900 "A National Crime at the Feet of Parents"; California 1901 ban for
  under-15s; Sputnik 1957 revival; 1983 A Nation at Risk resurgence.
- Do not invent statistics or quotes beyond these.

## TTS RULES (the narrator is ElevenLabs; avoid glitches)
- No mid-sentence dashes or colons; use periods and commas. Keep sentences fairly short and speakable.
- Avoid "'d" contractions (write "you would" not "you'd"). Contractions like won't/isn't/it's are fine.
- One idea per sentence where possible.

## OUTPUT FORMAT — return ONLY valid JSON, no markdown, matching:
{
  "title": "Homework Was Invented as a Punishment",
  "sections": [
    {
      "scene_label": "COLD OPEN",
      "environment": "classroom",
      "on_screen_text": ["short emphasis words only, or empty"],
      "narration": [ {"text": "one sentence.", "delivery": "neutral"} ],
      "visual": "one line describing the scene/action for the storyboard"
    }
  ]
}
- "delivery" must be one of: neutral, curious, question, brisk, weighty, surprised, skeptical, ominous, warm_cta.
- "environment" should be one of our scenes: classroom, courtroom, newsroom, news_studio, library, space,
  office, street (pick the best fit per section; classroom/courtroom/space/newsroom are the strong ones here).
- Target about 7 to 8 minutes of narration. Keep every line earning its place.

## V1 DRAFT TO IMPROVE AND EXPAND
COLD OPEN (classroom): Okay, you are going to love this one. Back in 1905 in Venice, Italy, a teacher
named Roberto Nevilis had a problem. His students would not learn. So he invented a punishment so
cruel they would never slack off again. He made them keep working after school was over, at home. He
invented homework, as a literal punishment. And it worked so well it spread across the whole planet.
Every worksheet, every essay, every Sunday night you spent crying over a math packet, traces back to
one annoyed Italian guy in 1905. Isn't that incredible. It is the perfect story.

THE TURN (hard cut): It is the perfect story. Which is exactly how you know it is nonsense. Roberto
Nevilis did not invent homework. Roberto Nevilis never existed. No records, no school, no documents.
He shows up in exactly one place, clickbait blogs. Some versions even say he did it in ten ninety five,
eleven years before the First Crusade. There were no classrooms in 1095.

WHY THE MYTH WORKS (newsroom): So why does everyone believe it. Because it feels true. We want
homework to have a villain. So the internet invented one. But the real story is so much better. Homework
was not dreamed up by a cranky teacher. It was rolled out by an entire government, on purpose, to make
people obey.

PRUSSIA (classroom/old): Rewind to the early 1800s. Prussia builds one of the first mandatory school
systems, the Volksschule. It was not really about reading and math. It was about molding loyal,
disciplined citizens. Homework was how the state reached past the school walls and into your home. It
was not punishment. It was programming.

AMERICA (ship to classroom): Enter Horace Mann. In the 1840s he visits Prussia, loves the discipline,
and brings the model home. Homework rides into American schools as a symbol of seriousness.

BACKLASH (courtroom/newsroom): By the early 1900s homework has powerful enemies. Doctors say it wrecks
kids health. In 1900 the Ladies Home Journal calls it a National Crime at the Feet of Parents. And in
1901 California bans it for every kid under fifteen. For years, homework was basically illegal. The
kids won.

SPUTNIK (space): Then in 1957 the Soviet Union launches Sputnik, and America panics. If the Soviets
win in space, they win in science. The fix everyone reaches for is pile the work back on. A beach ball
sized hunk of Soviet metal beeping in orbit is the reason you have a math packet due Monday.

NOW (classroom): Homework came roaring back and never left. The research on whether it actually helps
is famously lukewarm. We mostly keep it because we always have.

CLOSER (classroom): So next time you are up at midnight on an assignment, you cannot even blame Roberto
Nevilis. He is not real. You would have to blame Prussia, and a guy named Horace, and the Cold War, and
a satellite. Honestly, blaming a fake Italian man was easier.

CTA: If you had no idea homework was once an actual crime, there is a lot more hiding in the boring
stuff around you. Take a Second Glance. Subscribe, and I will see you in the next one.
