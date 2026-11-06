# Critique from a contact sheet

`qc.py` measures what can be measured: contrast, text size, overflow, held stills, loudness. It can't
say whether the video is any good. For that, look at it the way a juror looks at a page: every scene
at once, at rest, and judge only what's in the pictures.

```bash
uv run tools/contact_sheet.py out/video.mp4              # one settled frame per scene -> out/video.sheet.png
uv run tools/contact_sheet.py out/video.mp4 --keep-frames   # also each frame on its own, to look closer
```

## The passes

Make each pass on its own.

1. **One second.** Glance at the sheet and look away. What did you see? One answer (a colour story, a
   number, a shape). "Lots of charts" means nothing leads.
2. **The acts.** Can you see where the story turns from the colours alone? Count the field changes and
   compare them with the acts in `design.md`. A change without a turn, or a turn without a change, is a
   finding.
3. **Lightness.** Squint. Each neighbouring pair should differ clearly in lightness. Two neighbours of
   the same lightness flicker at the cut.
4. **The accent.** Point at the brand colour in each frame. It should be on one thing, the thing being
   said. Three places, or a chart with two hues, means the accent stopped meaning "here".
5. **Off-palette colours.** Any colour you didn't choose: a tint of the ground, a muddy mix, a default
   blue. Usually unhighlighted bars or a semi-transparent fill.
6. **Edges.** Do all titles start at the same x? Count the distinct left edges across the sheet.
7. **Type.** Count the sizes (five is the ceiling). Any title on three lines, any orphan word, any
   label under 28px at 1080p?
8. **One dominant thing.** In each frame, is there one thing to look at? A frame of equal small parts
   has no hierarchy.
9. **Sameness.** One word per scene's layout (statement, line chart, bars, figure + bar, ...). The same
   word three times in a row is the template showing; vary the composition, not the colour.
10. **Ground.** If the fields carry a pattern, is it the subject's own shape (`SKILL.md`, "A ground from the
    subject") and quiet enough that the type reads first? Does anything on it sit under a line of type? A
    pattern that could belong to any video is decoration: flat is better.
11. **Tells.** Rows of identical tiles, gradients, glows, shadows at rest, eyebrow labels above titles,
    monospace labels, 01/02/03 numbering.
12. **Phone.** At the size of a phone (shrink the sheet to a third), can every title and figure still be
    read? Can the chart's point be seen without its labels?
13. **Substance.** Does each frame carry what its narration claims, with the number visible? An empty
    frame waiting for the narration is a hole, not a rest.

## The score

Four criteria, 1-10, weighted: **design 40%** (composition, type, colour), **clarity 30%** (can the
point of each scene be read in the time it's on screen, on a phone), **idea 20%** (is there a visual
idea specific to this subject, carried through), **content 10%** (are the words and numbers specific
and true).

`overall = 0.4·design + 0.3·clarity + 0.2·idea + 0.1·content`

Real award-level work lands around 7.5-8. If your first score for your own render is 9, score it again
as someone who didn't make it.

**Caps** (they override the arithmetic):
- A title or statement on three lines, a row of identical tiles, a gradient or glow, a shadow at rest,
  or an eyebrow label in any frame: overall at most **6.5**.
- Colour that changes without a narrative turn (a field per scene): design at most **6.5**.
- Text under 28px at 1080p that the viewer needs, or any `qc.py --layout` contrast warning on it:
  clarity at most **6**.
- A `qc.py --render` still stretch nobody chose: clarity at most **7**.
- A number on screen or in the narration that the data doesn't support: content at most **4**, and fix
  it before anything else.

## Writing it down

```
ROUND n — <video>, <date>
Seen in one second: …
Acts vs fields: …
Layout words: intro=… / cards=… / …
Scores: design _ · clarity _ · idea _ · content _ → overall _._ (caps: …)
Top three problems, most visible first, each with the frame it shows in and the fix:
1. …
2. …
3. …
```

Fix in this order: anything untrue, then the acts and colour, then hierarchy, then type, then detail.
Render, make a new sheet, look again. Three rounds at most; stop when a round finds nothing above
detail level.

Adapted for video from taste-skill's `references/critique.md` (MIT, see `sources.md`).
