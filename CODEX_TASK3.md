# CODEX TASK 3 — remove residual gray corner dots (cosmetic cleanup, NO network)

In rendered environment scenes there are still faint GRAY FILLED CIRCLES (~40-70px radius) sitting
in the bottom-LEFT and bottom-RIGHT screen corners (visible in lab, space, street, kitchen proofs).
They read as artifacts, not intentional depth. An earlier pass removed most generic enrichment dots
but these corner circles remain.

TASK: Find their source in src/environments.py (and src/blueprint_presets.py if the foreground/
occluder layer adds them) and REMOVE them. They are likely a shared foreground "occluder dot" or
ground-shadow circle still applied to many environments, OR authored per-env corner circles. Keep
intentional authored foreground occluders (e.g. arena ropes/posts, desk edges) — only kill the
stray gray corner circles.

OPTIONAL (only if obvious + safe): the colored oval "pads" under staged actors (blue/yellow ellipses
under figures, visible in kitchen) look odd. If they come from a generic actor ground-shadow tinted
by colorRole, make them a single subtle neutral (muted, low opacity) or remove — but do NOT change
actor positions/slots. Skip if risky.

Compile-check after changes: npx.cmd tsc --noEmit in remotion; py -X pycache_prefix=%TEMP%\pc -m
compileall src scripts; py tests/test_scene_contracts.py. Don't break non-environment sections.
Append a DONE note to .codex_batch_progress.txt with files touched. Claude will render-proof
lab/space/street/kitchen after.
