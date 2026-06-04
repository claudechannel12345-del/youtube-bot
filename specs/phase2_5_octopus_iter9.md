# Octopus iteration 9 - CURVATURE-SPACE arm solver (fix tip flip + robotic motion at the source) + arm extension + arc-length taper

Builds on iter8. This is the MOTION/REALISM pass. Owner chose to bring the curvature solver forward because
the tentacle TIP FLIP and the ROBOTIC MOTION share ONE root cause: the current per-segment "aim each joint at
the target" chain (`resolveAngleConstrainedChain` in Chain.ts) produces a JITTERY centerline, especially at
the reaching tip, so (a) the rounded tip cap reflects/flips frame-to-frame, and (b) reaching looks
mechanical (the arm straightens toward the target instead of curling organically).

The fix (from the deep-research report .octopus_research.txt, section "Replace joint aiming with a
curvature-space arm solver", and Codex analysis .codex_iter8_discussion.txt): define the arm centerline by
CURVATURE over normalized arc length, integrate to recover the centerline. A curvature-defined centerline is
SMOOTH and TEMPORALLY STABLE, so the tip tangent varies slowly -> cap stops flipping AND motion reads
organic. READ both of those docs + the current code before starting.

Keep `npx tsc --noEmit` clean. ASCII only (zero non-ASCII bytes). Codex CANNOT render (esbuild spawn EPERM is
EXPECTED) - implement + tsc-check only; Claude renders + tunes. NO new deps.

Primary files: remotion/src/character/Chain.ts (new curvature solver), solveRig.ts (call it + per-sample
lag + endpoint correction), armOutline.ts (arc-length taper + stable tip cap), motion.ts (helpers if needed).
Default MERGE_MODE is now "goo" (set by Claude in iter8) - keep it.

---

## HARD CONSTRAINTS - do NOT break these (they already work and owner approved them)
- STATELESS / frame-local only. Remotion renders frames out of order. NO mutable state, NO previous-frame
  history. All "lag/follow-through" must come from sampling the analytic target track at delayed TIMES
  (as today via armTargetAt at delayed `time` values), never from stored state.
- Keep anchor-based targeting: `armTargetAt` (solveRig.ts ~145-189), `resolveRef`, reach limiting/clamp.
- Keep per-arm ACTIVITY gating so IDLE arms stay essentially STILL (activity = smoothstep(reach); idle
  arms = the splayed-curl REST shape owner liked in iter7/iter8, with ~zero per-frame wave).
- Keep the merge layer (goo default, polygon fallback) and the eyes/face on top. Do not touch CosmicOctopus
  render structure except where the tip-cap stability requires (armOutline only).
- Keep proportions from iter8 (MANTLE_SCALE, ROOT_TUCK, lengthened arms).
- The POINTING requirement is critical: when an arm reaches a target anchor (e.g. stat.main), its TIP must
  still land visually ON that target. Biological purity is secondary to "the octopus clearly points at the
  stat."

---

## 1. New curvature-space centerline solver (replaces resolveAngleConstrainedChain)

Add a new function in Chain.ts, e.g. `resolveCurvatureChain(input)`, returning `Point[]` (same shape the
outline code consumes). It builds the centerline by integrating curvature over arc length. Reference
implementation to ADAPT (from the report - do not copy blindly, integrate with our params):

```
theta = baseAngle + baseCurl
for i in 1..samples-1:
  u = i/(samples-1)                       // 0 at root, 1 at tip
  lag = lerp(rootLagFrames, tipLagFrames, u)   // more lag at tip
  target_u = targetAt(lag)                // delayed target sample (stateless)
  aimAngle = angleOf(target_u - pos[i-1])
  aimError = shortestAngle(aimAngle - theta)
  bend  = bendGain * gaussian(u, bendCenter, bendWidth) * aimError   // localized traveling bend
  curl  = baseCurl * pow(1-u, curlDecay) * curlDir                   // residual curl, fades gradually
  wave  = waveAmp * tipFade(u) * sin(TAU*((frame/fps) - u/waveLen) + armIndex*phase)  // small secondary
  kappa = bend + curl + wave
  theta += kappa * ds
  pos[i] = pos[i-1] + polar(ds, theta)
```

Key adaptations / requirements:
- **ds (segment length):** `length / (samples-1)` where `length = restLength * (1 + stretch)` (see section 3).
  Use enough samples (keep ~11-13) for a smooth curve.
- **Traveling bend that moves outward on reach:** `bendCenter` interpolates from ~0.30 (rest) to ~0.75-0.85
  as activity rises, so the bend propagates OUTWARD during a reach (this is the octopus "bend propagation"
  that reads organic). `bendGain` scales with activity so idle arms are not pulled toward the target.
- **Preserved curl:** `baseCurl ~0.5-0.7` rad, `curlDecay >1` (e.g. 1.6) so curl stays nearer the root and
  fades smoothly toward the tip - gives the resting splayed-curl shape AND keeps a graceful bend on reach
  (do NOT let the arm straighten into a rod). At rest (activity 0), curl alone defines the shape.
- **tipFade(u):** the wave amplitude must fall to ~0 over the last ~20-25% of the arm so the TIP is calm
  (this is critical for killing the flip - a jittery tip is what flips the cap). Also fade wave by
  (1 - 0.6*activity) so a reaching arm's tip is steadier.
- **Idle stillness:** waveAmp * activity-gate so activity 0 => no wave => the rest arms are static.
- **curlDir** per arm as today (alternating) for a natural fan.
- Pure/deterministic; vary phase by armIndex (no Math.random).

### Per-sample lag (stateless follow-through)
`targetAt(lag)` = evaluate the arm's analytic target at `time - lag/fps`. Today solveRig computes a single
`delayedTarget` via analyticLagPoint. For the curvature solver, instead pass into the solver a small closure
or 2-3 precomputed target samples (current, mid-delayed, tip-delayed) and interpolate per-sample by `u`
(root uses current, tip uses most-delayed). This preserves stateless follow-through and gives the tip a
natural trailing lag WITHOUT the old analyticLagPoint hack fighting the solver. Keep tip lag modest
(rootLagFrames ~1-2, tipLagFrames ~3-5) so it trails but does not wobble.

## 2. Endpoint correction (so pointing still lands on the target)

Codex flagged: a pure curvature integrator won't guarantee the tip lands exactly on `stat.main`. After
generating the centerline, apply a LIGHT endpoint correction, scaled by activity (so only reaching arms get
it, idle arms untouched):
- Compute `err = target - pos[last]`.
- Distribute `err * activity` across the OUTER portion of the arm using a smooth weight that is ~0 before
  ~u=0.5 and rises to 1 at the tip (e.g. smoothstep over u in [0.5,1]), so the correction bends the outer
  arm onto the target without kinking the base or creating a sharp tip.
- Keep the correction gentle; if `err` is large (target out of reach), the reach-limit clamp in armTargetAt
  already caps it - do not over-pull. The goal is "tip visibly on the stat", not a rigid IK solve.
This keeps the organic curvature shape while ensuring the point reads.

## 3. Limited arm EXTENSION / stretch (owner wants this - real octopus elongation)

Add limited proximal elongation on reach (the report's `maxStretch`):
- `stretch = maxStretch * activity` with `maxStretch ~0.10-0.16`. So a reaching arm lengthens ~10-16%,
  idle arms keep rest length. This adds life to the reach (arm extends toward the target, not just rotates).
- The stretch increases `length` (hence `ds`) for that arm on that frame. Because segment spacing now
  changes with stretch, the taper MUST move to arc length (section 4).
- Keep stretch SMOOTH via activity (no pop). Cap it so arms never look rubbery.

## 4. Arc-length taper (now required because arms stretch)

`taperedRadii` (armOutline.ts) is currently index-based. With stretch, index != arc length, so thickness
would distort. Change taper to evaluate the radius profile over NORMALIZED ARC LENGTH:
- Resample / parameterize the centerline by cumulative arc length, normalize to [0,1], and evaluate the
  (existing monotonic) radius profile against that normalized arc position - not the joint index.
- Keep the iter8 monotonic profile shape (fat base -> smooth taper -> blunt rounded tip floor). A good
  starter profile (report): u->radius approx (0,1.0)(0.12,0.96)(0.40,0.70)(0.72,0.34)(1.0,0.06-blunt floor),
  monotone. Keep the blunt rounded tip (do NOT taper to a point).
- Thickness stays INDEPENDENT of reach/activity (constant heft; only shape changes) - a reaching arm keeps
  the same width as a resting arm (owner nit from earlier).

## 5. Stable tip cap (the flip must be GONE)

With a smooth curvature centerline the tip tangent is now stable, so the cap can follow the local tip again:
- Derive the tip cap tangent from the last ~2 centerline segments (now smooth), with the epsilon guard.
  Because the wave is faded to ~0 at the tip (section 1) and the centerline is curvature-smooth, this
  tangent no longer jitters -> the cap stops mirroring/flipping.
- Keep the rounded blunt cap. Ensure cap tangent and final edge offsets use the SAME tangent (no kink).
- Do NOT reintroduce the iter8 3-segment over-smoothing that mis-angled curled rest tips; the smooth
  centerline means a short 2-segment baseline is both stable and correctly angled.

---

## Acceptance (Claude verifies by render, MERGE_MODE="goo" default; also spot-check polygon)
- `npx tsc --noEmit` clean.
- Render stills 0/60/120/180/228 + mp4, AND consecutive stills across the reach (e.g. frames 96-108) zoomed
  on the reaching-arm tip: the tip cap must NOT flip/mirror between consecutive frames (PRIMARY pass/fail).
- Reach reads ORGANIC: arm curls out with a traveling bend + slight elongation, tip lands on stat.main, no
  straight-rod look, no pop at beat boundaries.
- Idle arms still in the splayed-curl rest shape and essentially MOTIONLESS (rest-window frames ~identical).
- Resting tips correctly angled/rounded (not the iter8 mis-angle), arms keep constant heft, blunt rounded tips.
- No regression to proportions or the seamless merge.
- ASCII only; no new deps.

Write a concise summary (files changed, new solver fn name, key constants: baseCurl/curlDecay/bendCenter
range/bendGain/waveAmp/tipFade/maxStretch/lag values) to the -o output file.
