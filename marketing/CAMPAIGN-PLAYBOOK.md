# Marketing Campaign Playbook
## Build a Full Ad Campaign from Publicly Available Information

A repeatable process for generating complete, client-ready marketing campaign assets — social ads, email, print, and a live deployable showcase — using only public information about the client.

---

## Overview

**Input**: A client name, website, or brief description
**Output**: A fully deployed marketing campaign showcase with:
- Brand guidelines (derived from research)
- Facebook/Instagram ad mockups (HTML)
- Instagram Stories & Posts (HTML)
- Email campaign (HTML)
- Event poster / print asset (HTML)
- Social media copy (Twitter/X thread, LinkedIn/Facebook copy)
- Optional: Next.js AI-powered generator app (Claude API)
- Deployed to Vercel at a shareable URL

**Time to complete**: ~2–4 hours (mostly research + asset generation)

---

## Step 1 — Client Research (Public Sources Only)

Collect all publicly available information. Use `WebSearch` and `WebFetch`.

### Research Checklist

```
[ ] Official website — homepage, about, services/products
[ ] Social media profiles — Instagram, Facebook, LinkedIn, TikTok
[ ] Event pages — Eventbrite, Humanitix, or similar ticketing
[ ] Google Business Profile / reviews
[ ] Press mentions / media coverage
[ ] Competitor landscape (3–5 competitors)
[ ] Target audience signals (who engages, who they speak to)
```

### Key Data Points to Extract

| Field | Where to Find |
|-------|---------------|
| Brand name & tagline | Website homepage |
| Founder / key person | About page, LinkedIn |
| Mission & values | About page |
| Products / services / events | Services/events pages |
| Pricing / tiers | Pricing page or ticketing |
| Colours & fonts | Website CSS / visual inspection |
| Tone of voice | Existing copy |
| Target audience | About page, social bio, ad targeting |
| Social proof (stats, testimonials) | Website, Google reviews |
| Hashtags in use | Instagram posts |
| Key dates / deadlines | Events page |
| Competitors | Search "[niche] + [location]" |

---

## Step 2 — Create Brand Guidelines

Save as `marketing/[client-slug]/brand-guidelines.md`

Use the template at `marketing/_template/brand-guidelines-template.md`.

Sections to fill:
1. **Brand Overview** — who, what, why, founder, website, social handles
2. **Brand Personality** — 5–6 traits with descriptions
3. **Colour Palette** — primary, secondary, accent (hex codes), with usage notes
4. **Typography** — display font, heading font, body font, CTA font
5. **Key Messages** — signature phrases, taglines, mission language, urgency lines
6. **Imagery Style** — photography direction, mood, what to avoid
7. **Do's and Don'ts** — explicit guardrails
8. **Campaign Goal** — specific, measurable (e.g. "sell 200 tickets")

---

## Step 3 — Build Campaign Assets

### Folder Structure

```
marketing/
  [client-slug]/
    brand-guidelines.md          ← Step 2 output
    index.html                   ← Campaign showcase hub
    vercel.json                  ← Deployment config
    ads/
      facebook-ad-mockups.html   ← 3–6 ad variations
    social-media/
      instagram-posts.html       ← Feed post mockups
      instagram-stories.html     ← Story mockups (9:16)
      facebook-linkedin-ads.md   ← Ad copy text
      twitter-x-thread.md        ← Thread copy
    email/
      email-campaign.html        ← Full email mockup
    print/
      event-poster.html          ← A3/A4 poster or flyer
    generator/                   ← Optional: AI generator app
      app/
      package.json
      vercel.json
```

### Asset Build Order (recommended)

1. `brand-guidelines.md` — reference for everything else
2. `index.html` — scaffold the hub first (add links as assets are created)
3. `ads/facebook-ad-mockups.html` — highest ROI asset for most clients
4. `social-media/instagram-posts.html`
5. `social-media/instagram-stories.html`
6. `email/email-campaign.html`
7. `print/event-poster.html`
8. Copy decks (`facebook-linkedin-ads.md`, `twitter-x-thread.md`)

---

## Step 4 — Build the Campaign Showcase Hub (index.html)

The `index.html` is a single-page portal that links to all assets. Include:

- Hero section with brand name, tagline, campaign goal
- Nav links to each asset section
- Preview thumbnails / iframe previews of each deliverable
- "Open full page" links for each asset
- Brand colour palette and font preview strip
- Download/export notes for the client

See `marketing/_template/index-template.html` for the scaffold.

---

## Step 5 — (Optional) AI Generator App

Build a Next.js app that uses the Claude API so the client can generate more content on-demand.

