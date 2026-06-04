# YouTube Bot — Build Progress (RESUME FILE)

**If you are an AI resuming this project: read this file first, then `RESEARCH.md` (the
★ FINAL PLAN section), then continue from the phase marked 👉 RESUME HERE.**

Last updated: 2026-06-02 (session start of build)

---

## How this build works
- **Claude (Opus)** specs each phase + reviews/verifies the code.
- **Codex** (`gpt-5.5`) does the heavy coding. Invoke headless:
  ```
  codex exec --skip-git-repo-check -C /e/youtube-bot -s workspace-write "<task or 'implement specs/phaseN.md'>"
  ```
  - Codex auth: re-login via `codex login` if you see `refresh_token_reused` / 401.
  - Windows sandbox is set to `unelevated` in `~/.codex/config.toml` (REQUIRED — `elevated`
    breaks headless shell). Don't revert it.
  - Capture Codex's final message with `-o <file>` if needed.

## Key approved decisions (from RESEARCH.md ★ FINAL PLAN)
- Engine: **Remotion-first** (free for solo individual). Stay solo or it's $100/mo.
- Voice: **gpt-4o-mini-tts**, steered + script-written-for-speech.
- Captions: **upload SRT**, NO burned-in subtitles (burn only on Shorts).
- AI video clips: **OFF by default**, pluggable shot provider, only 2-4 hero shots when justified.
  Use Veo Lite ($0.05/s)/Fast ($0.10/s) — **NEVER Sora 2 (deprecated, dies Sept 24 2026)**.
- Thumbnails: **free**, composed from the video's own frames + text; generate ~3, user picks.
- Title + hook: auto-generate a couple, user picks.
- Cadence: ~2-3×/week (not daily). Upload ~16:00 UTC, Mon-Wed.
- Monetisation: must show authorship — original angles, narrative/editing variance, cited
  sources, + a per-episode **production log**. Human picks title/thumb/hook before publish.

---

## ⚠️ ACTION ITEMS FOR USER (one-time, manual)
- **Re-auth YouTube for captions.** Caption upload needs the `youtube.force-ssl` scope. The code
  now uses it, but the stored refresh token was made with the old `youtube` scope. Regenerate:
  `python auth/get_refresh_token.py` → update the `YOUTUBE_REFRESH_TOKEN` GitHub secret.
  Until then, SRT upload fails (non-fatal) and videos ship with no captions.

## Phase checklist

- [x] **Phase 1 — Voice + captions** ✅ DONE (reviewed by Claude)
  - [x] `tts_generator.py`: gpt-4o-mini-tts + `instructions` steering + per-sentence render w/ timing
  - [x] `caption_generator.py` (new): accurate global SRT from sentence timings
  - [x] `video_assembler.py`: removed burned ASS subtitles
  - [x] `uploader.py`: SRT via `captions().insert()` + scope bumped to `youtube.force-ssl`
  - [x] `auth/get_refresh_token.py`: scope bumped to `youtube.force-ssl`
  - [x] `main.py`: wired timing → SRT → uploader
  - Note: fixed mojibake Codex wrote into the INSTRUCTIONS string (watch for non-ASCII in Codex writes).
- [x] **Phase 2 — Script + ideation** ✅ DONE (reviewed by Claude)
  - [x] `research.py`: brainstorm-6-then-select, recent-topic avoidance, `why_original` + `key_facts`
  - [x] `script_generator.py`: retention structure, template vocab, title/hook/thumbnail options, validation
  - [x] `main.py`: append `script["title"]` to `data/topic_history.json` after upload (keep latest 50)
  - ⚠️ Phase 6 TODO: `data/topic_history.json` won't persist across GitHub Actions runs (ephemeral
    checkout). Must commit it back in the workflow OR use actions/cache, or topic variance resets each run.
- [x] **Phase 3 — Remotion engine** ✅ DONE (reviewed + render-tested by Claude)
  - [x] Full `remotion/` project: Root/Episode/Background/theme/types + all 10 templates with real motion
  - [x] `src/remotion_renderer.py` bridge (copy audio -> props.json -> `npx remotion render` -> cleanup)
  - [x] `main.py` switched to Remotion; deleted `animation_generator.py` + `video_assembler.py`
  - [x] `npm install` OK, `tsc --noEmit` clean, **real render of 4 templates verified** (stills looked great)
  - [x] Fixed: font loading limited to latin subset (was 28 net reqs/render); renderer uses
        `--props=props.json` + `NODE_OPTIONS=--use-system-ca`
  - **CI notes for Phase 6 / final:**
    - Workflow must: setup Node, `cd remotion && npm install`, AND `apt-get install ffmpeg`
      (Python tts/concat calls system ffmpeg/ffprobe; they are NOT on this Windows box but ARE in CI).
    - First render downloads Chromium headless shell (network needed once).
    - Local testing on this machine needs `NODE_OPTIONS=--use-system-ca` (TLS-intercepting network);
      no-op on CI. ffmpeg is not on local PATH, so full local end-to-end (with audio) can't run here —
      visual render path is proven; audio path will first run in CI.
