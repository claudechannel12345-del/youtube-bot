# Octopus OVERHAUL plan (research-grounded) - for owner approval before building

## Why the current octopus is crude (root cause)
We hand-rolled arms as a "tapered ribbon around a bezier" with an aggressive linear taper and a too-wide
base -> triangles. There is no angle constraint on the arm bend, so arms fold over each other. The body
is a full circle (reads as "circle with lines"), too big, and draw order puts some arms in front. We were
reinventing the wheel badly.

## The established technique (from research)
2D procedural creatures (the satisfying fish/snake/lizard animations) use a well-known method:
- A LIMB IS A CHAIN of joints with a FIXED link distance, where each joint follows the previous one and
  the bend angle between consecutive links is CLAMPED by an angleConstraint ("higher = loose, lower =
  rigid"). The angle clamp is what prevents kinks AND prevents arms folding over themselves. (argonautcode
  animal-proc-anim; Alan Zucconi IK.)
- The BODY/LIMB SHAPE is drawn as a SMOOTH FILLED OUTLINE around the chain: at each joint place two points
  PERPENDICULAR to the spine at distance = radius[i] (a per-joint radius profile), then connect all the
  left points, a ROUNDED tip, and the right points into one filled polygon. Rounded ends, organic width -
  NEVER triangles.
- Reaching/pointing = move the chain's end target; the angle-constrained chain naturally curves to reach
  it (CCD/FABRIK-style). Games animate tentacles exactly this way (long bone chain so no sharp angles).
- Undulation/secondary motion = let the chain follow a target that drifts on a sine wave; the chain's lag
  gives free, natural follow-through.

## Remotion compatibility (the catch + fix)
The classic chain evolves from its PREVIOUS-frame positions (stateful). Remotion renders frames in random
order (stateless). Fix: resolve each arm chain ANALYTICALLY per frame from (a) the arm's root point at
this frame and (b) a target sampled at t - lag (the existing analytic-lag trick), applying the
angle-constrained follow-the-leader from root to target. Deterministic, stateless, still gives lag/
follow-through. This replaces the bezier-ribbon arm code entirely.

## The redesign (addresses every piece of owner feedback)
1. SHAPE = more octopus, less "circle + lines": MANTLE becomes a smaller, rounded TEARDROP/DOME head (not
   a full circle), shrunk a lot so it does NOT dominate the frame. Arms radiate from a hidden crown UNDER
   the rear of the mantle.
1b. SEAMLESS BODY (owner emphasis): the mantle and arms must read as ONE continuous organic mass, NOT a
   circle with tentacles attached. Technique (no heavy filters):
   - Mantle bottom does not end in a hard circular edge; it widens into a CROWN/SKIRT (a smooth curved
     band/web) that fans out and blends into the 8 arm bases - like a real octopus head -> web -> arms.
   - Each arm's BASE joint is anchored INSIDE the lower mantle (overlapping, not touching the perimeter),
     and the arm's base radius approximately matches the local body/crown width so the fills are
     continuous with no notch.
   - Body + crown + all arms share the SAME fill (a single continuous purple->teal gradient across the
     whole creature). Draw all fills as one group with NO internal per-part stroke seams; define the
     outer edge with a single soft drop-shadow glow (and optionally one outer silhouette stroke), so there
     is no visible circle boundary where arms meet the body.
   - Net effect: a smooth teardrop mass that organically tapers out into 8 curling arms - one silhouette.
2. TENTACLES via angle-constrained chains (8-12 joints each): they STRAIGHTEN and curve smoothly, do NOT
   fold over each other (angle clamp). Render via perpendicular RADIUS OUTLINE with a GENTLE, mostly-even
   taper that ROUNDS at the tip - kills the triangle look. Arms longer + thinner than now.
3. LAYERING: draw ALL arms BEHIND the mantle for v1 (clean). (Optional later: 1-2 draping in front for
   depth - not now.)
4. SIZE: shrink the whole creature; it should read as a character in the lower-left, not fill the screen.
5. EYES: keep the detailed eyes (owner likes them). MOUTH: keep a mouth, tuned to look good (subtle,
   non-childish) - owner wants to keep it if it looks good.
6. COLOR/glow unchanged direction (Cosmos Dark purple->teal, soft accent glow).
7. Keep stat/ring/camera scene as-is; just fix the StatScene label clipping ("signals" cut to "gnals").

## Build approach
- New/rewritten: character/Chain.ts (joints, linkSize, angleConstraint, stateless resolve from root->lagged
  target), character/armOutline.ts (perpendicular radius-profile -> filled path with rounded tip),
  rewrite CosmicOctopus.tsx (smaller teardrop mantle + 8 chain-arms drawn behind, eyes, tuned mouth),
  adjust solveRig.ts to feed each arm a root + lagged target + radius profile. Keep expression rig + eyes.
- Verify: tsc clean, render stills at 0/60/120/180/228, eyeball against the round-body/curling-tentacle
  reference. Iterate with Codex; Claude reviews stills each pass.
- This is a meaningful rewrite of the arm system (the rest of the slice pipeline stays).

## Sources
- argonautcode/animal-proc-anim (chain + angle constraint + radius outline): https://github.com/argonautcode/animal-proc-anim
- Alan Zucconi, IK for Tentacles: https://www.alanzucconi.com/2017/04/12/tentacles/
- Alan Zucconi, Intro to Procedural Animations: https://www.alanzucconi.com/2017/04/17/procedural-animations/
- Verlet/physics tentacle reference (octopus sim): https://bionichaos.com/Octopus2D/
