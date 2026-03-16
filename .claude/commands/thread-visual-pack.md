# /thread-visual-pack

Generate a coordinated set of visual briefs for an entire tweet thread - header card, supporting inserts, and a visual system that reads as a coherent series.

## Usage
Provide the thread file path or paste the thread content via $ARGUMENTS. This skill produces a complete visual pack: one header card brief + briefs for 2-3 supporting insert cards + AI image prompts for each.

## What you must do

1. Read `strategy/BRAND-GUIDE.md` before generating anything
2. Read the thread content from $ARGUMENTS (file path or pasted text)
3. Analyze the thread structure:
   - Identify the 1 opening tweet (always gets a header card)
   - Identify 2-3 tweets that would benefit from a supporting visual (data points, architecture diagrams, key claims)
   - Note the content tier (1/2/3/4) - this determines how much visual decoration is appropriate
4. Define a **visual system** for the thread - a consistent look that ties all cards together
5. Generate individual briefs for each card
6. Generate AI image prompts for each card that requires a generated visual

## Output format

---

## Thread Visual Pack

**Thread**: [title or first tweet excerpt]
**Content tier**: [1/2/3/4]
**Total cards**: [N]
**Visual theme**: [1-sentence description of the visual system]

---

### Visual System Definition

The visual system ensures all cards in the thread look like a series.

| Element | System-wide spec |
|---|---|
| Background | [consistent across all cards - e.g., TEL Black #090920] |
| Accent color | [consistent highlight color - e.g., TEL Blue #14C8FF] |
| Geometric motif | [consistent motif - e.g., hexagonal grid, 10% opacity] |
| Typography | New Hero throughout; Bold for headlines, Regular for body |
| Logo | Present on Card 1 (header) only; omit from insert cards |
| Card numbering | [e.g., subtle "1/5", "2/5" in corner using TEL Gray #424761] |

---

### Card 1 — Header (Tweet 1)

**Tweet**: [quoted text]
**Purpose**: Set the visual identity of the thread; signal institutional quality

**Canvas**: 1200 x 675px (16:9)
**Background**: [spec]
**Headline on card**: [max 8 words extracted from tweet]
**Visual element**: [description]
**AI image prompt**:
```
[full Midjourney/Flux prompt]
```

---

### Card 2 — Insert (Tweet [N])

**Tweet**: [quoted text]
**Purpose**: [e.g., visualize the four miner groups / illustrate the fee formula / show the governance hierarchy]

**Canvas**: 1080 x 1080px (1:1)
**Background**: [spec - must match visual system]
**Headline on card**: [if any]
**Visual element**: [description - diagram, icon set, data visualization, abstract]
**AI image prompt** (if needed):
```
[full prompt, or "N/A - use diagram template"]
```
**Diagram spec** (if applicable):
> [Describe any structured diagram - e.g., "4-node diagram: Validators, Developers, Liquidity Miners, Stakers arranged in a square with connecting lines. Each node: hexagon shape, 60px, Royal Blue fill with TEL Blue border. Labels in New Hero Regular 18px TEL White."]

---

### Card 3 — Insert (Tweet [N])

[same format as Card 2]

---

### Card 4 — Insert (Tweet [N]) [if applicable]

[same format as Card 2]

---

### Production checklist

- [ ] All cards use consistent background color/gradient
- [ ] All cards use New Hero font
- [ ] Logo only on Card 1
- [ ] No text rendered inside AI-generated images (text placed in Figma post-production)
- [ ] All hex values match brand palette exactly
- [ ] No promotional language in any on-card copy
- [ ] Cards pass the regulatory newsletter test (would this look appropriate in an institutional brief?)
- [ ] Thread tier compliance: Tier 1 = minimal graphics, type-focused; Tier 2+ = richer visuals allowed

### Figma workflow
1. Start with brand template (dark background, logo top-left, hexagon motif layer)
2. Generate AI visuals using prompts above
3. Import AI visual as background layer; reduce opacity to 40-60% if too busy
4. Add glass panel overlay (dark with 15% transparency) behind text areas
5. Place copy in New Hero
6. Export at 2x resolution (2400x1350px for headers, 2160x2160px for inserts)

---

$ARGUMENTS
