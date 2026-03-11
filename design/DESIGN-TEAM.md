# Design Team
## Telcoin Association Marketing Agency

The design team produces all visual and video content. Agents generate scripts, storyboards, shot lists, AI prompts, and creative briefs — these feed directly into external rendering tools (Midjourney, Runway, CapCut, etc.) for final production. One exception: `Carousel Growth Engine` is fully autonomous and publishes directly to TikTok and Instagram with no human in the loop.

---

## Team Roster

### Creative Direction
| Agent | Role | File |
|---|---|---|
| `Visual Storyteller` | Lead creative — storyboards, narratives, video direction, multimedia | `agency-agents/design-visual-storyteller.md` |
| `Brand Guardian` | Visual consistency — ensures everything looks and feels Telcoin | `agency-agents/design-brand-guardian.md` |
| `Whimsy Injector` | Creative edge — adds personality, unexpected delight, memorability | `agency-agents/design-whimsy-injector.md` |

### Image Production
| Agent | Role | File |
|---|---|---|
| `Image Prompt Engineer` | AI image prompts for Midjourney, DALL-E, Flux, Adobe Firefly | `agency-agents/design-image-prompt-engineer.md` |
| `Inclusive Visuals Specialist` | Representation accuracy — defeats AI bias for human-featuring images/video | `agency-agents/design-inclusive-visuals-specialist.md` |

### Video & Social
| Agent | Role | File |
|---|---|---|
| `TikTok Strategist` | Short-form video concepts, scripts, trends, hooks | `agency-agents/marketing-tiktok-strategist.md` |
| `Instagram Curator` | Reels direction, Stories, visual-first captions | `agency-agents/marketing-instagram-curator.md` |
| `Carousel Growth Engine` | **Autonomous** — generates + publishes TikTok/Instagram carousels end-to-end | `agency-agents/marketing-carousel-growth-engine.md` |
| `Content Creator` | Long-form video scripts, YouTube, explainers, voiceover copy | `agency-agents/marketing-content-creator.md` |

---

## What the Design Team Produces

### Images
- **AI image prompts** → paste into Midjourney, DALL-E, Flux, Adobe Firefly, Stable Diffusion
- **Photography art direction docs** → brief for photographers or stock selection
- **Infographic data** → brief for designers (Figma, Canva, Adobe Illustrator)
- **Brand asset direction** → logos, icons, color usage in context

### Video
- **Short-form scripts** → TikTok (15–60s), Instagram Reels (15–90s), YouTube Shorts
- **Long-form scripts** → YouTube explainers (3–10min), council recap summaries, announcements
- **Storyboards** → shot-by-shot visual descriptions for editors or AI video tools
- **Shot lists** → camera angles, cuts, visual beats for each scene
- **Video prompts** → paste into Runway ML, Sora, Kling AI for AI-generated footage
- **Voiceover scripts** → clean copy for ElevenLabs or human VO talent
- **Caption + subtitle text** → formatted for CapCut, Premiere, or DaVinci

### Carousels (Autonomous)
- `Carousel Growth Engine` handles everything: analyzes telcoin.org/telcoin.network → generates 6 slides via Gemini → publishes to TikTok + Instagram via Upload-Post API → fetches analytics → improves next carousel automatically

---

## Production Pipeline

### For Static Images
```
Brief Claude with:
  → Topic + mood + audience + platform dimensions

Run these agents in parallel:
  → Visual Storyteller: narrative concept + mood board description
  → Image Prompt Engineer: 3-5 Midjourney/DALL-E prompts
  → Inclusive Visuals Specialist: (if humans featured) representation-safe prompts

Output files saved to: design/output/images/

Then: paste prompts into Midjourney / DALL-E / Flux → render → review
```

### For Short-Form Video (TikTok / Reels)
```
Brief Claude with:
  → Message + target audience + platform + length

Run these agents in parallel:
  → TikTok Strategist OR Instagram Curator: hook, script, trending audio direction
  → Visual Storyteller: storyboard (shot by shot)
  → Image Prompt Engineer: key frame prompts for AI-generated visuals

Output files saved to: design/output/video/

Then: use Runway ML / Kling / CapCut to render or edit → publish
```

### For Long-Form Video (YouTube / Announcements)
```
Brief Claude with:
  → Topic + key messages + audience + desired length

Run in sequence:
  1. Content Creator: full script with voiceover + on-screen text notes
  2. Visual Storyteller: storyboard + shot list + B-roll direction
  3. Brand Guardian: review script for tone + messaging accuracy

Output files saved to: design/output/video/

Then: record VO via ElevenLabs or human → edit in Premiere / DaVinci
```

### For Carousels (Autonomous)
```
Tell Claude:
  "Launch Carousel Growth Engine on [URL]. Audience: [specify]. Platform: TikTok + Instagram."

Agent does everything:
  → Scrapes URL with Playwright
  → Generates 6 slides via Gemini (9:16, 768x1376, JPG)
  → Publishes via Upload-Post API
  → Fetches analytics
  → Saves learnings to learnings.json
  → Reports published URLs back to you
```

