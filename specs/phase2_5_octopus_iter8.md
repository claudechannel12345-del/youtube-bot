# Octopus iteration 8 - tip-glitch fix, proportions, polygon-union merge (toggle, keep gooey)

Builds on iter7. This is the STRUCTURAL/SILHOUETTE pass (NO motion-model change - the curvature/reach
realism work is iter9, do NOT touch the motion solver's feel here beyond the tip-cap fix). Owner approved
this scope after a deep-research report (.octopus_research.txt) + Codex analysis (.codex_iter8_discussion.txt).
READ BOTH of those plus the current code before starting.

Keep `npx tsc --noEmit` clean. ASCII only (zero non-ASCII bytes in any file). Codex CANNOT render (esbuild
spawn EPERM is EXPECTED) - do not try to render; just implement + tsc-check. Claude renders + tunes constants.

New dependency ALREADY INSTALLED by Claude: `polygon-clipping` (MIT, TS types at
node_modules/polygon-clipping/dist/polygon-clipping.d.ts, exports `union`). Do NOT run npm install.

Primary files: remotion/src/character/armOutline.ts, solveRig.ts, CosmicOctopus.tsx, and a NEW file
remotion/src/character/silhouette.ts.

---

## A. FIX the tip "mirror/flip" glitch (do this FIRST, isolated, low risk)

ROOT CAUSE (confirmed in .codex_iter8_discussion.txt): the rounded tip cap derives its direction from ONLY
the final ~14% of the last arm segment. `tipCapPath` (armOutline.ts:24-29) computes its tangent from just
`tip - previous`, where `previous` = `tipPrepB` (86% out, armOutline.ts:65-70). That terminal direction is
the least stable part of the aim-at-target chain, so when the second-to-last joint swings around the moving
delayed target, the cap normal flips sides -> the tip appears to mirror frame-to-frame.

FIX (deterministic, frame-local, no state):
- Compute the tip tangent from a LONGER SMOOTHED BASELINE, not the last 14%. Use a weighted average of the
  last ~3 centerline segment vectors (e.g. vectors p[n]-p[n-1], p[n-1]-p[n-2], p[n-2]-p[n-3] with weights
  like 0.5/0.3/0.2), normalize, with an EPSILON GUARD that skips any segment vector shorter than ~1e-3 and
  falls back to the next valid one (final fallback = baseAngle direction).
- Use that SAME stable tangent/normal for BOTH the tip cap AND the final left/right edge offset points near
  the tip, so the cap and the outline edges agree (no kink where they meet).
- Keep the rounded blunt cap shape (kappa bezier) exactly as-is otherwise.
- The blunt tip radius / taper is unchanged in this section.

VALIDATION NOTE for Claude: render consecutive frames over a curling-tip window and confirm the cap no
longer swaps sides. Isolate this before judging anything else (the glitch can masquerade as motion weirdness).

---

## B. PROPORTIONS - shrink the head, lengthen the arms

Owner: head/mantle too big relative to tentacles. Per Codex: do NOT shrink global `bodyScale` (it drives
arms, roots, radii, positioning together - proportion would not change). Instead shrink ONLY the head+face
and lengthen the arms.

- In CosmicOctopus.tsx add a const `MANTLE_SCALE = 0.88` and wrap the ENTIRE body-local visual group
  (mantle fill, glow path, rim stroke, spots, eyes, brows, mouth) in an extra `scale(${MANTLE_SCALE})` so
  the head AND its face features shrink together uniformly (face proportions stay correct on the smaller
  head). Expose MANTLE_SCALE as a single tunable const (Claude will fine-tune 0.84-0.92 on render).
- In solveRig.ts pull the arm ROOTS inward ~10% so they still tuck inside the now-smaller head and keep
  enough overlap for the merge (multiply each armConfigs[].root x/y by ~0.9, OR add a `ROOT_TUCK = 0.9`
  factor applied where `config.root` is used at solveRig.ts ~216). Roots MUST still sit inside the mantle
  silhouette (overlap is what the merge needs).
- Lengthen arms: increase each `armConfigs[].length` by ~18% (e.g. 1.42 -> 1.68, 1.36 -> 1.60, 1.30 ->
  1.54) and increase the idle target distances ~15% (scale the idle x/y magnitudes) so the resting splay
  reads longer/more prominent, matching the reference where legs are clearly longer than the body is tall.
- Keep base radius about the same (Codex suggested ~0.116-0.122 * bodyScale; current is
  `bodyScale * (0.124 - (index % 4) * 0.003)` at solveRig.ts ~243 - you may drop the 0.124 to ~0.120 so the
  longer arms do not read as heavy tubes). Tip radius stays `bodyScale * 0.04`.

Target look: smaller rounded head sitting in a wider, longer splayed crown of curling legs (the reference).

---

## C. POLYGON-UNION silhouette merge as a TOGGLE (keep gooey as fallback)

Owner wants to TRY a true geometric silhouette union (cleaner than the blur for crisp edges) but wants the
gooey filter KEPT so we can flip back. Implement BOTH, switchable by ONE const.

### C1. New module remotion/src/character/silhouette.ts
- Export a function that takes: the solved arms (each has `points: Point[]` and `radii: number[]`), and the
  body mantle as a polygon in the SAME screen-space coordinates, and returns a single SVG path string (the
  unioned outer silhouette) using `polygon-clipping`'s `union`.
- Build each arm's outline RING as a closed polygon of [left edge points ... tip cap arc samples ...
  reversed right edge points] using the SAME stable-tangent offset logic as section A (reuse it - factor the
  offset/tangent helpers so the polygon ring and the bezier outline agree). Sample the rounded tip cap into
  ~6-8 points so the union has a smooth blunt end.
