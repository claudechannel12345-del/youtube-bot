# Octopus iteration 5 - design fixes + MOTION validation

Builds on the overhaul (r4). Owner feedback to address. Then we render an MP4 to verify MOTION (not just
stills). Keep tsc clean, no new deps, no installs.

## Design fixes
1. EYEBROWS look wrong. Redo the brow geometry: simple, clean, smoothly-curved strokes, correctly placed
   just above each eye, symmetric at rest, with a natural slight arc. They should read as subtle brows,
   not thick/jagged/detached/over-angled marks. Expression still drives raise/angle, but the BASE shape
   must look natural and tidy. Cap how extreme the angle/raise can get so they never look broken.

2. TENTACLES - BEEF UP + BLUNT TIPS:
   - Increase overall arm thickness (wider base radius and a fuller mid-section) so arms have real
     octopus heft - not thin/wiry.
   - The tip must NOT taper to a true point. End each arm in a ROUNDED, BLUNT tip: the radius profile
     should bottom out at a non-trivial minimum (e.g. ~30-45% of the arm's mid width) and be capped with a
     round end, so tips look soft and rounded, never sharp.

3. SEAMLESSNESS - arms must emerge FROM the web, not above it:
   - Right now arm roots sit ABOVE the webbing (arms appear to sprout from a point on the body), which
     defeats the seamless look. LOWER the arm root/attachment points DOWN INTO the web/crown so each arm
     flows OUT OF the web mass.
   - The web/crown should visually WRAP the arm bases (the bottom skirt of the body extends down and
     around where arms begin), so head -> web -> arms is one continuous mass with no "sprouting from a
     point" look. Tune the crown shape + arm root radius so the bases blend into the web with no notch or
     gap, and no visible attachment point above the web.

4. REST EXPRESSION (Claude's call): at rest the octopus should look ALERT and gently CURIOUS - eyes ~85-
   100% open (NOT half-lidded/sleepy), soft neutral-to-curious brow, calm steady gaze. No droopy/tired
   look. Keep the subtle mouth.

## MOTION quality (the important part - it must animate smoothly, not just render nice stills)
The per-frame stateless resolve MUST produce temporally smooth motion across frames:
- Targets (body position, arm targets, gaze, expression weights) must interpolate CONTINUOUSLY over time
  (eased, no instant jumps) so consecutive frames differ smoothly - NO popping/teleporting.
- Beat-to-beat transitions (enter -> point -> react -> settle) must ease in/out, not snap.
- Undulation must be continuous (phase advances smoothly with frame), and the analytic lag must be
  continuous (no discontinuity where the lagged sample crosses a keyframe boundary).
- The arm chains must not jitter frame-to-frame: ensure the resolve is deterministic and stable for
  nearby frames (small time delta -> small pose delta).
Double-check there are no per-frame randomness calls that would flicker (seed any noise by joint index,
not by frame-random).

## Acceptance (Claude runs locally)
- tsc --noEmit clean.
- Render stills 0/60/120/180/228 (design check).
- Render a full MP4 of the Slice (npx remotion render src/index.ts Slice out.mp4) and review the MOTION:
  smooth undulation, smooth body drift, clean eased beat transitions, no pop/jitter, arms flow from the
  web. Hand the MP4 to the owner to watch.
