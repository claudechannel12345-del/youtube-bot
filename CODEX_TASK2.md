# CODEX TASK 2 — wire generated signature props into environments (NO network needed)

We now have 35 generated brand-style props in data/generated_assets.json. Environments read as
generic boxes because they don't use them. Make environments place signature props so each scene is
instantly recognizable. The rendering of generated shapes already works (fit-to-box, shapeSpace
"local") via _asset_element in src/blueprint_presets.py (lines ~478-499). Compile-check after each
step (npx.cmd tsc --noEmit in remotion; py -X pycache_prefix=%TEMP%\pc -m compileall src scripts;
py tests/test_scene_contracts.py). Do NOT break non-environment sections or existing scenes. ASCII
only. Log DONE notes to .codex_batch_progress.txt. You cannot render; Claude will render-proof.

## STEP 1 — factor generated-shape injection into a reusable helper
In src/blueprint_presets.py extract the generated-asset injection logic (the `if generated:` block in
_asset_element that sets generatedAssetName / shapeSpace="local" / shapes) into a helper like
`_apply_generated(element, requested_name) -> bool` (returns True if it injected). Use it in
_asset_element (no behavior change) AND in _scene_actor_elements so that a scene actor/prop whose
asset name matches a generated asset renders the generated shapes (currently scene actors call
_element directly and would NOT resolve a generated name). Keep person/registry actors unchanged.

## STEP 2 — add env "set_props" (background signature set-dressing)
- In src/environments.py, add an optional "set_props" list to environment dicts. Each item:
  {"asset": "<generated_or_registry_name>", "x": <0..W>, "y": <0..H>, "scale": <float>, "z": <int>}.
  z in the MIDGROUND band (~80-160) so props sit behind actors (actors z 200-399) but in front of the
  backdrop. Place props sitting on the floor line, spread left/right, AVOIDING the center actor slots
  and the env text_zone. Tasteful counts (1-3 per env), no clutter. Coords are for 1920x1080.
- In build_scene_stage (src/blueprint_presets.py), after the midground layer and BEFORE actors,
  convert env["set_props"] into elements using the generated/registry resolution (reuse STEP 1
  helper for generated; _registry path for registry names). Respect each prop's x/y/scale/z.
- get_vertical_environment: scale/transform set_props for vertical like other layers (nice-to-have;
  if hard, at least don't crash — drop or clamp props in vertical).
- Back-compat: envs without set_props render exactly as before.
- Validator: src/scene_script_validator.py / artdirector_validator.py must accept set_props assets
  (generated names or registry names); don't flag them.

## STEP 3 — populate set_props per environment (art direction)
Use ONLY names that exist (35 generated: barn, beach_umbrella, beaker, bookshelf, cactus_tall,
chalkboard, dining_table, dumbbell, filing_cabinet, fire_hydrant, flask, framed_painting, globe,
hospital_bed, iv_stand, library_ladder, microscope, office_chair, palm_tree, park_bench, pine_tree,
refrigerator, ringed_planet, robot_arm, rocket, school_desk, street_sign, stove, telescope, tent,
theater_curtain, tractor, traffic_light, vault_door, wheelchair). Suggested mapping (adjust positions
so nothing overlaps the center actor or the top-left text_zone; sit props on the floor):
- lab, lab_clean: microscope, flask, beaker
- library: bookshelf (left), bookshelf (right), library_ladder
- classroom: chalkboard (back, upper area but not in text_zone), globe, school_desk
- hospital: hospital_bed, iv_stand
- office: office_chair, filing_cabinet
- boardroom: framed_painting, office_chair
- bank: vault_door, filing_cabinet
- street: traffic_light, fire_hydrant, park_bench
- city_rooftop: park_bench, street_sign
- space: ringed_planet (upper, not text_zone), rocket, telescope
- desert: cactus_tall
- forest: pine_tree, tent
- beach: beach_umbrella, palm_tree
- farm: barn, tractor
- factory_floor: robot_arm
- theater: theater_curtain
- restaurant: dining_table
- gym: dumbbell
- kitchen: stove, refrigerator
- museum: framed_painting
Leave arena, courtroom, newsroom, news_studio, podcast_studio, voting_booth, airport, mountain,
field, stage as-is (already fine or no clean prop match) unless an obvious existing prop fits.

When done: append DONE notes listing files touched + which environments got set_props, and tell Claude
to render-proof these envs with scripts/proof_env.py: library, lab, classroom, office, space, beach,
farm, kitchen, street.
