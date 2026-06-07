# Engine Guide

This project renders videos from script JSON, deterministic blueprints, and
Remotion. Environment-aware scenes are optional. Any section without an
`environment` must continue through the legacy non-environment blueprint path.

## Scene Scripts

A section may declare a concrete environment:

```json
{
  "environment": "arena",
  "environment_variant": "night",
  "beats": [
    {
      "id": "beat_01",
      "type": "emphasize",
      "actors": [
        {"id": "red", "asset": "person", "slot": "red_corner", "colorRole": "accent"},
        {"id": "blue", "asset": "person", "slot": "blue_corner", "colorRole": "blue"}
      ],
      "text_overlays": [{"role": "headline", "text": "RED WINS"}]
    }
  ]
}
```

Environment fields:

- `environment`: known id from `src/environments.py`, such as `arena`,
  `courtroom`, `lab`, `office`, `news_studio`, or `podcast_studio`.
- `environment_variant`: optional `day`, `night`, `crowded`, or `empty`.
- `actors`: beat-level staged actors or props. Use 1 to 4 actors.
- `text_overlays`: environment scenes use at most one meaningful overlay; it is
  placed in the environment `text_zone` with no backdrop.

Beat-level `environment` and `environment_variant` override section-level
values. Inline refs like `arena:night` are supported, but the explicit
`environment_variant` field is preferred in authored JSON.

Do not add `actors` to non-environment beats. Slots only exist inside an
environment.

## Environments

Environments live in `src/environments.py`. Each builder returns:

- `id`
- `backdrop`, `midground`, and `foreground` primitive shape lists
- `text_zone` as `{x, y, w, h}`
- `slots` keyed by stable slot id

The proven visual pattern is:

- palette roles only: `ink`, `accent`, `blue`, `green`, `yellow`, `lavender`,
  `muted`, `white`, `paper`, `paper_deep`
- thick ink strokes
- perspective-lite floor or depth cues
- foreground occluder for depth
- clear `text_zone` with no backdrop behind scene text
- tasteful element counts; recognizable place details without clutter

When adding an environment:

1. Add a `build_<id>()` function in `src/environments.py`.
2. Return non-empty `backdrop`, `midground`, and `foreground` layers.
3. Add named slots with `_slot(x, y, scale, z)`.
4. Keep foreground slots lower/larger than midground and background slots.
5. Add the builder to `ENVIRONMENT_BUILDERS`.
6. Add the id and slots to `src/cutaway_vocab.py`.
7. Run the lint/compile checks below.

`get_environment()` enriches the authored scene with shared depth marks,
variant details, and `slot_docs`. `get_vertical_environment()` adapts the same
environment for Shorts.

## Assets

Flat-vector registry assets live in `remotion/src/cutaway/registry.tsx`.
Every registry asset must also be wired into:

- `REGISTRY_ASSETS` in `src/cutaway_vocab.py`
- the director asset catalog in `src/director.py`
- `assetBaseSize` in `remotion/src/cutaway/GenericBlueprintRenderer.tsx`

Actor assets may be people, role figures, props, or curated generated assets.
Generic `person` actors can use `pose` to select variants such as
`person_pointing`, `person_sitting`, `person_walking`, `person_left`, and
`person_right`.

## Generated Assets

`scripts/generate_asset.py` builds a Gemini prompt for a primitive shape-list
asset. It is dry-run by default and does not require network access:

```powershell
py scripts/generate_asset.py trophy_alt "simple trophy with thick ink outline"
```

To generate for real, set `GEMINI_API_KEY` and pass `--run`. The script writes
validated assets to `data/generated_assets.json`. Generated assets must use the
same primitive vocabulary and palette roles as authored assets.

Review generated assets with:

```powershell
py scripts/review_generated.py
cd remotion
npx.cmd remotion still src/index.ts Cutaway out/generated_assets_review.png --props=props_generated_assets_review.json --frame=30
```

Curate for recognizability, scale, style match, and clutter before using them
in authored scripts.

## Validation

Run the scene schema validator for strict environment/actor checks:

```powershell
$env:PYTHONPATH='src'
py -m scene_script_validator data/color_script_scenes.json
```

Run the richer lint report before rendering:

```powershell
py scripts/lint_script.py data/color_script_scenes.json --inventory
```

The lint report checks:

- environment ids and variants
- actor slot membership
- actor assets, color roles, poses, and motions
- actor count limits
- scene text limits
- narration text matching the joined section sentences
- beat sentence spans
- environment, slot, and asset usage

Compile checks after changes:

```powershell
py -X pycache_prefix=$env:TEMP\pc -m compileall src scripts tests
cd remotion
npx.cmd tsc --noEmit
```

Render/proofing is still required for visual changes. Claude should inspect
place readability, text-zone clearance, slot depth/scale, foreground occluders,
and generated asset recognizability.
