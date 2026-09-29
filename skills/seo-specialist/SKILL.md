---
name: seo-specialist
description: Technical SEO, keyword research, on-page optimization, link building, and keyword-cannibalization audits. Use when the task involves search rankings, organic traffic, meta tags/titles/H1s, Core Web Vitals, structured data, hreflang/international SEO, backlinks, or diagnosing why multiple pages compete for the same query. Triggers on "SEO", "search rankings", "organic traffic", "keyword research", "cannibalization", "backlinks", "Core Web Vitals", "meta description", "hreflang".
---

# SEO Specialist

Search engine optimization guidance covering technical SEO, content/keyword strategy, on-page
optimization, and link authority building. Apply this directly to the user's site/content in the
current conversation — no separate agent identity needed.

## Critical rules (always apply)

- **White-hat only.** Never recommend link schemes, cloaking, keyword stuffing, hidden text, or
  anything that violates search engine guidelines.
- **User intent first.** Every optimization must serve the searcher's intent — rankings follow
  value, not the reverse.
- **E-E-A-T.** Content recommendations must demonstrate Experience, Expertise,
  Authoritativeness, and Trustworthiness.
- **Core Web Vitals thresholds are non-negotiable:** LCP < 2.5s, INP < 200ms, CLS < 0.1.
- **No guesswork.** Base keyword targeting on actual search volume, competition data, and intent
  classification. Require sufficient data before declaring a ranking change a trend.

## Cannibalization check — mandatory before any on-page change

Before proposing **any** title tag, H1, meta description, or content change to a page that's part
of a topic cluster, check whether another page already competes for the same primary keyword.
Two pages ranking for the same query at similar positions with split clicks = active
cannibalization, and it must be resolved before further optimization.

- With Search Console access → see `references/cannibalization-audit.md` for the GSC-based
  cross-page query map and resolution workflow.
- Without GSC access (new site, no access granted, auditing a competitor) → same file has a
  sitemap + title/H1 grep fallback method.

## Workflow

1. **Discovery** — technical crawl audit, Search Console review, competitive landscape, baseline
   metrics. Full checklist: `references/technical-seo-audit.md`.
2. **Keyword & content strategy** — build the keyword universe by topic cluster and intent, map
   existing content, identify gaps. Full framework: `references/keyword-and-content-strategy.md`.
3. **Cannibalization audit (blocker)** — run before touching any page in a cluster. See above.
4. **On-page & technical execution** — fix crawl issues, implement structured data, optimize
   Core Web Vitals, ship content. Checklist: `references/technical-seo-audit.md`.
5. **Authority building** — link acquisition via digital PR, content-led link building, strategic
   outreach. Full plan template: `references/link-building.md`.
6. **Measurement** — track rankings weekly, segment organic traffic by landing page/intent,
   report ROI, refine strategy.

## International SEO

Multi-language/region sites need reciprocal hreflang (every URL in the set links to all others,
or Google ignores the set) plus a separate `lang` attribute — see
`references/technical-seo-audit.md#international-seo` for the validated template and the
mixed-language-single-page pitfall.

## Success metrics to report against

50%+ YoY non-branded organic traffic growth · top-3 for 30%+ of the target keyword portfolio ·
90%+ crawlability/indexation with zero critical errors · all Core Web Vitals "Good" ·
steady domain-authority growth · 3%+ organic conversion rate · 20%+ featured-snippet capture ·
5:1 organic traffic value to content cost within 12 months.

## Communication style

Evidence-based (cite data, not vague claims), framed around search intent, technically precise
but explained for non-specialists, recommendations ranked by impact vs. effort, realistic
timelines — SEO compounds over months, not days.
