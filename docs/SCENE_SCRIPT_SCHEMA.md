# Scene Script Schema

This document covers the environment-aware fields on a generated script. These
fields are optional; sections without `environment` continue through the legacy
non-environment renderer path.

## Section Fields

- `environment`: optional environment id such as `arena`, `courtroom`, `lab`,
  or `podcast_studio`. Use it only when the section benefits from a concrete
  staged place.
- `environment_variant`: optional variant: `day`, `night`, `crowded`, or
  `empty`.
- `beats`: required list. Environment sections may stage actors per beat.

Environment ids may also be written inline as `arena:night`, but the explicit
`environment_variant` field is preferred for script JSON.

## Beat Fields

- `environment`: optional beat-level override. If omitted, the section
  environment is used.
- `environment_variant`: optional beat-level variant override.
- `actors`: optional list of 1 to 4 staged actors or props. If omitted on an
  environment beat, the renderer synthesizes fallback actors from beat assets.
- `text_overlays`: optional; scene stages use at most one overlay and place it
  in the environment `text_zone` without a label backdrop.

Non-environment beats should not declare `actors`, because slots only have
meaning inside an environment.

## Actor Fields

Each actor is an object:

```json
{
  "id": "red_fighter",
  "asset": "person",
  "slot": "red_corner",
  "colorRole": "accent",
  "pose": "pointing",
  "motion": "point"
}
```

- `id`: optional stable id, matching `^[a-zA-Z][a-zA-Z0-9_]{1,40}$`.
- `asset`: registry asset or curated generated asset name. Generic people may
  use `person`; pose-specific rendering can select `person_pointing`,
  `person_sitting`, and similar variants automatically.
- `slot`: required for authored actors, and must be a slot from the effective
  environment.
- `colorRole`: optional palette role only, such as `ink`, `accent`, `blue`,
  `green`, `yellow`, `lavender`, `muted`, `white`, `paper`, or `paper_deep`.
- `pose`: optional `idle`, `arms_up`, `pointing`, `sitting`, `walking`, `left`,
  `right`, or `lean`.
- `motion`: optional renderer motion or alias such as `idle`, `point`, `lean`,
  `micro_bob`, or `pulse`.

## Validation

Use the validator before rendering authored environment scripts:

```powershell
$env:PYTHONPATH='src'; py -m scene_script_validator data/color_script_scenes.json
```

It reports clear paths like `sections[0].beats[1].actors[0].slot` for unknown
slots, unknown assets, invalid variants, duplicate actor ids, and actor-count
limits. Warnings identify fallback behavior, such as missing actors or extra
scene text overlays.
