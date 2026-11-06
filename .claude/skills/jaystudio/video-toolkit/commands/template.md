---
description: List available templates and their features
---

# Template

List available video templates or create new ones.

## Entry Point

On invocation, scan templates and present options:

### Step 1: Scan Templates

```
1. Glob templates/*/package.json
2. For each template:
   - Read package.json for name/description
   - Check for src/config/*-config.ts
   - Count available scene types
   - Check for README or docs
```

### Step 2: Present Templates

```
Available templates:

  1. **sprint-review**
     For: Internal demos, release videos, sprint reviews
     Scenes: title, overview, demo, split-demo, summary, credits
     Features:
       - Config-driven content
       - Demo video playback with labels
       - Split-screen comparisons
       - Animated backgrounds
       - JIRA reference overlays

  2. **product-demo**
     For: Marketing videos, product launches, feature demos
     Scenes: title, problem, solution, demo, feature, stats, cta
     Features:
       - Dark tech aesthetic
       - Problem → Solution narrative
       - Stats cards with animations
       - Call-to-action endings
       - Narrator PiP support

Actions:
  → View template details: enter number
  → Create video with template: /video
  → Create new template: 'new'
```

### Template Details View

When user selects a template:

```
Template: sprint-review

## Overview

Best for internal demos, release videos, and sprint reviews.
Shows features/fixes with live demos and technical overlays.

## Scene Types

| Type | Description | Visual |
|------|-------------|--------|
| title | Opening title card | Slide |
| overview | Bullet points/highlights | Slide |
| demo | Single video demo | Video + label |
| split-demo | Side-by-side comparison | Two videos |
| summary | Stats and recap | Slide |
| credits | Closing credits | Slide |

## Components

- TitleSlide - Animated title with logo
- OverviewSlide - Staggered bullet animations
- DemoSection - Video with JIRA labels
- SplitScreen - Left/right video comparison
- SummarySlide - Stats with spring animations
- AnimatedBackground - Floating shapes

## Config Structure

Edit `src/config/sprint-config.ts`:

```typescript
export const sprintConfig = {
  title: "Sprint Release",
  subtitle: "Version 2.1",
  overview: ["Feature 1", "Feature 2"],
  demos: [
    {
      title: "Dark Mode",
      video: "demos/dark-mode.mp4",
      jiraRef: "PROJ-123"
    }
  ],
  stats: { features: 3, fixes: 5 }
};
```

## Example Projects

- sprint-review-cho-oyu (in projects/)

## Usage

Create a project with this template:
  /video → select "Sprint Review"

Preview locally:
  cd projects/{name} && npm run studio

Render:
  npm run render
```

---

## New Template Flow

When user selects 'new':

### Step 1: Gather Information

```
Let's create a new template.

Template name: (e.g., "tutorial", "changelog", "comparison")
Description: (what type of videos is this for?)
```

### Step 2: Choose Starting Point

```
How would you like to start?

  1. Copy existing template (recommended)
     → Choose sprint-review or product-demo as base
     → Modify for your needs

  2. Minimal template
     → Basic Remotion setup
     → Single placeholder composition
     → You build from scratch

  3. From existing project
     → Convert a project in projects/ into a reusable template
```

### Step 3: Define Scene Types

```
What scene types should this template support?

Common options:
  - title, intro, outro, credits (bookends)
  - demo, split-demo, screenshot (visuals)
  - overview, summary, stats (information)
  - problem, solution, feature, cta (narrative)
  - chapter, step, tip (educational)

Enter scene types (comma-separated):
```

### Step 4: Create Template

**If copying existing:**
```bash
cp -r templates/{base}/ templates/{name}/
```

Then modify:
1. Update `package.json` name and description
2. Rename config file: `{base}-config.ts` → `{name}-config.ts`
3. Update `Root.tsx` to reference new config
4. Adjust/add scene components as needed
5. Update types.ts with new scene types

**If minimal:**
```bash
cd templates
npx create-video@latest {name} --yes
```

Then set up:
1. Create `src/config/{name}-config.ts`
2. Create `src/config/types.ts`
3. Create `src/config/theme.ts` (or import from lib)
4. Create `src/config/brand.ts` placeholder
5. Set up component directories

**If from project:**
1. Copy project to templates/
2. Remove project-specific content from config
3. Generalize hardcoded values
4. Extract reusable patterns

### Step 5: Verify Setup

```bash
cd templates/{name}
npm install
npm run studio
```

### Step 6: Confirmation

```
Template created: templates/{name}/

Files:
  ✅ package.json
  ✅ src/Root.tsx
  ✅ src/config/{name}-config.ts
  ✅ src/config/types.ts
  ✅ src/config/theme.ts

Next steps:
  1. Edit config to define your content structure
  2. Create/modify components for your scene types
  3. Test with: cd templates/{name} && npm run studio
  4. Use with: /video → select your new template

See docs/creating-templates.md for detailed guidance.

⚠️  Restart Claude Code to see the new template in /video.
```

---

## Template Structure Reference

Each template in `templates/` follows this structure:

```
templates/{name}/
├── package.json           # Remotion project config
├── src/
│   ├── Root.tsx           # Composition entry point
│   ├── config/
│   │   ├── theme.ts       # Visual styling
│   │   ├── brand.ts       # Brand integration (generated)
│   │   ├── types.ts       # TypeScript types
│   │   └── {name}-config.ts  # Content configuration
│   └── components/
│       ├── core/          # Shared components
│       ├── slides/        # Slide components
│       └── demos/         # Demo components
├── public/
│   ├── demos/             # Video assets
│   ├── audio/             # Voiceover, music
│   └── images/            # Logos, screenshots
└── remotion.config.ts     # Remotion settings
```

---

## Template Evolution

Templates are designed to grow and improve over time. Track evolution in each template:

### Adding Features to Existing Templates

```
1. Identify the need (from project work or user requests)
2. Plan the addition:
   - New scene type? → Update types.ts, create component
   - New component? → Add to appropriate folder
   - New config option? → Extend config types
3. Implement with backward compatibility
4. Update template README and CLAUDE.md
5. Test in existing projects
6. Document in _internal/CHANGELOG.md
```

### Template Maturity Indicators

| Indicator | Meaning |
|-----------|---------|
| Scene types | Number of supported content types |
| Components | Reusable building blocks |
| Config flexibility | How customizable without code changes |
| Brand integration | Uses brand.ts for theming |
| Documentation | README completeness |

### Promoting Patterns to Shared Library

When patterns emerge across templates:

```
1. Identify common components/utilities
2. Extract to lib/ (e.g., lib/components/, lib/animations/)
3. Import in templates instead of duplicating
4. Document in lib/README.md
```

---

## Evolution

This command evolves through use. If something's awkward or missing:

**Local improvements:**
1. Say "improve this" → Claude captures in `_internal/BACKLOG.md`
2. Edit `.claude/commands/template.md` → Update `_internal/CHANGELOG.md`
3. Share upstream → `gh pr create`

**Remote contributions:**
- Issues: `github.com/digitalsamba/claude-code-video-toolkit/issues`
- PRs welcome for new templates, components, documentation

History: Created as unified template listing/creation command
