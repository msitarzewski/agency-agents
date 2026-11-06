# Qwen-Edit Prompting Guide

## Prompt Structure

**Optimal length:** 50-200 characters (short and specific beats long and detailed)

**Formula:** `[Action], [details], [constraints]`

## Always Include Constraints

Preservation constraints significantly improve results:
- "Keep face unchanged"
- "Maintain original pose"
- "Preserve facial features"
- "Keep expression the same"
- "Preserve the person's identity"

## Prompt Patterns

### Reframing (Fix Cropped Images)

When head/body is cropped out of frame:

```
Reframe this photo as a portrait composition with the woman's full head visible, positioned in the lower portion of the frame with sky above
```

**Critical:** Pair with negative prompt to avoid artifacts:
```
--negative "blur, blurry, ghostly, distortion, abstract, haze, fog, out of focus"
```

**What doesn't work for cropped images:**
- "Zoom out" - adds letterboxing/black borders
- "Viewpoint change" - destroys identity, creates silhouettes
- "Extend the image" - not an outpainting model

### Character Transformations

```
"{Character name}, wearing {costume details}, {pose/action}, {background}, {lighting style}, {aesthetic keywords}"
```

Examples:
- `"James Bond 007, wearing a tuxedo with bow tie, holding a martini glass, casino background, suave and sophisticated, cinematic lighting, spy thriller aesthetic"`
- `"Neo from The Matrix, wearing long black leather trench coat, dark sunglasses, green digital rain code background, cyberpunk aesthetic"`

### Style Transfer

```
"Apply {style} style" or "Restyle as {style}"
```

Examples:
- `"Apply Monet impressionist style, like Water Lilies"`
- `"Restyle as cyberpunk with neon lighting"`
- `"Make it look like a vintage 1970s photograph"`

### Clothing/Accessory Changes

```
"Change {item} to {new item}, maintain pose"
```

Examples:
- `"Change blue t-shirt to red hoodie, maintain pose"`
- `"Add sunglasses and a warm smile"`
- `"Replace jacket with leather bomber jacket"`

### Lighting/Color

```
"{Lighting effect}, {mood keywords}"
```

Examples:
- `"Add warm sunset tones, golden hour lighting"`
- `"Cinematic dramatic lighting with shadows"`
- `"Enhance lighting, studio portrait quality"`

## What Makes Prompts Fail

| Problem | Why |
|---------|-----|
| Too vague | "Make it better" - no specific direction |
| Too long | 350+ chars - model gets confused |
| Background replacement | "Place in X" creates halos/artifacts |
| Extreme changes | Fundamentally altering the scene |
| Dark scenes | Identity gets lost in shadows |

## Negative Prompts

Always consider what to avoid:

| Use Case | Negative Prompt |
|----------|-----------------|
| Reframing | blur, blurry, ghostly, distortion, abstract, haze, fog, out of focus |
| Zoom out | black borders, letterbox, vignette, dark edges, frames, cropped |
| Portraits | deformed, disfigured, bad anatomy, extra limbs |
| Style transfer | photo-realistic (if you want artistic) |