- [x] **Phase 4 — AI hero-clip layer** ✅ DONE (reviewed by Claude)
  - [x] `src/shot_provider.py`: ShotProvider/NoneProvider/VeoProvider + get_provider + select_hero_indices
  - [x] `main.py` wires it; default (SHOT_PROVIDER=none, MAX_AI_CLIPS=0) = free no-op, identical output
  - [x] `ImageFocus.tsx` renders optional `<OffthreadVideo>` when a clip is provided; renderer copies clips
  - Note: VeoProvider is opt-in + UNTESTED (no keys/never enabled); fails gracefully to motion graphics.
- [x] **Phase 5 — Shorts pipeline** ✅ DONE (reviewed + still-rendered by Claude)
  - [x] `remotion/src/Short.tsx` vertical 1080x1920 composition (registered as 2nd comp "Short")
  - [x] `src/shorts_generator.py`: select 1-3 segments + render via Remotion Short
  - [x] `src/uploader.py`: `upload_short` (+#Shorts, no thumb/SRT) via shared `_upload_media`
  - [x] `main.py`: stores per-section captions, generates+uploads shorts after main (non-fatal), toggle MAKE_SHORTS
  - [x] Verified: Short still rendered clean (vertical, header band, big caption, progress bar)
- [x] **Phase 6 — Timing + alerting + production log + CI** ✅ DONE (reviewed by Claude)
  - [x] `requirements.txt`: removed Manim
  - [x] `src/production_log.py` + main.py writes per-episode authorship log (topic, angle, why_original,
        key_facts, title/hook/thumbnail options, templates, shorts ids)
  - [x] `.github/workflows/daily_video.yml`: cron Mon/Wed/Fri 16:00 UTC + dispatch; Node+Python; ffmpeg +
        best-effort chromium libs (24.04 libasound2t64 fallback); npm install; runs `python src/main.py`
        from root; commits topic_history + production_logs back; opens an issue on failure
  - [x] Final integration check: full `tsc --noEmit` clean + all 12 python modules compile

## ✅ BUILD COMPLETE — remaining MANUAL deploy steps (user)
1. **Re-auth YouTube for force-ssl** (captions): `python auth/get_refresh_token.py` -> update the
   `YOUTUBE_REFRESH_TOKEN` GitHub secret. Without this, caption upload fails (non-fatal).
2. **Commit + push** all changes to GitHub (NOT done automatically).
3. **Test run**: GitHub -> Actions -> Daily YouTube Video -> Run workflow. Watch the logs.
4. Optional later: enable AI hero clips via `SHOT_PROVIDER=veo` + `MAX_AI_CLIPS=2` (costs money).

## Session log
- 2026-06-02: Research done (RESEARCH.md), Codex cross-check done (CODEX_REVIEW.md), plan
  approved. Fixed Codex Windows sandbox (elevated->unelevated). Phases 1-6 built.
- 2026-06-03: DEPLOYED. Merged PR #1, force-ssl re-auth, first run SUCCESS (video Hye5uztN6ns +
  3 Shorts, captions worked). gh CLI installed. Thumbnail blocked pending channel phone-verify.

---

## v2 — ENGAGEMENT UPGRADE (planned, brainstormed w/ Codex in .codex_flair.txt) 👈 NEXT WORK
User feedback after first video: looks+sounds great, but (a) script is a bit boring, wants
Veritasium/Vsauce energy - informative but personal/dramatic/digestible; (b) still feels like a
SLIDESHOW, wants real animation flair.

Root causes: one template per section animates in then sits static -> hard cut (slideshow); the
per-sentence TTS cues are generated but NOT passed into Remotion; script has no narrative spine.

### Locked decisions
- **Animation scope: ALL-IN / experimental.** Word/sentence-sync visuals (pass cues into Remotion,
  each section = mini-timeline), virtual camera + parallax, flowing transitions (@remotion/transitions
  TransitionSeries) + carry-over motif, never-freeze idle motion, NEW cinematic scene families
  (zoom-to-scale, misconception-flip, evidence-board, cause-effect, mechanism-cutaway), recurring
  animated guide motif. All FREE/procedural, headless-CI safe.
- **Script: narrative-spine planning step** in research.py (central_question, viewer_assumption,
  false vs real explanation, stakes, reveal_ladder, running_analogy, payoff) -> script written from it.
  Curious-narrator + 2nd-person thought experiments. Tension per section. No fabricated anecdotes/bio.
- **Persona: named = "The Reframe"** - curious, intimate, slightly conspiratorial guide; blend of
  Vsauce cleverness + Veritasium tension + Kurzgesagt clarity; opens on a destabilizing question,
  plants an open loop, talks to "you", closes on a lingering reframe. Bake a persona bible into the
  script generator. (No fake biography - personality only.)
- **AI b-roll: build FREE procedural version first**, revisit paid AI clips only if still needed.
- **Voice delivery: match the persona** (tune gpt-4o-mini-tts instructions to the energy).

### USER'S IDEA (heard 2026-06-02) + Codex reconciliation -> v2.5 plan
User's idea: introduce a recurring CHARACTER as the spine (3blue1brown "Pi creature" model = rigged
procedural vector puppet posed by code, NOT a hand-drawn Kurzgesagt bird). Pick a per-video THEME, write
the script with the character in mind, then an AI "director" pass reads the FINAL script + sentence
timings and stages the character into scenes performing the narration (point at the stat, peek at a
diagram, shrink on a cosmic zoom, look puzzled at a misconception). Voice can BE the character or a
narrator beside it. ALSO fix the voice: too slow/monotone -> faster baseline, inquisitive on questions,
slow+weighty on key lines, brisk on connective tissue, tonal shift on questions.

