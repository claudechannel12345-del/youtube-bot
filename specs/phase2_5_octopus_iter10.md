# Octopus iteration 10 - CALM ORGANIC MOTION (drop precise pointing, fix hinge + rest-crossing + glitch)

Builds on iter9b. STRATEGIC RESET on motion, agreed with owner. The octopus motion regressed: the reaching
arm HINGES (half the arm stays frozen, the outer half swings/stretches to the target), the resting legs CROSS
over each other instead of a clean natural fan, and one resting leg GLITCHES/pops. Owner decision: STOP trying
to make an arm precisely point at / touch a screen target. Instead prioritize GOOD, ORGANIC, CALM,
REALISTIC-LOOKING motion first ("focus on the movement and the look of the movement, not pointing exactly to
the thing"). Pointing can be gently re-added LATER once the base motion looks great.

This pass is mostly SUBTRACTIVE - remove the machinery that fights the organic primitives. Do NOT add new
complexity. Keep ALL the structural wins from iter7-9b: seamless body (goo default), proportions
(MANTLE_SCALE), the merge toggle, expressions/eyes, arc-length taper + beefy blunt arms, the smooth
curvature centerline (the tip flip is fixed - keep it fixed).

Keep `npx tsc --noEmit` clean. ASCII only (zero non-ASCII bytes). Codex CANNOT render (esbuild spawn EPERM is
EXPECTED) - implement + tsc-check only; Claude renders + judges motion + tunes constants. No new deps.

Primary files: remotion/src/character/Chain.ts (resolveCurvatureChain), solveRig.ts (armConfigs idle + how
arms are driven), remotion/src/scene/Slice.tsx (convert keyframes from precise-point to gesture). Possibly
motion.ts.

---

## 1. REMOVE the endpoint correction (this is the hinge - delete it)

In Chain.ts `resolveCurvatureChain`, DELETE the entire endpoint-correction block (currently lines ~108-127:
computing `error = target - tip` and shifting points by `smoothstep((u-0.5)/0.5) * activity * 0.92`). That
block translates only the OUTER half of the arm toward the target, which freezes the inner half and hinges
the outer half = the exact bug owner reported. The function should simply RETURN the integrated curvature
centerline `points` with no post-hoc endpoint pull.

## 2. Arms no longer precisely point - they GESTURE (whole-arm, gentle, directional)

We keep a gentle directional influence so an "active" arm can sweep/raise toward a general direction, but it
must move the WHOLE arm as one graceful curve - never hinge, never stretch to land a tip on a point.

In resolveCurvatureChain:
- Drastically REDUCE the target-aim strength: `bendGain` max ~0.7 (was 2.65). The arm should lean toward the
  target's general direction, not solve to it.
- WIDEN the bend so the whole arm participates: `bendWidth` ~0.45-0.6 (was ~0.15-0.2) and `bendCenter`
  ~0.45-0.55 (mid-arm), roughly constant (do NOT march it all the way out to 0.82 on activity - that plus
  high gain is what whipped the tip). A wide, mid-centered, low-gain bend = the whole arm arcs gently.
- The aim should use the arm's OVERALL direction to a soft directional target, not a per-segment re-aim that
  can swing. Compute `aimError` once from the arm root (or a smoothed heading), not freshly at every segment
  from the moving delayed target (per-segment re-aim contributes to the unnatural snap). A single gentle
  whole-arm bend toward the gesture direction is the goal.
- Keep `activity` (smoothstep of reach) only as the GESTURE strength (how much an arm raises/sweeps). At
  activity 0 the arm is pure idle curl + undulation (section 4). Keep it smooth (no discrete flips).

## 3. Calm, ALIVE idle - gentle continuous undulation (not frozen, not jittery)

Owner wants realistic-looking motion, so idle arms should NOT be frozen - they should sway softly like an
octopus hanging in water. But it must be CALM and SMOOTH (low amplitude, low frequency), never the old
mechanical wriggle.
- Give every arm a small BASELINE traveling undulation even at activity 0: e.g. waveAmp has a floor like
  `0.035 + 0.06*activity` (instead of being fully gated to 0 by activity). Keep frequency LOW (slow wave),
  phase offset per arm by armIndex so they don't move in lockstep.
- Keep the tip-wave fade (tip stays calm so the cap is stable - do NOT undo the flip fix) and root fade.
- The body already has buoyancy bob + mantle pulse - keep gentle. Arms should drift WITH the body.
- Net target: a slowly breathing, softly undulating, underwater-floating creature. Smooth, continuous,
  organic. Render-judge: motion should read as flowing soft-body, no pops, no stiffness, no frantic wiggle.

## 4. Clean, symmetric, natural REST fan (like the reference - no crossing)

The resting legs currently cross over each other in pairs and look unnatural. Rework `armConfigs` in
solveRig.ts so the 6 legs sit in a SYMMETRIC, natural, gently-curling fan like the owner's reference octopus:
- 3 per side, mirrored left/right. Outer legs sweep OUT and curl (tips curling), middle legs angle out
  moderately, inner legs shorter and more downward. NO two legs crossing/overlapping at rest.
- Re-tune each arm's idle target (x,y), baseAngle, and curlDir so the fan is even and reads like the
  reference resting pose (round body sitting in a tidy splayed crown of curled legs).
- curlDir should make legs curl in a natural, consistent way (e.g. outward), not random alternation that
  causes crossings. Verify the left side mirrors the right.
- They should be calm/alive per section 3 (gentle sway), holding this clean fan shape.

## 5. Find and FIX the resting-leg glitch/pop

One resting leg pops/glitches even when it should be calm. Audit for DISCONTINUITIES (anything that jumps
between frames):
- In solveRig `interpolateIntent` / `armTargetAt`, discrete switches at `progress > 0.5` (mode, preset,
  locomotionMode, arm target) cause a one-frame jump. Make any value that affects geometry CONTINUOUS across
  keyframe boundaries (interpolate, don't step). A discrete arm `target` switch mid-blend is a prime suspect.
- Check the `targetAt(framesAgo)` delayed sampling near t=0 / clamped times for a discontinuity.
- Ensure no NaN/Infinity path (e.g. atan2 of a zero-length vector, division by ~0) that would snap a leg.
- The goal: every resting leg moves only via the smooth undulation in section 3 - zero pops.

## 6. Slice.tsx - convert keyframes from precise-point to GESTURE

The Slice demo keyframes currently target a0 at `stat.main` with reach 1 (precise point). Convert to the new
calmer style so the render showcases good motion, NOT pointing:
- Keep the body beats (drift in, gentle lean toward the stat's side, gaze shifts to the stat, a calm
  "notice/react" with expression curious->surprised). Keep timings.
- Replace the precise arm `target: stat.main, reach: 1` with a soft GESTURE: a gentle raise/sweep of one or
  two arms in the stat's general direction (modest reach ~0.4-0.6, NO precise target landing), while the
  rest of the arms keep the calm idle fan. The octopus should look like it CALMLY GESTURES toward / notices
  the stat via lean + gaze + a loose arm, not a rigid point.
- Remove any keyframe that demands a tip land on an anchor.

---

## Acceptance (Claude judges by render, MERGE_MODE="goo")
- `npx tsc --noEmit` clean.
- Render mp4 + stills 0/40/80/120/180/228 + consecutive frames for smoothness checks.
- NO hinge: arms move as whole graceful curves, never half-frozen/half-stretched.
- Rest legs sit in a clean symmetric natural fan (no crossing), like the reference.
- Idle is CALM but ALIVE: gentle continuous soft-body undulation + drift, smooth, no pops, no stiffness, no
  frantic wiggle.
- NO glitch/pop on any resting leg across the whole clip.
- Tip flip stays fixed; arms stay beefy with blunt tips; body/proportions/merge unchanged.
- The gesture toward the stat reads as a calm notice (lean+gaze+loose arm), not a precise point.
- ASCII only; no new deps.

Write a concise summary (files changed, what was removed, new motion constants: bendGain/bendWidth/bendCenter,
waveAmp floor, idle fan config, glitch root cause + fix) to the -o output file.
