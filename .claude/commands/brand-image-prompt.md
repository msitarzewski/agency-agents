# /brand-image-prompt

Generate a production-ready AI image prompt for a Telcoin Association tweet graphic.

## Usage
Provide the tweet text or topic. This skill will output a complete prompt formatted for Midjourney, Flux, or DALL-E 3, using the official brand guidelines.

## What you must do

1. Read `strategy/BRAND-GUIDE.md` before generating any prompt
2. Read the tweet text provided (or use $ARGUMENTS as the tweet topic/text)
3. Generate THREE prompt variants:
   - **Variant A**: Dark background (primary) - TEL Black #090920 base with glowing blue elements
   - **Variant B**: Abstract/conceptual - no text in image, pure visual metaphor for the tweet topic
   - **Variant C**: Human-focused - if the topic involves real people, inclusion, or mobile users

## Prompt structure (apply to all variants)

Each prompt must include, in order:
1. **Subject**: What the image depicts, tied to the tweet topic
2. **Style**: "digital art, institutional brand photography, governance aesthetic"
3. **Lighting**: "glowing electric blue light, deep shadows, high contrast"
4. **Geometry**: "hexagonal geometric shapes, crystalline structure, layered glass panels"
5. **Color palette** (mandatory, exact):
   - Background: deep navy to near-black (#090920 TEL Black)
   - Primary accent: Royal Blue (#3642B2)
   - Highlight: Electric cyan-blue (#14C8FF)
   - Text-safe areas: dark glass panels with subtle translucency
6. **Composition**: "left-aligned layout, rule of thirds, negative space on right for text overlay"
7. **Aspect ratio**: "--ar 16:9" for tweet header; "--ar 1:1" for tweet card insert
8. **Quality**: "--v 6 --style raw --q 2" (Midjourney) or equivalent for other tools
9. **Negative prompt** (Midjourney --no flag): "text, watermark, logo, cartoon, anime, neon, rainbow, busy background, cluttered, stock photo, cheesy corporate"

## Brand rules for image content

- No text rendered inside the AI-generated image (text is placed in post-production via Figma)
- Never generate images that look promotional or consumer-brand (no smiling people holding phones in ads)
- Human subjects: diverse, professional, real-world contexts (not staged stock photo looks)
- Never use: explosions, confetti, rocket ships, moon imagery, upward arrows as visual metaphors
- Safe metaphors for Telcoin: networks/nodes, mobile devices in real use, currency/transaction flows as light paths, governance/institution imagery (neutral meeting rooms, documents), telecom infrastructure (towers, fiber, data centers)

## Output format

Return:

### Variant A — Dark/Glowing (PRIMARY)
```
[full prompt text]
```
**Tool**: Midjourney / Flux / DALL-E 3
**Best for**: Tweet header image, thread opener

### Variant B — Abstract/Conceptual
```
[full prompt text]
```
**Best for**: Mid-thread visual break, data point illustration

### Variant C — Human-Focused (if applicable)
```
[full prompt text]
```
**Best for**: Financial inclusion narrative, user story tweets

### Post-production notes
- Import into Figma with brand template
- Place New Hero Bold for headline text over dark glass panel area
- Logo: top-left, horizontal version, 1 mark height from top
- Color-correct to match exact hex values if AI output drifts

$ARGUMENTS
