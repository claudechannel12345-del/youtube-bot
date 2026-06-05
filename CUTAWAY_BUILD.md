# Cutaway Engine - Autonomous Build Log (2026-06-04)

Owner is away for a few hours. Goal: a full ~8-10 min GPS video in the new clean-flat
cutaway style, voiced via CI, **uploaded UNLISTED** for review. If incomplete, this file
documents exactly what's polished vs rough.

## Locked decisions
- Art: CLEAN FLAT / LIGHT. bg #F7F4EC, ink #1E1E24, coral accent #FF5A3C. Bold geometric,
  thick outlines. **v3 style = simple (old) detail level + new sharpness** (miter joins,
  tighter radii, outlined windows, grounding shadows).
- No recurring character. Narrator = dry & witty. Lane = anything interesting.
- Captions = OPTION C: only sparse styled coral key-phrases burned in as design; full
  sentences shipped as an uploaded SRT for toggleable YouTube CC. (No always-on subtitle bar.)
- Codex does the mass coding; Claude specs/reviews/renders.

## Architecture of record
`.codex_cutaway_arch.txt` (Codex co-design). Brief: `.codex_cutaway_brief.txt`.

## Plan / status
- [x] Style proof (GPS cold-open, clean-flat) - rendered, owner approved the look
- [x] Style v3 - revert to simple detail, keep sharpness (remotion/src/flat/*)
- [x] PKG1 Contracts - cutaway_vocab.py + remotion/src/cutaway/types.ts + script_generator beats (Codex) - DONE, tsc+py verified
- [x] PKG2 Cutaway Remotion engine + scene families (Codex) - DONE (1st dispatch hung on stdin; 2nd ok)
- [x] PKG3 director.py (rules-first) + local props builder (Claude, hand-written) - DONE
- [x] Claude review+fix pass on engine renders (I can see output, Codex can't): fixed (1) BLANK FRAMES
      (director now tiles beats to cover whole section - gaps were rendering blank), (2) HEADLINE TEXT
      OVERLAP (anchor 'headline' was missing -> defaulted to dead-center over assets; asset-bearing beats
      now use small bottom labels + added missing anchors + capped sizes), (3) sparse scenes (asset scale
      0.9->1.05). Verified via before/after stills (cut_* vs fix_*).
- [x] Full SILENT local render (slice_stills/gps_full_silent.mp4) - DONE, owner reviewed, "looked really good"
- [x] Clock icon "tire" nit fixed (registry clock/atomic_clock now scale the whole group so the
      outline thins with size) - verified (slice_stills/clockfix_6800.png)
- [~] VOICED render + UNLISTED upload path (Codex mass-coding, be2ddnt4w): render_cutaway() in
      remotion_renderer, staticFile audio fix in CutawaySection, scripts/render_voiced.py (TTS ->
      director -> render -> upload), uploader UPLOAD_PRIVACY=unlisted, .github/workflows/cutaway_pilot.yml
      (workflow_dispatch). Spec: .codex_voiced_spec.txt. -> then trigger workflow, get unlisted link.
- [ ] Deepen script to ~8-10 min (currently ~4 min) - later
- [ ] minor: grounding shadow shows under floating satellites in space scenes - later
- [ ] PKG3 director.py (rules-first) + pipeline integration (Codex)
- [ ] Full dry-witty GPS script, hand-written w/ beats (Claude)
- [ ] Full SILENT local render of the whole video (proves visual pipeline end-to-end)
- [ ] Captions: SRT export (full) + burned coral key-phrases (design)
- [ ] Voiced render via CI + UNLISTED upload
- [ ] Writeup: polished vs rough

## Notes / decisions made solo (owner: change freely on return)
- Hand-writing the first script myself so the dry-witty voice is genuinely good and can seed
  the persona doc, rather than trusting the unproven auto-generator for the first artifact.
- Keeping grounding shadows (read as polish/depth, not "detail").

## Status log
- (in progress) v3 style set; dispatching Codex PKG1 (contracts).