Claude + Codex AGREED (see .codex_character.txt for full detail):
- **Character = occasional GUIDE at key beats (3-5 of ~10-16 sections), NOT full-time.** Full-time +
  limited motions = childish/cheap next to clean Cosmos Dark. Scarcity keeps it charming + de-risks build.
- **Tone: "abstract curious observer" / observatory-instrument-with-eyes. NOT animal/blob/kid mascot.**
  Body fill ~#15152A, accent-dimmed stroke, white eyes/BG pupils, simple brows/mouth, bezier-stroke arms,
  optional pointer + ONE tiny prop (magnifier/question_mark/tiny_planet/warning_dot/scale_ruler).
  Renders 12-18% screen height. Pure React/SVG, headless-CI safe, no images/assets.
- **Rig:** expressions {neutral,curious,surprised,skeptical,thinking,excited,concerned} as numeric pose
  params (eyeOpen,pupilX/Y,brow angles/raise,mouthCurve/Open,bodySquash). Actions {none,enter,exit,idle,
  point_at,peek,react,think,carry_object,scale_with_zoom,look_at}. Closed ScreenAnchor set (corners,
  headline,stat,diagram_core,panels,process_step_N). spring() for entrances/reactions, interpolate() for
  pos/scale/brows/pupils, gentle sin() idle. NO walk cycle in v1.
