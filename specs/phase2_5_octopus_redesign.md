# Octopus redesign + slice cleanup (iteration 2)

The slice pipeline works. This pass fixes the CHARACTER DESIGN + staging only. Primary file:
remotion/src/character/CosmicOctopus.tsx (the SVG render of a ResolvedPose). May also touch solveRig.ts /
motion.ts (arm shape/length/curl), rigTypes.ts (arm count 6 -> 8), the Slice plan (scale/position), and
wherever on-screen debug text is drawn. ASCII only in Python (none here). Keep tsc --noEmit clean. No new
deps, no installs.

## 0. CRITICAL: remove ALL on-screen debug text
There is burned-in debug text in the render ("DRIFT", and a beat label that truncated to "C_UNT"). Remove
every on-screen debug/dev label from the character render, CharacterLayer, StatScene, and Slice. Nothing
but the intended scene content may draw text. Double-check no locomotion-mode or beat-name string is
rendered anywhere.

## 1. Target silhouette (the whole point of this pass)
The owner's reference image conveys ONE thing only: the BODY SHAPE/PROPORTION. Take NOTHING else from it
- not eyes, not suction-cup styling, not outline style, not color. All detailing is our own design
(our detailed eyes from section 2, Cosmos Dark colors from section 3, bioluminescent glow).

Shape to hit: a large ROUNDED BULBOUS MANTLE (head/body) whose lower half flows SMOOTHLY and continuously
into 8 THICK TENTACLES that taper from a wide base to a thin, gently CURLED tip. No visible seam between
body and arms - they read as one organic creature, NOT a circle with thin legs attached.

Redesign CosmicOctopus so:
- **Mantle:** a big rounded dome - broad, slightly taller-than-typical rounded form (think a rounded
  inverted teardrop / a circle whose bottom third widens into the arm crown). It should occupy a generous
  share of the character bounds.
- **Arms: 8** (bump from 6). Each arm is a TAPERED path: wide where it meets the body (each base overlaps
  the body's lower perimeter so the fill is continuous - no gap, no stuck-on look), tapering to a thin tip
  that CURLS (curl the last ~25-35%, alternate curl direction / amount per arm so it looks natural, not
  symmetrical). Arm length ~1.3-1.7x the mantle radius.
- **Continuity:** body and arm bases share the same fill so the silhouette is one shape. Give the whole
  creature a subtle darker RIM/outline stroke (like an illustrated octopus) for a clean, intentional look.
- (No suction-cup detailing required - that came from the reference; do not mimic it. Keep arms clean.)

## 2. Face - less childish, still expressive (it is SILENT)
- **Eyes:** KEEP the existing DETAILED eyes (white sclera + distinct pupils + highlight + brows) - do NOT
  replace them with plain black dots. They just need to be REFINED/REDEFINED: cleaner, better-proportioned
  shapes, set well on the upper mantle, reading as intelligent and characterful rather than cartoonish.
  Preserve the full expressive rig (gaze tracking, pupil move, widen on surprise, narrow on skeptical,
  blink). The detail in the eyes is a feature the owner likes - sharpen it, don't strip it.
- **Mouth:** remove the big smile. Default = none or a tiny, subtle neutral mark. Only show a small mouth
  shape on strong reactions (surprise), and keep it understated.
- **Brows:** keep subtle for expression, thin strokes.

## 3. Color (Cosmos Dark, original - NOT orange)
- Body fill: deep cosmic violet/purple, ideally a soft vertical gradient toward teal at the base
  (use theme.ts palette: purple #9B5DE5 / teal #06D6A0 / bg #0D0D1A; darken for the body so text stays
  dominant). Rim outline: a darker shade of the body or a dim accent.
- Eyes: keep the detailed treatment - lighter sclera + darker pupils + a small specular highlight (NOT
  flat black dots). Tune for legibility against the dark body.
- Bioluminescent spots: FEW and SOFT (a handful), glowing in the section accent via gentle CSS
  drop-shadow - not flat polka dots. Glow intensity still tied to energy.

## 4. Size + staging
- Scale the octopus UP (~40-60% larger than current) and keep it FULLY ON-SCREEN with margin from the
  edges (no clipping). Default resting spot: lower-left, but inset so all 8 arms are visible.
- **Legible pointing:** on the point beat, ONE tentacle clearly extends and uncurls toward the stat.main
  anchor while the other arms pull back / curl in, so the gesture reads as "look at this number." The
  reaching arm should straighten (less undulation in its outer half) so the point is unambiguous.
- Ensure the StatScene label ("signals mapped...") does not overlap the number/ring - nudge it below the
  ring with clear spacing.

## 5. Keep the rig intact
Do not regress the stateless analytic-lag motion, IK, undulation, or expression blending. The tapered
curling tentacles must still be driven by the spline + IK + undulation (curl is part of the rest pose;
undulation rides on top; reach straightens the pointing arm). 8 arms x ~6 control points is fine.

## Acceptance (Claude will render locally)
- `cd remotion && npx tsc --noEmit` clean.
- Re-render stills at frames 0, 60, 120, 180, 228 (npx remotion still, no ffmpeg needed).
- Visual check: reads clearly as a ROUND-BODIED OCTOPUS with 8 tapering curling tentacles (matches the
  reference silhouette, original colors), fully on-screen, no debug text, no goofy grin, pointing arm
  clearly indicates the stat, label not overlapping.
