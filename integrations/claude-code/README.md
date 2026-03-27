# Claude Code Integration

The Agency was built for Claude Code. No conversion needed — agents work
natively with the existing `.md` + YAML frontmatter format.

## Install

```bash
# Copy all agents to your Claude Code agents directory
./scripts/install.sh --tool claude-code

# Or manually copy a category
cp engineering/*.md ~/.claude/agents/
```

## Activate an Agent

In any Claude Code session, reference an agent by name:

```
Activate Frontend Developer and help me build a React component.
```

```
Use the Reality Checker agent to verify this feature is production-ready.
```

## Agent Directory

Agents are organized into divisions. See the [main README](../../README.md) for
the full current roster.

---

## Skills (Lightweight Alternative)

Skills are token-efficient task instructions — 20–50 lines vs 100–400 for agents.
Use them when you want focused, one-shot execution without loading a full persona.

```bash
# Install all skills to Claude Code commands directory
cp -r skills/engineering skills/product skills/content \
      skills/sales skills/testing skills/design \
      ~/.claude/commands/

# Or install selectively
cp skills/engineering/code-review.md ~/.claude/commands/
```

Invoke with a slash command:

```
/code-review
/debug
/architect
/prd
/sprint-plan
/outreach
```

### Agents vs Skills

Use **agents** when you want Claude to embody a specialist for a whole session — personality, workflow, and domain depth loaded upfront.

Use **skills** when you want a precise, repeatable action — review this code, write this PRD, plan this sprint — without the token overhead of a full persona.

See [`skills/README.md`](../../skills/README.md) for the full skill catalog and file format.
