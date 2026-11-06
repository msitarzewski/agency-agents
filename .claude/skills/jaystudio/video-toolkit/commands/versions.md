---
description: Check dependency versions and toolkit updates
---

# Versions

Check for version mismatches in project dependencies and toolkit updates.

## Entry Point

On invocation, perform checks and present results:

### Step 1: Detect Context

```
1. Check if in a project directory (has package.json with Remotion)
2. Read _internal/toolkit-registry.json for toolkit version
3. Determine what checks to run
```

### Step 2: Run Checks

#### Toolkit-wide staleness (always)

```bash
uv run scripts/check_versions.py          # table; add --json when scripting
```

This is the source of truth for everything below the project-level check. It reports every
Remotion pin under `templates/`, `examples/`, `showcase/`, `tests/` against the latest npm
release (patches behind, age of the pin), flags caret ranges and projects whose pins disagree,
checks `uv.lock` against `pyproject.toml` plus outdated *direct* Python deps, and compares the
registry version with the latest GitHub release. Staleness alone is informational — bumps are
deliberate (see "Bump policy" below). Caret ranges and internal mismatches are defects.

It also checks that every pinned project is listed in `.github/dependabot.yml`. A project
missing there is skipped by the monthly grouped bump and drifts behind. When you add a new
Remotion template or example, add its directory to `dependabot.yml` in the same PR. CI runs
`check_versions.py --offline --remotion-only --strict` and fails on a gap.

#### Project Dependency Check (if in project)

```bash
# Run Remotion's built-in version checker
npx remotion versions
```

