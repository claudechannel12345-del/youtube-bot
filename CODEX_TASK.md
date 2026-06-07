# CODEX TASK — generated-asset sizing + environment cleanup (NO network/Gemini needed)

Context: We now generate brand-style props as primitive shape-lists (data/generated_assets.json,
14 assets so far). They render via GenericBlueprintRenderer when a blueprint element has
`shapes` + `shapeSpace`. Two problems to fix. Compile-check after each (npx.cmd tsc --noEmit in
remotion/; py -X pycache_prefix=%TEMP%\pc -m compileall src scripts). Do NOT break existing
non-generated rendering. Log work to .codex_batch_progress.txt. ASCII only in Python.

## TASK 1 — fit local generated shapes to their box (FIXES overflow)
Generated assets use local coords centered near 0,0 in a -512..512 box. Today an element with
`shapeSpace: "local"` renders shapes at raw coords * a fixed scale, so large-coord assets overflow
their panel/slot. Fix in remotion/src/cutaway/GenericBlueprintRenderer.tsx (the renderShapes /
generated-image path):
- When shapeSpace === "local": compute the bounding box of ALL the element's shapes (handle rect,
  circle, ellipse, line, polygon points, and path — for path you can parse the numbers already
  extracted elsewhere, or approximate using the numeric coords in `d`). Then compute a transform
  that scales the shapes uniformly so the bbox fits within the element's resolved size box
  (size.mode "box" -> w/h; size.mode "scale" -> base box ~320x320 * scale), and translates so the
  bbox center maps to the element's point. Apply via an SVG <g transform="translate(...) scale(...)">
  wrapper around the local shapes (do NOT mutate coords per-shape if a group transform is cleaner).
- shapeSpace === "frame" (environments) must keep absolute behavior UNCHANGED.
- Keep the brand ink stroke; when scaling down, optionally keep stroke width visually reasonable
  (a non-scaling stroke is nice-to-have, not required).
Verify: scripts/review_generated.py contact sheet should show every asset INSIDE its panel, none
overflowing. (Claude will render the still to confirm.)

## TASK 2 — remove the noisy shared "enrichment" marks in environments
In src/environments.py the shared get_environment enrichment adds generic foreground "occluder dots"
(big gray circles that land in the corners) and a faint empty rounded panel near the top-left text
zone. On render these read as artifacts, not depth. Remove/disable the GENERIC enrichment dots and
the empty top-left panel. KEEP each environment's authored, intentional foreground occluder (e.g.
arena ropes/posts) and authored set dressing. Net: environments should look intentional, no random
gray balls in corners, no empty box overlapping the text zone.
Verify: scripts/proof_env.py <env> then render — arena/courtroom/hospital/library should have no
stray corner circles or empty top-left panel. (Claude will render to confirm.)

## TASK 3 (only if quick) — raise validator/cap consistency
generate_asset MAX_SHAPES is now 38. If src/artdirector_validator.py or scene_script_validator.py
hardcode a 30-shape limit for generated assets, bump to match (38). Don't change unrelated limits.

When done: append a DONE summary per task to .codex_batch_progress.txt noting files touched and what
Claude must render-proof.
