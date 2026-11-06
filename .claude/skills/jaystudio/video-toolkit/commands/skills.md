---
description: List installed skills or create new ones
---

# Skills

List installed skills and their status, or create new skills.

## Entry Point

On invocation, scan skills and present:

### Step 1: Scan Skills

```
1. Glob .claude/skills/*/SKILL.md
2. For each skill:
   - Read SKILL.md frontmatter for metadata
   - Extract: name, status, description, triggers
   - Check for reference.md (detailed docs)
3. Read _internal/toolkit-registry.json for additional metadata
4. Sort by status (stable first), then alphabetically
```

### Step 2: Present Skills

```
Installed skills:

  Stable:
  ──────
  1. **remotion** - Video compositions with React
     Triggers: Remotion, video composition, animations, interpolate, spring

  2. **elevenlabs** - AI voiceover and audio generation
     Triggers: voiceover, TTS, voice cloning, sound effects, music

  Beta:
  ─────
  3. **ffmpeg** - Video/audio conversion and processing
     Triggers: convert video, resize, compress, extract audio

  4. **playwright-recording** - Browser demo capture
     Triggers: record demo, browser recording, screenshot

Actions:
  → View skill details: enter number
  → Create new skill: 'new'
  → Check skill maturity: see _internal/ROADMAP.md
```

### Skill Details View

When user selects a skill:

```
Skill: remotion

Status: stable
Description: Create programmatic videos using React with Remotion

## Triggers

Use this skill when:
- Creating video compositions with React
- Working with Remotion animations (interpolate, spring)
- Rendering videos to MP4/WebM/GIF
- Building frame-by-frame animations
- Using <Sequence>, <Series>, <AbsoluteFill>

## Key Patterns

Animation:
  const opacity = interpolate(frame, [0, 30], [0, 1]);

Sequencing:
  <Series>
    <Series.Sequence durationInFrames={90}>...</Series.Sequence>
  </Series>

Media:
  <OffthreadVideo src={staticFile('demo.mp4')} />
  <Audio src={staticFile('voiceover.mp3')} />

## Files

- .claude/skills/remotion/SKILL.md
- .claude/skills/remotion/reference.md (detailed API docs)

## Related

- elevenlabs (audio generation)
- ffmpeg (asset conversion)
```

---

## New Skill Flow

When creating a new skill:

### Step 1: Gather Information

```
Let's create a new skill.

Skill name: (e.g., "terminal-recording", "accessibility")
Description: (one sentence)
Category: (video, audio, automation, other)
```

### Step 2: Define Triggers

```
When should Claude use this skill?

List trigger phrases (one per line):
- "record terminal session"
- "asciinema"
- "terminal demo"
- "CLI recording"
```

### Step 3: Initial Content

```
What knowledge should this skill contain?

  1. I'll provide documentation/examples
  2. Help me research and build it
  3. Start with a minimal template
```

### Step 4: Create Skill Files

1. Create directory: `.claude/skills/{name}/`

2. Write `SKILL.md`:
```markdown
---
name: {name}
status: draft
description: {description}
triggers:
  - trigger1
  - trigger2
---

# {Name} Skill

{Description}

## When to Use

Use this skill when:
- {trigger context 1}
- {trigger context 2}

## Key Concepts

{Core knowledge}

## Common Patterns

{Code examples, commands, workflows}

## References

- {Links to documentation}
```

3. Optionally create `reference.md` for detailed documentation

4. Update `_internal/toolkit-registry.json`:
```json
{
  "skills": {
    "{name}": {
      "path": ".claude/skills/{name}/",
      "description": "Brief description of the skill",
      "status": "draft",
      "created": "YYYY-MM-DD",
      "updated": "YYYY-MM-DD"
    }
  }
}
```

### Step 5: Confirmation

```
Skill created: .claude/skills/{name}/

Files:
  ✅ SKILL.md - core skill knowledge
  ⬜ reference.md - add detailed docs later

Status: draft

Next steps:
  1. Add content to SKILL.md
  2. Test the skill in real usage
  3. Promote to beta once validated
  4. See _internal/ROADMAP.md for maturity process

⚠️  IMPORTANT: Restart Claude Code to load the new skill.
```

---

## Skill Maturity Levels

| Status | Meaning | Promotion Criteria |
|--------|---------|-------------------|
| **draft** | Just created, untested | Verify examples work |
| **beta** | Functional, needs validation | Use in real project |
| **stable** | Battle-tested, recommended | No known issues, complete docs |

### Promotion Process

**draft → beta:**
1. Verify all code examples work
2. Test core functionality
3. Document any issues in `_internal/reviews/`
4. Fix critical issues

**beta → stable:**
1. Use in a real project
2. Gather feedback
3. Complete documentation
4. No known critical issues

---

## Skill Structure Reference

```
.claude/skills/{name}/
├── SKILL.md         # Core knowledge (required)
│   - Frontmatter: name, status, description, triggers
│   - When to use
│   - Key concepts
│   - Common patterns
│
└── reference.md     # Detailed docs (optional)
    - API reference
    - Full examples
    - Troubleshooting
```

---

## Registry

Skills are tracked in `_internal/toolkit-registry.json`:

```json
{
  "skills": {
    "remotion": {
      "path": ".claude/skills/remotion/",
      "description": "Remotion video framework",
      "status": "stable",
      "created": "2025-12-04",
      "updated": "2025-12-04"
    }
  }
}
```

---

## Important Notes

**After creating or modifying skills:**
```
⚠️  Restart Claude Code to load changes.

Skills are loaded at startup. New skills, updated triggers,
or modified content won't take effect until you restart.
```

---

## Evolution

This command evolves through use. If something's awkward or missing:

**Local improvements:**
1. Say "improve this" → Claude captures in `_internal/BACKLOG.md`
2. Edit `.claude/commands/skills.md` → Update `_internal/CHANGELOG.md`
3. Share upstream → `gh pr create`

**Remote contributions:**
- Issues: `github.com/digitalsamba/claude-code-video-toolkit/issues`
- PRs welcome for new skills, improvements, documentation

History: Created as unified skill management command
