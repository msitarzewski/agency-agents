---
name: remotion
description: Toolkit-specific Remotion patterns — custom transitions, shared components, and project conventions. For core Remotion framework knowledge (hooks, animations, rendering, etc.), see the `remotion-official` skill.
---

# Remotion — Toolkit Extensions

> **Core Remotion knowledge** lives in `.claude/skills/remotion-official/` (synced from the official [remotion-dev/skills](https://github.com/remotion-dev/skills) repo). This file covers **toolkit-specific** patterns only.

## Shared Components

Reusable video components in `lib/components/`. Import in templates via:

```tsx
import { AnimatedBackground, SlideTransition, Label } from '../../../../lib/components';
```

| Component | Purpose |
|-----------|---------|
| `AnimatedBackground` | Floating shapes background (variants: subtle, tech, warm, dark) |
| `SlideTransition` | Scene transitions (fade, zoom, slide-up, blur-fade) |
| `Label` | Floating label badge with optional JIRA reference |
| `Vignette` | Cinematic edge darkening overlay |
| `LogoWatermark` | Corner logo branding |
| `SplitScreen` | Side-by-side video comparison |
| `NarratorPiP` | Picture-in-picture presenter overlay |
| `Envelope` | 3D envelope with opening flap animation |
| `PointingHand` | Animated hand emoji with slide-in and pulse |
| `MazeDecoration` | Animated isometric grid decoration for corners |

## Motion Craft

Before animating a scene, read [motion-craft.md](motion-craft.md). It covers durations and staggers in frames,
choosing an ease by what the move does, springs by damping ratio, read time for on-screen text, a beat grid that
doesn't drift, transitions with a cause, and the defaults that make a video look generated (several of which
toolkit components produce unless you choose otherwise).

## Custom Transitions

The toolkit includes a transitions library at `lib/transitions/` for scene-to-scene effects beyond the official `@remotion/transitions` package.

### Using TransitionSeries

```tsx
import { TransitionSeries, linearTiming } from '@remotion/transitions';
// Import custom transitions from lib (adjust path based on your project location)
import { glitch, lightLeak, clockWipe, checkerboard } from '../../../../lib/transitions';
// Or import from @remotion/transitions for official ones
import { slide, fade } from '@remotion/transitions/slide';

<TransitionSeries>
  <TransitionSeries.Sequence durationInFrames={90}>
    <TitleSlide />
  </TransitionSeries.Sequence>
  <TransitionSeries.Transition
    presentation={glitch({ intensity: 0.8 })}
    timing={linearTiming({ durationInFrames: 30 })}
  />
  <TransitionSeries.Sequence durationInFrames={120}>
    <ContentSlide />
  </TransitionSeries.Sequence>
</TransitionSeries>
```

### Available Custom Transitions

| Transition | Options | Best For |
|------------|---------|----------|
| `glitch()` | `intensity`, `slices`, `rgbShift` | Tech demos, edgy reveals, cyberpunk |
| `rgbSplit()` | `direction`, `displacement` | Modern tech, energetic transitions |
| `zoomBlur()` | `direction`, `blurAmount` | CTAs, high-energy moments, impact |
| `lightLeak()` | `temperature`, `direction` | Celebrations, film aesthetic, warm moments |
| `clockWipe()` | `startAngle`, `direction`, `segments` | Time-related content, playful reveals |
| `pixelate()` | `maxBlockSize`, `gridSize`, `scanlines`, `glitchArtifacts`, `randomness` | Retro/gaming, digital transformations |
| `checkerboard()` | `gridSize`, `pattern`, `stagger`, `squareAnimation` | Playful reveals, structured transitions |

**Checkerboard patterns:** `sequential`, `random`, `diagonal`, `alternating`, `spiral`, `rows`, `columns`, `center-out`, `corners-in`

### Transition Examples

```tsx
// Tech/cyberpunk feel
glitch({ intensity: 0.8, slices: 8, rgbShift: true })

// Warm celebration
lightLeak({ temperature: 'warm', direction: 'right' })

// High energy zoom
zoomBlur({ direction: 'in', blurAmount: 20 })

// Chromatic aberration
rgbSplit({ direction: 'diagonal', displacement: 30 })

// Clock sweep reveal
clockWipe({ direction: 'clockwise', startAngle: 0 })

// Retro pixelation
pixelate({ maxBlockSize: 50, glitchArtifacts: true })

// Checkerboard patterns
checkerboard({ pattern: 'diagonal', gridSize: 8 })
checkerboard({ pattern: 'spiral', gridSize: 10 })
checkerboard({ pattern: 'center-out', squareAnimation: 'scale' })
```

### Transition Duration Guidelines

| Type | Frames | Notes |
|------|--------|-------|
| Quick cut | 15-20 | Fast, punchy |
| Standard | 30-45 | Most common |
| Dramatic | 50-60 | Slow reveals |
| Glitch effects | 20-30 | Should feel sudden |
| Light leak | 45-60 | Needs time to sweep |

### Preview Transitions

Run the showcase gallery to see all transitions:

```bash
cd showcase/transitions && npm run studio
```

## Toolkit Conventions

These are choices specific to this toolkit. For general Remotion best practices (interpolation clamping, `useVideoConfig`, `delayRender`, `staticFile`, no CSS animations), see the `remotion-official` skill.

1. **All projects use 30fps** — Timing: frames = seconds × 30
2. **playbackRate must be constant** — For variable/extreme speeds, pre-process with FFmpeg
3. **Video/audio components** — Templates use `<OffthreadVideo>` and `<Audio>` from `remotion`. Upstream now also documents `<Video>`/`<Audio>` from `@remotion/media` (newer, has trim props + pitch shifting). Both render correctly; prefer the toolkit's choice when extending existing templates for consistency.

## Project Timing Conventions

| Scene Type | Duration | Notes |
|------------|----------|-------|
| Title | 3-5s (90-150f) | Logo + headline |
| Overview | 10-20s | 3-5 bullet points |
| Demo | 10-30s | Adjust playbackRate to fit |
| Stats | 8-12s | 3-4 stat cards |
| Credits | 5-10s | Quick fade |

**Pacing:** ~150 words/minute for voiceover. Voiceover drives timing.

## Advanced API

For detailed API documentation on all hooks, components, renderer, Lambda, and Player APIs, see [reference.md](reference.md).

## License Note

Remotion has a special license. Companies may need to obtain a license for commercial use. Check https://remotion.dev/license

---

## Feedback & Contributions

If this skill is missing information or could be improved:

- **Missing a pattern?** Describe what you needed
- **Found an error?** Let me know what's wrong
- **Want to contribute?** I can help you:
  1. Update this skill with improvements
  2. Create a PR to github.com/digitalsamba/claude-code-video-toolkit

Just say "improve this skill" and I'll guide you through updating `.claude/skills/remotion/SKILL.md`.
