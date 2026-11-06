# Design sources

**Plug in your own design skill, or use ours.** A design source is any skill, guide or person that decides
how something should look: the palette, the type, the idea. The toolkit depends on none of them. Its own
source, **ours**, is `video-design` itself (the act palettes in `palettes.md` with the project's brand), and
any installed design skill can take its place, because everything goes through the handoff (`design.md`).

## Choosing one for a project

1. If `project.json` has `design.source`, use it.
2. Otherwise offer, in this order:
   - **ours** (the toolkit's own, nothing to install);
   - each source in the registry's `designSources` that is installed in this session, the recommended one
     marked. A plugin skill shows up with its plugin's prefix, so match the registry's `skill` with or without
     it (`frontend-design` is installed as `example-skills:frontend-design` from Anthropic's plugin);
   - "another design skill": the user names one.

   Don't offer every skill whose description mentions design or brand. That sweeps in skills that aren't design
   sources, such as a brand-guidelines skill that applies another company's colours.
3. Record the choice in `project.json`:

   ```json
   { "design": { "source": "taste-skill", "file": "design.md" } }
   ```

   `source` is the registry key for a listed source (`ours`, `taste-skill`, `frontend-design`), so every session
   saves the same value for the same choice; for an unlisted skill it is the skill's name as invoked (e.g.
   `acme:house-style`). `"source": "ours"` means the toolkit's own: `video-design` picks an act palette from
   `palettes.md` and fills it with `brands/<name>/`.

Whatever the source, its output goes into `design.md` (`handoff.md`) before anything is built, and the
rules in `SKILL.md` still apply on top. When a source contradicts one (a gradient, a glow, a third
field colour), the video rule wins unless the brand requires it; write the exception under "Rules
turned off".

## Known sources

These are listed in the registry (`_internal/toolkit-registry.json`, `designSources`).

| Source | What it's good for | Install |
| --- | --- | --- |
| **taste-skill** (recommended plug-in) | Dealt directions and palettes from 247 studied sites, measured house rules, a juror's critique with caps. Its colour chapters, one-accent rule and critique translate well to video. MIT. | `/plugin marketplace add Leonxlnx/taste-skill` then `/plugin install taste-skill@taste-skill` ([repo](https://github.com/Leonxlnx/taste-skill)) |
| **frontend-design** (Anthropic) | General visual direction for interfaces: a bold aesthetic stance, type pairing. Written for web pages, so expect to turn down its effects (gradient meshes, glows) for video. | Anthropic's skills repo: [anthropics/skills](https://github.com/anthropics/skills) |
| **Ours** (the toolkit's own, the default) | `video-design`'s act palettes and rules, filled with `brands/<name>/brand.json`. | Nothing to install |
| **Your own** | A team design system, an agency's house style, a skill you wrote. | See below |

"Recommended" means it's the one we currently find gives the best results on video, not that the
toolkit needs it. It changes when something better turns up.

## Bringing your own

Any skill works if it can tell `video-design` five things, which is what `design.md` asks for: the
grounds (one per act, two or three), the ink on each, the one accent, the type family and weights, and
the rules it wants off. It doesn't need to know about Remotion, frames or narration.

To list a design source for other users, open an issue with:
- a link and a one-line description;
- its licence (it must allow use in videos people publish);
- the `design.md` it produced for `examples/data-chart-stars`, and that example's contact sheet
  rendered with it (`uv run tools/contact_sheet.py out/data-chart-stars.mp4`), so sources can be
  compared on the same video.

Listed sources go in the README's "Design sources" table and the registry. They are not copied into
the toolkit; users install them from their own repos.

## Credit

Parts of `video-design` are adapted from taste-skill (https://github.com/Leonxlnx/taste-skill),
Copyright (c) 2026 Leonxlnx, MIT License: the colour-fields-as-chapters idea, lightness between
neighbouring fields, the one-accent rule, the two-line headline and five-size limits, and the critique's
weighted score and caps. The palettes in `palettes.md` marked "taste" are from its library. The rest is
the toolkit's own, from making these videos.
