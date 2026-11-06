---
description: Share improvements - issues, PRs, skills, templates
---

# Contribute

Help users contribute improvements back to the toolkit without sharing their private project work.

## Entry Point

When invoked, determine the contribution type:

```
How would you like to contribute?

  1. **Report an issue** - Bug, missing feature, or question
  2. **Submit an improvement** - PR for command, skill, template, or docs
  3. **Share a new skill** - Package domain knowledge you've developed
  4. **Share a template** - Generalize a project into a reusable template
  5. **Share an example project** - Showcase a real project (configs + scripts, no large media)

Which would you like to do?
```

---

## Option 1: Report an Issue

```
I'll help you create a GitHub issue.

What type of issue?
  1. 🐛 Bug report
  2. 💡 Feature request
  3. 📝 Documentation improvement
  4. ❓ Question

Describe the issue:
```

Then generate issue with `gh issue create`:

```bash
gh issue create \
  --repo digitalsamba/claude-code-video-toolkit \
  --title "Bug: description" \
  --body "## Description

[User's description]

## Steps to Reproduce

[If bug]

## Expected Behavior

[If bug]

---
Reported via /contribute command"
```

---

## Option 2: Submit an Improvement

### Step 1: Verify Safety

```
Let me check what would be shared...

✅ Safe to share:
   .claude/commands/video.md (modified)
   .claude/skills/ffmpeg/SKILL.md (modified)

❌ Ignored (stays private):
   projects/ (your video work)
   assets/voices/ (your voice samples)
   .env (secrets)

Does this look right?
```

### Step 2: Create Branch & Commit

```bash
# Show current status
git status

# Create branch
git checkout -b improve/short-description

# Stage toolkit files only
git add .claude/ templates/ lib/ docs/ _internal/ tools/ brands/default/

# Commit with description
git commit -m "$(cat <<'EOF'
Improve: short description

Longer description of what changed and why.

🤖 Generated with Claude Code
EOF
)"
```

### Step 3: Create PR

```bash
gh pr create \
  --title "Improve: short description" \
  --body "$(cat <<'EOF'
## Summary

What this PR improves.

## Changes

- Change 1
- Change 2

## Testing

How to test the improvement.

---
🤖 Generated with Claude Code
EOF
)"
```

### Step 4: Confirmation

```
PR created! 🎉

View at: [PR URL]

Your projects/ directory was NOT included.
Only toolkit improvements were shared.

After merge, you can update your local copy:
  git checkout main
  git pull
```

---

## Option 3: Share a Skill

### Step 1: Identify Skill

```
Which skill would you like to share?

Found in .claude/skills/:
  1. ffmpeg (beta) - already in toolkit
  2. my-new-skill (draft) - your addition

Or describe a new skill to create.
```

### Step 2: Prepare Skill

Check skill is ready:
- [ ] SKILL.md has clear description
- [ ] Examples are tested and work
- [ ] No project-specific paths or secrets
- [ ] Status is at least "beta"

### Step 3: Create PR

Same as Option 2, but focused on `.claude/skills/{name}/`

---

## Option 4: Share a Template

### Step 0: Is it actually a template? (ask this first)

Most "new template" ideas are really a **brand profile**. Ask before anything
else, and take the answer seriously — this is the single most common wrong turn
in this command:

```
What makes your video different from the closest existing template?

  a. Colors, fonts, logo, narrator voice
  b. Scene pacing / timing values
  c. Different scenes, different structure, different composition code

If (a) or (b) only -> you want a BRAND PROFILE, not a template.
```

**If (a) or (b):** stop here and run `/brand` instead. Templates read their
palette, fonts and voice from a brand (`voice.brand` in `config.json` points at
`brands/<name>/voice.json`), and timing values like `lead`/`tail`/`xfade` live
in your project's own `config.json`. Copying a template to change those produces
a near-identical fork that stops inheriting fixes to the original — worse for
you than for the toolkit.

A brand profile does not need to be committed to this repo to work. Keep it
local unless it is genuinely useful to other people.

**Only continue below if (c)** — the composition code itself differs.

### Step 1: Identify Template

```
Templates are generalized from projects.

Do you have a project you'd like to turn into a template?
Or an existing template in templates/ to share?
```

### Step 2: Generalize (if from project)

```
To turn a project into a shareable template:

1. Copy to templates/:
   cp -r projects/my-video templates/my-template

2. Remove project-specific content:
   - Clear demo videos from public/demos/
   - Reset config to example values
   - Remove generated audio
   - Update README with generic instructions

3. Verify it works:
   cd templates/my-template
   npm install
   npm run studio

4. Check it is not a near-duplicate — diff every file against the
   template you started from:

   for f in <new-template>/*; do
     diff -q "<base-template>/$(basename "$f")" "$f" 2>/dev/null
   done

   Identical composition code (build.py, gen_captions.py, src/) means this
   should be a brand profile plus project config, not a template. Go back
   to Step 0.

Ready to proceed?
```

### Step 3: Create PR

Same as Option 2, but focused on `templates/{name}/`

---

## Option 5: Share an Example Project

Example projects showcase real-world usage. They include configs, scripts, and documentation but NOT large media files.

### Step 1: List Available Projects

