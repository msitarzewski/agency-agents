# Plugin Marketplace (Claude Code / VS Code / Claude Desktop)

The Agency ships a Claude-format **plugin marketplace**: a
`.claude-plugin/marketplace.json` registry that publishes each division as an
installable **skills plugin**. Claude Code, Claude Desktop, VS Code (Agent
Plugins, Preview), and GitHub Copilot CLI all read this format directly — no
build step, no conversion, and the source agent `.md` files stay untouched in
their division folders.

> **Source/dist split:** the raw marketplace lives on the **`plugins` branch**
> of this repo (a generated `dist`), published automatically by CI from `main`.
> Consumers point at `Marinski/agency-agents#plugins` (the `#plugins` selects the
> dist branch — supported by both VS Code `chat.plugins.marketplaces` `#ref` and
> Claude Code marketplace `ref`). The `main` branch never commits the generated
> tree, keeping the source diff tiny and easy to merge with upstream.

Each division becomes one plugin (`agency-<division>`, e.g. `agency-engineering`,
`agency-finance`). Each plugin ships the division's specialists as **skills**
(the default `skills/` and `agents/` layout) named by their agent filenames, e.g.
`engineering-frontend-developer`, `marketing-seo-specialist`. Skills are
model-invocable by their `description` and user-invocable via `/`, and they work
across web chat, the Claude Desktop Chat tab, and Cowork — the widest reach of
any plugin component. Add the marketplace once, then install the divisions you
need.

> **Install scope:** marketplace/plugin installs are per-surface — adding the
> marketplace locally in one app (e.g. Claude Desktop's Settings) is a local
> install and does not automatically reach a separate web session or another
> device. Install it in each surface where you want the skills.

## Install

### Claude Code / Claude Desktop

In a Claude Code session (or the Desktop app's **Settings → Plugins → Add
marketplace → Add from a repository**):

```text
/plugin marketplace add Marinski/agency-agents#plugins
/plugin install agency-engineering@agency-agents
/reload-plugins
```

Or non-interactively from a terminal:

```bash
claude plugin marketplace add Marinski/agency-agents#plugins
claude plugin install agency-engineering@agency-agents        # default scope: user
claude plugin install agency-engineering@agency-agents --scope project
```

> `owner/repo` shorthand clones over SSH by default. Prefer HTTPS with
> `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1`. The `#plugins` suffix selects the dist
> branch; omit it only when the regository's default branch is the dist.

### VS Code (Agent Plugins, Preview)

Add the marketplace to your `settings.json`:

```json
{
  "chat.plugins.enabled": true,
  "chat.plugins.marketplaces": ["Marinski/agency-agents#plugins"]
}
```

Then open the **Extensions** view (`Ctrl+Shift+X`), search `@agentPlugins`,
accept the marketplace trust prompt on first install, and install the divisions
you want from the **Agent Plugins** list.

### GitHub Copilot CLI

Plugins installed via the GitHub Copilot CLI's plugin marketplace flow are
shared with VS Code automatically. See the [GitHub Copilot CLI plugin
reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-plugin-reference)
for the marketplace command.

## Using the skills

Invoke a specialist by name — either the slash form or plain language:

```text
/agency-engineering:engineering-frontend-developer build me a responsive nav
```

```text
Use the frontend developer specialist to create a landing page
```

```text
Check this code with the code reviewer specialist
```

Claude matches skills by their `description`, so you can also just describe the
task and let Claude pick the right specialist.

## What you get

| Plugin | Division | Skills |
| --- | --- | --- |
| `agency-academic` | Academic | 6 |
| `agency-design` | Design | 10 |
| `agency-engineering` | Engineering | 58 |
| `agency-finance` | Finance | 5 |
| `agency-game-development` | Game Development | 21 |
| `agency-gis` | GIS | 13 |
| `agency-healthcare` | Healthcare | 3 |
| `agency-marketing` | Marketing | 36 |
| `agency-paid-media` | Paid Media | 7 |
| `agency-product` | Product | 5 |
| `agency-project-management` | Project Management | 7 |
| `agency-sales` | Sales | 9 |
| `agency-security` | Security | 12 |
| `agency-spatial-computing` | Spatial Computing | 6 |
| `agency-specialized` | Specialized | 57 |
| `agency-support` | Support | 6 |
| `agency-testing` | Testing | 9 |

Counts are generated from the roster and may grow as new agents are added.

## Updates

Claude Code re-pulls the marketplace and treats every commit as a new plugin
version (the manifests deliberately omit a `version` field, so the git commit
SHA is used). VS Code checks for updates automatically and on
**Extensions: Check for Extension Updates**. No manual step.

## For maintainers

The `plugins/` tree and `.claude-plugin/marketplace.json` are **generated output,
never committed to `main`**. The division folders remain the single source of
truth; the generated files are byte-identical copies of the agent content.

Regenerate and check locally after adding, renaming, or editing an agent or
division:

```bash
python3 scripts/build-marketplace.py
```

CI publishes the dist automatically: a push to `main` triggers
`.github/workflows/publish-plugin-marketplace.yml`, which rebuilds from the new
source, runs `scripts/check-plugin-marketplace.sh` (plus `claude plugin
validate` and a skill-registration smoke test), then force-publishes the result
to the `plugins` branch. Consumers see the new version as a new commit, so
updates arrive with no manual step.

To publish manually (same steps CI runs, against `origin`):

```bash
scripts/publish-marketplace.sh
```

`.gitignore` and `scripts/check-plugin-marketplace.sh` both enforce the split —
the checker fails any source commit that tracks `plugins/` or the generated
marketplace manifest.
