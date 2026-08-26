# Designer Skills Import Notes

## Source
- Local snapshot import from claude code designer-skills-main on 2026-04-28.

## Assumptions
- Claude marketplace packaging metadata is treated as informational only.
- Workspace remains .cursor-local (no .cursor-plugin packaging in this phase).
- Imported command semantics are preserved, with namespaced command IDs and explicit skill-path references for compatibility.

## Compatibility adaptations
- Commands renamed to <plugin>-<command> to avoid collisions.
- Command text updated to point to .cursor/skills/<plugin>/<skill>/SKILL.md where skill IDs were previously ambiguous.
- Migration is additive phase-1; no command/skill removals performed.

## Known unknowns
- Upstream sync policy is not yet automated; this import is a local snapshot.
- Some generic slash-command follow-up prompts in source content were remapped heuristically to namespaced command names.
