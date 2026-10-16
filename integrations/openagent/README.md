# OpenAgent Integration

[OpenAgent (5dive-ai/openagent)](https://github.com/5dive-ai/openagent) is an
open spec for an agent's identity: one YAML file with its name, role, face,
written voice and one line of behavior. `scripts/convert.sh --tool openagent`
writes one `<slug>.persona.yaml` per agency agent into `integrations/openagent/`.
The generated files are not committed (see `.gitignore`); regenerate them locally.

## What maps to what

| Agent frontmatter / body | Persona field |
|---|---|
| `name` | `name`, and `id` (slugified) |
| `description` | `role` |
| `vibe` (falls back to `description`) | `behavior` |
| `emoji` (falls back to 🤖) + `color` | `face.ref` + `face.anchor` |
| first 4 bullets of the Communication Style section | `voice.written.rules`, first example as `voice.written.sample` |
| source path | `ext.agency-agents.source` |

The spec has no emoji field, so the emoji stands in for the face image. A tool
that cannot load `face.ref` as an image falls back to a monogram. The agent's
full instructions are not copied: a persona is the identity, and the agent file
stays the source for everything else.

## Generate

From the repository root:

```bash
./scripts/convert.sh --tool openagent
```

## Install

```bash
./scripts/install.sh --tool openagent
```

Personas install to `~/.openagent/personas/<slug>.persona.yaml`. Use
`--division` / `--agent` to install a subset, or set `OPENAGENT_PERSONAS_DIR`
to override the destination.

## Use

The `openagent` CLI reads these files (Node 18+, no install needed with `npx`):

```bash
# check a file against the spec's JSON Schema
npx @5dive/openagent validate ~/.openagent/personas/frontend-developer.persona.yaml

# render it as a PNG card
npx @5dive/openagent card ~/.openagent/personas/frontend-developer.persona.yaml -o card.png

# put the identity into a harness's own persona file (Claude Code: ~/.claude/CLAUDE.md);
# --remove takes it out again
npx @5dive/openagent install --to=claude-code ~/.openagent/personas/frontend-developer.persona.yaml
```

`install --to=` also accepts `codex`, `hermes` and `openclaw`. It adds a marked
block above what the harness file already holds and never overwrites it.
