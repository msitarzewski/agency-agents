# Claude Cowork Integration

The Agency maps naturally to Claude Cowork's plugin system — each division becomes
a plugin, and each agent becomes a skill inside that plugin.

## Structure

```
claude-cowork/
├── agency-design/
│   ├── .claude-plugin/plugin.json   # plugin manifest
│   └── skills/
│       ├── brand-guardian/SKILL.md
│       ├── ui-designer/SKILL.md
│       └── ...
├── agency-engineering/
│   ├── .claude-plugin/plugin.json
│   └── skills/
│       ├── frontend-developer/SKILL.md
│       └── ...
└── ... (one plugin per division)
```

## Install

```bash
# Generate the integration files (if not already present)
./scripts/convert.sh --tool claude-cowork

# Install all plugins to your Claude Cowork plugins directory
./scripts/install.sh --tool claude-cowork
```

The installer copies each `agency-*` plugin folder to:
- **macOS:** `~/Library/Application Support/Claude/cowork-plugins/`
- **Linux:** `~/.config/claude/cowork-plugins/`
- **Custom:** Set `CLAUDE_COWORK_PLUGINS_DIR=/your/path` before running

Restart Claude after installing to load the new plugins.

## Available Plugins

| Plugin | Description |
|--------|-------------|
| `agency-design` | Design-focused specialists (e.g., branding, UI/UX, visuals). See `.claude-plugin/plugin.json` in this plugin for the up-to-date list of skills. |
| `agency-engineering` | Engineering and development specialists. See `.claude-plugin/plugin.json` in this plugin for the up-to-date list of skills. |
| `agency-marketing` | Marketing, growth, and channel-specific specialists. See `.claude-plugin/plugin.json` in this plugin for the up-to-date list of skills. |
| `agency-product` | Product strategy and discovery specialists. See `.claude-plugin/plugin.json` in this plugin for the up-to-date list of skills. |
| `agency-project-management` | Project and operations management specialists. See `.claude-plugin/plugin.json` in this plugin for the up-to-date list of skills. |
| `agency-support` | Support, analytics, and operations support specialists. See `.claude-plugin/plugin.json` in this plugin for the up-to-date list of skills. |
| `agency-testing` | QA, validation, and testing specialists. See `.claude-plugin/plugin.json` in this plugin for the up-to-date list of skills. |
| `agency-specialized` | Advanced and cross-cutting specialists. See `.claude-plugin/plugin.json` in this plugin for the up-to-date list of skills. |
| `agency-spatial-computing` | Spatial computing and XR-focused specialists. See `.claude-plugin/plugin.json` in this plugin for the up-to-date list of skills. |

## Usage

Once installed, activate any agent by mentioning its skill name in Claude Cowork:

```
Activate Brand Guardian and create a brand identity for my startup.
```

```
Use the Reality Checker to review this feature spec.
```

```
Switch to Frontend Developer mode and build me a React component.
```

## Why These Agents Work Great in Cowork

Most of The Agency's specialists — design, marketing, product, project management,
support — are knowledge-work agents, not coding agents. Claude Cowork is built for
exactly this kind of work: long-running tasks, file reading/writing, research, and
multi-step workflows without a code environment.

Claude Code is the right tool for engineering agents; Claude Cowork is the right
tool for everything else.
