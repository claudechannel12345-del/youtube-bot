# Fix list - "The Referee Sees Red" v1 (from owner critique 2026-06-05)

Source: voice critique (transcript in _braindump_color_critique.txt, NOT for voice cloning - owner
wasn't speaking clearly). Overall verdict: "sounds really good in general." Below = everything to fix.

## A. VOICE / DELIVERY (TTS pacing + tone)
A1. **Overall: too flat / monotone / "dry in a really bad way."** Wants it more UPBEAT, more emotion,
    actually interesting to listen to. (Biggest note - likely needs a voice-settings retune and/or a
    more energetic delivery; tension with the "dry-witty" plan.)
A2. Intro sounds different from the rest - too "grandiose"/quiet. Make it match the body.
A3. "Same height. Same weight. Same training." - needs more pause between each.
A4. "That sounds like superstition. It isn't." - weird EXHALE on "it isn't," tone off. Fix/remove.
A5. "It's a coin flip." - sounds like the start of a sentence, not its own line. Fix cadence.
A6. "It didn't." - weird exhale, wrong tone.
A7. "...isn't a fair coin. [PAUSE] So something was loading it." - needs a pause; there was none.
A8. "I am dominant" - sounds British(!). Re-render / adjust.
A9. "Across primates, birds, fish, [PAUSE] red tends to mean the same thing." - needs the pause.
A10. Transition "...being fair. [BIG PAUSE] Once you know to look for it..." - needs a bigger pause
     (major section transition).
A11. "Not occasionally, [PAUSE] consistently." (~2:41) - wrong toning; reads as one flat sentence.
A12. Transition "Now move it somewhere the score actually matters." (~3:06) - bigger pause before it.
A13. "It doesn't switch off because the stakes went up... gets better at hiding." (~2:46) - needs a
     dramatic pause; tone off.
A14. "...this one is wobbling and you should be..." (~4:17) - tone wrong.
A15. "What changed? [PAUSE] The sports did." - no pause at all, sounds wrong.
NOTE: many of these are the per-sentence pause/delivery pacing - fixable via delivery tags + pause
gaps. The pronunciation ones (A8 British, "zebra finches") need phonetic spelling or rephrasing.

## B. SCRIPT / WRITING
B1. **Intro jumps straight in.** Add a hook first: "how I discovered this" (the SAT story) + why it's
    interesting, THEN go into the meat.
B2. "zebra finches" pronounced wrong - respell phonetically or reword.
B3. **Romantic-red passage is too complicated** - too many buzzwords ("wobbling," "suspicious of
    anyone who sells it," "tidy color story bends the people studying it"). Doesn't make sense / "not
    a good line." SIMPLIFY so it actually lands.
B4. "mid-history" (~2:45) - unclear word. Replace.
B5. **Section 9 kills its own suspense:** asks "where does that leave the red advantage?" then
    immediately reveals "50.5%." Restructure so the reveal earns a beat of suspense first.
B6. **Ending is abrupt / bad.** Add a real closing statement - leave viewers with something
    interesting (a hook out, not a hard stop).

## C. GRAPHICS / ANIMATION
C1. **More frequent graphics + more variety/change** overall (less static).
C2. **Mandrill/animals section: the graphic doesn't make sense** (a "light" + person around a
    circle). Needs an actual animal graphic (mandrill / bird) - requires new vector assets.
C3. Romantic-red scene (~3:57): "circle with person and a light, light pointing backwards" - makes no
    sense for the topic. Redo.
C4. Male character should read as male / female as female (romantic-red "woman in red" beat) - distinct
    characters, not two identical figures.

## Execution notes
- A3-A15 + B*: doable locally now (script + pacing rebuild, then re-render voiced - free, no upload).
- A1 (upbeat voice) + C2/C4 (new animal + gendered characters): need owner decision on approach.

## v3 RESOLUTION (2026-06-05, autonomous pass)
JIBBERISH (the big one) - likely cause = style 0.30 on the instant clone + ultra-short isolated
clips. Fixed defensively: (1) pass previous_text/next_text CONTEXT to ElevenLabs so short clips render
stably; (2) style 0.30->0.0; (3) stability 0.45->0.5; (4) script uses COMPLETE sentences only (no
1-2 word fragments rendered alone). NOTE: unverifiable by ear here - owner must confirm on the v3.
PAUSES - moderated all tiers + removed every mid-sentence fragment split, so pauses only fall at real
sentence ends. EXHALES/UM - addressed via higher stability + context + no stray text (no perfect TTS
toggle exists in v2 model). VOICE - reverted to the old clone (OOLdd0, script-read, more emotional)
per owner.
SCRIPT - intro discovery hook added, romantic-red simplified, section-9 suspense fixed, real outro,
"mid-history" replaced.
GRAPHICS (all verified via stills): person_female simplified (no hair, dress only, narrow shoulders);
mandrill redesigned to read as a primate face + scaled up; gavel redesigned (clear); generic_object
face-card removed -> plain box; new 'document' asset for the test scene; stray ground-ring removed;
single-subject object scenes scaled up (less bare); red/blue routed into object scenes too; the
counter '42' placeholder + net-grid scenes replaced.
OUTPUT: v3 = Desktop/color_VOICED_v3.mp4 (rendered autonomously). Still OPEN for owner: judge the
voice energy + confirm jibberish gone; mandrill could be refined further; music bed still to be added
(drop a YT Audio Library track in data/music/).
