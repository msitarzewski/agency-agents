# Command Code Integration

[Command Code](https://commandcode.ai) is a coding agent (a Claude Code–style
CLI) that discovers **Agent Skills** from `~/.commandcode/skills/`. Each agency
agent is rendered as a standalone skill: a directory named `agency-<slug>/`
containing a `SKILL.md` with `name` and `description` frontmatter and the agent
persona as the instruction body.

This is the same `SKILL.md` format used by the Antigravity and Osaurus
integrations (the shared `skill-md` renderer), so the generated files are
byte-identical to those tools' output.

The generated files come from `scripts/convert.sh --tool command-code`, which
writes one directory per agency agent into `integrations/command-code/`. Those
generated files are not committed (see `.gitignore`); regenerate them locally.

## Generate

From the repository root:

```bash
./scripts/convert.sh --tool command-code
```

## Install

```bash
/path/to/agency-agents/scripts/install.sh --tool command-code
```

Skills install to `~/.commandcode/skills/agency-<slug>/SKILL.md` (user scope) —
the directory Command Code reads skills from. Use `--division` / `--agent` to
install a subset, or set `COMMAND_CODE_SKILLS_DIR` to override the destination.

Restart your Command Code session (or run `commandcode skills` to inspect) so
the new skills are discovered.

## Regenerate

After modifying source agents:

```bash
./scripts/convert.sh --tool command-code
./scripts/install.sh --tool command-code
```

## Troubleshooting

### Command Code not detected

Make sure `commandcode` is in your PATH, or that `~/.commandcode/` already
exists:

```bash
which commandcode
commandcode --version
```

### Integration files not generated

Generate the Command Code skills before installing:

```bash
./scripts/convert.sh --tool command-code
```
