---
name: video-design
description: Visual design for videos - colour by act, type scale, chart and layout rules for 16:9 and 9:16 scenes, a design.md handoff that any design skill can fill, and a contact-sheet critique of the render. Use when designing or refining how a video looks (title cards, data scenes, slides, a whole video's palette), when a scene looks generic or busy, when choosing colours for a video, or when /design or /scene-review asks for visual work. Works on its own with a brand, or takes direction from a design source such as taste-skill, Anthropic's frontend-design, or the user's own design skill.
---

# Video design

A web design skill knows pages: scrolling, hover states, a nav bar. A video has none of that. It has
scenes the viewer can't pause on, a narration that sets the pace, a phone in someone's hand or a
projector at the back of a room. This skill is the toolkit's video layer: it takes a design direction
from wherever it comes from and turns it into scenes, then checks the render the way a juror would.

## Three layers

```
design source (optional, the user's choice)  →  design.md (the handoff)  →  video-design (this skill)  →  qc.py + critique
taste-skill, frontend-design, a team's own        palette, type, acts,        fields per act, one data        layout, contrast,
design skill, a brand guide                       rules on/off                accent, type steps, motion      stills, contact sheet
```

- **The design source** gives the direction: a palette, a typeface, an idea. Any skill that can do that
  works, and none is required: with ours (the default), this skill writes `design.md` itself from an act
  palette and the brand. Plug in your own design skill, or use ours. The project
  records its choice in `project.json` (`design.source`). See `sources.md`.
- **`design.md`** lives in the project. It is the contract: what the source decided, mapped onto the
  video's acts, plus any house rule turned off and why. A different source means a different
  `design.md`, not different code. See `handoff.md`.
- **This skill** applies it with the rules below, which hold whatever the source says, because they
  come from how video is watched rather than from taste.

## Rules for video

**Colour follows the story.**
- Two or three fields at most, and a field changes only when the narrative does (a new act, not a new
  scene). A colour that changes every scene means nothing; one that changes at the turn tells the
  viewer something turned. Write the acts down first (`handoff.md`), then give each act its field.
- Neighbouring fields differ in **lightness**, not only hue: light, mid, dark. Two fields of the same
  lightness (orange and sky blue) flicker at the cut, and even ffmpeg's cut detector can't see the
  change.
- Fields meet with a hard cut. Content can fade out and in; the ground does not cross-fade.
- **One data accent.** The brand colour goes on the thing the narration is talking about (the bar it
  names, the line, the number) and nowhere else. Everything else is ink or one neutral step. Never a
  tint of the ground (45% black over lime renders as olive, a colour nobody chose).
- Text on a coloured field is the field's ink at full strength, or at 70-80% for secondary lines if it
  still passes contrast. Grey text on colour reads as dirt.

**Type.**
- Five sizes per video, decided once. At 1080p: display 200-260, figure 112-132, title 64-72,
  label 32-36, note 28. The phone floor is 28px at 1080p (`qc.py --layout` checks 2.6% of the short side).
- One family, two weights at most. Tracking -0.03 to -0.05em on display sizes, leading 0.9-1.0.
- A title or statement is two lines at most, broken by hand at the phrase (`<br />`), never left to
  wrap. Count it: ~32 characters a line at display size on 1920px. An orphan word on a third line is
  the most visible tell there is.
- Numbers in tabular figures, so a counting number doesn't jitter.

**Layout.**
- One left edge for every title in the video (the same x in every scene); charts and figures may run
  wider, but headings never move.
- One dominant thing per scene: the chart, the figure, or the statement. A big number and a chart can
  share a scene only when the number is what the chart adds up to.
- No row of identical tiles (four black boxes for four steps). Use one shape with stops on it, a
  sentence, or a sequence that reveals on the narration.
- No gradients, glows, drop shadows on things at rest, glass panels or decorative shapes. A flat field,
  the product itself, a real picture, or a ground drawn from the subject (below).
- Footnotes and sources: one line, at the note size, at the bottom left. A scene that needs three
  lines of notes needs a sentence of narration instead.

**A ground from the subject.** A flat field is the default and often right. When it reads dull, don't decorate
it: draw the subject's own structure on it. Ask what shape the thing already has: a calendar has a week grid, a
song a beat grid or staff, code a line-number gutter, a map its contours, a chat its message column, a
spreadsheet its cells. That shape, and nothing invented, becomes the ground.
- Hairlines in the field's ink at 10-16% (a little less on dark fields). It should read on a phone and
  disappear behind the type; if a viewer notices the lines before the words, halve them.
- One motif for the whole video, the same on every type scene. Scenes with the product or a chart get no
  ground: they are already the picture.
- Things on the ground use the subject's own vocabulary (a calendar's event cards, a chat's bubbles), as
  outlines in the ink, and land on the words that name them (`cue()`). They sit above and below the type,
  never under its lines.
- It can carry a turn: fill it while the narration lists, empty it on the question. That's the difference
  between texture and an idea.
- Record it in `design.md` under "Ground". Never noise, stock imagery, blobs or a generated background; those
  are the decoration this replaces.

**Charts** (`lib/components/DataChart.tsx`).
- Flat area fill at 15% or less (`area="flat"`), square columns (`radius={0}`), no legend on a single
  series, 3-7 gridlines or none.
- The accent lands on the narrated bar or line on its word (`highlightAt` / `growAt` from `cue()`); a
  second group, if any, in ink or white, never a second hue.
- Every number on screen comes from the data file, and every number the narration says is checked
  against it at build time (see `examples/data-chart-stars` and the `check()` pattern).

**Transitions.** An act change is a hard cut, or `wipe()` from `@remotion/transitions` when a moving edge helps;
never a cross-fade between fields. When one scene shows the same thing again in a new way (the same chart in
another design, a screen after the fix), turn it in place with `PageTurns` (`lib/components`), each turn on the
word that names the new page. Effect transitions (`lib/transitions`: glitch, light leak, zoom blur) are a brand
choice, not a default; record one under "Rules turned off" in `design.md`.

**Motion** belongs to `.claude/skills/remotion/motion-craft.md`: timing in frames, read time, and the
defaults that look generated. Each change on screen lands on the word that names it (`cue()`), so a
held scene always has a next action, which is what `qc.py --render`'s still-stretch check looks for.

## Workflow

1. **Acts.** Write the video's acts (two to four) and which scenes each holds. This is the most
   important design decision and it is made in words.
2. **Direction.** Use the project's design source if `project.json` names one; otherwise offer the
   installed ones (`sources.md`), or use ours: an act palette from `palettes.md` with the brand.
3. **`design.md`.** Fill it from the source's direction (`handoff.md`): a field per act, ink, the one
   accent, the five type steps, the ground (flat, or the subject's own shape), rules turned off with a reason.
4. **Build** the scenes to it.
5. **Check.** `uv run tools/qc.py --project <p> --layout` and `--render out/video.mp4`.
6. **Look.** `uv run tools/contact_sheet.py out/video.mp4` tiles one settled frame per scene. Critique
   it with `critique.md`, fix the top three, render, look again. Three rounds at most.

## Files

| File | Read it when |
| --- | --- |
| `handoff.md` | Writing or reading `design.md`: the format, and a worked example. |
| `sources.md` | Choosing a design source, plugging in another, or listing one for others. |
| `critique.md` | Reviewing a render from its contact sheet: the passes, the score, the caps. |
| `palettes.md` | Act palettes that already work on video, mapped to roles, with their sources. |

Parts of these rules (colour fields as chapters, lightness between neighbours, one accent, two-line
headlines, five sizes, the critique's score and caps) are adapted for video from
[taste-skill](https://github.com/Leonxlnx/taste-skill) by Leonxlnx (MIT). See `sources.md`.