- **Director: deterministic rules FIRST, LLM director SECOND (Codex's key add).** Build a rule-based
  stager (template+delivery -> beats) to prove the rig, THEN add src/director.py (LLM, closed vocab,
  strict validation, falls back to rules/no-character if invalid). Director runs AFTER tts so it has real
  per-sentence timings. Closed vocab mirrored in Python (validate) + TS (types). Max 2-3 beats/section.
- **Theme = THIN:** running_metaphor + motif + small prop_set + accent_bias only. NO costumes, NO layout/
  typography/background changes. research.py emits running_metaphor; director maps to motif+props.
- **Voice:** script_generator emits per-sentence {text, delivery} (enum: neutral,curious,question,brisk,
  weighty,surprised,skeptical,ominous,warm_cta). tts_generator maps each to an instructions string +
  speed (0.25-4.0 supported; base pace 1.0 -> ~1.07-1.08; weighty/ominous below 1.0). Nearly free since we
  already render per-sentence. SHIPS FIRST, improves video even with character disabled.

### v2.5 ARCHITECTURE OF RECORD = .codex_octopus.txt (full detail). Key decisions below.
**Pipeline order:** research -> script (sentence objects + delivery) -> tts (per-sentence, returns
timings+delivery) -> **director.py (NEW, post-TTS so it has real timings)** -> remotion_renderer (writes
director plan + cues + theme into props.json) -> Remotion (deterministic).

**Octopus rig (remotion/src/character/):** pure SVG (not canvas). Each arm = ONE tapered path generated
from 5-7 Catmull-Rom control points -> cubic Bezier each frame. 6 arms MVP, 8 later. 2-bone IK (law of
cosines) for reach/point. CRITICAL INSIGHTS:
- **Stateless follow-through via ANALYTIC LAG** (Remotion frames are random-access -> NO mutable springs).
  Sample the interpolated target at t, t-lag, t-2*lag; arm tips use delayed sample, shoulders use current.
  Spring-like lag with zero frame history.
- **Separate "intent solve" (where arm goes: IK/idle) from "style offset" (undulation/lag/tremble).** Wave
  offset is applied perpendicular to the base curve, decays near shoulder + near tip when pointing, so
  undulation and pointing never fight. Apply follow-through to TARGET values before spline gen, not to the
  path after.
- Mantle: buoyancy bob (sin), mantle pulse (scaleX/Y inverse), body lean. Jet = engine locomotion mode
  (anticipation squash -> shoot -> settle overshoot), NOT a director path. Expression = normalized numeric
  weights blended over 8-16 frames (eyes+glow matter most; mouth subtle since silent). Chromatophore =
  20-40 spots max, CSS drop-shadow not heavy SVG filters. Per-frame recompute is cheap; only memoize
  static config. Perf risks = overdraw/backdropFilter/big shadows, NOT the spline math.

**Slider schema (OctopusIntentKeyframe):** time, preset?, position{x,y 0..1}, scale 0.08-0.28, depth
-400..300, gaze(anchor|xy), bodyLean -1..1, energy 0..1, expression{name:weight}, locomotionMode,
arms{a0..a7:{mode,target:anchorRef,reach,curl,priority}}. Clamps keep it on-screen / non-hyperextended.
Interp: position/lean/gaze = spring; depth/energy = ease; expression = linear 8-16f; arm target switches
discrete, reach/curl interpolate. Validate -> repair(clamp) -> preset -> deterministic -> no-char (per
section, never whole video).

**Animated content engine (remotion/src/scene/):** DELETE floating-bubbles Background (keep only a base
space gradient). Scene families (StatScene/ComparisonScene/DiagramScene/ProcessScene/TimelineScene...)
animate continuously, cue-driven (counts, strokeDashoffset traces, assemble, flip, focus). **SHARED
ANCHOR SYSTEM is the cohesion key:** octopus arm IK target id == content element anchor id (e.g.
"stat.main", "diagram.core", "diagram.node.0..5", "safe.lower_left"). content_beat.actor =
content|octopus|both; if both, element starts near arm tip then lands at anchor; if char off/fallback,
beat plays without arm dependency.

**Pseudo-3D camera (remotion/src/scene/SceneCamera):** SceneWorld(perspective:1200, preserve-3d) >
SceneCamera(inverse transform: translate3d/rotateX/rotateY/scale) > 5-7 DepthPlanes (z -300..+180; octopus
on z~60-140 so camera affects it; cameraLocked:true only for 0.5-1.5s reactions). Plan in 1920x1080 world
coords. Moves: hold/push_in/pull_back/dolly_l/r/tilt_reveal/orbit_slight/fly_through/snap_reframe/
match_cut_push. AVOID backdropFilter (current surface() uses it - reduce as cards go); animate only
transform/opacity/strokeDashoffset. @remotion/three deferred (not justified yet).

**Director (src/director.py):** ONE whole-episode LLM call (has all timings, keeps continuity, emits
sparse closed-vocab plan not prose). DIRECTOR_VOCAB + build_deterministic_plan() + call_llm_director() +
validate + repair + per-section fallback. Mirrored TS types. Full JSON schema in .codex_octopus.txt
(theme + episode.camera[] + sections[]{scene_family,transition,density,anchors[],content_beats[],
character{presence,cameraLocked,keyframes[]}}).

### FINALIZED PHASING (build in order; each: spec -> Codex impl -> Claude review + render-test stills)
- **2.5A Voice + cue props** (low effort, very high impact) -- DONE (Codex impl + Claude review).
  script_generator emits per-sentence {text,delivery} (9-enum, validated/normalized, concat==narration);
  tts_generator maps delivery -> instructions + speed; main.py passes sentences. Claude HARDENED the TTS
  call (_speech_create): gpt-4o-mini-tts may reject `speed` -> probe once, on rejection disable speed for
  the run and fall back to instructions-only pacing (so a speed 400 can't crash the pipeline). 3 files
  compile clean, zero non-ASCII. NOT yet run end-to-end (needs CI API keys + ffmpeg) -- verify on next run.
  NOTE: cues are already in props (captions) from before; sentence delivery does not yet drive visuals
  (that is 2.5B+).
- **2.5B Animated content + base camera** (HIGHEST for killing slideshow, med risk): remove bubbles; add
  SceneWorld/SceneCamera/CueTimeline; convert stat_reveal/diagram/process first; <=1 camera move/section.
- **2.5C Octopus MVP, deterministic** (high impact, high risk): 6 arms x 5 pts; drift/point/react/exit
  (NO jet yet); expressions neutral/curious/surprised(+skeptical/thinking); multi_build for diagram/
  process; enable on stat/diagram/process/comparison/title. Glow tied to energy, mantle breathing.
- **2.5D Director**: src/director.py whole-episode call, validate/repair/fallback, log decisions.
- **2.5E Jet + strong presence**: add jet/trails/chromatophore; raise presence across most sections;
  dense-scene step-aside rules. (Jet only AFTER drift/point read clean -- a bad jet looks cheaper than none.)
- **2.5F New scene families**: mechanism_cutaway, evidence_board, misconception_flip, cause_effect,
  zoom_to_scale on same anchors/beats/camera.

### SMALLEST VERTICAL SLICE (build right after 2.5A to prove the whole pipeline before breadth):
one stat_reveal section + one sentence delivery=surprised/weighty + cue-timed stat count/ring trace +
octopus enters lower-left, points at stat.main, reacts + one push_in camera move + a deterministic
fallback plan. Render-test stills at 0/25/50/75/95%. MEASURE CI RENDER TIME here (sets the real per-video
estimate; current ~40-70min, v2.5 est ~65-120min -> will bump CI timeout 90->~150 + keep fps/concurrency/
segment-count optimization knobs ready).

---

## >>> RESUME HERE (fresh terminal, 2026-06-03 session 4) <<<
We are mid-iteration on the COSMIC OCTOPUS design+motion in the standalone Remotion "Slice" test comp.
Latest build = **iter7** (Codex impl via spec specs/phase2_5_octopus_iter7.md; tsc clean; Claude rendered).
iter7 made BIG progress: (a) SEAMLESS one-mass body+arm join via an SVG gooey/metaball filter (octoGoo,
GOO_BLUR=7 const in CosmicOctopus.tsx) - owner's #1 ask, SOLVED; (b) 6 legs (was 8); (c) reference-style
SPLAYED+CURLED rest pose (SUPERSEDES the old hang-down decision - owner changed it after re-sending the
orange-octopus reference); (d) smooth monotonic arm taper (mid-lump gone); (e) less-robotic reach tuning.
Stills iter7_frame_0/60/120/180/228 + iter7_slice.mp4 in remotion/slice_stills/.

**iter7 owner verdict (2026-06-03):** gooey filter is GOOD - KEEP it (reaching arm acceptable after all, the
"eaten arm" worry was overstated). Remaining issues -> iter8/iter9: (a) tentacle CURVED TIP glitches/mirrors
side-to-side (real bug); (b) movement still robotic; (c) PROPORTIONS off - head too big vs tentacles.

**RESEARCH DONE:** owner supplied a deep-research report (copied to repo .octopus_research.txt; orig
D:\Downloads\Deep Research Report on an Octopus Animation System...docx). Claude read it + dispatched Codex
read-only to cross-check vs our code -> Codex analysis in .codex_iter8_discussion.txt. Key findings:
- Tip glitch root cause = tip cap tangent OVERFITS the final ~14% of the last IK segment (tipCapPath uses
  only tip-tipPrepB); terminal direction is unstable -> cap normal flips. Fix = smoothed multi-segment
  terminal tangent + epsilon guard (iter8 A).
- Report's #1 realism rec = CURVATURE-SPACE solver (preserved curl + traveling Gaussian bend that moves
  outward + small wave + LIMITED STRETCH/arm elongation), replacing per-segment aim-at-target. Codex says
  adopt as HYBRID not full replacement (pure curvature integrator won't guarantee tip lands on stat.main;
  pointing accuracy matters) -> iter9.
- Report rec polygon/SDF silhouette UNION (martinez/polygon-clipping) as cleaner than gooey. Owner wants to
  TRY it but KEEP gooey reversible -> iter8 C as a toggle.
- Arc-length taper: only matters once arms STRETCH (fixed link length now => index==arclength). Pair it with
  arm-extension in iter9 (owner correctly connected these).
- DEFER (3D/photoreal-only, not our path): Blender/Eevee/Cycles, DeepLabCut reference-fitting, FEM/soft-body.

**SPLIT AGREED with owner:**
- **iter8 (STRUCTURAL) - DONE + RENDERED + owner-reviewed (Codex task bkn9lwkqd, spec ...iter8.md):**
  (A) tip tangent smoothed (3-seg); (B) proportions MANTLE_SCALE=0.88, ROOT_TUCK=0.9, armConfigs.length +18%,
  idle +15%, base radius 0.120; (C) polygon-union merge in NEW silhouette.ts (polygon-clipping dep), behind
  MERGE_MODE:'polygon'|'goo' toggle; rigTypes SolvedArm carries baseAngle.
  - OWNER VERDICT "not there yet": PROPORTIONS = GOOD (smaller head, longer legs, matches reference). But
    (1) POLYGON mode facets the rounded tips -> "weirdly angled" rest tips (goo mode rest tips are SMOOTH);
    (2) the tip FLIP during the reach PERSISTS (iter8 3-seg tangent reduced but did NOT kill it).
  - Claude diagnosis (validated by zoomed consecutive-frame renders, Pillow now installed for crop/zoom):
    angled rest tips = polygon faceting (FIXED by defaulting to goo). The reach FLIP is FUNDAMENTAL: the
    aim-at-target chain makes a JITTERY centerline, worst at the moving reaching tip, so the rounded cap
    reflects/flips frame-to-frame. SAME root cause as "robotic motion." Band-aid caps can't fully fix it.
  - Claude SET DEFAULT MERGE_MODE="goo" (CosmicOctopus.tsx) - fixes the angled-rest-tip facet. polygon kept
    as fallback (its tip faceting would need more cap samples/smoothing if ever revived).
- **iter9 (MOTION/REALISM) - DONE + RENDERED + owner-reviewed (Codex bv6vif20o + Claude taper tune = iter9b):**
  curvature-space solver landed (resolveCurvatureChain in Chain.ts replaces the aim-at-target chain). FIXED
  the tip flip (smooth stable centerline - validated by consecutive-frame montages). Claude tuned the taper
  back up (armOutline taperedRadii fatter profile + base radius 0.12->0.132) after the solver thinned arms.
  - OWNER VERDICT (iter9b): NOT good - "possibly worse than first iterations", raised PIVOT. Three concrete
    failures: (a) reaching arm HINGES - inner half frozen, outer half swings/stretches to target (CAUSE =
    the endpoint-correction block at end of resolveCurvatureChain, Chain.ts ~108-127, shifts only u>0.5 pts);
    (b) resting legs CROSS over each other in pairs, not a clean natural fan (CAUSE = armConfigs idle config);
    (c) a resting leg GLITCHES/pops (discontinuity, likely discrete mode/target flip at progress>0.5).
  - Owner floated DeepLabCut. Claude's honest take (agreed): DeepLabCut is OFFLINE calibration (track real
    octopus video -> extract motion numbers -> tune the procedural solver), NOT a runtime engine; needs
    footage+compute+days; STILL feeds our solver so it can't fix structural kinks. = phase-2 polish, NOT now.
