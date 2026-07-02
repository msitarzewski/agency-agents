# Agent Identity Glyphs

This directory proposes a lightweight identity layer for the Agency Agents
roster. Each source agent receives:

- a stable display name for avatar-style UI use
- a role glyph classification
- a lightweight fictional persona
- deterministic pixel-glyph avatar metadata

Generated PNG avatars are intentionally not committed. Run the generator to
create them locally:

```bash
node scripts/generate-agent-glyphs.mjs
```

By default, generated images are written to `.cache/agent-glyphs/`, which is
already ignored by this repository.

## Files

- `glyph-v3.json` maps every agent source file to its identity metadata,
  including agent type, specialty, display name, generated avatar path, and
  persona fields.
- `scripts/generate-agent-glyphs.mjs` renders 128x128 transparent PNG avatars
  and a contact sheet from the manifest.

## Persona Fields

Each agent entry includes a `persona` object with:

- `background`: short professional background for identity cards
- `memory`: a grounded work or life memory
- `hobbies`: three ordinary interests
- `selfIntroduction`: one first-person profile sentence

## Design Intent

The glyphs are compact 16x16 pixel identities designed for sidebars, pickers,
and agent rosters. They use:

- division colors from `divisions.json`
- division-specific silhouettes
- role-specific badge marks
- deterministic hash variation per agent

The visual system is original and avoids copying third-party product marks.
