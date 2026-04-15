# Multi-Agent Workflow: Landing Page Sprint

> Ship a conversion-optimized landing page in one day using 4 agents.

## The Scenario

You need a landing page for a new product launch. It needs to look great, convert visitors, and be live by end of day.

## Agent Team

| Agent | Role in this workflow |
|-------|---------------------|
| Content Creator | Write the copy |
| UI Designer | Design the layout and component specs |
| Frontend Developer | Build it |
| Growth Hacker | Optimize for conversion |

## The Workflow

### Morning: Copy + Design (parallel)

**Step 1a — Activate Content Creator**

```
Activate Content Creator.

Write landing page copy for "FlowSync" — an API integration platform
that connects any two SaaS tools in under 5 minutes.

Target audience: developers and technical PMs at mid-size companies.
Tone: confident, concise, slightly playful.

Sections needed:
1. Hero (headline + subheadline + CTA)
2. Problem statement (3 pain points)
3. How it works (3 steps)
4. Social proof (placeholder testimonial format)
5. Pricing (3 tiers: Free, Pro, Enterprise)
6. Final CTA

Keep it scannable. No fluff.
```

**Step 1b — Activate UI Designer (in parallel)**

```
Activate UI Designer.

Design specs for a SaaS landing page. Product: FlowSync (API integration platform).
Style: clean, modern, dark mode option. Think Linear or Vercel aesthetic.

Deliver:
1. Layout wireframe (section order + spacing)
2. Color palette (primary, secondary, accent, background)
3. Typography (font pairing, heading sizes, body size)
4. Component specs: hero section, feature cards, pricing table, CTA buttons
5. Responsive breakpoints (mobile, tablet, desktop)
```

### Midday: Build

**Step 2 — Activate Frontend Developer**

```
Activate Frontend Developer.

Build a landing page from these specs:

Copy: [paste Content Creator output]
Design: [paste UI Designer output]

Stack: HTML, Tailwind CSS, minimal vanilla JS (no framework needed).
Requirements:
- Responsive (mobile-first)
- Fast (no heavy assets, system fonts OK)
- Accessible (proper headings, alt text, focus states)
- Include a working email signup form (action URL: /api/subscribe)

Deliver a single index.html file ready to deploy.
```

### Afternoon: Optimize

**Step 3 — Activate Growth Hacker**

```
Activate Growth Hacker.

Review this landing page for conversion optimization:

[paste the HTML or describe the current page]

Evaluate:
1. Is the CTA above the fold?
2. Is the value proposition clear in under 5 seconds?
3. Any friction in the signup flow?
4. What A/B tests would you run first?
5. SEO basics: meta tags, OG tags, structured data

Give me specific changes, not general advice.
```

## Timeline

| Time | Activity | Agent |
|------|----------|-------|
| 9:00 | Copy + design kick off (parallel) | Content Creator + UI Designer |
| 11:00 | Build starts | Frontend Developer |
| 14:00 | First version ready | — |
| 14:30 | Conversion review | Growth Hacker |
| 15:30 | Apply feedback | Frontend Developer |
| 16:30 | Ship | Deploy to Vercel/Netlify |

## Key Patterns

1. **Parallel kickoff**: Copy and design happen at the same time since they're independent
2. **Merge point**: Frontend Developer needs both outputs before starting
3. **Feedback loop**: Growth Hacker reviews, then Frontend Developer applies changes
4. **Time-boxed**: Each step has a clear timebox to prevent scope creep
