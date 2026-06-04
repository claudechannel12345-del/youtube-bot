# Phase 2.5 VERTICAL SLICE - prove the whole pipeline before breadth

Architecture of record: .codex_octopus.txt (read it for the rig technique detail). This slice builds the
SMALLEST end-to-end proof: one animated stat scene + the cosmic octopus pointing/reacting + one camera
move, driven by a HARDCODED deterministic plan (NO LLM director yet, NO audio dependency). Goal is a
clean still-frame render we can eyeball locally.

ASCII only in any Python. TypeScript/TSX may use normal characters. No new npm deps (pure SVG + CSS 3D).
Match all `remotion`/`@remotion/*` versions already in package.json. Do NOT run npm/pip installs.

## Why a standalone test composition
Add a Remotion composition "Slice" (1920x1080, 30fps, ~8s) registered in Root.tsx with HARDCODED inline
props (no props.json, no audio, no Python). This lets us render PNG stills via `npx remotion still`
(no ffmpeg needed) to verify the octopus + scene + camera look good in isolation. The real Episode wiring
comes in Phase B/C; this slice is the throwaway-ish proving ground (keep it; reused as a visual regression).

## New files (remotion/src/)
scene/
  anchors.ts        - Anchor type + a canonical resolver (normalized 0..1 world coords -> px in 1920x1080).
  SceneWorld.tsx    - outer container: perspective 1200, overflow hidden, transformStyle preserve-3d.
  SceneCamera.tsx   - inverse camera transform (translate3d/rotateX/rotateY/scale) from a CameraState; one
                      move type for the slice: push_in (interpolate zoom 1.0 -> ~1.08 + slight z), eased.
  DepthPlane.tsx    - wraps children at a given translateZ.
  CueTimeline.ts    - tiny helper: given beats [{time,duration}] + fps + frame, return active beat +
                      local progress (0..1). Used by the scene + character.
scene/families/
  StatScene.tsx     - the one animated content family for the slice. Renders a big stat that COUNTS UP on
                      a cue beat (interpolate number), a ring that traces via strokeDashoffset, a label
                      that snaps on after the count. Exposes anchor "stat.main" at its number center and
                      "headline" at the title. Continuous subtle motion (no frozen frame). Cosmos Dark
                      theme.ts colors. NO floating-bubble background - just the base space gradient.
character/
  rigTypes.ts       - OctopusIntentKeyframe + ArmIntent + ExpressionName + LocomotionMode + AnchorRef
                      (mirror the schema in .codex_octopus.txt section 2). Plus ResolvedPose.
  splines.ts        - Catmull-Rom (5-7 pts) -> cubic Bezier path string.
  ik.ts             - 2-bone IK (law of cosines): shoulder + target + upper/lower lengths -> elbow + tip,
                      bend direction from bendBias/side. Clamp target to maxReach.
  motion.ts         - analytic lag sampler (sample interpolated target at t, t-lag, t-2lag; tips delayed,
                      shoulders current) + perpendicular undulation (sin along segmentT, decays at
                      shoulder and at tip when reaching) + buoyancy bob + mantle pulse. STATELESS (frame in,
                      values out) - NO mutable springs (Remotion frames are random-access).
  expressions.ts    - expression name -> numeric pose channels (eyeOpen,pupilX/Y,browRaise,browAngle,
                      mouthCurve,mantleSquash,glowIntensity); blend by weights, normalized.
  solveRig.ts       - given keyframes + frame + fps + resolved anchors: interpolate intent (position/scale/
                      gaze/lean/energy spring-ish via Remotion spring or eased interpolate; arms reach/curl
                      interpolate; expression linear over ~12f), run IK per arm, apply undulation+lag,
                      output a ResolvedPose (body transform, per-arm bezier path, eye/brow/mouth/glow).
  CosmicOctopus.tsx - pure SVG render of a ResolvedPose: mantle (tapered ellipse/path, deep purple/teal),
                      6 arms (tapered paths + a translucent glow-stroke duplicate behind), 2 eyes (white
                      sclera, BG pupils, tracks gaze), simple brows, subtle mouth, ~20-30 glowing spots
                      (chromatophore) via CSS drop-shadow (NOT heavy SVG filters). Accent from current
                      section. ~15% of 1080 height by default.
  CharacterLayer.tsx- places CosmicOctopus on its depth plane, runs solveRig per frame from the plan's
                      character keyframes + resolved anchors.

## The hardcoded slice plan (inline in the Slice composition, mirrors director schema shape)
- One section, scene_family "stat", duration ~8s, fps 30.
- anchors: headline (x .5 y .22), stat.main (x .5 y .5), safe.lower_left (x .16 y .78).
- content_beats: count stat 0 -> target over t=1.5..3.5s (kind "count"); ring trace 1.5..3.5; label snap
  at 3.6 (kind "label").
- camera: push_in focus stat.main, 0..8s, ease.
- character keyframes (octopus):
  - t=0.4: enter from safe.lower_left area (position offscreen-lower-left -> safe.lower_left), drift,
    expression curious, energy .4, gaze headline.
  - t=2.0: point one arm (a0) at stat.main (reach .9, curl .1), expression curious->surprised building,
    bodyLean +.3, energy .6, gaze stat.main.
  - t=3.7: react (expression surprised .8), small recoil/scale pop, two arms splay, energy .8.
  - t=6.5: settle back to drift/idle, expression neutral->curious, gaze headline.
  No jet in the slice (drift/point/react only).

## Deterministic only
No src/director.py in this slice. The plan above is hardcoded TS inside the Slice composition (or a
slice_plan.ts). This proves the RENDER half. The Python director that GENERATES such plans is Phase D.

## Acceptance (Claude will run locally)
- `cd remotion && npx tsc --noEmit` clean.
- Render stills at multiple frames (no ffmpeg needed):
  `npx remotion still src/index.ts Slice out_00.png --frame=0 --props=...` (or hardcoded, no props) and
  at frames ~ 0%, 25%, 50%, 75%, 95% of the 8s (frames 0, 60, 120, 180, 228 at 30fps).
  Use NODE_OPTIONS=--use-system-ca locally if TLS errors (local only; gated off in CI).
- Visual check: octopus reads as an octopus (mantle + 6 flowing arms), eyes track, one arm clearly points
  at the stat number, expression shifts curious->surprised, stat counts + ring traces, camera pushes in,
  NO floating bubbles, nothing occludes the stat readout.

## Notes for the implementer
- Per-frame recompute is fine; memoize only static config (arm constants, anchor table).
- Avoid backdropFilter and giant box-shadows (CI overdraw risk).
- Keep arm segment math cheap. 6 arms x ~6 pts.
- Everything STATELESS and deterministic (frame -> pixels), so stills at any frame are correct.
