# BACKLOG — autonomous Codex work queue

RULES (apply to every item):
- Follow the PROVEN pattern: src/environments.py (arena) + scripts/make_scene_proof.py. Palette roles
  only (incl paper/paper_deep/white), thick ink strokes, perspective-lite, a FOREGROUND OCCLUDER for
  depth, tasteful element counts (no clutter), text only for emphasis/quote/stat.
- NEVER break sections without an "environment" (the live color video must still render the old way).
- After each item: compile-check (py -X pycache_prefix=%TEMP%\pc -m compileall src; npx.cmd tsc
  --noEmit in remotion/ if TS touched). If it fails, FIX before moving on.
- Mark each item DONE in .codex_batch_progress.txt with files touched + notes + anything Claude must
  render/proof. ASCII only in Python. You cannot render video; make code correct + compiling.
- Work items top-to-bottom. Don't stop until killed or the list is done.

## A. SCENES / ENVIRONMENTS
A1. text_zone per environment (clear region, no backdrop behind it); build_scene_stage places scene
    text there. Add to arena/courtroom/newsroom.
A2. Expand env library (arena-pattern, each clearly its place + slots + text_zone): lab, street,
    office, classroom, stage, field, space (cream/night band, not black), kitchen.
A3. More environments: museum, hospital, factory_floor, beach, forest, mountain, desert, restaurant,
    gym, library, bank, airport, boardroom, theater, news_studio, podcast_studio, voting_booth,
    farm, lab_clean, city_rooftop.
A4. Per-env DAY/NIGHT or EMPTY/CROWDED variants where cheap (a variant arg on the builder).
A5. scripts/build_color_script_scenes.py -> data/color_script_scenes.json: map the fight/Olympic/
    color-swap/two-suspects sections -> arena (red/blue fighters + referee in slots; swap beat swaps
    corner colors), courtroom section -> courtroom. Keep narration sentences IDENTICAL (audio cache).
A6. Depth/scale polish: ensure slot scale/y/z give consistent foreground>midground>background sizing
    across all envs; document each env's slots.

## B. ASSET / PROP LIBRARY (flat-vector, registry.tsx + vocab + catalog + baseSize)
B1. Common props as registry assets (arena-pattern shapes): car, tree, house, coin/money, trophy,
    book, bag, bottle, cup, box, key, lightbulb, lock, shield, flag, ball, camera, microphone,
    laptop, chart_bar, chart_line, pie_chart, arrow_up, arrow_down, checkmark, cross, question_mark,
    warning, gear, magnet, brain, dna, pill, syringe, scale_justice, ballot, crown, target.
B2. Character variety: person poses/variants (arms_up, pointing, sitting, walking), facing left/right,
    and roles via color/props (doctor, scientist, judge, athlete, suit). Keep the matched flat style.
B3. Weather/nature bits: sun, cloud, rain, star, moon, mountain_shape, wave, fire, plant.
B4. Wire every new asset into REGISTRY_ASSETS + the catalog + assetBaseSize.

## C. PROP GENERATOR (Gemini shape-list) - tooling only; do not require network to compile
C1. scripts/generate_asset.py: name+desc -> Gemini prompt (brand rules + PrimitiveShape vocab + 3-4
    few-shot existing-asset shape-lists) -> shape-list JSON -> validate (legal types/fills/coords,
    <=30 shapes) -> data/generated_assets.json keyed by name. Use gemini_utils.generate(PRO_MODELS);
    if no key/client, dry-run (emit prompt + note) so it compiles/tests offline.
C2. Renderer + director path so a blueprint element/asset can reference a generated asset by name and
    draw its shape-list (reuse element.shapes). Validator accepts known generated names.
C3. scripts/review_generated.py: render a contact sheet of generated assets for curation (Claude runs).

## D. DIRECTOR / SCENE INTELLIGENCE
D1. Extend the LLM art-director (DIRECTOR_MODE=llm) to also CHOOSE an environment per section + stage
    actors into slots (validate->repair->rules fallback; rules own the render). Offline/curated, not
    live-on-render. Don't call Gemini at compile time.
D2. Per-pose subtle motions (idle bob, point, lean) mapped to actor "pose"/"motion".
D3. A "scene script" schema doc + validator: a section may declare environment + per-beat actors;
    validate slots/assets/limits with clear errors.

## E. SHORTS
E1. Let scripts/make_short.py use ENVIRONMENTS too (vertical 1080x1920 variants of slots/backdrops),
    so Shorts are scenes, not centered cards.
E2. scripts/make_shorts_batch.py: from a full script, auto-pick 2-3 hook moments and emit vertical
    short scripts (each links to the main video).

## F. INFRA / TESTS / DOCS
F1. tests/ for the validator + blueprint presets + environments (pytest or plain asserts) -
    legal/illegal blueprints, env/slot checks, back-compat (non-env section == old output).
F2. scripts/lint_script.py: validate a script JSON (envs exist, slots valid for env, assets known,
    invariant holds, text limits) and print a report.
F3. docs/ENGINE.md: how to author a scene script (environments, slots, actors, text rules) + how to
    add an environment + how the generator works.
F4. Cleanup: remove dead code paths, unify duplicated anchor/palette constants between TS and Python
    where safe (without changing behavior).

## G. QUALITY PASSES
G1. Improve weakest existing assets (mandrill readability, gavel proportions, finch) - small refinements.
G2. Self-review: re-read all environments + assets; list in progress file anything that likely looks
    off and why, for Claude to render-check.
G3. Final: write a top-of-file SUMMARY in .codex_batch_progress.txt - done / partial / needs-proof /
    risks, per section A-G.
