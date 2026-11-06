---
description: Guided Playwright browser recording
---

# Record Browser Demo

Help me record a browser demo for a Remotion video project.

## Project Integration

Before gathering configuration, check if we're in a project context:

1. **Check for active project:**
   - Look for `project.json` in current directory or parent `projects/*/`
   - If found, read it to understand:
     - Which scenes need demo recordings
     - Expected asset paths
     - Scene instructions

2. **If project context found:**
   ```
   I see you're working on: {project.name}

   Scenes needing recordings:
     ⬜ Scene 3: Dark mode demo → demos/dark-mode.mp4
        Instructions: Navigate to Settings → Toggle dark mode
     ⬜ Scene 5: Login flow → demos/login.mp4
        Instructions: Show login → enter credentials → redirect

   Which scene would you like to record? (or enter a new recording)
   ```

3. **After recording completes:**
   - Update `project.json` scene status to `"asset-present"`
   - Add session entry
   - Regenerate project CLAUDE.md

---

## Your Tasks

1. **Gather Recording Configuration**
   Use the AskUserQuestion tool to collect the following information:

   **Question 1 - Basic Setup:**
   - URL to record (e.g., "https://myapp.com/dashboard")
   - Output filename (without extension, e.g., "dashboard-walkthrough")

   **Question 2 - Output Location:**
   Ask where to save the recording. Options:
   - `./output` (default, local to playwright folder)
   - Detect from current project (look for nearest `public/demos/` folder)
   - Custom path (let user specify)

   **Question 3 - Viewport:**
   - 1080p (1920x1080) - Default, matches Remotion
   - 720p (1280x720) - Smaller files
   - Mobile (390x844) - iPhone 14 size
   - Custom dimensions

   **Question 4 - Recording Mode:**
   - **Interactive** - Opens a visible browser window. User manually performs actions while it records. Good for exploring or one-off recordings.
   - **Script Template** - Generates a TypeScript file in `playwright/scripts/flows/` with boilerplate. User edits the script to add specific actions, then runs it. Good for repeatable recordings.

   **Question 5 - Window Scale (for laptops):**
   - 75% (default) - Fits MacBook screens, records at full 1080p
   - 100% - Full size window (needs large monitor)
   - 50% - Very small window for tiny screens

   **Question 6 - Additional Settings (optional):**
   - slowMo delay (default: 50ms, suggest 75-100ms for complex UIs)
   - Recording duration limit (optional, for interactive mode)

2. **Execute the Recording**

   **For Interactive Mode:**
   Run the interactive recording script:
   ```bash
   cd REPO_ROOT/playwright
   npx tsx scripts/record-interactive.ts \
     --url "USER_URL" \
     --name "USER_NAME" \
     --output "USER_OUTPUT_DIR" \
     --viewport "USER_VIEWPORT" \
     --scale USER_SCALE \
     --slowMo USER_SLOWMO
   ```

   Note: Default scale is 0.75 (75%) which fits laptop screens while recording at full 1080p.

   **For Script Template Mode:**
   a) Generate a new script file at `playwright/scripts/flows/{name}-recording.ts`
   b) Use the template pattern from `form-demo.ts` but customize:
      - Set the URL
      - Set output name and directory
      - Set viewport
      - Add helpful comments for the user to fill in actions
   c) Tell the user how to run it: `npx tsx scripts/flows/{name}-recording.ts`

3. **Report Results**
   After recording completes, report:
   - File path of the saved MP4
   - Duration in seconds
   - Frame count at 30fps
   - The exact value to use in `sprint-config.ts`: `durationSeconds: X`

## Script Locations

- Interactive script: `playwright/scripts/record-interactive.ts`
- Flow templates: `playwright/scripts/flows/`
- Output (default): `playwright/output/`

## Viewport Presets

| Name | Dimensions | Use Case |
|------|------------|----------|
| 1080p | 1920x1080 | Default, matches Remotion |
| 720p | 1280x720 | Smaller file size |
| Mobile | 390x844 | iPhone 14 |
| Tablet | 1024x768 | iPad landscape |

## Tips to Share with User

- **Stopping**: Press `Esc` key in the browser window, or `Ctrl+C` in terminal
- **Interactive mode**: The browser will open and start recording immediately. Perform your actions naturally. Recording continues across page navigations.
- **Script mode**: Edit the generated file to add your click/fill/scroll actions, then run it as many times as needed for a clean take.
- **Debugging**: If the recording doesn't look right, re-run with `DEBUG=true` prefix to see the browser in script mode.
- **Cursor**: The orange cursor dot and click ripples are automatically added.
- **Scale**: Default 75% scale fits laptop screens while still recording at full 1080p resolution.
- **Cookie banners**: Common cookie consent popups are automatically dismissed.

---

## Evolution

This command evolves through use. If something's awkward or missing:

**Local improvements:**
1. Say "improve this" → Claude captures in `_internal/BACKLOG.md`
2. Edit `.claude/commands/record-demo.md` → Update `_internal/CHANGELOG.md`
3. Share upstream → `gh pr create`

**Remote contributions:**
- Issues: `github.com/digitalsamba/claude-code-video-toolkit/issues`
- PRs welcome for recording features, browser support, documentation
