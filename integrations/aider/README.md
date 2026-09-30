# Aider Integration

`CONVENTIONS.md` is the roster index: every agent's name, what it is for, its
division, and the path to its full instructions.

## Why an index and not the agents

Aider keeps a conventions file in context for the whole session — that is the
point of the file. The 279 agent bodies together are about 3.8 million
characters, roughly a million tokens, so a conventions file holding all of them
does not fit in any model and costs a fortune in the attempt.

The index is about 97,000 characters (~24k tokens). Load it read-only so aider
marks it cacheable, and pull in a single agent's full instructions when you
actually need them.

## Install

```bash
# Run from your project root
cd /your/project
/path/to/agency-agents/scripts/install.sh --tool aider
```

## Use an agent

Naming the agent is usually enough — its description is already in context:

```
Use the Frontend Developer agent to refactor this component.
```

When you want the agent's full instructions, read its file into the session.
The index gives you the path:

```
/read-only /path/to/agency-agents/engineering/engineering-frontend-developer.md
```

## Manual usage

```bash
aider --read CONVENTIONS.md
```

`--read` marks the file read-only and lets aider cache it when prompt caching
is enabled, so the index is not re-sent on every turn.

## Regenerate

```bash
./scripts/convert.sh --tool aider
```