- **iter10 (CALM-MOTION RESET) - IN PROGRESS (Codex bltiiuqs1, spec specs/phase2_5_octopus_iter10.md):**
  OWNER DIRECTION (middle of "simplify" and "keep fixing"): DROP precise pointing (it's what breaks the
  motion); prioritize GOOD organic CALM realistic-looking soft-body motion FIRST; pointing can be beefed up
  LATER. Mostly SUBTRACTIVE: (1) DELETE endpoint correction (the hinge); (2) arms GESTURE not point - bendGain
  2.65->~0.7, widen bendWidth, mid bendCenter, whole-arm single heading (no per-segment re-aim); (3) calm-but-
  ALIVE idle = small baseline undulation even at activity 0 (waveAmp floor ~0.035), low freq, keep tip-fade so
  flip stays fixed; (4) clean SYMMETRIC rest fan (rework armConfigs idle, no crossing, consistent curlDir);
  (5) fix resting-leg glitch (continuity audit); (6) Slice.tsx keyframes -> calm gesture (lean+gaze+loose arm
  raise reach 0.4-0.6, no precise target). KEEP all structural wins. Claude judges motion by render.
  NOTE: if iter10 motion still isn't good, owner may PIVOT the character strategy (de-scope/replace octopus).

- **iter9 (superseded notes) (Codex task bv6vif20o, spec specs/phase2_5_octopus_iter9.md):**
  owner chose to bring the CURVATURE-SPACE solver forward NOW (fixes flip + robotic motion at the source).
  Replace resolveAngleConstrainedChain with a curvature-over-arclength integrator (smooth stable centerline):
  preserved curl + traveling Gaussian bend (bendCenter moves outward on reach) + tip-faded wave + limited
  stretch (maxStretch ~0.10-0.16*activity). Keep stateless lag (per-sample delayed target), anchor targeting,
  activity gating (idle still), goo/polygon merge, iter8 proportions. ADD activity-scaled ENDPOINT CORRECTION
  over the outer arm so the tip still lands on stat.main (pointing must read). Move taperedRadii to NORMALIZED
  ARC LENGTH (arms stretch now). Tip cap back to short 2-seg baseline (centerline is smooth now) - flip must
  be GONE. Claude validates by zoomed consecutive reach-frame renders (PRIMARY pass/fail = no tip flip).
