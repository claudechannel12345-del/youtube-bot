# YouTube Bot — Overhaul Research Report (DRAFT v1, pre-Codex review)

Date: 2026-06-02
Author: Claude (Opus). Status: **DRAFT — awaiting Codex cross-check + user approval.**
Scope: voice, animation engine, subtitles, topic originality, video format, shorts,
upload timing, monetisation risk. Costs priced per path. No code changed yet.

---

## 0. The finding that reshapes everything (read first)

YouTube's **"inauthentic content"** rule (renamed from "repetitious" in July 2025, broadened
again July 15 2026) drove the **largest mass-termination of AI channels in YouTube history in
January 2026**. The reported pattern that got killed:

> *faceless format + synthetic voiceover + templated scripts + upload schedule built around
> volume instead of substance.*

That is an almost exact description of the current bot. AI-assisted content **is** still
monetisable in 2026 — but only when it shows "original value," "significant human input," a
"unique narrative," and is **not** mass-produced.

**Direct consequence:** the three stated goals — *fully hands-off*, *daily*, *revenue* — are in
tension. You can have any two cleanly; all three on the current pattern is the exact profile being
demonetised. The overhaul below is built to resolve that tension, but it requires two preference
trade-offs (a light human gate + lower cadence) called out in §8.

---

## ★ FINAL PLAN (v2 — reconciled with Codex cross-check, 2026-06-03)

Codex independently web-verified the facts (it couldn't read this file due to a Windows
sandbox issue — to be fixed before the coding phase). Net result: we agree, and the plan is now
**Remotion-first, default-zero-paid**, which fits "as free as possible" better than my draft Path B.

**Corrected pricing (Codex, from official docs 2026-06-03):**
- Veo 3.1 **Fast $0.10/s** (720p), **Standard $0.40/s**, **Lite $0.05/s** ← Lite is the cheap tier I missed; audio included on all.
- **Sora 2: deprecated, shuts down Sept 24 2026 → DO NOT USE.** (Resolves the open question.)
- Kling 3.0 ~$0.10–0.20/s; Wan 2.6 ~$0.025–0.15/s; Grok ~$0.05–0.07/s (audio uncertain — verify empirically).
- gpt-4o-mini-tts confirmed (~$0.015/min).

**Remotion licensing RESOLVED:** **Free for a solo individual**, including commercial *and*
automated use ("Create and automate"). The $100/mo Automators tier only applies to companies/teams
of 4+. → Remotion is the engine; it's free as long as you stay solo.

**The agreed pipeline (baseline cost ≈ $0.20/video, ≈ $2–6/mo):**
1. **Remotion** renders the whole video on GitHub Actions (free). Rich motion graphics: kinetic
   text, charts, animated diagrams, maps, timelines, data viz — NOT a slideshow.
2. **Free real assets** where rights permit: public-domain / Wikimedia / Internet Archive / gov
   media / generated diagrams. (Not the core, per your earlier note — supplementary.)
3. **AI video clips = optional, OFF by default.** A pluggable "shot provider" layer, capped per
   episode, used only for 2–4 hero/impossible shots that earn their cost. Veo Lite/Fast or budget
   models — never Sora 2. Paid video is the exception, not the layer.
4. **Voice:** gpt-4o-mini-tts, steered + script-written-for-speech.
5. **Captions:** accurate SRT uploaded (no burn-in); burned captions only on Shorts.
6. **Thumbnails (free):** compose 3 from the video's own high-contrast frames + bold 3–5 word
   text, brand colors → you pick one. (No paid image API; Codex confirms this is the right call.)
7. **Title + hook:** auto-generate a couple, you pick.

**Monetisation — Codex's key escalation (most important):** reduced cadence + human-pick is **NOT
enough**. YouTube's policy explicitly names templated/low-variation/slideshow/generic-AI content.
To pass YPP we must show **authorship evidence**: materially different topics, original research
angles, unique narrative structure, non-template editing variance between videos, cited sources,
substantive commentary. **Add a per-episode "production log"** (sources, outline, asset licenses,
human decisions, editorial notes) to defend monetisation/appeals.

**Build order:** unchanged from §9 below, with animation = Remotion-first (not Path B). Phase 1
(voice + script-for-speech + SRT) is low-risk/high-impact and the place to start.

---

## 1. Voice (decision already made: gpt-4o-mini-tts)

**Why the current voice is robotic:** `tts-1-hd` + `fable` is OpenAI's *oldest* TTS model. It
has no prosody control, so it reads everything flat.

**`gpt-4o-mini-tts` (the pick):**
- Pricing: token-based ≈ **$0.015/min** ($0.60/1M input text tokens + ~$10–12/1M audio tokens).
  A 10-min video ≈ **$0.15**. Negligible.
