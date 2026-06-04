# Octopus iteration 6 - remove skirt, still-at-rest arms hanging DOWN, fix glitch, slimmer base, rounded tips

Builds on iter5. Owner feedback, in priority order. Keep `npx tsc --noEmit` clean. No new deps, no installs.
Primary files: remotion/src/character/CosmicOctopus.tsx, solveRig.ts, Chain.ts, armOutline.ts.

## 1. REMOVE the skirt / web mesh (it is unnecessary now)
The arms attach at the base of the body, so the fanned-out skirt/web overlay is no longer needed and looks
wrong. In CosmicOctopus.tsx DELETE the two bottom "skirt" paths:
- the `M -86 50 C ... Z` fill (the crown/skirt fan, ~opacity 0.72), and
- the `M -78 55 C ... Z` inner shadow band (`fill="#143D4B"`, opacity 0.2).
Keep the mantle body, glow, rim stroke, spots, eyes, brows, mouth. After removing the skirt, the arm roots
(which are drawn BEHIND the body) must still tuck cleanly under the lower edge of the mantle so there is no
gap and no visible attachment point - arms simply emerge from under the base of the body. If needed, nudge
the arm root anchor points (armConfigs[].root) slightly UP/INWARD so their bases sit just under the mantle
bottom, not poking out beside it.

## 2. REST POSE: arms hang DOWN and stay essentially STILL
This is the most important fix. Two parts.

### 2a. At rest the arms hang downward relative to the body
Right now the idle targets splay the arms wide out to the sides. Instead, at rest the 8 arms should DRAPE
DOWNWARD below the body (like a resting octopus / jellyfish hanging), only gently fanned - NOT spread wide
horizontally. Rework armConfigs[].idle (and baseAngle if needed) so the resting arm centerlines point
mostly DOWN (+y), with only a modest left/right spread that increases a little for the outermost arms. The
outer two on each side can angle out a bit; the inner ones hang nearly straight down. Keep them gently
curved/relaxed, not stiff. Net look: a soft downward curtain of 8 arms under the body.

### 2b. Idle arms must be (near) MOTIONLESS - only arms "in action" move
Owner: "the tentacles don't have to move that much or even at all when the octopus is doing nothing. They
should stay at rest like downwards, and the tentacles that are being used can be raised up and put into
action." So:
- Define a per-arm ACTIVITY in [0,1] driven by that arm's continuous `reach` (and only that arm's reach),
  e.g. activity = smoothstep(reach). At rest reach=0 -> activity=0.
- The arm undulation/`swimWave` amplitude (in Chain.ts) and any per-frame motion of the arm MUST scale by
  activity, so an idle arm (activity 0) has ZERO or near-zero per-frame wave - it is a static downward
  drape. Do NOT drive idle-arm motion off the global `energy`/buoyancy. The body can still bob gently, but
  resting arms should look calm and basically still, not constantly wriggling.
- When an arm is put into action (reach increases), it RAISES toward its target and its undulation turns on
  smoothly via activity. So motion appears only on the working arm(s); the rest hang quietly.
- A very subtle shared drift is OK if it is tiny and smooth, but the default read must be "still".

## 3. FIX the glitching / skipping (arms pop between frames)
The arms visibly glitch/skip frame-to-frame. Root cause to fix: discontinuities feeding the chain solve.
- In solveRig.ts the arm `mode` is chosen discretely (`progress > 0.5 ? toIntent.mode : fromIntent.mode`)
  and then `pointAssist`/`reachForChain` (and thus `angleConstraint` and `curl`) depend on that DISCRETE
  mode. When mode flips at progress=0.5 these jump in a single frame -> the chain snaps to a new config =
  the skip. FIX: make pointAssist / reachForChain / angleConstraint / curl depend ONLY on the CONTINUOUS
  interpolated `reach` (and activity), never on a discrete mode switch. Remove the `mode === "point"` branch
  from the chain inputs; derive everything from reach via smooth functions.
- Ensure the analytic lag (analyticLagPoint over t, t-lag, t-2lag) does not overshoot or introduce a
  discontinuity at keyframe boundaries; for a static idle target it must collapse to the static point
  (lag of a constant = constant). If the quadratic extrapolation can overshoot, clamp it or fall back to a
  simple eased 1-step lag.
- Guarantee: for a small frame delta the resolved chain points move only a small amount everywhere
  (temporal stability). No frame-random calls; any noise seeded by joint/arm index, not by frame randomness.
- Idle arms (activity 0) should resolve to a deterministic static downward curve every frame (identical
  shape across nearby frames) so they cannot skip at all.

## 4. Slimmer arm base
Arms are a bit too beefy at the base. Reduce the base radius: in solveRig.ts taperedRadii base from
`bodyScale * (0.142 - ...)` down to about `bodyScale * (0.108 - (index % 4) * 0.003)`. Keep a fuller mid and
the rounded blunt tip; just trim the base so arms are slimmer where they meet the body. Tune so arms still
read as having heft but are not bulbous at the root.

## 5. TRULY rounded tips (no sharp angle)
The tips still read as a sharp angle, not rounded. In armOutline.ts the side outline currently meets the tip
arc at a corner. Make the tip a smooth, genuinely ROUNDED cap:
- The radius profile should ease smoothly to a non-trivial tip radius (keep blunt, ~35-40% of mid), and the
  left/right outline must approach the tip TANGENTIALLY so there is no corner where the side meets the cap.
- Render the tip as a proper semicircular cap of radius = the last joint radius, centered on the centerline
  tip, with correct arc sweep so it bulges OUTWARD (convex), and the two side paths meet it smoothly.
- If helpful, add 1-2 extra interpolated centerline samples near the tip so the spline curves into the cap
  instead of ending abruptly. The end result must look like a soft rounded finger tip, never a point or a
  flat/angular end. Verify visually on multiple arms.

## Acceptance (Claude renders + validates locally - do NOT attempt to render in the Codex sandbox)
- tsc --noEmit clean.
- (Claude) render stills 0/60/120/180/228 -> design check: no skirt, arms hang down at rest, slimmer bases,
  rounded tips.
- (Claude) render full MP4 + extract consecutive frames (ffmpeg `-ss <sec> -frames:v N`, NO -vf select -
  Remotion's ffmpeg has --disable-filters) -> verify idle arms are still and there is NO glitch/skip; the
  working arm raises/moves smoothly while the others hang quietly.
