# Qwen-Edit Examples

Real results from experiments. This document will grow as we learn.

---

## Reframing Cropped Images (2026-01-04)

**Problem:** Portrait photo with head cropped at top (missing hair/forehead)

### What Failed

| Approach | Result |
|----------|--------|
| "Zoom out to show full scene" | Dark letterboxing borders around image |
| `--viewpoint three-quarter` | Silhouette with no face, complete disaster |
| "Reframe as portrait..." (no negative) | Blurry ghostly face, nightmare fuel |

### What Worked

**Prompt:**
```
Reframe this photo as a portrait composition with the woman's full head visible, positioned in the lower portion of the frame with sky above
```

**Negative:**
```
blur, blurry, ghostly, distortion, abstract, haze, fog, out of focus
```

**Result:** Clean portrait with full head, nice hair, clear face, professional look

### Variations Tested

| Settings | Result |
|----------|--------|
| steps=8, guidance=1.0 | Good baseline |
| steps=16, guidance=1.0 | Cleaner detail, nice clouds |
| steps=8, guidance=3.0 | More dramatic/windswept, moodier |
| steps=16, guidance=3.0 | Most "zoomed out", sharp, shows more torso |

**Conclusion:** The negative prompt was the key differentiator. Parameter tuning gave variations but all were usable once negative prompt was added.

---

## Character Transformations (2026-01-01)

From `docs/qwen-edit-patterns.md`:

| Transformation | Identity | Quality |
|----------------|----------|---------|
| James Bond (tux, casino) | Excellent | Excellent |
| Neo (Matrix, leather coat) | Good | Excellent |
| John Wick (tactical, neon) | Excellent | Excellent |
| Top Gun (flight suit) | Excellent | Excellent |
| Forrest Gump (running) | Good | Excellent |
| Indiana Jones (fedora, whip) | Good | Excellent |
| Peaky Blinders (flat cap) | Good | Excellent |
| Corporate headshot | Drifted | Good |
| Jedi (dark temple) | Lost | Poor |

**Key insight:** Dark scenes lose identity. Strong visual references (iconic costumes) work best.

---

## Background Replacement (2026-01-03)

**Status:** Generally fails with single-image approach - use multi-image compositing instead

| Attempt | Result |
|---------|--------|
| "Place in cottage interior" | Black void |
| "Place in garden" | Flat green with halo around subject |
| Multi-image compositing (generic prompts) | Merged faces incorrectly |

**Update (2026-01-04):** Multi-image compositing CAN work - see "Identity-Preserving Composites" below.

---

## Identity-Preserving Composites (2026-01-04)

**Problem:** Place a person into a new corporate/office scene while preserving their identity

### What Failed

| Approach | Result |
|----------|--------|
| "Place woman from first image into office from second" | Different person entirely |
| Mood words: "serene", "wellness", "coach" | Generic stock-photo face, lost identity |
| Very low guidance (1.0) | Artifacts, weird results |
| "Keep same face" (vague) | Ignored by model |
| Walking poses | More identity drift than static poses |

### What Worked

**Prompt:**
```
The Irish woman with shoulder-length wavy dark auburn hair from first image is now standing confidently in the open plan office from second image. Same warm friendly smile, same facial features, black blazer, professional.
```

**Negative:**
```
different ethnicity, different hair color, straight hair, different face shape, generic stock photo
```

**Settings:** steps=16, guidance=2.0

**Result:** Good identity preservation - hair, smile, pose, outfit all recognizable. Open plan office background integrated naturally.

### Prompt Pattern for Composites

```
The [ethnicity/nationality] [gender] with [specific hair: length, texture, color] from first image
is now [pose/action] in the [scene type] from second image.
Same [distinctive feature 1], same [distinctive feature 2], [outfit description].
```

### Key Insights

1. **Explicit identity anchors** - "Irish woman with shoulder-length wavy dark auburn hair" beats vague "same woman"
2. **Describe distinctive features** - Hair texture, color, specific outfit items help anchor identity
3. **Negative prompts for drift** - "different ethnicity, different hair color, straight hair" prevents common failures
4. **Mid guidance (2.0)** - Sweet spot for composites. Too low = artifacts, too high = identity loss
5. **Pose consistency** - Matching the original pose (e.g., arms crossed) preserves identity better than new poses
6. **Avoid mood words** - "Serene", "wellness", "coach" trigger generic stock-photo aesthetics

### Guidance Scale for Composites

| Guidance | Result |
|----------|--------|
| 1.0 | Artifacts, unpredictable |
| 1.5 | Better but still some drift |
| 2.0 | Best balance - identity preserved, good scene integration |
| 2.5 | Scene dominates, identity starts to drift |

---

## Pose and Camera Angle Changes (2026-01-04)

**Problem:** Change a person's pose or camera angle while preserving identity and outfit

### Pose Changes - What Worked

| Pose | Prompt Pattern | Result |
|------|----------------|--------|
| Arms open/welcoming | "Same woman, same face, same [outfit], but with arms at her sides in a relaxed open pose, welcoming body language" | ✅ Worked well |
| Hands on hips | "Same woman, same face, same [outfit], hands on hips power pose, confident leadership stance" | ✅ Worked well |

**Key:** Use negative prompt to exclude original pose: `"arms crossed, defensive pose"`

### Camera Angles - Mixed Results

| Angle | Prompt Pattern | Result |
|-------|----------------|--------|
| Three-quarter view | "three-quarter view angle, slightly turned to the right" | ❌ Minimal change |
| Low angle (looking up) | "camera angle from slightly below looking up, empowering perspective" | ✅ Worked |

### Settings

- **steps:** 14
- **guidance:** 2.0 (same as composites)

### Key Insights

1. **Pose changes work** - Arm positions, hand placement can be modified successfully
2. **Camera angles are inconsistent** - Vertical angle changes (low/high) work better than rotation (three-quarter)
3. **Be explicit about what to remove** - Negative prompt should exclude the original pose
4. **Identity preserved well** - Face and outfit remain consistent through pose changes

### Prompt Pattern for Pose Changes

```
Same woman, same face, same [outfit description], [new pose description], [mood/context]
```

**Negative:**
```
different person, different face, [original pose to remove]
```

---

## Template for Adding New Examples

```markdown
## [Use Case Name] (YYYY-MM-DD)

**Problem:** [What were you trying to achieve]

### What Failed
| Approach | Result |
|----------|--------|
| ... | ... |

### What Worked
**Prompt:** ...
**Negative:** ...
**Settings:** steps=X, guidance=Y
**Result:** [Description]

### Key Insight
[What we learned]
```
