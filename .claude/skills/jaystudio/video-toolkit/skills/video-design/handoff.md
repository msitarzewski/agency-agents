# design.md: the handoff

`design.md` sits in the project root. Whatever gave the direction (a design skill, a brand guide, the
user in conversation) is written down here in one shape, so the build, the critique and the next
session all read the same decisions. Changing source means rewriting this file, not the code.

Keep it short: a page. The values in it are what the scenes use; a scene that needs a colour or a size
that isn't here is a sign the file is missing a decision.

## Format

```markdown
# Design: <project>

Source: <design source and what it dealt, e.g. "taste-skill, direction colour-chapters, palette
orange-sky-lime (seed 1125998202), palette redrawn for brand"; or "ours: brand + bone + black">
Brand: <brands/<name>>

## Acts
| Act | Scenes | Says | Field |
| --- | --- | --- | --- |
| 1 Who | intro | <one line> | identity |
| 2 The work | cards, outcomes, notes, escalations | <one line> | record |
| 3 Getting better | better, models, cost | <one line> | lab |
| 4 Close | close | <one line> | identity |

## Fields
| Field | Ground | Ink | Data accent | Other data | Secondary ink |
| --- | --- | --- | --- | --- | --- |
| identity | #ea580c | #111111 | ink | — | ink 80% |
| record | #f4f1ea | #111111 | #ea580c | #d9d4c7 | ink 75% |
| lab | #161615 | #f4f1ea | #ea580c | #3b3a37 | ink 75% |

## Type
Family: <Inter>, weights <800 / 400>
Steps (1080p): display <220> · figure <112> · title <72> · label <36> · note <28>
Display tracking <-0.04em>, leading <0.95>

## Ground
<flat> or <the subject's shape, e.g. "week grid: 7 columns and hour rows, ink 16%, type scenes only; meetings
land as outlined event cards in the hook and empty on the question">

## Layout
Title edge: x = <120>
<anything else decided once: margins, where sources go>

## Rules turned off
- <rule> — <why, in one line> (or "none")
```

## How a source maps onto it

A design skill made for pages deals things a video doesn't have (a hero, a nav, buttons) and things it
does (a palette, a type system, an idea). Take the second kind and map it:

| A page skill deals | design.md gets |
| --- | --- |
| ground, ink, accent | the main field's ground and ink; the accent becomes the **data accent** |
| section fields / chapter colours | one field **per act** (not per scene); keep two or three, ordered by lightness |
| type system (face, weights, sizes) | family and weights as dealt; sizes mapped onto the five video steps |
| the idea ("X becomes Y") | the acts' "Says" column and the intro's composition |
| hero, sections, nav, buttons, scroll scenes | nothing: video has scenes, `motion-craft.md` handles motion |
| imagery rules | keep: real pictures and the product's own UI beat drawings and stock |

When the source's palette fights the brand or the subject, keep its **proportions** (one ground, one
ink, one accent) and take the colours from the brand, and say so under Source.

## Worked example: Lugh's work (2026-11)

The first version used one colour per scene (orange, sky, lime, black, in turn). The critique found the
colours meant nothing (sky held both "the work" and "testing models"), orange and sky flickered at the
cut, and 45% ink over each ground made olive and steel-blue bars. Rewritten by act:

- Acts: who Lugh is (intro) · the work (cards, outcomes, notes, escalations) · how it got better (the
  model switch, testing models, cost) · close. The notes and escalations scenes moved ahead of "how it
  got better" so the second act stays together.
- Fields: identity = Digital Samba orange, record = bone, lab = near-black: mid, light, dark, so every
  act change is a clear cut, and there are three in two minutes.
- Data accent: orange on bone and black; ink on orange. Other bars one neutral step per field.
- Type: five steps; the close broken by hand onto two lines; the intro's four tiles became one track.
