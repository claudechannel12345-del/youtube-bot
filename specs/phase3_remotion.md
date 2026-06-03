# Phase 3 spec — Remotion animation engine (retire Manim)

Goal: replace the Manim "animated slideshow" with a real motion-graphics engine. Remotion renders
the FULL video (visuals + sequenced narration audio) at 1920x1080 / 30fps. NO burned captions
(captions are uploaded as SRT from Phase 1). Style = "Cosmos Dark".

Stack present locally: Node v24, npm 11, npx. Use TypeScript (Remotion default). ASCII only in all
source (no smart quotes/em-dashes). Do NOT run a full render (needs assets + chromium) — instead
`npm install` then typecheck with `npx tsc --noEmit`.

## A. Project layout — create under `remotion/`
```
remotion/
  package.json          # deps: remotion, @remotion/cli, react, react-dom, typescript, @types/react, @types/react-dom; plus @remotion/google-fonts
  tsconfig.json
  remotion.config.ts    # video config (image format jpeg ok), overwrite true
  public/               # render-time assets (audio mp3s copied here) — gitkeep it
  src/
    index.ts            # registerRoot(Root)
    Root.tsx            # <Composition id="Episode" component={Episode} calculateMetadata=... />
    Episode.tsx         # top-level: maps sections -> sequenced <Section/>
    theme.ts            # Cosmos Dark constants + accent cycle + font
    types.ts            # Props + Section types
    Background.tsx      # animated drifting-particles bg (subtle, looping)
    Captions.tsx        # NOT NEEDED (no burned captions) — skip
    templates/
      TitleCard.tsx  StatReveal.tsx  Comparison.tsx  Timeline.tsx  Process.tsx
      Quote.tsx  ListReveal.tsx  MapHighlight.tsx  Diagram.tsx  ImageFocus.tsx
      index.ts          # TEMPLATES map: template name -> component
```

## B. Theme (`theme.ts`) — Cosmos Dark
- `BG = "#0D0D1A"`, `WHITE = "#FFFFFF"`, `MUTED = "#A9B0C7"`.
- `ACCENTS = ["#FFD166", "#06D6A0", "#EF476F", "#9B5DE5"]`; `accentFor(i) = ACCENTS[i % 4]`.
- Font: load a bold clean sans via `@remotion/google-fonts` (e.g. Inter or Montserrat). Export the
  loaded `fontFamily`. Headlines bold/extrabold.

## C. Props contract (`types.ts`) — what Python passes via --props
```ts
type Section = {
  durationInFrames: number;   // round(audioSeconds * fps)
  audioSrc: string;           // filename in public/, used via staticFile()
  template: string;           // one of the 10; fallback "title_card"
  key_phrase: string;         // ON-SCREEN HEADLINE
  on_screen: Record<string, any>; // template-specific (see Phase 2 vocab)
  accentIndex: number;        // for accent cycling
};
type EpisodeProps = { fps: number; width: number; height: number; sections: Section[]; };
```
- `Root.tsx` uses `calculateMetadata` to set fps (30), width (1920), height (1080), and
  `durationInFrames = sum(section.durationInFrames)` from input props. Provide small non-empty
  `defaultProps` so the Studio/typecheck works.

## D. Episode.tsx — sequencing
- Render `<Background/>` behind everything (absolute fill).
- For each section, accumulate an offset and render
  `<Sequence from={offset} durationInFrames={s.durationInFrames}>` containing:
  - `<Audio src={staticFile(s.audioSrc)} />`
  - the template component resolved from `TEMPLATES[s.template] ?? TitleCard`, passed
    `{section: s, accent: accentFor(s.accentIndex)}`.
- Each template receives the full section + accent and shows for the whole sequence.

## E. Template components — REAL motion (this is the whole point; no static slides)
Common: dark transparent surface, generous margins, headline (`key_phrase`) prominent. Use
`spring()` + `interpolate()` driven by `useCurrentFrame()`/`useVideoConfig()`. Stagger element
entrances. Add a gentle continuous drift/scale so nothing is frozen. Use the accent color.
- **TitleCard**: big headline springs up + fades; subtitle (on_screen.subtitle) staggers in below;
  accent underline draws across.
