---
name: synthetic-ui-demo
description: Product demo and release-notes videos with no screen recording. Rebuild the app's screens as static React from its source code, then drive them in Remotion with a scripted cursor and camera (lib/components Stage + Cursor). Use when making a product walkthrough, feature demo, release-notes or changelog video for an app whose source you can read, or when a Playwright recording would be flaky, need test data, or go stale. Triggers include synthetic demo, rebuild the UI, release video, feature walkthrough, product demo from source, scripted cursor, camera zoom on UI, no screen recording.
---

# Synthetic UI Demos

Nothing is screen-recorded. Claude Code reads the product's repo, rebuilds only the screens a scene shows as static
React, and a scripted cursor and camera perform the flow in Remotion. Every click is a frame number, so a scene
re-renders identically, never needs a seeded account or a live environment, and is updated by editing code when the
product changes.

**Reference builds** (read them alongside this skill; both build without the product repos):

- `examples/ds-free-schedule-demo`: one 26s flow (schedule a call) with a narrator tile. The simplest complete case.
  Its `src/Demo.tsx` is a single timeline with every cursor keyframe, click and camera move.
- `examples/ds-release-649`: an 80s release-notes video, eight scenes across three apps. `templates/ds-release-notes` is the
  reusable shape of it (ships as release 650). `src/Release.tsx` sequences
  the scenes, `src/scenes/` has one file per release item, and `src/room/` and `src/ac/` are the screen kits.

## When to use this vs. Playwright

| Synthetic (this skill) | Playwright recording (`/record-demo`) |
|---|---|
| You can read the app's source | You only have the running app |
| Release notes and feature tours that get redone every release | One-off capture of real behaviour or real data |
| The flow needs data you don't have (a full call, other users, an admin view) | The real thing is easy to reach and looks right as is |
| Camera moves, exact click timing, re-renders after a voice change | Long, complex interactions that would be costly to rebuild |

## Building blocks (`lib/components`)

```tsx
import { Stage, typed, cursorAt, near } from '../../../../lib/components';

<Stage
  url="app.example.com/settings"             // address bar; host darker than path
  camera={CAMERA}                             // [{ f, z, x, y }] in canvas px, eased, clamped to the window
  path={PATH}                                 // [{ f, x, y }] cursor keyframes in canvas px
  clicks={CLICKS}                             // frames that squash the cursor and throw a ripple
  aiNote                                      // "People shown are AI-generated" (or pass your own text)
  canvasWidth={1440} canvasHeight={810}       // the defaults
>
  <SettingsScreen field={typed(frame, 'Q4 Product Review', 128)} />
</Stage>
```

- `Stage` draws browser chrome around a fixed-size app canvas, applies the camera, and puts the cursor on top at
  zIndex 100. At zoom 1 the window is `fit` (0.8625) of the frame width. Keyframes repeat a value to hold it.
- `Cursor` and `cursorAt` work on their own for a non-browser scene; `near(cursor, target)` drives hover states.
- Product-specific screen kits (theme, icons, layouts) stay in the project. They are not lib material.

## Method

### 1. Pull a visual spec from the app repo, with subagents

Send one subagent per app or area, in parallel, and have each return a compact spec rather than file dumps:

- **Theme:** palette, font stack, radii, spacing, shadows (from the theme file or CSS variables).
- **Strings:** the exact English locale strings for every label, menu item, dialog and toast the scene shows
  (`public/locales/en/*.json`, `src/i18n/locales/en/*`). Never paraphrase UI text.
- **Icons:** if the app uses an icon font, its icomoon/fontello `selection.json` holds each glyph's SVG paths. Extract
  the ones you need into a small JSON and render them as `<svg><path d=...>`. Otherwise copy the SVG components.
- **Layout and behaviour:** component tree for the screens shown, toolbar order, defaults, what each control does.

Read the default branch from the remote (`git show origin/main:path`, or `git fetch` then read `origin/<default>`).
**Local checkouts are often stale** and will give you last quarter's UI.

For release notes, trace each item to the commit and component that ship it first. That gives you the exact strings
and the default values to show.

### 2. Rebuild only what a scene shows, on a fixed canvas

- Lay every element out with absolute positions on a fixed canvas (1440x810 is a good default). Export the rects
  that matter as constants (`SAVE_BTN = { x, y, w, h }`), so click targets are arithmetic, not guesses.
- Build only what the camera sees. A panel that is never in shot can be a flat colour.
- Keep it static React: no state, no effects. Every visual change is a function of `frame`.
- Put the kit in its own folder (`src/ui/`, `src/room/`) with a `theme.ts` for constants.

### 3. Voice first, then put the timeline in frames

