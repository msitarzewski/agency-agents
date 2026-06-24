# Eclipse Digital — Fork Strategy

This repository is Eclipse Digital's internal fork of an upstream agent library. This document
records how we manage the fork so it stays useful instead of drifting with 200+ files of upstream
churn.

## Source of truth

**Our curated set is the source of truth, not upstream.** We froze the library down to a house
team that matches our services and customized those agents with Eclipse context. We do not bulk
merge upstream. We cherry-pick specific upstream commits when they add real value.

- House team manifest: `eclipse/eclipse-house-team.agents`
- House context (brand voice, tech stack, client standards, draft policy): `eclipse/house-standards.md`
- Repo-level guidance for Claude Code sessions: `CLAUDE.md`

## What we pruned

We removed everything that does not serve a US digital marketing agency:

- **Whole divisions:** `academic/`, `game-development/`, `gis/`, `spatial-computing/`
- **Non-US / China-market agents:** WeChat, Douyin, Weibo, Xiaohongshu, Baidu, Bilibili, Kuaishou,
  Zhihu, cross-border and China ecommerce, Korean and French market specialists, study-abroad, etc.
- **Out-of-scope / esoteric agents:** crypto and blockchain, embedded firmware, and off-vertical
  specialists (healthcare, legal, loan officer, real estate, hospitality, retail returns, ESG, etc.)

Agents that are plausibly useful but not yet customized stay on the **bench** (still on disk, still
installable). Promote a bench agent into the house team by customizing it and adding it to
`eclipse/eclipse-house-team.agents`.

When you delete an entire division directory, you must also update `divisions.json`, the
`AGENT_DIRS` arrays in `scripts/convert.sh` and `scripts/lint-agents.sh`, and the path filters in
`.github/workflows/lint-agents.yml`, or `scripts/check-divisions.sh` fails.

## Remotes

```bash
# origin = our fork (default push target)
git remote -v

# Add upstream once (confirm the URL; the i18n variants point to jnMetaCode/agency-agents)
git remote add upstream https://github.com/jnMetaCode/agency-agents.git
```

## Cherry-pick workflow (occasional)

```bash
git fetch upstream
git log --oneline upstream/main         # scan what changed upstream

# Pull in a specific improvement (e.g. a pipeline fix or a bench agent we want)
git checkout -b cherry/<short-name>
git cherry-pick <commit-sha>
# Resolve conflicts. Keep our Eclipse customizations; take upstream's logic.

# Re-run the guards before merging
bash scripts/lint-agents.sh <changed-files>
bash scripts/check-divisions.sh
bash scripts/check-tools.sh
bash scripts/check-agent-originality.sh <changed-files>
```

Prefer cherry-picking tooling and pipeline fixes (`scripts/`, CI) over wholesale agent updates.
Re-customizing a freshly pulled agent is cheap; untangling a 200-file merge is not.

## Draft and human-review policy

Everything these agents produce is a **draft**. A human Eclipse team member reviews anything
client-facing or anything that touches a production site before it ships. Agents do not publish,
deploy, or send. This is non-negotiable during the pilot and after.

## Pilot

We are piloting in **Claude Code** on internal, non-client work first. Install the house team with:

```bash
./scripts/install.sh --tool claude-code --agents-file eclipse/eclipse-house-team.agents
```

Evaluate whether the agents improve output before rolling out more widely or to client work.
