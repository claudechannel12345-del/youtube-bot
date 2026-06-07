# CODEX TASK 7 — homework.mp4 visual fixes (framing safe-area + declutter scenes)

Owner reviewed the first render. Visual problems to fix. Compile-check after each step (py -X
pycache_prefix=%TEMP%\pc -m compileall src scripts; py tests/test_scene_contracts.py; npx.cmd tsc
--noEmit in remotion if TS touched). ASCII only. Do NOT break the 31 code envs, generated envs, or the
homework pipeline. Append "DONE CODEX_TASK7 STEP N ..." to .codex_batch_progress.txt after each step.
You cannot render; Claude proofs. Owner's exact complaints are quoted per step.

## STEP 1 — FRAMING / SAFE-AREA BUG (highest priority, affects many scenes)
Symptoms: "the text is completely cut off on top" (headline clipped at top edge on many scenes);
"some of the bottom of it's cut off" (scene bottom clipped); "his legs are cut off" (actor feet below
frame). Root cause is elements placed outside the 1920x1080 safe area.
- Find where scene headline/label text is positioned (likely src/blueprint_presets.py build_scene_stage
  text_zone handling + the env text_zone y values in src/environments.py, and the label render in
  remotion/src/cutaway/GenericBlueprintRenderer.tsx or Label component). Ensure headline text top edge
  sits at LEAST ~64px below the frame top and never clips: clamp text_zone y to a top safe margin and
  make the label box account for its own height/wrap so ascenders are not cut.
- Ensure actor slots and set_props stay fully inside the frame: actor feet (slot y + scaled height)
  must be <= 1080 - bottom_safe (~48px). Add a clamp in build_scene_stage so any slot/set_prop whose
  rendered extent would exceed the frame is nudged up / scaled to fit. Do NOT distort; just keep in-frame.
- Add/extend a test asserting: for every code+generated env, each slot center y and each set_prop y is
  within [safe_top, 1080-safe_bottom], and text_zone is within the top safe band.

## STEP 2 — DECLUTTER AUTHORED ENV SET-DRESSING (classroom worst)
Owner on the classroom open: "super super cluttered", "random stuff on the ground", "a little blue box
... don't know what it is", "box over top of the carpet", "some random lines flowing through the screen",
"something above the teacher's head ... super cluttered", "piece of paper or something on the wall",
"something ... with a rectangle and a circle on top", "random squares on the floor", "these don't look
like any assets I know". Also "random gray boxes on the scene" (~6:03) and "black box on the ground"
the actor stands on in another scene.
- In src/environments.py, STRIP the noisy AUTHORED decorative midground/foreground primitives (stray
  lines, small boxes/rectangles, paper-on-wall marks, rectangle+circle blobs, floor squares, gray
  boxes, the dark pad/box under actors) from the code environments - ESPECIALLY classroom, plus any env
  that adds little unexplained shapes. KEEP: the backdrop wall band, one floor line, the real generated
  set_props, and a clean wall feature (e.g. classroom whiteboard) only if it reads clearly.
- The goal: each scene = clean cream wall + floor + a few RECOGNIZABLE set_props + actors. No mystery
  primitives. When unsure whether a shape reads as a real object, REMOVE it.
- Do not remove generated set_props or slots. Re-run the env contract + scene tests.

## STEP 3 — SCENE-SPECIFIC FIXES
- SPACE (owner liked rocket+telescope, keep them): "the planets are like stacked on top of each other.
  There should be separated." Adjust the space env set_prop positions so planets/ringed_planet do not
  overlap (space them horizontally), and make sure nothing in space sits below the frame (ties to STEP 1).
- LIBRARY (owner: "I can tell this is a library, looks pretty good" BUT): "there's background shelves
  without any books on them, which they should be filled in", "I don't know why there's shelves in the
  foreground" (remove redundant foreground shelf), "wrong kind of ladder". For now: remove the
  foreground duplicate shelf and ensure background bookshelves use the generated `bookshelf` prop (which
  has books) rather than an empty authored shelf. The ladder + any book-fill that needs a new/regen prop:
  LEAVE A NOTE for Claude (Claude regenerates props with the LLM; you cannot).
- Anywhere an actor "stands on a black box": remove that box (part of STEP 2 declutter).

NOTE for Claude (prop regen needed, network - Codex cannot): (a) globe has "weird thick lines on the
outside" - regen globe with cleaner outline; (b) library_ladder is "the wrong kind of ladder" - regen as
a tall rolling library ladder; (c) confirm bookshelf prop shows filled books. When done, list every env
Claude must render-proof (at minimum: classroom, library, space, plus any env you decluttered).
