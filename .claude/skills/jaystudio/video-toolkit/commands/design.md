# Design

Sets and refines how a video looks with the `video-design` skill, taking direction from the project's design
source: plug in your own design skill (taste-skill, Anthropic's frontend-design, a team's own), or use ours
(video-design's act palettes with the brand).

It works at any phase, including before a single scene is built:
- **Direction** (the whole video): pick the design source and write `design.md` (acts, a field per act, ink, the
  one accent, the type steps). `/video` runs this for a new project; `/design` runs it for a project made without
  it, or to change direction.
- **Refine** (one scene): restyle a scene within `design.md`.
- **Critique** (the whole video): a contact sheet of the render, read against `design.md`.

## Usage

```
/design              # No design.md yet: set the direction. Otherwise: choose direction, a scene, or critique
/design direction    # Set or change the whole video's direction
/design [scene-id]   # Refine one scene
/design critique     # Contact sheet + critique of the latest render
```

---

## Step 1: Discover Project Context

First, find and understand the current project:

1. **Locate the project**
   - Check if in a project directory (has `project.json` or template config)
   - If not, scan `projects/` for active projects
   - If multiple, ask user which project

2. **Read project configuration**
   - `project.json` if exists (scenes, phase, brand)
   - Or template config: `src/config/sprint-config.ts` or `src/config/demo-config.ts`
   - Brand/theme: `src/config/theme.ts`

3. **Build scene inventory**
   - List all scenes from config, or from `project.json` / the scene plan if nothing is built yet
   - Identify which are slide-type (designable) vs demo-type (video playback)
   - Note each scene's purpose from config content

4. **Pick the mode**
   - `direction`, `critique` or a scene id given: do that.
   - No argument and no `design.md`: **Direction** ("Design source", then "Direction for the whole video").
     Refining a scene before the video has a direction restyles it twice.
   - No argument and `design.md` exists: ask whether to change the direction, refine a scene (Step 2), or
     critique the render (Step 8).

---

## Design source

If `project.json` has `design.source`, use it. Otherwise ask, offering only: "ours", the
registry's `designSources` that are installed in this session (match each `skill` with or without a plugin
prefix), and "another design skill". Don't scan every installed skill for design words; that offers skills
that aren't design sources. A recommended source that isn't installed can be mentioned with its `install` line:

```
Which design source should set the direction?
1. Ours: video-design's act palettes with brands/{brand}/ (nothing to install)
2. taste-skill (recommended, installed)
3. frontend-design (installed)
4. Another design skill (name it)
```

Save the answer as `"design": {"source": "<registry key, or the skill's name if unlisted>", "file": "design.md"}`
in `project.json` (e.g. `"taste-skill"`), so later sessions don't ask again. The rules are in
`.claude/skills/video-design/sources.md`.

---

## Direction for the whole video

1. Choose the design source (above).
2. Invoke the source with the scene plan (what each scene says, where the story turns), the audience, the format
   (16:9 or 9:16) and the brand. For ours, pick an act palette from `.claude/skills/video-design/palettes.md`.
3. Invoke `video-design` to map the direction onto the video: acts at the story's turns, a field per act, ink,
   the one accent, the five type steps, a ground from the subject where a field would otherwise be dull.
4. Show a one-line-per-act summary and let the user redirect before writing anything.
5. Write `design.md` (`.claude/skills/video-design/handoff.md`) and `project.json` `design`, then put the values in
   the theme or brand config so every scene picks them up. Scenes that are already built are then refined one at a
   time (Step 2 onward), starting with the title, which sets the video's title edge.

---

## Step 2: Identify Target Scene

If no scene specified in command, show discovered scenes:

```
## Design Refinement

**Project:** {project_name}
**Template:** {template_type}

Which scene would you like to refine?

| # | Scene ID | Type | Description |
|---|----------|------|-------------|
{list slide-type scenes discovered from config}

(Demo/video scenes are not shown - they display recorded content)

Enter scene ID or number:
```

---

## Step 3: Understand Scene Context

Before asking the design source for direction, gather specific context:

1. **Read the target slide component**
   - Find component file from scene type mapping
   - e.g., `src/components/slides/{Type}Slide.tsx`

2. **Read scene content from config**
   - What text/data does this scene display?
   - What's the intended message?

3. **Understand position in sequence**
   - What scene comes before? What mood does it leave?
   - What scene comes after? What mood should we set up?

4. **Check current mood/intent** (if defined in project.json)
   - If scene has `designNotes.mood`, use that
   - If not, infer from content or ask user

---

## Step 4: Establish Scene Mood

If the scene doesn't have a defined mood, ask the user:

```
## Scene Mood

What feeling should the "{scene_id}" scene evoke?

The scene contains: {brief content summary}
It follows: {previous scene summary}
It leads to: {next scene summary}

Suggested moods based on content:
- {suggestion_1}
- {suggestion_2}

Or describe the mood you want:
```

Common mood dimensions:
- **Energy**: calm ↔ energetic
- **Tone**: serious ↔ playful
- **Warmth**: cool/professional ↔ warm/inviting
- **Trust**: edgy/provocative ↔ safe/reliable

---

## Step 5: Direction, then the video layer