NOTE: `polygon-clipping` dep installed in remotion/; Pillow installed for py -3 crop/zoom of renders.
HELPER: to zoom a render -> `py -3` + PIL Image.open().crop().resize(); montage consecutive frames to see flip.

To see current state: `cd remotion` then `npx remotion still src/index.ts Slice slice_stills/check.png
--frame=120` (or watch slice_stills/iter7_slice.mp4). Read "ITERATION HISTORY" + "RESOLVED with user"
below before changing anything (owner decisions are locked - do NOT relitigate). Workflow + Codex-dispatch
gotcha are in "LOCAL DEV WORKFLOW" below.

## CURRENT STATE - octopus design iteration (2026-06-03, session 2)
Phase 2.5A (voice) = DONE (see above). Then built the VERTICAL SLICE (Codex) = standalone Remotion
composition "Slice" (registered in Root.tsx, 1920x1080, 30fps, 240 frames) with HARDCODED plan, no audio/
API. Files created: remotion/src/scene/ (anchors.ts, SceneWorld.tsx, SceneCamera.tsx, DepthPlane.tsx,
CueTimeline.ts, Slice.tsx), scene/families/StatScene.tsx, remotion/src/character/ (rigTypes.ts,
splines.ts, ik.ts, motion.ts, expressions.ts, solveRig.ts, CosmicOctopus.tsx, CharacterLayer.tsx).
Slice = one stat scene (counts 0->12,840, ring traces) + push-in camera + octopus enter/point/react/settle.

### TECHNIQUE WE LOCKED (after research - sources in specs/phase2_5_octopus_overhaul_PLAN.md)
Octopus is built with the established 2D procedural-creature method, NOT hand-rolled ribbons:
- Each ARM = a CHAIN of joints, fixed link length, with a CLAMPED bend angle between links
  (angleConstraint) -> smooth curves, NO folding over itself. (argonautcode/animal-proc-anim; A. Zucconi.)
- Each arm DRAWN as a filled OUTLINE around the chain spine: perpendicular offsets at each joint by a
  radius profile, gentle/even taper, ROUNDED BLUNT TIP (never a true point/triangle).
- STATELESS per-frame resolve (Remotion renders frames in random order -> NO previous-frame state): resolve
  each chain fresh per frame from its root toward a TIME-LAGGED target (analytic lag) for follow-through.
- SEAMLESS body: small rounded TEARDROP mantle whose bottom widens into a CROWN/WEB that wraps the arm
  bases; arms emerge FROM the web (roots DOWN IN the web, not above it); body+web+arms share ONE continuous
  purple->teal gradient, no internal stroke seams, edge = soft drop-shadow. ALL arms drawn BEHIND mantle.

### OWNER DESIGN FEEDBACK (locked - do NOT relitigate these)
- Reference image (orange cartoon octopus on Desktop) = BODY SHAPE ONLY (round body tapering into curling
  legs). Take NOTHING else from it (not eyes, color, suckers, outline).
- KEEP the detailed eyes (sclera+pupils+highlight+brows) - NOT black dots. Eyebrows must be clean/natural.
- KEEP a subtle mouth (tuned, not childish) - owner wants it if it looks good.
- Body must be SMALL (not fill screen) and SEAMLESS with arms (one mass, not circle+lines).
- Tentacles: beefy (not wiry), blunt rounded tips (no point), smooth (no folding), BEHIND the body.
- Cosmos Dark colors, soft accent glow.

### ITERATION HISTORY (stills in remotion/slice_stills/)
- frame_* = v1 (cute bug, debug text "C_UNT" burned in - BAD). r2_* = round body+detailed eyes kept, but
  thin-noodle arms. r3_* = thick filled arms but triangle-tapered + folded. r4_* = OVERHAUL (chains +
  outline + smaller teardrop + behind-body + label fixed) = best so far, reads as an octopus.
