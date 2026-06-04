# Octopus iteration 7 - SEAMLESS one-mass body+arms, 6 legs, reference-style splayed rest pose, smoother taper, less-robotic reach

Builds on iter6c. Owner reviewed iter6c_slice.mp4: "good start, not nearly ready to lock - needs a lot of
work." Owner re-supplied the orange cartoon octopus reference (round body flowing seamlessly into curling
legs, blunt rounded tips, legs splayed/curled around the body at rest). Owner priorities, IN ORDER:

1. **The body<->arm join must be SEAMLESS** (TOP priority). "You cannot tell where the arm starts and the
   body ends." Make it read as ONE continuous mass, not a circle with lines attached.
2. **Arms are beefy enough but LUMPY in the middle** - the thickness must taper SMOOTHLY, no mid-arm bulge.
3. **Movement still looks ROBOTIC** - the way a tentacle stretches/reaches is not animal-like yet.
4. **Reduce 8 legs -> 6 legs** (8 is too many / busy).
5. **Rest pose must mimic the reference image**: at rest the legs SPLAY OUTWARD and CURL around the body
   (like the reference / a sitting octopus), NOT hang straight down. (This SUPERSEDES iter6's "hang straight
   down" decision - owner explicitly changed it. Idle arms still stay near-MOTIONLESS, just in the splayed-
   curl shape.)

Owner explicitly said: "worry about aesthetics later once it's working" - so glow/color/face polish is OUT
of scope this pass. Focus on STRUCTURE: seamless mass, 6 legs, reference rest pose, smooth taper, organic reach.

Keep `npx tsc --noEmit` clean. NO new npm deps, NO installs. ASCII only. Codex CANNOT render (esbuild spawn
EPERM in sandbox is EXPECTED) - Claude renders + tunes any visual constant afterward.

Primary files: remotion/src/character/CosmicOctopus.tsx, solveRig.ts, armOutline.ts, Chain.ts.
Also: remotion/src/scene/Slice.tsx (only to remap arm ids a6/a7 -> the new 6-arm id set; see section 6).

---

## 1. SEAMLESS one-mass body+arms via an SVG "gooey" merge filter (TOP priority)

Right now the body mantle and each arm are SEPARATE filled `<path>` elements layered on top of each other.
They share the gradient color but each has its own silhouette, so the join is visible. We want the body +
all arm silhouettes to FUSE into a single continuous outline with smooth fillets where they meet.

Technique: the standard SVG "gooey"/metaball filter = blur the alpha, then push the alpha through a steep
threshold so overlapping shapes merge into one blob, then composite the original colored graphic back on top
of that merged alpha.

### 1a. Add the filter to `<defs>` in CosmicOctopus.tsx
Add (tune-able constant `GOO_BLUR` near the top of the file, start at `GOO_BLUR = 7`):

```xml
<filter id="octoGoo" x="-30%" y="-30%" width="160%" height="160%" colorInterpolationFilters="sRGB">
  <feGaussianBlur in="SourceGraphic" stdDeviation={GOO_BLUR} result="blur" />
  <feColorMatrix in="blur" mode="matrix"
    values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 26 -11" result="goo" />
  <feComposite in="SourceGraphic" in2="goo" operator="atop" />
</filter>
```
Notes for whoever wires this:
- The `feColorMatrix` last row (alpha) `0 0 0 26 -11` sharpens the blurred alpha into a hard merged edge
  (slope 26, bias -11). These two numbers + `GOO_BLUR` are the tuning knobs; expose `GOO_BLUR` as a const so
  Claude can adjust it from a single place after rendering. Do NOT hardcode it inline in the JSX twice.
- `colorInterpolationFilters="sRGB"` avoids the dark halo you get with the default linearRGB.
- `feComposite ... operator="atop"` paints the ORIGINAL gradient-filled graphic back, clipped to the merged
  alpha, so color/gradient stays correct and only the SILHOUETTE is merged.

### 1b. Wrap ONLY the silhouette shapes (mantle + arms) in the filtered group
Restructure the render so the filter wraps the body mantle path AND all arm paths together, and NOTHING else:

```
<g filter="url(#octoGoo)">
   {pose.arms.map(renderArm)}        // all arm fills (gradient)
   <path d={mantlePath} fill="url(#octopusBody)" ... />   // body teardrop fill
</g>
// everything below renders ON TOP, OUTSIDE the filter (must stay crisp):
<g> glow overlay, rim, spots, eyes, brows, mouth </g>
```
CRITICAL: the eyes, brows, mouth, glow spots, rim stroke, and the soft radial body-glow overlay must be
OUTSIDE the goo filter (they must not blur/merge). Only the solid gradient SILHOUETTE shapes go inside.
Keep the eyes/face positioned in the body's local transform as today.

### 1c. Make the arms overlap the body a LOT so the merge has material to fuse
For a clean fillet, each arm root must sit well INSIDE the body, not just touch its edge.
- In solveRig.ts armConfigs, move every arm `root` UP into the lower-mid of the body (smaller +y, e.g.
  y in ~0.42..0.62 in body-local units instead of 0.66..0.86) so the first joint/outline starts inside the
  mantle.
- Give the arm a FAT root radius (see section 2) so the base is wide where it overlaps the body.
- Arms still render BEHIND the mantle within the filtered group (arms first, mantle second) so the body
  reads in front and the arms appear to grow out from under it - but now the gooey merge removes the seam.

The end goal: the lower half of the body and the tops of the arms form ONE smooth continuous silhouette -
you cannot point to where an arm "starts". Test by eye on a render; tune GOO_BLUR up if a seam still shows,
down if the whole creature gets too melted/blobby or fine features (rounded tips) disappear.

---

## 2. SMOOTH arm taper (kill the mid-arm lump)

The lump comes from `taperedRadii` in armOutline.ts: it builds the profile in two piecewise segments joined
at t=0.55 (shoulderToMid then easedTip), which creates a kink/bulge around the middle.

Replace `taperedRadii` with a SINGLE smooth monotonically-decreasing profile from a fat base to a rounded
blunt tip, no piecewise seam. Suggested:

```ts
export const taperedRadii = (jointCount: number, baseRadius: number, tipRadius: number): number[] =>
  Array.from({length: jointCount}, (_, index) => {
    const t = index / Math.max(1, jointCount - 1);          // 0 at root, 1 at tip
    const tipFloor = Math.max(tipRadius, baseRadius * 0.30); // blunt rounded tip, never a point
    // smooth ease-out taper: fat near base, gentle, rounds off to the tip floor. No kink.
    const eased = 1 - Math.pow(t, 1.45);                     // monotonic, smooth, no mid bulge
    return tipFloor + (baseRadius - tipFloor) * eased;
  });
```
Keep the profile MONOTONIC (each radius <= the previous) so there is never a bulge. Base stays beefy (owner
approved the iter6c heft). If after rendering the arm looks too even/cylindrical, the exponent (1.45) is the
single knob - higher = thinner faster toward the tip. The rounded blunt TIP cap logic in armOutlinePath
(tipCapPath) stays as-is.

IMPORTANT consistency fix: today the REACHING arm reads THINNER than resting arms because the radius scales
off bodyScale and the geometry slims as it straightens. Make arm thickness depend ONLY on the per-arm base
radius and the taper profile - NOT on reach/activity/straightness. A reaching arm must keep the SAME heft as
a resting arm; only its SHAPE changes, never its thickness. (In solveRig.ts the `taperedRadii(... bodyScale *
(0.124 - (index % 4) * 0.003) ...)` call should keep a constant per-arm base independent of reach.)

---

## 3. Less-robotic, more animal-like reach

A real tentacle reaching keeps an S-curve and curls/uncurls; it does not snap into a stiff straight rod.
In Chain.ts the reach currently nearly kills the curl (`curlAmount = curl * (1 - reachAmount * 0.72)`) and
loosens angle limits a lot, so a reaching arm straightens into a rod.