```
generator/
  app/
    page.tsx          ← UI with form (audience, tone, goal, channels)
    api/
      generate/
        route.ts      ← Claude API call with brand guidelines as system prompt
  package.json
  vercel.json
  .env.example        ← ANTHROPIC_API_KEY placeholder
```

**System prompt pattern**: Load `brand-guidelines.md` content as the system prompt so Claude always generates on-brand content.

**UI inputs**: Channel (Instagram/Facebook/Email/etc.), Tone, Target Audience, Goal, CTA

See `marketing/_template/generator/` for the full scaffold.

---

## Step 6 — Deploy to Vercel

### Root-level `vercel.json` (static site — no builds key)

```json
{
  "rewrites": [
    { "source": "/ads/(.*)", "destination": "/ads/$1" },
    { "source": "/social-media/(.*)", "destination": "/social-media/$1" },
    { "source": "/email/(.*)", "destination": "/email/$1" },
    { "source": "/print/(.*)", "destination": "/print/$1" }
  ]
}
```

> **Critical**: Do NOT add a `"builds"` key for static HTML projects. This causes Vercel errors.

### Generator app `vercel.json` (Next.js)

```json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "outputDirectory": ".next"
}
```

### Deploy commands

```bash
# Static showcase (from client folder root)
cd marketing/[client-slug]
vercel --prod

# Generator app (from generator subfolder)
cd marketing/[client-slug]/generator
vercel --prod
```

### Environment variables (generator app only)

Set in Vercel dashboard or via CLI:
```bash
vercel env add ANTHROPIC_API_KEY
```

---

## Step 7 — Handoff to Client

Deliver:
1. **Live URL** — the deployed Vercel showcase link
2. **GitHub branch** — all source files in version control
3. **brand-guidelines.md** — editable brand document
4. **Copy decks** (`.md` files) — ready to paste into ad platforms
5. **Generator app URL** — if built, for ongoing content creation

### Client Instructions Template

```
Hi [Client],

Your campaign assets are ready. Here's everything:

🌐 Campaign Showcase: [vercel-url]
   All your ads, social posts, email, and print assets in one place.

✍️ Copy Decks (paste-ready):
   - Facebook/LinkedIn Ads: [link to .md file]
   - Twitter/X Thread: [link to .md file]

🤖 AI Content Generator (optional): [generator-url]
   Enter your ANTHROPIC_API_KEY to generate more on-brand content.

📁 Source Files: [github-branch-link]

Brand guidelines are in brand-guidelines.md — update this as your brand evolves.
```

---

## Replication Checklist (New Client)

```bash
# 1. Create client folder
cp -r marketing/_template marketing/[new-client-slug]

# 2. Fill in brand-guidelines.md from research
# 3. Build assets (customise HTML templates with brand colours/copy)
# 4. Update index.html hub
# 5. Deploy
cd marketing/[new-client-slug]
vercel --prod
```

---

## Quality Checklist Before Delivery

```
[ ] All brand colours match guidelines (check hex codes)
[ ] All fonts match guidelines
[ ] No placeholder text ([CLIENT], [DATE], etc.) remaining
[ ] All CTAs link to real URLs (or noted as "replace with X")
[ ] Email renders correctly at 600px width
[ ] Instagram posts are 1:1 ratio (1080×1080)
[ ] Instagram Stories are 9:16 ratio (1080×1920)
[ ] Facebook ads are 1.91:1 ratio (1200×628) for feed
[ ] vercel.json has no "builds" key (for static sites)
[ ] Deployed URL is accessible publicly
[ ] Generator app: ANTHROPIC_API_KEY env var set
```

---

## Asset Dimensions Reference

| Format | Dimensions | Ratio |
|--------|-----------|-------|
| Facebook/Instagram Feed Ad | 1200×628px | 1.91:1 |
| Instagram Square Post | 1080×1080px | 1:1 |
| Instagram Story | 1080×1920px | 9:16 |
| Facebook Cover | 1640×624px | — |
| Email Width | 600px | — |
| A4 Print Poster | 210×297mm / 2480×3508px | — |
| Twitter/X Card | 1200×675px | 16:9 |

---

## Time Budget Per Asset

| Asset | Estimated Time |
|-------|---------------|
| Research + brand guidelines | 30–45 min |
| Facebook ad mockups (3–6 ads) | 30–45 min |
| Instagram posts + stories | 30–45 min |
| Email campaign | 20–30 min |
| Print poster | 20–30 min |
| Copy decks | 15–20 min |
| Showcase hub (index.html) | 20–30 min |
| Generator app | 45–60 min |
| Deployment + QA | 15–20 min |

---

## Examples

| Client | Niche | Branch |
|--------|-------|--------|
| Thriving Through Menopause | Medical aesthetics symposium | `claude/menopause-symposium-marketing-ojszT` |

---

*Template version: 1.0 — March 2026*