- **StatReveal**: large number (on_screen.stat) COUNT-UP animation from 0 to the value (parse number,
  keep suffix like % or x); label (on_screen.label) fades in; accent ring/arc draws around it.
- **Comparison**: two panels slide in from left/right (on_screen.left/right + *_label); a divider
  draws down the middle; slight alternating bob.
- **Timeline**: a horizontal line draws across; event dots (on_screen.events) pop in staggered with
  labels; the active dot pulses.
- **Process**: step boxes (on_screen.steps) appear in sequence with arrows drawing between them.
- **Quote**: large quotation marks scale in; quote text (on_screen.quote) reveals; attribution
  (on_screen.attribution) fades in last.
- **ListReveal**: bullet items (on_screen.items) reveal one-by-one with accent bullets sliding in.
- **MapHighlight**: a stylized abstract map/grid backdrop with a pulsing accent marker + place label
  (on_screen.place). (No external map API; a stylized vector/grid look is fine.)
- **Diagram**: a central shape with labeled callout lines to parts (on_screen.parts) drawing out
  staggered.
- **ImageFocus**: if a b-roll asset is provided later it would go here; for now render a stylized
  framed panel with kinetic `on_screen.overlay_text` over an accent gradient (no external image yet).
- `templates/index.ts` exports `TEMPLATES: Record<string, React.FC<{section, accent}>>` and is the
  single source the Episode uses; unknown template -> TitleCard.

## F. Python integration — `src/remotion_renderer.py` (NEW)
- `REMOTION_DIR = <repo>/remotion`, `FPS = 30`, `WIDTH = 1920`, `HEIGHT = 1080`.
- `render_video(sections, output_path) -> None` where `sections` is a list of dicts each with:
  `{"audio_path","duration","template","key_phrase","on_screen"}` (built by main.py).
  Steps:
  1. Ensure `remotion/public/` exists. For each section i: copy its `audio_path` to
     `remotion/public/audio_{i:03d}.mp3`; build a section prop with
     `durationInFrames = max(1, round(duration*FPS))`, `audioSrc = "audio_{i:03d}.mp3"`,
     template/key_phrase/on_screen, `accentIndex = i`.
  2. Write props `{fps,width,height,sections}` to `remotion/props.json`.
  3. Run: `npx remotion render src/index.ts Episode <abs output_path> --props=./props.json`
     with `cwd=REMOTION_DIR` (shell=False, check=True, capture stderr; raise RuntimeError with the
     tail of stderr on failure).
  4. Clean copied audio files from public/ afterward (leave .gitkeep).
- Use `subprocess.run([... "npx", "remotion", "render" ...])`. On Windows use `npx.cmd` if needed;
  detect via `shutil.which`. Keep it cross-platform (CI is Ubuntu).

## G. `src/main.py` — switch to Remotion, retire Manim
- Remove imports/use of `animation_generator` and `video_assembler`. Add
  `from remotion_renderer import render_video`.
- In the per-section loop: keep `synthesize_section` + cue collection + `get_audio_duration`.
  Build a `sections` list of `{"audio_path","duration","template","key_phrase","on_screen"}` pulling
  `template`/`on_screen` from the script section (default template "title_card", on_screen {}).
- Replace steps 3-4: after audio for all sections, call `render_video(sections, video_path)`.
  Keep building the SRT from CUES and uploading as before. Keep thumbnail + upload steps.
- Delete `src/animation_generator.py`. `src/video_assembler.py` is now unused — delete it too.
- Keep all the print/progress statements reasonable.

## H. Verify
- `cd remotion && npm install` (report success/failure).
- `cd remotion && npx tsc --noEmit` to typecheck all TSX (report PASS/FAIL + first errors).
- `py -m py_compile src/main.py src/remotion_renderer.py` (AST check is fine if pycache write denied).
- Do NOT run a full `remotion render` (needs real audio + chromium). Report a per-file changelog.