- Key upgrade: **steerable** via a natural-language `instructions` parameter (tone, emotion,
  pacing) — not available on tts-1. ~50% cheaper than ElevenLabs.
- The ChatGPT "Advanced Voice" you like is a *realtime conversational* model, **not** exposed as
  a script-to-file TTS API. gpt-4o-mini-tts is the closest controllable substitute.

**To actually fix the sound (not just swap models):**
1. Switch model to `gpt-4o-mini-tts`.
2. Add an `instructions` style prompt (e.g. *"warm, curious documentary narrator; natural pauses
   at commas and full stops; slight emphasis on surprising words; unhurried"*).
3. Fix the **script** for speech: contractions, shorter sentences, ellipses/em-dashes for
   breath, no bullet-y fragments. Robotic delivery is ~half model, ~half script written for the eye.
4. Render per-sentence and reassemble for cleaner pacing + accurate caption timing (see §3).

*Alternative if still not good enough:* ElevenLabs (~$5–22/mo) is the quality ceiling. Hold as
fallback; gpt-4o-mini-tts first.

---

## 2. Animation engine — THE fork (priced)

### Correction on prior claims
- **3Blue1Brown = Manim** (geometric/math). **Ted-Ed = human freelance 2D animators** (not Manim).
  "Fully automated, character-driven like Ted-Ed" is **not** achievable with Manim. The current
  output is literally circles+text = an animated slideshow. You're right to scrap it.

### The realistic options, priced (assume ~10-min video; daily=30/mo, 3×/week=12/mo)

| Path | What it is | Look | Cost/video | Cost/mo (12 / 30) | Headless CI? |
|------|-----------|------|-----------|-------------------|--------------|
| **A. Pure Remotion** | React-coded motion graphics | Polished YouTube motion-graphics (shapes, icons, kinetic text, charts, transitions). No characters. | ~$0.20 | **$2.40 / $6** | ✅ proven |
| **B. Remotion + budget AI clips** | Remotion base + ~30s/video AI clips (Wan/Grok ~$0.05/s) | Motion graphics + occasional real moving footage for hooks/key moments | ~$1.70 | **$20 / $51** | ✅ |
| **C. Remotion + Veo 3.1 Fast clips** | Base + ~30s/video Veo Fast ($0.15/s, native audio) | Same as B but cinematic-grade hero clips | ~$4.70 | **$56 / $141** | ✅ |
| **D. Full AI video** | Entire 10-min from Veo/Sora/Kling | Most "real animation" | Veo Fast $90, Std $240; Kling $76 | **$900+ / $2,700+** | ✅ but absurd cost + consistency hell |

**AI video reference pricing (with native audio unless noted):** Veo 3.1 Fast **$0.15/s**, Veo 3.1
Standard **$0.40/s**, Kling 3.0 **$0.126/s**, Sora 2 **~$0.10/s**, budget (Wan 2.6 / Grok) **~$0.05/s**.

**Consistency (the old blocker, now tractable):** reference-image systems solve identity drift —
Veo 3.1 "Ingredients to Video" (3–4 ref images), Seedance 2.0 "Identity Lock" (9 images), Sora
reference/cameos. So a recurring visual motif/character across clips is now feasible, at the cost
of a storyboard→reference→generate→assemble orchestration layer. (NOTE: a "Sora is gone" headline
appeared — Sora API availability must be verified by Codex.)

**Remotion licensing — must verify (Codex):** free for individuals & companies ≤3 people, even
commercial (headcount-based). BUT a separate **"Remotion for Automators"** tier ($0.01/render,
**$100/mo minimum**) is described as *for "automated video pipelines."* As a solo individual the
free license most likely applies, but the Automators language is ambiguous for an automated
pipeline. **This is a potential $100/mo gotcha — confirm before building on Remotion.**

### My recommendation (to be challenged by Codex): **Path B → C**
Start with **Path B** (Remotion core + budget AI hero clips). It delivers genuine animation and
movement, formats like a real YouTube video (not a deck), runs headless in CI, and stays ~$20–50/mo.
Upgrade the AI-clip layer to **Veo Fast (Path C)** once the pipeline is proven and only if quality
demands it. **Path D is off the table** on cost + consistency. Manim is retired except possibly for
genuine math/diagram inserts.

---

## 3. Subtitles — drop burned-in, use a real caption track

- 2026 best practice: **upload an SRT** (YouTube indexes it for search + gives the CC toggle) rather
  than only burning pixels into the frame.
- We have the exact script + per-sentence TTS timing, so we can generate a **precise SRT** (better
  than YouTube auto-caption) and upload via the `captions.insert` API. Remove the ASS burn-in entirely.
- Exception: **Shorts** benefit from stylish *burned* captions (mobile, sound-off). Keep burned
  captions **only** in the Shorts pipeline (§5).

---

## 4. Topic originality + packaging (the click problem)

- Stop rehashing top videos — that's both a CTR dead end and a monetisation ("inauthentic") risk.
- Build an **ideation engine** that produces *original angles*: counterintuitive framing, gap
  analysis (questions the niche hasn't answered well), "before/after" reveals (those thumbnails get
  ~+35% CTR), and specific named facts/sources.
- **Packaging = angle-first:** title carries outcome + specificity + curiosity gap; generate
  several title/thumbnail candidates per video. Optimising *both* title & thumbnail ≈ +40% CTR vs one.
- Thumbnails: one concept, minimal clutter, surprise/curiosity, blue = trust for educational.
- Feeds the human gate in §8 (the "genuine human creativity" signal monetisation now requires).

---

## 5. Video format (YouTube, not a presentation)

Rebuild `script_generator.py` around retention structure, not 20 equal "sections":
- **Cold-open hook in first ~5s** (open on the most surprising moment, then "here's how we got here").
- Pattern interrupts, varied shot/scene rhythm, no uniform section cadence.
- Chapters, mid-video re-hook, end screen / CTA, B-roll rhythm.
- **Shorts pipeline (new):** auto-cut 2–3 vertical 20–45s clips from each long-form (strongest hook
  moments), burned stylish captions, posted on a **separate schedule** (Shorts and long-form peak at
  opposite times). Shorts = acquisition layer only.

---

## 6. Upload timing

- Long-form educational: weekday **afternoons 2–4 PM ET**, **Mon–Wed** strongest. Publish **2–3h
  before** peak so the algorithm indexes it → target **~12 PM ET = ~16:00 UTC** (vs current 15:00).
- Shorts: schedule **separately** from long-form (opposite peak times).
- Long term: switch to data-driven from YouTube Studio Audience heat-map once there's history.

---

## 7. Reliability (carry-over)

- Silent fallback (solid dark clip on render fail) hides failures. Add logging + a failure
  notification (e.g. email / GitHub issue / webhook) so a degraded video doesn't publish unnoticed.

---

## 8. The two preference trade-offs (need your call)

1. **Light human gate vs zero-touch.** Monetisation in 2026 effectively requires a visible
   human-creativity signal. Cheapest insurance: a ~2-min approval step (approve/redo title +
   thumbnail + hook, or final video) before publish. This breaks "zero manual steps" but is the
   single biggest factor in *not getting demonetised*. Option to stay fully auto and accept the risk.
2. **Cadence: daily → ~2–3×/week.** Daily volume is itself a flagged signal and dilutes per-video
   quality. Fewer, better, more original videos both survive policy and grow faster now. Daily is
   possible but raises both cost and demonetisation risk.

---

## 9. Proposed build order (after approval)

1. Voice swap + script-for-speech + per-sentence render + SRT generation/upload (kills two
   problems: robotic voice + burned subs). *Low risk, high impact.*
2. Script generator → YouTube retention format + ideation/packaging engine.
3. Animation: Remotion core (Path B), retire Manim. **(Mass coding → hand to Codex, I review.)**
4. AI hero-clip layer (budget model first), reference-image consistency.
5. Shorts pipeline.
6. Timing + reliability/alerting + (optional) human gate.

---

## 10. Open questions for Codex (cross-check targets)

- Verify Veo 3.1 / Kling / budget-model **per-second pricing** and that audio is included.
- Verify **Sora 2 API** availability ("Sora is gone" headline).
- Resolve **Remotion licensing** for a solo *automated pipeline* (free vs $100/mo Automators).
- Sanity-check the **per-video cost math** in §2.
- Challenge the **Path B recommendation** — is full-AI ever justified, or a cheaper non-Remotion
  motion-graphics route (e.g. pure FFmpeg/Motion Canvas) better?
- Pressure-test the **monetisation strategy** (cadence + human gate) against latest enforcement.

---

## Sources
- gpt-4o-mini-tts pricing/steerability: tokenmix.ai, costgoat.com/pricing/openai-tts, openai.com/api/pricing
- AI video pricing: buildmvpfast.com/api-costs/ai-video, costgoat.com/pricing/google-veo, modelslab.com, devtk.ai
- Veo 3.1 tiers: aifreeapi.com Veo 3.1 pricing, mindstudio.ai Veo comparison
- Remotion: remotion.dev/docs/license, remotion.pro/license, remotion.dev/docs/ssr (GitHub Actions)
- Captions: opus.pro shorts captions, zorgsubtitle.com upload subtitles 2026
- Monetisation: invideo.io faceless-AI policy, flocker.tv inauthentic enforcement, alici.ai compliance playbook
- Packaging/CTR: influenceflow.io 2026 CTR guide, medium TitleHooks packaging
- Timing: socialpilot.co, buffer.com best-time-to-post
- AI consistency: mindstudio.ai Sora reference system, genra.ai/verticalstudio character consistency
</content>