Parse output for:
- Version mismatches between @remotion/* packages
- Any packages on different versions

#### Toolkit Version Check

```
1. Read current version from _internal/toolkit-registry.json
2. Fetch latest from GitHub API:
   https://api.github.com/repos/digitalsamba/claude-code-video-toolkit/releases/latest
3. Compare versions
```

#### Bump policy

Templates pin exact Remotion versions for reproducibility (people clone at a tag). Being
N patches behind is expected. Bump on a driver — a needed feature/fix, starting a new project,
or a quarterly check — one template at a time, `sprint-review-v2` first, and only with the
render-baseline check green (`scripts/render-baseline.mjs`, see `tests/render-baseline/`).

### Step 3: Present Results

**All Good:**
```
Version Check

## Project: my-video

  Remotion packages: 4.0.387 (all aligned)

## Toolkit

  Remotion pins: 4.0.425 across 9 projects (92 patches behind latest 4.0.518, pinned 188d ago)
  Python: uv.lock in sync, 2 direct deps outdated (elevenlabs, boto3)
  Current: v0.18.0
  Latest:  v0.18.0

Everything consistent. Remotion is behind by policy — run a bump when there's a driver.
```

**Issues Found:**
```
Version Check

## Project: my-video

  Version mismatch detected:

  | Package | Version |
  |---------|---------|
  | remotion | 4.0.383 |
  | @remotion/cli | 4.0.383 |
  | @remotion/google-fonts | 4.0.387 |

  To fix: npx remotion upgrade

## Toolkit

  Current: v0.2.0
  Latest:  v0.3.0

  New in v0.3.0:
  - Added transitions library
  - New /design command
  - Frontend-design skill

  To upgrade:
  git pull origin main

Actions:
  → Fix Remotion versions: 'fix'
  → View toolkit changelog: 'changelog'
```

---

## Fix Flow

When user chooses to fix Remotion versions:

### Step 1: Update package.json

```
1. Read package.json
2. Find all @remotion/* and remotion packages
3. Determine target version (latest installed or latest available)
4. Update all to same pinned version (no ^ prefix)
```

### Step 2: Reinstall

```bash
rm -rf node_modules package-lock.json
npm install
```

### Step 3: Verify

```bash
npx remotion versions
```

### Step 4: Confirm

```
Fixed Remotion versions.

All packages now on: 4.0.387

Restart Remotion Studio to apply changes.
```

---

## Toolkit Upgrade Flow

When upgrading toolkit:

### Step 1: Check Git Status

```bash
git status --porcelain
```

If uncommitted changes:
```
You have uncommitted changes. Commit or stash before upgrading.

  Modified files:
  - project.json
  - src/components/slides/TitleSlide.tsx

Options:
  → Stash changes: 'stash'
  → Cancel: 'cancel'
```

### Step 2: Pull Updates

```bash
git pull origin main
```

### Step 3: Show Changelog

```
Toolkit updated to v0.3.0

Changes:
- Added lib/transitions/ with 7 custom transitions
- New /design command for visual refinement
- Frontend-design skill for distinctive aesthetics
- Bug fixes in /scene-review

See _internal/CHANGELOG.md for full details.

Restart Claude Code to load new skills and commands.
```

---

## Bump Toolkit Flow (`/versions --bump-toolkit [version]`)

Maintainer mode: move every pinned Remotion project to one version, with the render-baseline
A/B as the gate. Only run on a clean tree on a branch.

### Step 1: Pick the target

```bash
uv run scripts/check_versions.py --json      # → remotion.latest, current pins
```

Default to `remotion.latest` unless the user named a version. Confirm:

```
Bump Remotion 4.0.425 → 4.0.518 across 10 projects (templates, examples, showcase, tests)?
Runs: rewrite pins → refresh lockfiles → smoke-render frame 0 → render-baseline A/B.
```

### Step 2: Run the bump

```bash
git checkout -b deps/remotion-4.0.518
uv run scripts/bump_remotion.py 4.0.518 --smoke --summary /tmp/bump-summary.md
```

The script rewrites `remotion` / `@remotion/*` pins (exact), refreshes each lockfile, smoke-renders
frame 0 of each Remotion project's first composition, runs `scripts/render-baseline.mjs ab`, and
prints a markdown summary. Non-zero exit = something failed; read the table before going on.
For a cautious first pass use `--only templates/sprint-review-v2` (the test-bed template).

### Step 3: Review and open the PR

```bash
git diff --stat
git add -A && git commit -m "DEPS: bump Remotion 4.0.425 → 4.0.518 across templates, examples, showcase, tests"
gh pr create --title "DEPS: bump Remotion 4.0.425 → 4.0.518" --body-file /tmp/bump-summary.md
```

CI (`render-baseline.yml`) re-runs the A/B on Linux and comments the per-frame table. Any
differing frame fails the check by design — open the artifacts, look at the diff images, and
either accept (comment why on the PR) or hold the bump.

### Step 4: After merge

- Note the new pin in `_internal/CHANGELOG.md`.
- If frames differed and were accepted, record what changed and why in the PR — that is the
  calibration data for eventually relaxing the `--threshold`.

Dependabot (`.github/dependabot.yml`) opens the same kind of PR monthly for the `remotion`
group; it goes through the identical CI gate, so reviewing it is Step 3 without Step 2.

---

## Automatic Checks

Consider running version check automatically:

1. **On /video resume** - Check project before starting work
2. **Before render** - Warn if mismatches detected
3. **Weekly reminder** - Check for toolkit updates

These are suggestions for future enhancement.

---

## Version Sources

| Component | Version Source |
|-----------|----------------|
| Toolkit | `_internal/toolkit-registry.json` → `version` |
| Remotion | `node_modules/*/package.json` via `npx remotion versions` |
| Latest toolkit | GitHub Releases API |
| Latest Remotion | npm registry or `npx remotion upgrade --check` |

---

## Common Issues

### Remotion Version Mismatch

**Cause:** Using `^4.0.0` allows different minor versions to install independently.

**Prevention:** Pin exact versions in package.json:
```json
{
  "@remotion/cli": "4.0.387",
  "remotion": "4.0.387"
}
```

### Toolkit Out of Date

**Cause:** Haven't pulled from upstream recently.

**Check:**
```bash
git fetch origin
git log HEAD..origin/main --oneline
```

---

## Evolution

This command evolves through use. If something's awkward or missing:

**Local improvements:**
1. Say "improve this" → Claude captures in `_internal/BACKLOG.md`
2. Edit `.claude/commands/versions.md`
3. Share upstream → `gh pr create`

**Future ideas:**
- Check Node.js version compatibility
- Check Python tool dependencies
- Check ElevenLabs API version
- Automated weekly checks
