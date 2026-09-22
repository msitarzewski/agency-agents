# SPEC — Marketplace restructure: sub-agents → skills (`commands/` default layout)

> **Superseded (source/dist split):** the shipped layout below now lives in a
> **generated dist published to the `plugins` branch** (see
> `PLUGIN-MARKETPLACE-SPEC.md` banner). This doc's generated output is no longer
> committed to `main`; `build-marketplace.py` emits `plugins/<division>/{skills,agents}/`
> copies of the kebab-case agent stems, CI validates a fresh build, and
> `scripts/publish-marketplace.sh` (or the publish workflow) force-publishes the
> result to `plugins`. Keep reading only as the historical decision record.

**Status:** Superseded (implemented via the branch-split; see note above)
**Date:** 2026-07-31
**Supersedes:** the component-layout decisions in `PLUGIN-MARKETPLACE-SPEC.md`, specifically the per-division `<division>/.claude-plugin/plugin.json` design and the explicit `agents` field
**Branch base:** `main` (feature already merged to fork + draft PR #750 → upstream)

---

## 0. TL;DR

- The shipped marketplace does not load a single agent: Claude Code (verified CLI **2.1.201** and latest **2.1.220**) **ignores the explicit `agents`/`commands`/`skills` path fields** in `plugin.json`. Only **default directories** (`agents/`, `commands/`, `skills/`) register components. `claude plugin validate` accepts the explicit fields (schema-valid), but the runtime registers nothing — confirmed via `claude plugin details` (0 components) and the user's Desktop/Cowork tests (agents unfindable, "0 Skills" row).
- **Fix: ship each division's specialists as *skills*, in a default `commands/` directory.** Proven empirically: real agent `.md` files (frontmatter untouched, Title-Case names intact) placed in `<plugin-root>/commands/` register as skills named by their **existing filenames** (e.g. `engineering-frontend-developer`), with no content edits.
- Skills are the right currency anyway: per Anthropic's plugin docs, **skills work in web chat, the Desktop Chat tab, and Cowork**, while **sub-agents run only in Cowork**. Our files define no `tools`/`model`, so nothing is lost by dropping agent semantics.
- Layout moves to a new top-level `plugins/<division>/` tree (default layout, no explicit component fields). `plugins` is added to `NON_DIVISION_DIRS` in `scripts/check-divisions.sh` — the documented extension point.
- The generated copies are **byte-identical to the source** files; `build-marketplace.py` generates them and CI drift-checks them, so the division folders stay the canonical single source of truth (same "generated but committed" exception already established for the manifests).

---

## 1. Why this restructure (evidence)

### 1.1 The explicit path fields do not register components

Installed and inspected with `claude plugin details` (the CLI's component-inventory command) on CLI **2.1.201** and **2.1.220**:

| `plugin.json` configuration | `claude plugin details` |
| --- | --- |
| `"agents": ["./code-reviewer.md"]` (file at plugin root) | Agents **(0)** |
| `"agents": ["./agents/code-reviewer.md"]` | Agents **(0)** |
| `"agents": ["./custom-agents/code-reviewer.md"]` | Agents **(0)** |
| `"agents": ["./engineering-frontend-developer.md", …]` (kebab-cased frontmatter names) | Agents **(0)** |
| `"commands": ["./engineering-frontend-developer.md", …]` (explicit field) | Skills **(0)** |
| no field + default `agents/` directory | Agents **(1)** ✓ |
| no field + default `commands/` directory (flat `.md`) | **Skills (1)** ✓ |
| no field + default `skills/<name>/SKILL.md` | Skills (1) ✓ |

Conclusion: explicit component-path fields are a runtime no-op in current Claude Code regardless of naming, path form, or file location. Only the default-directory scans load components. `claude plugin validate` accepts the explicit fields, so validation is not a reliable signal.

### 1.2 Real agent files register as skills, as-is

Copied real files `engineering-frontend-developer.md` and `engineering-code-reviewer.md` (frontmatter `name: Frontend Developer` / `Code Reviewer`, untouched) into a default `commands/` directory. Result: **Skills (2) — `engineering-code-reviewer`, `engineering-frontend-developer`**. Skill names derive from the **filename stems**, falling back to the filename when the frontmatter `name` is not kebab-case. No frontmatter edits required.

### 1.3 Skills are the right primitive for this content

- **Cross-surface**: Anthropic's plugin docs: "The skills bundled in a plugin work across all three [web chat, Desktop Chat tab, Cowork]. Hooks and sub-agents run only in Cowork." This directly fixes the reported failures (agents invisible in web chat, "0 Skills" in Desktop, ambiguous Cowork resolution).
- **No capability loss**: our files declare no `tools`, `model`, `permissionMode`; they are pure persona + workflow instruction documents. Sub-agent-only benefits (isolated context, summary returns) are not used today.
- **Discoverable**: the Desktop/web plugin UI lists skills (fixing the "0 Skills" row); `/`-picker and model auto-invocation both work.

---

## 2. Final directory layout

New files; existing source `.md` files stay put, untouched, single-sourced.

```text
plugins/<division>/                       # NEW × 17 — one per division (top-level, git-tracked)
  .claude-plugin/plugin.json              #   metadata only — NO component path fields
  commands/<filename>.md                  #   generated byte-identical copies of that division's agents
.claude-plugin/marketplace.json           # UPDATED — sources now ./plugins/<division>
scripts/build-marketplace.py              # UPDATED — emits the new layout, removes the old one
scripts/check-plugin-marketplace.sh       # UPDATED — new drift + structural checks
.github/workflows/check-plugin-marketplace.yml   # UPDATED — adds a registration smoke test
integrations/plugin-marketplace/README.md        # UPDATED — skills invocation + cross-surface docs
README.md  integrations/README.md  integrations/claude-code/README.md  CONTRIBUTING.md   # UPDATED wording
scripts/check-divisions.sh               # UPDATED — NON_DIVISION_DIRS += plugins (documented extension point)
```

**Removed** (the broken explicit-field design):

```text
<division>/.claude-plugin/plugin.json     # DELETED × 17
```

**Explicitly NOT changed:** `divisions.json`, `tools.json`, `scripts/convert.sh`, `scripts/install.sh`, `scripts/lint-agents.sh`, `scripts/check-runbooks.sh`, `.gitignore`, `.gitattributes`, all 270 source agent `.md` files.

### Plugin root semantics

For `plugins/engineering/`, the plugin root is `plugins/engineering/`. The default `commands/` scan picks up every flat `.md` in it as a skill. The plugin.json carries only identity metadata:

```json
{
  "name": "agency-engineering",
  "displayName": "Agency — Engineering",
  "description": "The Agency Engineering division: 58 specialist skills.",
  "author": {
    "name": "Agency Agents"
  }
}
```

No `agents`, `commands`, `skills`, `hooks`, `mcpServers`, or `lspServers` fields — the default-directory layout is the contract.

---

## 3. Full example `marketplace.json`

```json
{
  "name": "agency-agents",
  "description": "The Agency — 17 installable agent divisions for Claude Code, VS Code, and GitHub Copilot CLI",
  "owner": {
    "name": "Agency Agents"
  },
  "plugins": [
    { "name": "agency-academic", "source": "./plugins/academic", "description": "Academic division (6 specialist skills)" },
    { "name": "agency-design", "source": "./plugins/design", "description": "Design division (10 specialist skills)" },
    { "name": "agency-engineering", "source": "./plugins/engineering", "description": "Engineering division (58 specialist skills)" },
    { "name": "agency-finance", "source": "./plugins/finance", "description": "Finance division (5 specialist skills)" },
    { "name": "agency-game-development", "source": "./plugins/game-development", "description": "Game Development division (21 specialist skills)" },
    { "name": "agency-gis", "source": "./plugins/gis", "description": "GIS division (13 specialist skills)" },
    { "name": "agency-healthcare", "source": "./plugins/healthcare", "description": "Healthcare division (3 specialist skills)" },
    { "name": "agency-marketing", "source": "./plugins/marketing", "description": "Marketing division (36 specialist skills)" },
    { "name": "agency-paid-media", "source": "./plugins/paid-media", "description": "Paid Media division (7 specialist skills)" },
    { "name": "agency-product", "source": "./plugins/product", "description": "Product division (5 specialist skills)" },
    { "name": "agency-project-management", "source": "./plugins/project-management", "description": "Project Management division (7 specialist skills)" },
    { "name": "agency-sales", "source": "./plugins/sales", "description": "Sales division (9 specialist skills)" },
    { "name": "agency-security", "source": "./plugins/security", "description": "Security division (12 specialist skills)" },
    { "name": "agency-spatial-computing", "source": "./plugins/spatial-computing", "description": "Spatial Computing division (6 specialist skills)" },
    { "name": "agency-specialized", "source": "./plugins/specialized", "description": "Specialized division (57 specialist skills)" },
    { "name": "agency-support", "source": "./plugins/support", "description": "Support division (6 specialist skills)" },
    { "name": "agency-testing", "source": "./plugins/testing", "description": "Testing division (9 specialist skills)" }
  ]
}
```

`source` is relative to the marketplace root (`./plugins/<division>`); `version` stays omitted (git-commit-SHA versioning).

---

## 4. Example plugin trees

### 4.1 `plugins/finance/` (flat division)

```text
plugins/finance/
  .claude-plugin/plugin.json
  commands/
    finance-bookkeeper-controller.md
    finance-financial-analyst.md
    finance-fpa-analyst.md
    finance-investment-researcher.md
    finance-tax-strategist.md
```

Each `commands/*.md` is a **byte-identical copy** of `finance/<same filename>`. Skill names = filename stems.

### 4.2 `plugins/game-development/` (division with engine subfolders)

Source files live under subfolders (`unity/`, `godot/`, …); the generated `commands/` tree is **flat**, one copy per agent with the **basename** preserved:

```text
plugins/game-development/commands/
  economy-designer.md
  game-audio-engineer.md
  game-designer.md
  level-designer.md
  narrative-designer.md
  technical-artist.md
  blender-addon-engineer.md          # from blender/
  godot-gameplay-scripter.md         # from godot/
  godot-multiplayer-engineer.md
  godot-shader-developer.md
  roblox-avatar-creator.md           # from roblox-studio/
  roblox-experience-designer.md
  roblox-systems-scripter.md
  unity-architect.md                 # from unity/
  unity-editor-tool-developer.md
  unity-multiplayer-engineer.md
  unity-shader-graph-artist.md
  unreal-multiplayer-architect.md    # from unreal-engine/
  unreal-systems-engineer.md
  unreal-technical-artist.md
  unreal-world-builder.md
```

**Basename-collision guard:** the generator fails if two frontmatter files within one division share a basename (they would map to the same skill name). Current divisions have no collisions; the guard is future-proofing.

---

## 5. Generator changes — `scripts/build-marketplace.py`

Behavior (same stdlib-only Python, mirrors `build-hermes-plugin.py`):

1. Read `divisions.json` (single source of truth).
2. For each division, scan `<division>/**/*.md`, keeping frontmatter files with a non-empty `name` (the same gate as `convert.sh`).
3. **Remove** the legacy `<division>/.claude-plugin/plugin.json` (and the now-empty dir) if present — this is a marketplace-owned artifact from the previous design; the script owns all generated marketplace output and converges it.
4. Emit `plugins/<division>/.claude-plugin/plugin.json` — metadata only (§2), **no component path fields**.
5. Emit `plugins/<division>/commands/<basename>.md` — **byte-identical** copies (UTF-8, LF, trailing newline) of each source file, flattenting subfolders; error on basename collisions.
6. Regenerate `plugins/` cleanly each run (wipe `plugins/<division>` before writing) so renamed/removed agents leave no orphans — mirroring `clean_tool_output` in `convert.sh`.
7. Emit `.claude-plugin/marketplace.json` with `source: "./plugins/<division>"`.

CLI unchanged: default writes in place; `--out <tmp>` builds to a scratch dir for the checker.

---

## 6. Checker changes — `scripts/check-plugin-marketplace.sh`

Fails the build if any of the following disagree:

1. **Drift (both directions):** a fresh `build-marketplace.py --out <tmp>` output must byte-match the committed `.claude-plugin/marketplace.json` and every `plugins/<division>/**` file. Because the copies are byte-identical to the source, this **also** proves every committed skill copy is in sync with its canonical agent file — editing an agent without regenerating fails CI.
2. **Source sync:** for each division, the set of `plugins/<division>/commands/*.md` basenames == the set of frontmatter `.md` filenames in `<division>` (exact match, both directions).
3. **Legacy layout absent:** no `<division>/.claude-plugin/plugin.json` exists anywhere (regression guard against the explicit-field design).
4. **Manifest structure:** marketplace name kebab-case + not on Claude's reserved list; `owner.name` present; plugin list matches `divisions.json` exactly (names `agency-<division>`, sources `./plugins/<division>`, each source dir contains `.claude-plugin/plugin.json`).
5. **Default-layout-only:** every `plugins/<division>/.claude-plugin/plugin.json` has `name`/`displayName`/`description`/`author` and **no** `agents`/`commands`/`skills`/`hooks`/`mcpServers`/`lspServers` keys.
6. **No `..`/`./`-prefix violations** anywhere in sources or file lists.

---

## 7. CI wiring — `.github/workflows/check-plugin-marketplace.yml`

Unchanged triggers (every PR + push to main). Steps:

1. `scripts/check-plugin-marketplace.sh` (structural + drift).
2. `claude plugin validate .` (non-`--strict`, deliberate — see note below).
3. **New registration smoke test** — prevents a regression to "installs but registers 0" ever again:
   ```bash
   export CLAUDE_CONFIG_DIR="$(mktemp -d)"
   claude plugin marketplace add "$PWD"
   claude plugin install agency-finance@agency-agents
   claude plugin details agency-finance | grep -q 'Skills (5)' || exit 1
   ```
   (npx-invoked `@anthropic-ai/claude-code`, same as the validate step.)

---

## 8. Changes to existing files

| File | Change |
| --- | --- |
| `divisions.json` | None |
| `tools.json` | None — marketplace stays orthogonal to the convert/install pipeline |
| `scripts/check-divisions.sh` | `NON_DIVISION_DIRS=(examples scripts integrations strategy plugins)` + extend the comment (documented extension point) |
| `scripts/convert.sh`, `scripts/install.sh`, `scripts/lint-agents.sh` | None — they scan division dirs only; `plugins/` is never scanned |
| `scripts/check-runbooks.sh` | None — its glob is `git ls-files "*/*.md"` (exactly one slash); `plugins/<div>/commands/<f>.md` is two levels deep and never matches. Verify at implementation time and note in the comment if desired |
| `.gitignore`, `.gitattributes` | None — `plugins/` files are committed artifacts (like the manifests) |
| `PLUGIN-MARKETPLACE-SPEC.md` | Leave as historical design record; the restructure spec supersedes its component-layout decisions |
| Docs (README Option 5, integrations index + claude-code README, `integrations/plugin-marketplace/README.md`, CONTRIBUTING) | Reword "agents/sub-agents" → "skills"; update invocation examples and the regenerate step (now also copies into `plugins/`) |

---

## 9. Consumption (updated worked examples)

**Claude Code / Claude Desktop (Code tab):**

```text
/plugin marketplace add Marinski/agency-agents#plugins
/plugin install agency-engineering@agency-agents
/reload-plugins
```

Then invoke a skill — slash form, or just describe the task:

```text
/agency-engineering:engineering-frontend-developer build me a responsive nav
```

```text
Use the frontend developer specialist to create a landing page
```

**VS Code (Agent Plugins):**

```json
{
  "chat.plugins.enabled": true,
  "chat.plugins.marketplaces": ["Marinski/agency-agents#plugins"]
}
```

Install the division from `@agentPlugins`; its skills appear in chat.

**Web chat / Desktop Chat tab:** per Anthropic's docs, plugin skills are available across web, Desktop chat, and Cowork. Caveat from the user's own testing: a marketplace added locally in Desktop is a **local** install and does not automatically reach a separate web session — installation scope/sync semantics are an open question to verify during implementation (§11).

---

## 10. Verification plan (implementation-time)

1. `python3 scripts/build-marketplace.py` → 17 plugin trees + marketplace.
2. `scripts/check-plugin-marketplace.sh` → PASS.
3. `claude plugin validate .` → PASS (only the intentional version warnings).
4. Sandbox install of one division → `claude plugin details` shows **Skills (N)** (the exact failure mode that motivated this spec).
5. All existing checks still PASS (`check-divisions.sh`, `check-tools.sh`, `check-runbooks.sh`, `check-hermes-plugin.py`).
6. Regenerate → idempotent (byte-stable).

---

## 11. Risks / open questions

1. **Skill-name derivation is observed behavior, not a documented contract.** Empirically Claude Code names `commands/` skills by filename stem when the frontmatter `name` is non-kebab. If a future release instead slugifies the frontmatter `name` (e.g. `frontend-developer`, losing the division prefix), names could become ambiguous across divisions. Mitigations: the CI registration smoke test asserts `Skills (5)` for finance; if naming regresses, the generator can rewrite the frontmatter `name` in the copy to the kebab filename (the copy is ours to edit; the source stays untouched).
2. **`commands/` vs `skills/` surfacing.** `commands/` registers as skills (proven) and is slash-invocable + model-invocable. Any surface-specific presentation difference in Desktop/web should be smoke-tested; `skills/<name>/SKILL.md` is the fallback layout with identical registration behavior.
3. **Web-chat installation/sync scope.** The user found a Desktop-local marketplace add does not reach a separate web session. Anthropic's "skills work across all three" presumes the plugin is installed in the surface's scope. Exact semantics (account-synced Customize vs local install) need a hands-on check; the docs should describe the scope accurately, not overpromise.
4. **Duplication is real and committed.** ~270 byte-identical copies live in `plugins/` (≈1–2 MB). The division folders remain the canonical source and CI enforces sync, but contributors must remember the regenerate step — CONTRIBUTING.md states it, and the drift check fails loudly when missed.
5. **`claude plugin validate --strict` cannot be used in CI** — it treats the intentionally-omitted `version` field as an error. Non-strict validate + the drift check + the registration smoke test cover the gap.
6. **Removal of the old layout is a hard break.** Existing installs of `agency-<division>` (any user who installed the broken build) will keep the old cached plugin until update; the marketplace's commit-SHA versioning makes the new build a new version, so updates should replace it. Worth a line in the PR body.
7. **Future sub-agent needs.** If isolated-context sub-agents are ever wanted, a plugin may ship both `skills/` and `agents/` default dirs — out of scope here, but the layout leaves room for it without another restructure.
