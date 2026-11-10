# Windsurf Integration

Each agent becomes one Windsurf workspace rule in `.windsurf/rules/<slug>.md`.
Rules are **project-scoped** — install them from your project root.

## Why one file per agent

Windsurf caps a workspace rule file at 12,000 characters and a
`global_rules.md` at 6,000, and drops whatever is past the limit. This
integration used to write the whole roster into a single `.windsurfrules`;
at 279 agents that file is about 3.9 million characters, so Cascade read the
header and part of the first agent and never saw the rest.

One file per agent fits inside the limit and matches how Windsurf expects
rules to be organised. Six percent of agents are long enough that their
instructions are trimmed at a section boundary; those files end with a pointer
to the full agent in this repo.

## Activation

Each rule carries `trigger: model_decision`, so only its `description` sits in
Cascade's system prompt. Cascade opens the full rule when the description looks
relevant to what you are doing. You can also name an agent directly:

```
Use the Frontend Developer agent to build this component.
```

The other activation modes Windsurf supports are `always_on`, `glob`, and
`manual`. `model_decision` is the right default for a roster this size —
`always_on` would put all 279 specialists in every prompt.

## Install

```bash
# Run from your project root
cd /your/project
/path/to/agency-agents/scripts/install.sh --tool windsurf
```

Installing the whole roster puts 279 descriptions in the system prompt. Most
projects want a subset:

```bash
./scripts/install.sh --tool windsurf --division engineering,testing
./scripts/install.sh --tool windsurf --agent frontend-developer,code-reviewer
```

Set `WINDSURF_RULES_DIR` to install somewhere other than `.windsurf/rules`.

### Upgrading from the single-file layout

Delete the old `.windsurfrules` from your project root. Windsurf still reads
it, and it is still over the limit.

## Regenerate

```bash
./scripts/convert.sh --tool windsurf
```