- Write one line per scene, **split at sentences** (one `.txt` per phrase), and generate the audio first
  (`voiceover.py --scene-dir ...`). Three takes and `tools/pick_takes.py` beat a single take plus `--max-wpm`: a
  clone copies its reference clip's pace and flatness, so if the lines come out rushed or monotone fix the clip with
  `tools/voice_prosody.py expand` rather than stretching the output (see "Clone Prosody" in CLAUDE.md). Read the
  measured durations, and `tools/captions.py` for word timings.
- Size each scene to its line plus a beat, and keep a header comment listing each line's start and length. That
  comment is the source of truth (see "Audio-Anchored Timelines" in CLAUDE.md).
- Everything is a frame constant at the top of the scene file: cursor keyframes, `CLICKS`, camera keyframes,
  UI state switches (`frame >= C.save` shows the dialog). Export the click frames so the parent can place click SFX.
- **Look the frames up from the narration, don't hand-set them.** `voice()` (`lib/components/cues.ts`; the
  ds-release-notes template has a copy) takes the scene's phrases with their `.captions.json` and start frames, and
  `cue('save')` returns the frame the word starts on. Anchor every action to the word it illustrates, with an offset,
  and every cursor and camera keyframe to those anchors:
  ```tsx
  import line06a from '../../public/audio/scenes/06a_link.captions.json';
  export const LINK_VOICE = voice([{ file: '06a_link', at: 10, captions: line06a }, ...]);
  const { cue } = LINK_VOICE;
  const C = { field: cue('before', { offset: -3 }), save: cue('save') };
  const PATH = [{ f: C.field - 6, ...field }, { f: C.save - 24, ...saveBtn }];
  ```
  Regenerate or re-time a phrase and the clicks, typing, cursor and camera follow it. A cue whose words are no
  longer said fails the bundle with the words that are. Options: `offset`, `edge: 'end'`, `after` (a frame, for a
  repeated word), `nth`, `in` (one phrase). The parent places the audio from `LINK_VOICE.lines`, so a phrase's start
  frame is written once. `templates/ds-release-notes/src/scenes/FreeCustomLink.tsx` is the worked example.

### 4. Split dense list lines at their pauses

A line that lists several things ("scheduling, contacts, recordings and transcripts") is too fast for one shot.
Split the audio at its pauses into phrase files (`07a`, `07b`, ...), give each phrase its own shot, and place each
phrase on its own beat. `ds-release-649`'s `moreVo` field does this.

### 5. Measure click targets from a contact sheet before the full render

A guessed coordinate is usually 20-50px off once the camera zooms. Render stills at every click frame and a few
frames before it, tile them, and check the cursor tip sits on the target:

```bash
i=1; for f in 46 78 122 212; do npx remotion still MyComp out/stills/s$i.png --frame=$f; i=$((i+1)); done
ffmpeg -start_number 1 -i out/stills/s%d.png -vf "scale=640:-1,tile=2x2" -frames:v 1 out/contact.png
```

Fix the constants, re-render the stills, and only then render the video.

### 6. Label AI-generated people on screen

Any person who is not real (FLUX.2 portraits in tiles, avatars, a narrator) gets a visible label: `aiNote` on the
`Stage`, or an "AI" badge on a narrator tile. Names, contacts and call data are invented too, so keep them plainly
fictional.

### 7. Render, then normalise

`tools/qc.py --project ...` before rendering, then `qc.py --render out/video.mp4 --fix` for -14 LUFS.
`qc.py --project ... --layout` checks the video's own text (captions, cards, the AI note) for size and contrast, and
lists the product UI's separately. `Stage` marks its window `data-qc="product"`; put the same attribute on any phone
or tablet mockup you build outside it, or its UI text is judged as the video's.

## Gotchas

- **Mono SVG logos render black.** A `logo_mono.svg` usually has black fills; on a dark background use
  `filter: brightness(0) invert(1)`.
- **Stale local branches.** Read `origin/<default>`, not whatever branch the local checkout is on.
- **`rsync --exclude src` also drops `node_modules/*/src`.** When copying a project or kit, anchor excludes to the
  transfer root with a leading slash: `--exclude /src`.
- **The camera clamps.** A camera centre near the canvas edge is pulled in so the window edge never shows past the
  frame. If a zoom lands somewhere unexpected, that is why; aim at a point further in.
- **Menus and dialogs must sit inside the canvas.** The canvas clips its children. Position a menu so it opens
  inward, as the real app does.
- **Hover states come from the cursor path.** Use `near(cursorAt(frame, PATH), target)` rather than a second set of
  frame constants, so moving a keyframe moves the hover with it.
- **A changed voice line moves everything after it.** In a cued scene the clicks, cursor and camera follow on their
  own, but the scene length and the later phrases' `at` still need checking. In a hand-set scene, re-measure every
  frame. Either way, update the header comment and the scene lengths, then re-check click stills. If a lip-synced narrator is driven by the assembled voice track, regenerate it too.
