# CODEX TASK 5 — data-driven, self-extending ENVIRONMENT library (NO live network in render)

Goal: environments can be DATA (not just code), so the director can reuse existing scenes OR generate
new ones that persist to the library. A scene = a simple BACKDROP + placed PROPS + SLOTS + a TEXT_ZONE.
Reuses the proven prop generator for the visual heavy lifting. Compile-check after each step
(py -X pycache_prefix=%TEMP%\pc -m compileall src scripts; py tests/test_scene_contracts.py; npx.cmd
tsc --noEmit in remotion if TS touched). Do NOT break the 31 code environments or existing scenes.
ASCII only. Append DONE notes to .codex_batch_progress.txt. You cannot render; Claude proofs.

## DATA MODEL — data/generated_environments.json (keyed by env id)
Each environment:
{
  "id": "bakery",
  "description": "...",
  "backdrop": [ <PrimitiveShape> ],   // FRAME coords for 1920x1080 (shapeSpace "frame"): wall band,
                                       // floor line, a window or sign. Few big shapes. Same shape schema
                                       // and validator as generate_asset (rect/circle/ellipse/polygon/
                                       // line/path, palette fills). Coordinates 0..1920 x, 0..1080 y.
  "set_props": [ {"asset":"oven","x":480,"y":720,"scale":0.9,"z":120}, ... ],  // props by name (registry
                                       // OR generated). z in midground band 80-160. Sit on the floor.
  "slots": { "baker": {"x":960,"y":760,"scale":1.4,"z":250,"role":"foreground"}, ... },  // 2-4 actor slots
  "text_zone": {"x":120,"y":90,"w":760,"h":150}   // a clear region for scene text (no props/slots inside)
}

## STEP 1 — loader + integration in src/environments.py
- Add load of data/generated_environments.json (cached).
- get_environment(env_id, variant=None): if env_id is a code ENVIRONMENT use it (unchanged); ELSE if in
  the generated store, BUILD the standard env dict the renderer expects from the data:
  backdrop -> backdrop layer (shapeSpace "frame"); set_props -> carried through as the env's set_props
  (same field build_scene_stage already consumes from code envs); slots -> slots; text_zone -> text_zone;
  midground/foreground may be empty lists. Return the same shape/contract code envs return (so
  build_scene_stage and validators work unchanged).
- has_environment / ENVIRONMENTS membership checks: include generated env ids.
- default_environment_slots / slot docs: include generated envs.

## STEP 2 — generator: scripts/generate_environment.py
- CLI: name + description, --run (mirror generate_asset.py structure/flags).
- build_env_prompt(name, desc): brand rules + the DATA MODEL above + FRAME coord system (1920x1080) +
  2 few-shot examples (convert two simple existing code envs, e.g. a plain room and the lab, into this
  data format by hand in the prompt) + the list of AVAILABLE prop names (registry + current generated)
  so the model prefers reusing props. Ask for 1-3 backdrop shapes, 2-4 set_props, 2-4 slots, 1 text_zone.
- Use src/llm.py llm_generate(tier="quality", json_mode=True). Parse with generate_asset._parse_json.
- validate_environment(env): backdrop shapes valid (reuse generate_asset._validate_shape but allow FRAME
  coords up to 1920/1080 - add a frame-bounds check, do not reuse the -512..512 BOX_LIMIT for these);
  >=1 backdrop shape; 2-4 slots each with finite x/y in frame; text_zone inside frame and NOT overlapping
  any slot center or set_prop position (clear region); set_props each reference a resolvable asset name.
- RESOLVE missing props: for any set_prop asset not in registry and not in generated_assets.json, CALL the
  prop generator (generate_asset) to create it (so a new scene auto-creates its missing props). If a prop
  cannot be made, drop that set_prop with a logged warning rather than failing the whole env.
- Persist valid env to data/generated_environments.json (merge, skip if id exists unless --force).
- Dry-run default (no --run / no key): print the prompt, write nothing.

## STEP 3 — validation + safety (rules own the render)
- src/scene_script_validator.py and src/artdirector_validator.py: accept generated env ids and their
  slots/set_props (generated or registry). A section referencing an unknown env must still fall back to a
  safe generic environment (no crash, no broken render).
- Add tests in tests/ for: building a generated env dict from data, slot/text_zone validation,
  set_props resolution (with a fake asset present), and back-compat (code envs unchanged).

NOTE: do NOT call any network at compile/test time. Generation is an offline build step. Claude will run
generate_environment.py --run and render-proof each new scene before it is trusted.
When done, list which envs/props Claude must render-proof.
