---
name: qwen-edit
description: AI image editing prompting patterns for Qwen-Image (Qwen-Image-Edit-2511 by default, Qwen-Image-2.1 as a non-commercial Modal opt-in). Use when editing photos while preserving identity, reframing cropped images, changing clothing or accessories, adjusting poses, applying style transfers, or character transformations. Provides prompt patterns, parameter tuning, and examples.
---

# Qwen-Image-Edit Skill

AI-powered image editing via `tools/image_edit.py`. The model depends on the deployment:

| Deployment | Model | License | Defaults | Max inputs |
|-----------|-------|---------|----------|------------|
| `--cloud modal` (default) | Qwen-Image-Edit-2511 | Apache-2.0, commercial OK | 8 steps, guidance 1.0 | 3 images |
| `--cloud modal`, app deployed with `IMAGE_EDIT_MODEL=qwen-image-2.1` | **Qwen-Image-2.1** (2026-09, unified gen+edit, 7B DiT, RGBA) | Qwen Research License -- **non-commercial** ("research or evaluation purposes only") | 40 steps, guidance 1.0 (no CFG) | 10 images |
| `--cloud runpod` | Qwen-Image-Edit-2511 + Lightning LoRA | Apache-2.0, commercial OK | 8 steps, guidance 1.0 | 3 images |

The tool prints `Model:` and `Steps:` after each edit, so you can tell which model the Modal app
runs and how many steps it took. Without `--steps`, each model runs its own default above.
Opt in with `IMAGE_EDIT_MODEL=qwen-image-2.1 uv run modal deploy docker/modal-image-edit/app.py`;
deploy again without it to switch back.

**Status:** Evolving - learnings being captured as we experiment. The prompt
patterns and parameter findings in `examples.md` / `parameters.md` were measured
on 2511; re-check them on 2.1 before relying on the exact numbers.

### Qwen-Image-2.1 specifics (Modal opt-in)

- **Not step-distilled** -- 40 steps is the model card default. The old 8-step
  default was tuned for 2511's Lightning LoRA, which 2.1 doesn't have here, so expect
  low step counts to cost quality (untested).
- **Sampled without guidance.** `--guidance 1.0` (default) is how the model is meant
  to run. `>1` switches on true CFG (blank negative prompt if you pass none) and
  doubles the cost of every step.
- **Multi-image:** the first `--input` is the image being edited ("image 1"); the
  rest are references in order ("image 2", ...). Up to 10. Output size follows the
  first image's aspect ratio at ~1MP.
- **Local edits:** draw a circle or paint an annotation on the image, or pass a
  separate mask as an extra `--input`, and say what to change there
  (e.g. "Remove the watch inside the red circle").
- **RGBA:** transparent PNG inputs keep their alpha. For a cut-out, prompt
  `"This is an RGBA image with transparency. <subject>. The image has alpha channel
  and the background is transparent."` -- the result comes back as an RGBA PNG only
  when the model actually produced transparency.

## When to Use This Skill

Use when the user wants to:
- Edit/transform photos while preserving identity
- Reframe cropped images (fix cut-off heads, etc.)
- Change clothing, add accessories
- Change pose (arm positions, hand placement)
- Apply style transfers (cyberpunk, anime, oil painting)
- Adjust lighting/color grading
- Add/remove objects
- Character transformations (Bond, Neo, etc.)

## When NOT to Use

- **Background replacement (single image)** - creates cut-out artifacts, halos
- **Face swapping** - cannot preserve identity from reference
- **Outpainting** - can't extend canvas reliably

## Use With Care

- **Multi-image compositing** - CAN work with explicit identity anchors (see examples.md for prompt patterns). Requires describing distinctive features (hair texture/color, ethnicity, outfit) and using guidance ~2.0
- **Camera angle changes** - Inconsistent results. Vertical angles (low/high) work better than rotational (three-quarter view)

## Quick Reference

```bash
# Basic edit
uv run tools/image_edit.py --input photo.jpg --prompt "Add sunglasses"

# With negative prompt (recommended)
uv run tools/image_edit.py --input photo.jpg \
  --prompt "Reframe as portrait with full head visible" \
  --negative "blur, distortion, artifacts"

# Style transfer
uv run tools/image_edit.py --input photo.jpg --style cyberpunk

# Background (use cautiously - often fails)
uv run tools/image_edit.py --input photo.jpg --background office

# Higher quality (RunPod / 2511 -- on Modal / 2.1 the 40-step default already is)
uv run tools/image_edit.py --input photo.jpg --prompt "..." --steps 16 --guidance 3.0 --cloud runpod

# Extract the subject onto a transparent background (Modal / 2.1)
uv run tools/image_edit.py --input product.jpg   --prompt "This is an RGBA image with transparency. The product from the photo. The image has alpha channel and the background is transparent."   --output product_cutout.png

# Multi-image composite (identity-preserving) -- settings tuned on RunPod / 2511
uv run tools/image_edit.py --input person.jpg background.jpg \
  --prompt "The [ethnicity] [gender] with [hair description] from first image is now in [scene] from second image. Same [features], [outfit]." \
  --negative "different ethnicity, different hair color, different face shape, generic stock photo" \
  --steps 16 --guidance 2.0 --cloud runpod

# Multi-image composite on Modal / 2.1 -- up to 10 references, defaults usually suffice
uv run tools/image_edit.py --input person.jpg outfit.jpg shoes.jpg background.jpg \
  --prompt "The person from image 1 wearing the outfit from image 2 and the shoes from image 3, standing in the scene from image 4. Same face and hair."
```

## Key Files

- `prompting.md` - Prompt patterns and structure
- `examples.md` - Good/bad examples from experiments
- `parameters.md` - Tuning steps, guidance, negative prompts

## Tool Location

`tools/image_edit.py` - CLI wrapper for the Modal (`docker/modal-image-edit/`) and RunPod
(`docker/runpod-qwen-edit/`) endpoints

## Related Docs

- `docs/qwen-edit-patterns.md` - Character transformation patterns
- `.ai_dev/qwen-edit-research.md` - Research notes