```
Found in projects/:

  1. digital-samba-skill-demo
     Marketing video for DS Claude Code skill
     Template: product-demo style

  2. sprint-review-cho-oyu
     iOS sprint review for Digital Samba Mobile
     Template: sprint-review

Which project would you like to share as an example?
```

### Step 1b: Contributor Recognition

```
We'd like to credit you for sharing this example!

Your name or organization: ___
Website URL (optional, for backlink): ___

This will appear in:
  - examples/README.md (Contributors table)
  - The example's own README.md
  - Project's CLAUDE.md

Leave blank to contribute anonymously.
```

### Step 2: Prepare for Sharing

```
Preparing: digital-samba-skill-demo

I'll copy to examples/ and remove large media files.
The following will be INCLUDED:

  ✅ Configs and source code
     - remotion/src/config/*.ts
     - remotion/src/components/**
     - remotion/package.json

  ✅ Documentation
     - VIDEO-SPEC.md
     - VOICEOVER-SCRIPT.md
     - CLAUDE.md
     - PROJECT-STATUS.md

  ✅ Small assets (logos, icons)
     - remotion/public/images/*.png
     - remotion/public/images/*.svg

The following will be EXCLUDED:

  ❌ Large media (gitignored)
     - remotion/public/demos/*.mp4
     - remotion/public/audio/*.mp3
     - node_modules/
     - .venv/
     - out/

  ❌ Secrets
     - .env

Proceed?
```

### Step 3: Copy and Clean

```bash
# Copy project to examples
cp -r projects/{name} examples/{name}

# Remove large media (will be gitignored anyway, but clean up)
rm -rf examples/{name}/remotion/public/demos/*.mp4 2>/dev/null
rm -rf examples/{name}/remotion/public/audio/*.mp3 2>/dev/null
rm -rf examples/{name}/remotion/node_modules 2>/dev/null
rm -rf examples/{name}/remotion/.remotion 2>/dev/null
rm -rf examples/{name}/remotion/out 2>/dev/null
rm -rf examples/{name}/.venv 2>/dev/null
rm -f examples/{name}/.env 2>/dev/null
rm -f examples/{name}/.DS_Store 2>/dev/null
```

### Step 4: Create ASSETS-NEEDED.md

Generate documentation of what media assets are needed:

```markdown
# Assets Needed

To run this example, you'll need to create/provide these assets:

## Demo Videos

| File | Duration | Description |
|------|----------|-------------|
| `public/demos/skill-install.mp4` | ~15s | Screen recording of skill installation |
| `public/demos/app-demo.mp4` | ~30s | Browser recording of app flow |

## Audio

| File | Duration | Description |
|------|----------|-------------|
| `public/audio/voiceover.mp3` | ~2:30 | Generated from VOICEOVER-SCRIPT.md |
| `public/audio/background-music.mp3` | ~3:00 | Subtle tech ambient |

## How to Create

### Demo recordings
Use `/record-demo` command or Playwright scripts

### Voiceover
```bash
uv run tools/voiceover.py --script VOICEOVER-SCRIPT.md --output public/audio/voiceover.mp3
```

### Background music
```bash
uv run tools/music.py --prompt "subtle tech ambient" --duration 180 --output public/audio/background-music.mp3
```
```

### Step 5: Update Example README

Ensure the example has a clear README.md with contributor credit:

```markdown
# Example: {name}

{Description from VIDEO-SPEC.md}

> Contributed by [{contributor_name}]({contributor_url})

## What This Demonstrates

- {Key feature 1}
- {Key feature 2}
- {Key feature 3}

## Quick Start

```bash
# Copy to your projects
cp -r examples/{name} projects/my-version
cd projects/my-version/remotion

# Install dependencies
npm install

# Create required assets (see ASSETS-NEEDED.md)
# ...

# Preview
npm run studio

# Render
npm run render
```

## Structure

{Brief overview of project structure}

## Assets

See `ASSETS-NEEDED.md` for required demo videos and audio files.

---

*Contributed by [{contributor_name}]({contributor_url})*
```

Also update `examples/README.md` Contributors table with new entry.

### Step 6: Commit and PR

```bash
git add examples/{name}
git commit -m "Add example: {name}

{Description}

Note: Large media files not included. See ASSETS-NEEDED.md.

🤖 Generated with Claude Code"

gh pr create \
  --title "Add example: {name}" \
  --body "## Summary

Adds {name} as a showcase example.

## What it demonstrates

- {feature 1}
- {feature 2}

## Assets

Large media files are gitignored. Users create their own using:
- /record-demo for screen recordings
- /generate-voiceover for narration
- tools/music.py for background music

---
🤖 Generated with Claude Code"
```

---

## Safety Checks

Before any contribution, verify:

```bash
# These should NOT appear in git status:
#   - projects/*
#   - assets/voices/*
#   - .env files
#   - Any client/company specific content

git status --porcelain | grep -E "^(projects/|assets/voices/|\.env)" && echo "⚠️  Private files detected!" || echo "✅ No private files in staging"
```

---

## Evolution

This command evolves through use. If something's awkward or missing:

**Local improvements:**
1. Say "improve this" → Claude captures in `_internal/BACKLOG.md`
2. Edit `.claude/commands/contribute.md` → Update `_internal/CHANGELOG.md`
3. Share upstream → `gh pr create`

**Remote contributions:**
- Issues: `github.com/digitalsamba/claude-code-video-toolkit/issues`
- PRs welcome for contribution workflow improvements
