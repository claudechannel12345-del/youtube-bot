# Octopus iteration 3 - THICK FILLED TENTACLES (silhouette fix)

Iteration 2 got the body + eyes + no-debug right. Remaining problems, in priority order. Primary file:
remotion/src/character/CosmicOctopus.tsx (+ solveRig.ts / motion.ts if needed for arm width/shape).
Keep tsc --noEmit clean. No new deps, no installs.

## 1. TENTACLES are the #1 fix - make them THICK FILLED tapered shapes (not thin strands)
Right now arms render as thin dark stroked lines, so they look like a tangle of noodles/wires. They must
look like the reference's THICK legs: each tentacle a FILLED, tapered shape.

Technique (do this):
- The rig already produces an arm CENTERLINE (spline points from IK + undulation + curl). Keep that as the
  centerline; do not regress the motion.
- Around that centerline, build a FILLED closed path (a "ribbon"): for each point along the centerline at
  parameter t in [0,1], offset left and right by halfWidth(t), where width tapers from WIDE at the base
  (comparable to ~28-40% of the mantle radius, so the base visually merges into the body) down to a thin
  rounded TIP (~2-4px) at t=1. Use a smooth taper (e.g. width = base * (1 - t)^1.3, clamped to a small
  min). Connect the left edge out to the tip and back along the right edge; round the tip.
- FILL each tentacle with the SAME body fill / gradient (purple -> teal) and give it the SAME darker RIM
  outline stroke as the mantle, so body + 8 arms read as ONE continuous creature.
- The base of each arm must OVERLAP the lower mantle (start a bit inside the body perimeter) so there is
  NO gap or seam - the body visibly tapers out into the arms.
- Glow: a soft CSS drop-shadow in the section accent on the whole creature group (NOT a thin bright stroke
  per arm). Avoid the thin teal outline-only look.
- Keep 8 arms. Curl the outer ~25-35% of each at rest, varied per arm. Undulation rides on the centerline
  as before (so the filled shape waves naturally).
- Render order: back arms (behind mantle) first, then mantle, then front arms, for depth.

## 2. Remove the smile
Default rest = NO mouth at all. Only a small, subtle mouth on a strong surprise reaction, understated.
No smile in neutral/curious/idle.

## 3. Fully on-screen - no clipping
The creature is clipped on the left/bottom edge. Inset its resting position so the ENTIRE body + all 8
arms are visible with margin (it can still sit lower-left, just moved inward). Verify at the entrance and
rest beats nothing crosses the frame edge.

## 4. Legible pointing
On the point beat, ONE front tentacle clearly extends and uncurls toward the stat.main anchor (straighten
its outer half, reduce its undulation, taper still applies) while the others stay curled/low - so it
visibly says "look at this number."

## 5. Label spacing
The StatScene label ("signals mapped in one clean pass") is clipped/tight on the left and close under the
number. Center it and place it clearly BELOW the ring with margin; ensure it is not clipped or overlapped
by the octopus or the ring.

## Acceptance (Claude renders locally)
- tsc --noEmit clean.
- Re-render stills frames 0,60,120,180,228.
- Check: 8 THICK filled tapering tentacles flowing from a round body (matches reference silhouette, our
  colors), one continuous creature, no thin-noodle look, no smile at rest, fully on-screen, pointing arm
  clearly indicates the stat, label clean below the ring.
