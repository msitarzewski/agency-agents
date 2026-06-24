# CLAUDE.md (Eclipse Digital fork)

This repository is Eclipse Digital's internal fork of an agent library. We have curated it down
to a **house team** of agents that match our services and customized them with Eclipse context.

## What to know before working here

- **Source of truth:** `eclipse/house-standards.md` holds our brand voice, tech stack, client
  standards, and the draft/review policy. Read it before producing any client-facing copy.
- **House team manifest:** `eclipse/eclipse-house-team.agents` lists the curated agents. Install
  with `./scripts/install.sh --tool claude-code --agents-file eclipse/eclipse-house-team.agents`.
- **Fork strategy:** see `eclipse/FORK.md`. Our curated set is the source of truth. We cherry-pick
  upstream changes selectively, we do not bulk-merge upstream.

## House rules (apply to all output)

- **No em-dashes.** Use commas, periods, parentheses, or colons. Do not use `—` or `–`.
- **Plain American English**, active voice, no hype/filler. US audiences and platforms by default.
- **WordPress runs on Wordify** managed hosting. Use staging + backup; never edit production
  directly. Hosting ops go through the Wordify MCP; project/task tracking goes through ClickUp MCP.
- **Everything is a draft.** A human reviews anything client-facing or anything touching a
  production site before it ships. Agents do not publish, deploy, or send.

## Working on the agent library itself

- Agent files are markdown with YAML frontmatter (`name`, `description`, `color` required).
- After editing or adding agents, run the guards before pushing:
  `bash scripts/lint-agents.sh <files>`, `bash scripts/check-divisions.sh`,
  `bash scripts/check-tools.sh`, `bash scripts/check-agent-originality.sh <files>`.
- New agents must stay under the 40% similarity threshold (`check-agent-originality.sh`). Write
  original content; do not clone an existing agent.
- If you delete an entire division directory, also update `divisions.json`, the `AGENT_DIRS`
  arrays in `scripts/convert.sh` and `scripts/lint-agents.sh`, and the path filters in
  `.github/workflows/lint-agents.yml`, or `check-divisions.sh` fails.