Make these changes in Chain.ts (keep it stateless / pure - no frame history):
- RETAIN more curl during reach: change the curl falloff so a reaching arm keeps a graceful bend, e.g.
  `curlAmount = curl * (1 - reachAmount * 0.40)` (was 0.72). The reaching arm should still arc toward the
  target, not go ramrod straight.
- Add a gentle S-shape on reach: bias the curl wave so the arm has an S (base curves one way, tip eases back
  toward the target) rather than a single uniform arc. A simple way: blend a second, lower-frequency wave
  term weighted by reachAmount, or shift the `curlWave` phase so mid-arm leads and the tip relaxes onto the
  target. Keep the TIP landing accurately on the target (pointing must still read clearly).
- Soften the straightening: reduce how much `loosenForReach` opens the angle limits (e.g. `1 + reachAmount
  * 0.42` -> `1 + reachAmount * 0.28`) so the arm bends through its reach instead of locking straight.
- Keep idle arms STILL: the existing `activity = smoothstep(reach)` gating of `swimWave`/undulation must
  stay - resting arms get ~zero per-frame wave. Do not reintroduce idle wiggle.
- Strengthen follow-through slightly so the tip trails the base as the arm moves (the analytic-lag path in
  solveRig.ts / motion.ts). A touch more lag on the tip = more life. Do NOT add state; keep the 3-sample
  analytic lag approach. Subtle - don't overshoot wildly.

This section is intentionally lighter-touch (owner: aesthetics later). Goal: the reach reads as a tentacle
curling out, not a mechanical arm extending.

---

## 4. SIX legs (down from eight)

In solveRig.ts rewrite `armConfigs` to SIX arms total, 3 per side (ids a0,a1,a2 on side +1; a3,a4,a5 on
side -1). Re-space their roots across the WIDE lower-mid of the body (see 1c - roots sit up inside the body)
and set `baseAngle` so they emerge fanning outward+downward. Keep `length`, `curlDir` alternating for a
natural fan. Remove a6,a7.

---

## 5. REST POSE = reference-style splayed curl (supersedes iter6 hang-down)

Rework the per-arm `idle` targets (and `baseAngle`) in armConfigs so that AT REST (reach=0) the 6 arms
SPLAY OUTWARD and CURL around/under the body like the reference image and a sitting octopus:
- Outer arms reach OUT to the sides (wider |x|) and curl, tips curling up/inward.
- Inner arms shorter, angled out moderately.
- Symmetric left/right. Gently curved, relaxed - not stiff, not a straight downward curtain.
- They must still be near-MOTIONLESS at rest (activity gating from section 3 stays). The splay is a STATIC
  resting shape, not animated wriggling.
The `curl` applied at idle (currently ~0.58 baseline) gives the curl; tune idle target x/y so the fan reads
like the reference (round body sitting in a splayed crown of curled legs).

---

## 6. Slice.tsx keyframe id remap (so it still compiles/runs)

Slice.tsx's characterKeyframes reference arm ids a0,a1,a2,a3,a6. With only 6 arms (a0..a5), a6 no longer
exists. Remap any a6/a7 references to valid new ids (e.g. a6 -> a5) so the working arm in the point/react
beats is still a real arm, and the pointing arm (a0) still reaches stat.main. Keep the beat timings and
targets the same; just fix the ids. Do not change the scene/camera/content.

---

## Acceptance (Claude will verify by render)
- `npx tsc --noEmit` clean.
- Render stills at frames 0, 60, 120, 180, 228 + full mp4 (Slice, 240f).
- Body and arms read as ONE seamless mass - no visible join (tune GOO_BLUR).
- Exactly 6 legs. Arms beefy with a SMOOTH taper (no mid lump), rounded blunt tips.
- At rest: legs splayed+curled like the reference, and STILL (rest-window frames ~identical).
- Reach: working arm curls out organically (not a stiff rod), tip lands on target, no glitch/pop at beat
  boundaries, reaching arm keeps the same heft as resting arms.
- No new deps; ASCII only; zero non-ASCII chars written into any file.

Write a short summary of what you changed (files + key constants) to the -o output file.
