# Agency OS — Lessons Learned

Operational learnings from live sessions. Update this file whenever a new insight or workflow discovery is made.

---

## Figma MCP — Status & How It Works

**Date**: March 17, 2026

### What was set up
- Added Figma's official remote MCP server to `.mcp.json` at the project root:
  ```json
  {
    "mcpServers": {
      "figma": {
        "type": "http",
        "url": "https://mcp.figma.com/mcp"
      }
    }
  }
  ```
- This uses Figma's **HTTP-based remote MCP** (not a local Node.js process), which requires no installation.

### Does it work in Claude Code on the web (cloud)?

**Yes — but only with a Figma access token.**

- The `.mcp.json` config is correct and will load on session start.
- However, `https://mcp.figma.com/mcp` requires OAuth or a Personal Access Token (PAT) sent as a Bearer token in the Authorization header.
- In a local Claude Code session, this can be passed via env var or MCP auth config.
- In cloud (web) sessions, MCP servers configured in `.mcp.json` **do load**, but the auth flow depends on whether the token is available as an env var in that environment.

### To make Figma MCP work in a new session (local or cloud)

1. Get a Figma Personal Access Token: Figma → Settings → Security → Personal access tokens
2. Store it as an env var: `FIGMA_ACCESS_TOKEN=your_token`
3. Or configure auth in `.mcp.json` (if the harness supports it):
   ```json
   {
     "mcpServers": {
       "figma": {
         "type": "http",
         "url": "https://mcp.figma.com/mcp",
         "headers": {
           "Authorization": "Bearer YOUR_TOKEN_HERE"
         }
       }
     }
   }
   ```
   **Note**: Do NOT commit a real token to the repo. Use env var substitution or set via `settings.local.json` (gitignored).

### What Figma MCP can do (when connected)
- Read frames, components, styles from a Figma file by URL
- Extract exact hex colors, typography specs, spacing values
- Generate accurate design specs without manual inspection
- Enable Claude to produce pixel-perfect Figma-ready briefs directly from the live file

### Current fallback (when MCP is unavailable)
- Use the brand guide at `strategy/BRAND-GUIDE.md` for all color/type specs
- Use `/tweet-card-brief` and `/thread-visual-pack` skills to generate Figma-ready design specs
- HTML card mockups can be produced as `.html` files for visual reference (see `campaign/execution/2026-03-17/`)

---

## TELx Council #19 Card — HTML Mockup Approach

**Date**: March 17, 2026

### What was produced
- `campaign/execution/2026-03-17/` contains a tweet card designed as an HTML file
- This serves as a visual reference / design spec when Figma MCP is not available
- The HTML card uses brand colors (#3642B2, #14C8FF, #090920) and can be screenshotted directly

### Lesson
When Figma MCP is unavailable, HTML mockups are an effective intermediate step:
1. Claude writes the HTML with brand-accurate styling
2. User screenshots it or opens in browser
3. Designer uses it as a reference in Figma
4. Eventually, with Figma MCP live, Claude will write directly to Figma frames

---

## Session Startup — `claude mcp list` Not Available in Hooks

**Date**: March 17, 2026

The `claude mcp list` CLI command is **not available** when run from inside a hook subprocess. It exits with SIGKILL (code 137). Do not use it in hook scripts for health checks.

**Workaround**: Check for `.mcp.json` existence and parse it with `cat`/`jq` instead.

---

## Git Branching

- Active campaign branch: `claude/campaign-iLgt5`
- Review/agent work branch (from GitHub task runner): `claude/review-codebase-agents-iLgt5`
- **Never mix** — campaign content goes to `campaign-iLgt5`, automated reviews go to their own branch

---

## Figma MCP — generate_diagram Capability & Limits

**Date**: March 17, 2026

### What generate_diagram does
- Creates FigJam (whiteboard) artifacts using Mermaid syntax
- Supports custom node styling via `classDef` — colors, fills, fonts, stroke
- Output is a real Figma file (FigJam board) accessible via URL
- Good for: flowcharts, status trackers, comparison diagrams, network diagrams
- Color support: full hex color in `fill:`, `stroke:`, `color:` — use Telcoin brand colors

### What it cannot do
- Cannot create Figma Design frames (the pixel-perfect static card tool)
- Cannot produce 1200×675 tweet card images directly
- The HTML card approach (`design/output/*.html`) remains the correct path for tweet card mockups

### Campaign infographics built in FigJam (March 17, 2026)
Four Telcoin content infographics created via Figma MCP for the @telcoinTAO campaign:

1. **Mainnet Readiness Status Tracker** — COMPLETE/IN PROGRESS/QUEUED milestone chain → mainnet launch
2. **eUSD & U.S. CBDC Policy** — Senate CBDC ban flowchart showing eUSD's carve-out position
3. **GSMA Stablecoin Framework** — Co-authorship and MNO validator model network diagram
4. **eUSD vs. Reserve-Backed Stablecoins** — Regulatory category distinction (eUSD vs. USDC)

### Best practice for campaign visuals
- FigJam diagrams: use for informational/explanatory infographics embedded in tweet threads
- HTML cards: use for tweet header cards (1200×675, brand-accurate, screenshot → Figma)
- Both approaches complement each other — diagrams for content, HTML for card format

### Wrong branch risk
The GitHub task runner creates its own claude/* branch. When starting a session, always verify `git branch` shows `claude/campaign-iLgt5` before committing. See Git Branching section above.

