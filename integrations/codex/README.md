# Codex Integration

Converts all Agency agents into Codex skills.

Each converted skill includes:

- `SKILL.md`
- `agents/openai.yaml`

Conversion output is written to:

```text
integrations/codex/
  AGENTS.md
  skills/
    frontend-developer/
      SKILL.md
      agents/openai.yaml
    backend-architect/
      SKILL.md
      agents/openai.yaml
    ...
```

## Chinese Description Support

Codex integration follows a simple rule: keep identifiers stable, but allow
human-readable description fields to use Chinese when needed.

Identifier layer (keep English / slug-friendly):

- `name`
- the slug derived from `name`
- the skill directory name (for example `frontend-developer`)
- the installation target directory name

Description layer (Chinese is allowed):

- `description`
- `vibe`
- the `SKILL.md` body
- description fields in `agents/openai.yaml` such as `short_description`

Why: the converter depends on `slugify(name)` to generate directories and
install paths. If `name` is changed to Chinese, the slug may become invalid or
empty, which would break directory naming and installation stability.
`./scripts/convert.sh --tool codex` fails fast in that case, so keep Chinese
content in `description`, `vibe`, and the body instead.

### Recommended Pattern

```yaml
name: Frontend Developer
description: Frontend specialist focused on modern web apps, React/Vue, and performance optimization
vibe: Detail-oriented, maintainability-focused, and accessibility-aware
```

### Not Recommended

```yaml
name: Frontend Specialist CN
description: Responsible for frontend architecture and implementation
```

Note: changing `name` away from a stable English slug-friendly value can break
slug generation and installation paths. Put localized content in `description`,
`vibe`, and the body instead.

## Convert

```bash
./scripts/convert.sh --tool codex
```

## Install

Codex is installed project-scoped to `./.codex/skills/`, matching the repo's
other project-local integrations.

```bash
# Project-scoped
./scripts/install.sh --tool codex
```

## Notes

- `integrations/codex/AGENTS.md` is generated as an index and usage guide.
- The installer does not copy `AGENTS.md` by default, so it will not overwrite
  an existing project-level `AGENTS.md`.
- Codex installation currently installs the full skill set (no agent filter).
- Codex follows the same project-scoped install pattern as Cursor, OpenCode,
  Aider, Windsurf, and Qwen in this repository.
- UTF-8 Chinese content is written to `SKILL.md` and `agents/openai.yaml`
  as-is, with no extra transcoding step.