- Build the BODY mantle polygon by sampling `mantlePath` (the cubic bezier) into ~48-64 points, then
  TRANSFORMING those local points into screen space by replicating the body transform that CosmicOctopus
  applies: scale by MANTLE_SCALE, then by pulseX/pulseY, then by (body.scale/100), then rotate(body.rotate
  in deg->rad), then translate(body.x, body.y). (Mirror exactly what the SVG transform does so the polygon
  lands where the rendered mantle is.)
- `union` all rings (arms + mantle) into one MultiPolygon. polygon-clipping also NORMALIZES self-intersecting
  rings, so a tightly-curled arm whose offset folded over itself gets cleaned automatically (bonus tip fix).
- Convert the resulting MultiPolygon's outer ring(s) to an SVG path string. Optionally apply ONE light
  Chaikin smoothing pass (corner-cutting) to soften the polygon facets - keep it deterministic, small.
- Keep it pure/stateless; no per-frame caches.

### C2. Wire the toggle in CosmicOctopus.tsx (or solveRig where the body polygon is assembled)
- Add a const `MERGE_MODE: "polygon" | "goo" = "polygon"` (default polygon - what owner wants to evaluate;
  Claude will render BOTH for comparison by flipping this one const).
- MERGE_MODE === "goo": render EXACTLY as iter7 (arms + mantle fill inside the `<g filter="url(#octoGoo)">`
  group). Leave the octoGoo filter + GOO_BLUR const fully intact in the file (do NOT delete the gooey path).
- MERGE_MODE === "polygon": render ONE `<path>` = the unioned silhouette from silhouette.ts, filled with the
  same `url(#octopusBody)` gradient, NO goo filter (or only a very small 1px AA blur if needed). Do NOT also
  draw the separate arm/mantle fills in this mode (the union replaces them).
- In BOTH modes the eyes/brows/mouth/spots/glow render ON TOP, OUTSIDE any merge, unchanged (they already do
  in iter7 - keep that; just make sure they sit on the new smaller head via MANTLE_SCALE from section B).
- The drop-shadow accent glow wrapper stays.

### C3. Coordinate-space care
The union MUST happen in one consistent space. Arms are already in screen space (absolute 1920x1080) from
solveRig. Transform the mantle polygon into that same screen space (C1). Verify the gradient still uses
userSpaceOnUse so it lines up under the unioned path (it does today, keep it).

---

## Acceptance (Claude verifies by render)
- `npx tsc --noEmit` clean.
- Render stills 0/60/120/180/228 + mp4, in BOTH MERGE_MODE="polygon" and ="goo" (Claude flips the const).
- Tip no longer mirrors/flips across consecutive frames (section A).
- Head visibly smaller, arms longer/more prominent - reads like the reference proportions (section B).
- Polygon mode: body + arms read as ONE crisp seamless mass, no seam, no melt. Goo mode still works as a
  fallback (toggle proven).
- No idle-arm wiggle regression; reach still points at stat.main; no new glitch.
- ASCII only; only dep is the already-installed polygon-clipping.

Write a concise summary (files changed, new consts MANTLE_SCALE / MERGE_MODE / ROOT_TUCK, key numbers) to
the -o output file.
