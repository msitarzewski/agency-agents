# Eclipse Digital Fork Strategy

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

Upstream is **`https://github.com/msitarzewski/agency-agents.git`**. This is the root of the
GitHub fork network (our repo's `source`), it is actively maintained, and it is where real
upstream changes land. An earlier draft of this file named `jnMetaCode/agency-agents`, but that
repo is itself a stale fork of `msitarzewski` and is not our upstream. The remote is configured in
this repo with pushes to upstream disabled so we cannot push to it by accident.

```bash
# origin   = our fork (default push target)
# upstream = msitarzewski/agency-agents (fetch only; push DISABLED)
git remote -v

# If a fresh clone is missing it, add it once:
git remote add upstream https://github.com/msitarzewski/agency-agents.git
git remote set-url --push upstream DISABLED
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
./scripts/install-house.sh
```

This wrapper defaults to Claude Code and only ever installs the house-team manifest. Do not use a
bare `./scripts/install.sh` during the pilot: with no `--agents-file` it installs every agent on
disk, including the uncustomized bench agents that carry no Eclipse context and no draft policy.

Evaluate whether the agents improve output before rolling out more widely or to client work.
