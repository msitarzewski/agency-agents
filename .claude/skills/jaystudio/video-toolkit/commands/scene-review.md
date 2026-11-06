---
description: Scene-by-scene review in Remotion Studio (before voiceover)
---

# Scene Review

Interactive scene-by-scene review using Remotion Studio. Critical quality gate before voiceover generation.

## Quick Start

```
/scene-review           # Review all scenes from beginning
/scene-review title     # Jump to specific scene by type
/scene-review 3         # Jump to scene 3
```

## Example Session

```
$ /scene-review

Remotion Studio running at http://localhost:3000

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Scene 1 of 6: title (4s, frame 0)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Navigate to frame 0 in Studio and watch the scene.

[1] Approve  [2] Adjust  [3] Refine  [4] Flag  [5] Skip

> 3 (Refine)

Invoking video-design (direction from the project's design source)...
Reading TitleSlide.tsx and adjacent scenes for context...

What aspect needs refinement?
- Color palette feels too flat
- Text animation needs more impact
- Background too static

> Background too static

[Makes changes to TitleSlide.tsx]

Check Remotion Studio - it hot-reloads automatically.
Better? [y/n/more changes]

> y

Scene 1 approved. Moving to Scene 2...
```

## Iterative Feedback Loop

The review follows this cycle for each scene:

```
┌─────────────┐
│ View scene  │◄──────────────────────┐
│ in Studio   │                       │
└──────┬──────┘                       │
       │                              │
       ▼                              │
┌─────────────┐    ┌─────────────┐    │
│  Evaluate   │───►│   Adjust    │────┤
│             │    │ (config)    │    │
└──────┬──────┘    └─────────────┘    │
       │                              │
       │           ┌─────────────┐    │
       │──────────►│   Refine    │────┘
       │           │ (component) │
       │           └─────────────┘
       ▼
┌─────────────┐
│   Approve   │───► Next scene
└─────────────┘
```

- **Adjust**: Change config values (text, duration, asset paths) → hot-reload → verify
- **Refine**: Invoke video-design for visual improvements → edit component → hot-reload → verify

Repeat until the scene looks right, then approve and move on.

## Purpose

Verify what Remotion will actually render matches your expectations:
- Visual content correct
- Timing appropriate
- Assets present and working
- Scenes in right order

## Entry Point

```
1. Identify current project (from cwd or glob projects/*/project.json)
2. Locate the template's config file (e.g., demo-config.ts, sprint-config.ts)
3. Start Remotion Studio
4. Walk through scenes one by one
```

---

## Step 1: Start Remotion Studio

```bash
cd projects/{project-name}
npm run studio
```

**Tell the user:**
```
Remotion Studio is running at http://localhost:3000

Open this in your browser to preview your video.
```

---

## Step 2: Explain the Timeline

```
## Remotion Studio Timeline

The timeline at the bottom shows your video structure:

┌───────────────────────────────────────────────────────────────┐
│  [Seq 1] [Seq 2] [Seq 3] [Seq 4] [Seq 5] [Seq 6] [Seq 7] ... │
└───────────────────────────────────────────────────────────────┘

- Each segment = one sequence (scene) from your config
- Click anywhere to jump to that frame
- Drag to scrub through
- Frame counter shows position (at 30fps: frame 30 = 1 second)

**Navigation:**
- Click start of a segment to review that scene
- Use arrow keys for frame-by-frame
- Spacebar to play/pause
```

---

## Step 3: Scene-by-Scene Review

Read the scenes array from the config file. For each scene:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Scene {N} of {total}

**Type:** {scene.type}
**Duration:** {scene.durationSeconds}s ({scene.durationSeconds * 30} frames)
**Timeline:** Jump to frame {cumulative_start_frame}

→ In Remotion Studio, navigate to frame {cumulative_start_frame}
→ Watch this scene play through

**Check:**
- [ ] Visual content looks correct
- [ ] Timing feels right
- [ ] Any assets load properly

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Approve - looks good
2. Edit - need to change something in config
3. Refine - improve visuals with video-design
4. Flag - note an issue to address later
5. Skip - review later
```

**Important:** Do NOT try to interpret or format the scene content. Let the user see it in Remotion Studio - that's the source of truth.

---

## Step 4: Handle Review Actions

### Approve
- Record as reviewed in project.json
- Proceed to next scene

### Edit
Ask what needs to change:
- "What needs editing? (headline text, duration, asset path, etc.)"
- Open the config file
- Make the edit
- Remotion Studio hot-reloads automatically
- "Check Remotion Studio - does it look right now?"
- If yes, approve. If no, continue editing.

### Refine (video-design skill)
For visual/aesthetic improvements beyond config changes:
1. Use the project's design source (`project.json` `design.source`; if unset, offer the installed design skills
   and "ours", as in `/design` step 5), update `design.md`, then invoke `video-design`. Read
   `.claude/skills/remotion/motion-craft.md` for motion (timing in frames, read time, the defaults that look
   generated)
2. Read the slide component (e.g., `src/components/slides/TitleSlide.tsx`)
3. Also read adjacent scenes to understand the visual narrative arc
4. Work with user iteratively on:
   - Color palette and mood
   - Typography and text animations
   - Background effects and atmosphere
   - Motion and timing
   - Visual coherence with surrounding scenes
5. Apply changes to the component file
6. User verifies in Remotion Studio (hot-reloads)
7. Continue refining or approve when satisfied

**When to suggest Refine:**
- Slide scenes (title, problem, solution, stats, cta) that feel generic
- When user says something "doesn't feel right" or wants more impact
- When visual contrast between scenes needs work
- When animations feel too basic or too busy
- When the scene shows a default from motion-craft's "Defaults that look generated" list (every element fading
  and sliding up, a title that keeps drifting, floating shapes, three cards in a row)

### Flag
Record an issue without blocking:
```json
{
  "reviewIssues": [
    { "scene": N, "note": "user's description of issue" }
  ]
}
```
Proceed to next scene.

### Skip
- Don't mark as reviewed
- Can return later
- Proceed to next scene

---

## Step 5: Timing Summary

After reviewing all scenes, show totals:

```
## Timing Summary

| # | Type | Duration | Ends At |
|---|------|----------|---------|
{for each scene: | N | type | Xs | M:SS |}

**Total: {sum}s ({minutes}:{seconds})**
```

---

## Step 6: Completion

```
## Review Complete

Reviewed: {N}/{total} scenes
Issues flagged: {count}

{if all reviewed and no blocking issues}
Ready for voiceover. Run `/generate-voiceover`

{if issues exist}
Outstanding issues:
- Scene {N}: {issue note}
- Scene {M}: {issue note}

Address these before generating voiceover?
```

Update project.json:
- Add `reviewStatus` per scene
- Update `phase` to "audio" if complete
- Add session entry

---

## Sync Check (Optional)

If project.json scene count differs from config file:

```
⚠️  Config has {X} scenes, project.json has {Y} scenes

This can happen if scenes were added/removed manually.
Options:
1. Continue with config (what Remotion will render)
2. Sync project.json to match config
```

---

## Re-running Review

If `/scene-review` is run on an already-reviewed project:

```
Previous review found.

1. Review all scenes fresh
2. Review only unapproved/flagged scenes ({N})
3. View review summary
```

---

## Key Principles

1. **Remotion Studio is truth** - the preview shows exactly what will render
2. **Don't interpret content** - let the user see it visually
3. **One scene at a time** - focused attention
4. **Track progress** - know what's been reviewed
5. **Non-blocking flags** - note issues without stopping the flow
6. **Hot reload** - edit config, see changes immediately in Studio