1. **Design source:** as in "Design source" above (already saved in `project.json` after the first session).
2. **Get the direction** from that source (invoke the skill with the scene's purpose, mood, neighbours and brand),
   or, for ours, pick an act palette from `.claude/skills/video-design/palettes.md`.
3. **Write or update `design.md`** in the project, in the shape in `.claude/skills/video-design/handoff.md`:
   acts, a field per act, ink, the one accent, the five type steps, rules turned off and why. If the project
   already has one, change only what this session decides.
4. **Invoke `video-design`** to apply it. Its rules hold whatever the source said (colour changes only at a
   narrative turn, one data accent, two-line titles, five sizes); motion follows
   `.claude/skills/remotion/motion-craft.md`. Where a source suggests a gradient, glow or decorative effect, the
   video rule wins unless the brand requires it, and the exception goes under "Rules turned off".

---

## Step 6: Iterative Refinement

Work with user in a back-and-forth loop:

1. **Propose changes** - Explain the design direction
2. **Implement** - Edit the component file
3. **Preview** - User checks Remotion Studio (hot-reload)
4. **Feedback** - User responds with what works/doesn't
5. **Refine** - Adjust based on feedback
6. **Repeat** until satisfied

**Common refinement areas:**
- Colour by act (which field this scene's act has, and whether a change here marks a turn)
- Typography (the five steps in design.md, line breaks, the title edge)
- Color palette (mood, contrast, warmth/coolness)
- Motion (timing, easing, entrance/exit)
- Decorative elements (taken from the subject or brand; particles, floating shapes and glows only on purpose)
- Visual hierarchy (what draws the eye)

---

## Step 7: Ensure Coherence

After refining a scene, consider its neighbors:

```
Does this scene:
- [ ] Flow naturally from the previous scene?
- [ ] Set up the next scene appropriately?
- [ ] Maintain consistent visual language with brand?
- [ ] Create appropriate contrast where needed?
```

If adjacent scenes need adjustment, offer to refine them too.

---

## Step 8: Look at the whole video

After a render, tile one settled frame per scene and critique it with `.claude/skills/video-design/critique.md`:

```bash
uv run tools/contact_sheet.py out/video.mp4
```

---

## Step 9: Document Changes

Update project.json (if exists) with refinement notes:

```json
{
  "scenes": [
    {
      "id": "{scene_id}",
      "designNotes": {
        "mood": "{established mood}",
        "refinements": "{description of visual changes made}"
      }
    }
  ]
}
```

Add session entry:
```json
{
  "sessions": [
    {
      "date": "YYYY-MM-DD",
      "summary": "Design refinement on {scene_id}: {brief description}"
    }
  ]
}
```

---

## Design Principles for Video

Whatever the design source, on video scenes (the full rules are in `.claude/skills/video-design/SKILL.md`):

1. **Video scale** - Everything needs to be larger than web UI (viewers are farther from screen)
2. **Motion matters** - Static designs that work on web may feel dead on video
3. **Time constraints** - Each scene has limited duration; don't over-animate
4. **Narrative arc** - Consider how visual intensity builds across scenes
5. **Contrast creates impact** - A calm scene makes the next dramatic scene hit harder
6. **Avoid the generated look** - Check the scene against "Defaults that look generated" in
   `.claude/skills/remotion/motion-craft.md`, and record any you keep on purpose in `designNotes`

---

## Scene Type Reference

These are common scene types, but projects may have different ones:

| Type | Common Purpose | Design Considerations |
|------|----------------|----------------------|
| title | Opening, brand intro | Set the mood, establish visual language |
| overview | Agenda, summary | Clarity, scannable layout |
| demo | Show functionality | Clean chrome, focus on content |
| summary | Recap, stats | Data visualization, credibility |
| credits | Closing | Graceful exit, brand reinforcement |
| problem | Pain points | Tension (if narrative calls for it) |
| solution | Resolution | Relief, hope |
| cta | Call to action | Energy, memorability |

**Note**: Not all projects use all types. The command discovers what's actually in the project.

---

## Example Session

```
User: /design

Claude: Let me discover your project...

Found project: "q4-release-video"
Template: sprint-review
Brand: digital-samba

## Design Refinement

Which scene would you like to refine?

| # | Scene ID | Type | Description |
|---|----------|------|-------------|
| 1 | title | title | "What's New in v2.5" |
| 2 | overview | overview | 4 feature highlights |
| 3 | summary | summary | Sprint stats |
| 4 | credits | credits | Team acknowledgment |

(3 demo scenes not shown)

User: 1

Claude: Let me gather context for the title scene...

[Reads TitleSlide.tsx, sprint-config.ts, theme.ts]
[Reads overview scene to understand what follows]

The title announces "What's New in v2.5" for Digital Samba.
It's followed by an overview of 4 features.

What mood should this title scene set?
- Excited/energetic (big release energy)
- Professional/trustworthy (enterprise feel)
- Warm/welcoming (team celebration)

User: Warm and celebratory - this was a big team effort

Claude: Got it - warm, celebratory mood for a team achievement.

Design source for this project: taste-skill (saved in project.json).
[taste-skill deals a direction; design.md records the acts, fields and type steps]
Invoking video-design...

I'll implement:
1. The title on the brand's identity field (orange), black ink, the version number at the figure size
2. The title broken by hand onto two lines, on the video's one title edge
3. The team names revealed on the narration's words, not one fade for everything
4. The next scene (overview) on the record field, so the cut marks the turn from "what" to "how"

[Makes changes]

Check Remotion Studio - how does it feel?
```