---

## Content Types × Agent Assignments

| Content Type | Primary Agent | Support Agents |
|---|---|---|
| TikTok video (scripted) | `TikTok Strategist` | `Visual Storyteller` (storyboard) |
| Instagram Reel | `Instagram Curator` | `Visual Storyteller` (storyboard) |
| TikTok/IG carousel (auto-publish) | `Carousel Growth Engine` | none needed |
| YouTube explainer | `Content Creator` | `Visual Storyteller` (storyboard) |
| Council recap video summary | `Content Creator` | `Executive Summary Generator` |
| Static social graphic | `Image Prompt Engineer` | `Visual Storyteller` (concept) |
| Human-featuring image | `Inclusive Visuals Specialist` | `Image Prompt Engineer` |
| Brand asset / logo context | `Brand Guardian` | `Image Prompt Engineer` |
| Infographic / data viz | `Visual Storyteller` | `Content Creator` (copy) |
| Announcement graphic | `Image Prompt Engineer` | `Brand Guardian` (review) |
| Meme / culture content | `Whimsy Injector` | `TikTok Strategist` |

---

## External Tools Paired with Each Agent

| Agent Output | Render With |
|---|---|
| Midjourney prompts | midjourney.com (Discord bot) |
| DALL-E prompts | ChatGPT Pro / OpenAI API |
| Flux prompts | fal.ai / Replicate / ComfyUI |
| Adobe Firefly prompts | firefly.adobe.com |
| Short video prompts | Runway ML (runwayml.com) |
| Short video prompts | Kling AI (klingai.com) |
| Short video prompts | Sora (sora.openai.com) |
| Video scripts / storyboards | CapCut / Premiere Pro / DaVinci Resolve |
| Voiceover scripts | ElevenLabs / Descript / human talent |
| Carousel (autonomous) | `Carousel Growth Engine` handles internally |
| Animated graphics | Adobe After Effects / Motion |

---

## Telcoin Visual Identity (for all design briefs)

### Color Palette
- **Primary**: Deep indigo/purple (#2D1B69 range) — Telcoin Network brand
- **Accent**: Bright cyan/teal — interactive elements, highlights
- **Dark background**: Near-black navy — most compositions
- **White/light grey**: Typography on dark

### Visual Language
- **Infrastructure, not speculation** — visuals should feel solid, engineered, real
- **Global + mobile-first** — phones, telecom towers, maps, people in emerging markets
- **Clean and technical** — not flashy crypto aesthetic; more fintech/enterprise credibility
- **Avoid**: Rockets, moons, lambos, neon green "hacker" aesthetics, generic "blockchain" sphere graphics

### Recurring Motifs
- Mobile phones receiving money transfers
- Telecom infrastructure (towers, fiber, data centers)
- World maps with connection lines between corridors
- GSMA branding adjacency (professional, institutional tone)
- Financial inclusion imagery — real people in real places (not stock photo diversity)

---

## Design Workflow: Council Recap → Video

When a council recap comes in, the design team can produce:

1. **90-second summary Reel** — `Content Creator` writes VO script, `Visual Storyteller` storyboards
2. **Key milestone graphic** — `Image Prompt Engineer` generates announcement image prompt
3. **Twitter carousel** (if top 3 takeaways worth a carousel post) — `Carousel Growth Engine` if autonomous, or `Visual Storyteller` + `Image Prompt Engineer` for manual

---

## Output File Naming

```
design/output/
  images/
    [topic]-social-graphic-[platform]-[date].md        ← image prompts + direction
    [topic]-midjourney-prompts-[date].md
  video/
    [topic]-tiktok-script-[date].md
    [topic]-youtube-script-[date].md
    [topic]-storyboard-[date].md
    [topic]-voiceover-[date].md
  briefs/
    [campaign]-visual-brief-[date].md
```

---

## Parallelization Patterns

**Full video package for an announcement:**
```
Simultaneously:
→ Content Creator: YouTube script (2-3 min)
→ TikTok Strategist: TikTok cut (30s hook version)
→ Visual Storyteller: storyboard + shot list
→ Image Prompt Engineer: 5 thumbnail/graphic prompts
```

**Social image batch:**
```
Simultaneously:
→ Image Prompt Engineer: 3 Midjourney variants (different moods)
→ Inclusive Visuals Specialist: people-focused version (safe for diverse representation)
→ Brand Guardian: review previous week's visuals for consistency issues
```

**Carousel sprint:**
```
Simultaneously:
→ Carousel Growth Engine on telcoin.network (auto-publish)
→ Carousel Growth Engine on telcoin.org/eusd (auto-publish)
→ Visual Storyteller: storyboard concept for next manual carousel
```