- iter5 (Codex task blo26yay1, DONE exit0; Codex couldn't render in-sandbox = esbuild spawn EPERM, normal):
  eyebrows redone as clamped quadratic strokes (clean/symmetric); tentacles beefed (base radius 0.105->0.142,
  tip min 0.018->0.04 ~38% of mid = rounded blunt arc cap, no point); arm roots lowered INTO web + skirt
  overlay wraps bases (seamless); rest eyes alert (min openness 0.85); gaze + arm-target interpolation
  smoothed; point-reach assist eased (clamp (reach-0.54)/0.32) so it doesn't pop at beat boundaries. Files:
  CosmicOctopus.tsx, solveRig.ts, armOutline.ts. tsc clean.
  - CLAUDE RENDERED + VALIDATED (this session): stills iter5_frame_0/60/120/180/228.png + full MP4
    slice_stills/iter5_slice.mp4 (240f/8s, 2.5MB). MOTION CHECK via ffmpeg-extracted consecutive-frame
    clusters (motion_check/a_* steady undulation f95-104, b_* beat transition f104-115): counter eases to a
    stop, ring fills smooth, label fades in smooth, octopus arms undulate + body drifts in small continuous
    deltas, no jitter/pop/teleport. MOTION CONFIRMED SMOOTH. (NOTE: Remotion's bundled ffmpeg has
    --disable-filters, so select/trim filters fail; extract frames via `-ss <sec> -frames:v N`, no -vf.)
  - REMAINING NITS (minor, owner to decide if worth another pass): lower web/arm mass slightly blobby on a
    couple frames (f120/f228) - arm separation in the skirt could read crisper. Otherwise approved-quality.
  - iter5 owner verdict: NOT approved. Feedback -> iter6.
- iter6 (spec specs/phase2_5_octopus_iter6.md; Codex task b6sylzkv4): (1) REMOVE skirt/web overlay (arms
  attach at body base, skirt unnecessary); (2) REST = arms hang DOWN + near-MOTIONLESS (per-arm
  activity=smoothstep(reach) gates undulation; idle arms static, only reach>0 arms raise/move); (3) FIX
  frame glitch/skip = make angleConstraint/curl/pointAssist/reachForChain depend ONLY on continuous reach,
  never on the discrete mode flip at progress>0.5 (that one-frame jump was the skip); analytic lag must
  collapse to constant for static idle target; (4) slimmer base radius ~0.108; (5) truly rounded tangential
  tip cap (iter5 tip still read as sharp corner). Owner words: skirt becoming unnecessary, tentacles
  glitching/skipping + shouldn't move at rest (hang down, only working ones raise), base too beefy, tips sharp.

  - iter6 RENDERED + VALIDATED (Claude): skirt paths removed by Codex; idle arms confirmed STILL (rest
    cluster frames identical) and NO glitch during reach (smooth) - the discrete-mode-flip fix worked.
    Working arm raises while others hang. BUT base-slim to 0.108 overshot -> arms too thin/wispy.
  - iter6b/c hotfixes (Claude, geometry-only, motion unaffected): (b) arm heft restored - taperedRadii base
    0.108->0.124 AND midRadius ratio 0.78->0.9 (fuller mid kills the wispy look without a bulbous base);
    (c) "MOON" REMOVED - the lobed webbing remnant was baked into mantlePath bottom (fanned to +/-91,102);
    replaced lower mantle with a clean rounded teardrop base "C 26 72 -26 72 -42 61". Stills iter6c_frame_*,
    mp4 iter6c_slice.mp4. tsc clean.
  - STATUS: octopus now = clean rounded body, no skirt/moon, arms hang down + still at rest, working arm
    raises, no glitch, beefier arms, rounded tips. AWAITING OWNER VERDICT on iter6c_slice.mp4.

- iter7 (spec specs/phase2_5_octopus_iter7.md; Codex task bn1ltlftr exit0; summary .codex_iter7_impl.txt):
  (1) SEAMLESS join via octoGoo SVG filter wrapping ONLY arm+mantle fills (eyes/brows/mouth/glow/spots
  render on top OUTSIDE the filter); GOO_BLUR=7 const. (2) armConfigs 8->6, roots moved UP into mantle
  (y 0.44-0.6), idle targets splayed OUTWARD+curl (x up to +/-1.12). (3) armOutline taperedRadii rewritten
  monotonic smooth (eased = 1 - t^1.45, tipFloor = max(tip, base*0.30)) - no mid kink. (4) Chain.ts: curl
  falloff on reach 0.72->0.40, loosenForReach 0.42->0.28, S-shape reach bias, idle activity-gating kept.
  (5) Slice.tsx a6->a5 remap. tsc clean. Files: CosmicOctopus.tsx, solveRig.ts, armOutline.ts, Chain.ts,
  Slice.tsx.
  - CLAUDE RENDERED + ASSESSED: WINS = seamless one-mass body (no visible join), rest pose matches the
    reference splayed-curl (frame 0), 6 legs, smooth taper. ISSUE = reaching arm gets EATEN by the goo
    threshold (thin extended strand falls below merge alpha -> point at stat doesn't read); slightly melty
    at blur 7. AWAITING owner verdict + owner's ChatGPT research (owner chose WAIT, do not start iter8 yet).

### >>> NEXT STEP (do this) <<<
1. WAIT for owner to paste ChatGPT animation research (seamless silhouette without merge-filter eating
   extended limbs). Owner explicitly chose to wait before iter8.
2. THEN plan iter8 from research: fix the reach reading (lower GOO_BLUR / beef+extend reach arm / merge only
   arm base) WITHOUT losing the seamless body. Then if octopus approved: finish slice (real cue timeline /
   director hooks), measure CI render time, build remaining scene families (Phase 2.5B+).

### LOCAL DEV WORKFLOW (this Windows box)
- Repo: E:\youtube-bot. Shell cwd defaults to C:\ -> use ABSOLUTE paths or Set-Location 'E:\youtube-bot...'.
- Python: use `py -3` (NOT `python`/`python3` - those are MS Store stubs). ffmpeg/openai NOT installed
  locally -> full pipeline can't run locally; only Remotion renders + tsc + ast-compile checks.
- Remotion: `cd remotion; $env:NODE_OPTIONS='--use-system-ca'; npx tsc --noEmit` then
  `npx remotion still src/index.ts Slice slice_stills/NAME.png --frame=N` (stills, no ffmpeg) /
  `npx remotion render src/index.ts Slice slice_stills/slice.mp4` (video). node 24, remotion 4.0.471.
- Codex: `codex exec --skip-git-repo-check -C /e/youtube-bot -s workspace-write -o OUT.txt "..."` (run in
  background). Specs live in specs/. Sandbox must stay `unelevated`. ASCII-only in Python (mojibake risk).
  GOTCHA (hit 2026-06-03): dispatch codex DIRECTLY via the Bash tool's run_in_background:true - do NOT wrap
  it in `nohup codex ... &`. Double-backgrounding detaches codex's stdin and it exits early doing NOTHING
  (exit 0, no edits, no -o file), and the harness only tracks the wrapper. Run codex exec as the foreground
  command of a backgrounded Bash call so the harness tracks codex itself and -o OUT.txt gets written.
  Codex CANNOT render (esbuild "spawn EPERM" in its sandbox is EXPECTED) - Claude does all renders.
- Validate MOTION from the mp4: Remotion's bundled ffmpeg has --disable-filters, so `-vf select/trim`
  FAIL. Extract consecutive frames by SEEK instead: `npx remotion ffmpeg -ss <seconds> -i in.mp4
  -frames:v N out_%03d.png -y` (frame N = N/30 s). Compare a rest-window cluster (should be identical =
  still) and a motion cluster (should change smoothly = no glitch).
- NOT committed/pushed yet (all v2.5 work is uncommitted working changes on disk). Owner decides when.

### RESOLVED with user (2026-06-02) -> ESCALATED to "all-in"
- **Voice:** narrator + SILENT visual character (character does not speak). CONFIRMED.
- **Mascot = COSMIC OCTOPUS** (bioluminescent little cephalopod, deep purple/teal + glowing accent
  spots, big intelligent eyes, drifts through space). Name TBD. Chosen for: alien-intelligent science
  vibe, max expressiveness, and the multi-arm SUPERPOWER (each tentacle points/grabs/builds a different
  diagram element at once). Reads clearly as a living creature (user requirement).
- **Scope ESCALATED: go all-in, not occasional.** User: the character is critical because the AI voice
  is mediocre, so visuals must carry personality. More presence IF the rig holds up; octopus drifts so it
  suits frequent presence. Steps aside when a scene is too dense so it never covers content.
- **Rig = PARAMETRIC "slider" model (user's idea, adopted as foundation).** AI sets sparse high-level
  INTENT keyframes (position xy, scale, gaze xy, per-arm reach targets, body_lean, energy/intensity,
  expression-blend weights, locomotion mode). Engine generates natural motion: procedural tentacle
  splines (5-7 pts) + traveling-wave undulation + 2-bone IK reach + spring follow-through + buoyancy
  bob + mantle-pulse breathing + jet-dart locomotion + chromatophore glow/color-as-emotion. AI NEVER
  hand-poses geometry; named presets (point/react/jet/idle) exist as safe fallback. Tentacle soft-body
  is the main engineering cost but is a known achievable technique.
- **CRITICAL: kill the "slideshow" two ways.** (1) The CONTENT must actually animate when the octopus is
  off-screen - figures/graphs/lines/planes/diagrams build, trace on, transform, NOT static cards over a
  floating-bubbles bg. DELETE the floating-bubbles Background. (2) Octopus "superpower": its arms can
  detach/place elements so character + content are one world.
- **Pseudo-3D camera (user wants it).** Approach: CSS 3D transforms (perspective/rotateX-Y/translateZ) +
  parallax depth planes + a virtual camera that pushes in / dollies / fly-throughs between scenes. Free,
  CI-safe. Real 3D (@remotion/three) deferred as a later upgrade (perf/CI risk).
- Voice Phase A is independent - can ship in parallel with mascot R&D.

### NEXT: Codex deep-dive (.codex_octopus.txt) on full architecture, THEN spec phase-by-phase.
Build order per phase: spec -> Codex implements -> Claude reviews + render-tests (stills), as phases 1-6.
