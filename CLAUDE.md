# CLAUDE.md — Telcoin Association Agency

## What This Repository Is

**The Agency** is a collection of 80+ specialized AI agent personalities in markdown format, designed for use with Claude Code, GitHub Copilot, Cursor, Aider, Windsurf, Gemini CLI, and other AI coding tools.

- **No frontend code** — pure `.md` agent definitions
- **No package.json** — no npm/Node.js dependencies
- **No compiled assets** — documentation only
- **Conversion scripts** in `/scripts/` transform agents to tool-specific formats

---

## Figma MCP Integration

### MCP Server Configuration

The Figma remote MCP server is configured in `.mcp.json` at the project root:

```json
{
  "mcpServers": {
    "figma-remote-mcp": {
      "type": "http",
      "url": "https://mcp.figma.com/mcp"
    }
  }
}
```

This file must be committed to git so Claude Code on the web picks it up automatically when starting a session.

### Authentication

Figma MCP uses OAuth — no API keys needed. Per session:
1. Run `/mcp` in Claude Code
2. Select `figma-remote-mcp`
3. Authenticate via browser
4. Authorization persists for the session

### Available Figma MCP Tools

| Tool | Purpose |
|------|---------|
| `get_design_context` | Primary tool — fetch component code, screenshot, and hints from a Figma node |
| `get_screenshot` | Capture visual screenshot of a Figma node |
| `get_metadata` | Fetch file/node metadata |
| `get_variable_defs` | Fetch design token variables from Figma |
| `get_code_connect_map` | View Code Connect mappings |
| `add_code_connect_map` | Add a Figma component → codebase component mapping |
| `send_code_connect_mappings` | Push Code Connect mappings to Figma |
| `generate_diagram` | Create diagrams in FigJam |
| `create_design_system_rules` | Analyze codebase and generate design system rules |

### Figma URL Parsing

Extract `fileKey` and `nodeId` from Figma URLs:

```
figma.com/design/:fileKey/:fileName?node-id=:nodeId
```

- Convert `-` to `:` in `nodeId` (e.g., `123-456` → `123:456`)
- For FigJam boards: `figma.com/board/:fileKey/` → use `get_figjam`

---

## How Figma Is Used in This Repo

Since this repo contains no compiled UI, Figma MCP is used for:

1. **Designing agent card UIs** — visual representations of agents for marketing/docs
2. **Generating design briefs** — passing Figma designs to the `design-ui-designer.md` agent
3. **Creating diagrams** — multi-agent workflow diagrams via FigJam
4. **Documenting design tokens** — exporting Figma variables as token references for agent guidance

When a Figma URL is provided, always call `get_design_context` first.

---

## Design Token Conventions (Documented in Agents)

The design system documented across agents uses these conventions:

### Colors (CSS Custom Properties)
```css
--color-primary-100 / -500 / -900
--color-secondary-100 / -500 / -900
--color-success: #10b981
--color-warning: #f59e0b
--color-error: #ef4444
--color-info: #3b82f6
```

### Typography
```css
--font-family-primary: 'Inter', system-ui, sans-serif;
--font-family-secondary: 'JetBrains Mono', monospace;
--font-size-xs: 0.75rem    /* 12px */
--font-size-sm: 0.875rem   /* 14px */
--font-size-base: 1rem     /* 16px */
--font-size-lg: 1.125rem   /* 18px */
--font-size-xl: 1.25rem    /* 20px */
--font-size-2xl: 1.5rem    /* 24px */
```

### Spacing (4px base unit)
```css
--space-1: 0.25rem   /* 4px */
--space-2: 0.5rem    /* 8px */
--space-3: 0.75rem   /* 12px */
--space-4: 1rem      /* 16px */
--space-6: 1.5rem    /* 24px */
--space-8: 2rem      /* 32px */
--space-12: 3rem     /* 48px */
--space-16: 4rem     /* 64px */
```

### Shadows
```css
--shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
--shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
--shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
```

---

## Project Structure

```
/
├── .mcp.json                  # MCP server config (Figma remote MCP)
├── CLAUDE.md                  # This file
├── README.md                  # Full agent roster and use cases
├── CONTRIBUTING.md            # How to add/modify agents
├── design/                    # 8 design-focused agents
│   ├── design-ui-designer.md         # Design systems, component libraries
│   ├── design-ux-researcher.md       # User research, testing
│   ├── design-ux-architect.md        # IA, CSS frameworks
│   ├── design-brand-guardian.md      # Brand consistency
│   ├── design-visual-storyteller.md  # Data visualization
│   ├── design-whimsy-injector.md     # Delight and micro-interactions
│   ├── design-image-prompt-engineer.md # AI image generation
│   └── design-inclusive-visuals-specialist.md # Accessibility
├── engineering/               # 16 engineering agents
├── marketing/                 # 11 marketing agents
├── game-development/          # 20+ game dev agents
├── testing/                   # 8 QA agents
├── project-management/        # 5 PM agents
├── support/                   # 6 ops agents
├── spatial-computing/         # 6 XR agents
├── specialized/               # 15 specialist agents
├── product/                   # 3 product agents
├── strategy/                  # Strategic docs and playbooks
├── examples/                  # Multi-agent workflow examples
├── scripts/                   # convert.sh, install.sh, lint-agents.sh
└── integrations/              # Tool-specific converted formats
```

## Agent File Format

Every agent follows this structure:

```markdown
---
name: Agent Name
description: One-line description
color: purple
---

# Agent Name Personality

## 🧠 Your Identity & Memory
## 🎯 Your Core Mission
## 🚨 Critical Rules You Must Follow
## 📋 Your Deliverables
## 🔄 Your Workflow
```

---

## Styling / Implementation Philosophy

When implementing UIs described by agents in this repo:

- **Framework**: React with TypeScript (agents assume modern React patterns)
- **Styling**: CSS Custom Properties for tokens; Tailwind CSS acceptable
- **Accessibility**: WCAG 2.1 AA minimum — built into foundation, not added later
- **Performance**: Optimize assets; design with loading states in mind
- **Responsive**: Mobile-first; all breakpoints covered

---

## Scripts

```bash
./scripts/convert.sh      # Convert .md agents → Cursor (.mdc), Aider, Windsurf, etc.
./scripts/install.sh      # Install agents to ~/.claude/agents/, ~/.cursor/rules/, etc.
./scripts/lint-agents.sh  # Validate agent file structure
```

## Tool Integration Map

| Tool | Format | Location |
|------|--------|----------|
| Claude Code | `.md` | `~/.claude/agents/` |
| GitHub Copilot | `.md` | `~/.github/agents/` |
| Cursor | `.mdc` | `.cursor/rules/` |
| Aider | `CONVENTIONS.md` | project root |
| Windsurf | `.windsurfrules` | project root |
| Gemini CLI | `SKILL.md` | `~/.gemini/extensions/` |
