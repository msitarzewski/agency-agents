# Content Engine State — orchidea.digital

> Drop this file in your project root before running the weekly runner.
> Fields marked **[FILL IN]** need your input before Cycle 1.

---

## Brand Configuration

```yaml
brand_name: "orchidea.digital"
brand_description: >
  Senior-led automated marketing platform that replaces the need for a full
  marketing hire. Delivers 15 SEO articles, 60 social posts, and 8 email
  campaigns monthly — all scheduled automatically and optimized from
  performance data. Tagline: "Your Marketing Team. Automated."
primary_audience: >
  Founders, CMOs, and marketing leads at mid-market companies and funded
  startups (Series A–C, 20–200 employees) who need consistent, on-brand
  content output but can't justify a $150K+ marketing hire. They're
  time-starved, growth-focused, and skeptical of agencies that overpromise.
brand_voice: >
  Confident and direct — we make a specific guarantee, we back it with data.
  Senior-grade thinking, no fluff or filler. Occasionally dry wit. Never
  corporate-speak or AI-hype buzzwords (we're above that). Write for people
  who have seen bad agencies and don't have time to waste.
content_goals:
  - "SEO authority — rank for automated marketing, AI content marketing, and marketing automation keywords"
  - "Lead generation — content that ends with a clear path to a demo or discovery call"
  - "Brand credibility — showcase results, specificity, and expertise to convert skeptics"
content_pillars:
  - "AI in Marketing — how AI is changing search, content, and buyer behavior"
  - "Marketing Automation — workflows, tools, ROI of automation vs. hiring"
  - "Growth Without Hiring — how lean teams scale marketing output"
  - "Performance & Measurement — tracking what works, attribution, cutting waste"
  - "Digital Transformation — AI roadmaps, adoption, governance for mid-market"
active_platforms:
  - blog            # primary SEO channel → Framer CMS via N8N
  - linkedin        # strongest B2B channel → LinkedIn API via N8N
  - twitter         # @orchideadigital → Twitter API via N8N
  - instagram       # @orchidea.digital → Instagram Graph API via N8N
  - facebook        # Meta company page → Facebook Pages API via N8N
  - email           # weekly newsletter → ConvertKit broadcast via N8N
linkedin_config:
  company_page: "orchidea-digital"
  executive_personal_brand: "Dylan Angloher"    # CEO — highest-reach personal brand
  formats: [document_carousel, article, company_posts, executive_post]
  newsletter: false                              # set to true + name when launched
email_config:
  provider: convertkit
  segment: "Newsletter subscribers"
  send_day: Friday
  send_time: "8:00am EST"
  cta_default: "book a demo"                    # override per cycle in plan
  sequence_tags:
    - clicked_demo_cta: "demo-nurture"
    - clicked_article: "engaged-reader"
publishing_config:
  approval_tool: airtable
  airtable_base: "Content Pipeline"
  airtable_table: "Content Queue"
  automation: n8n
  n8n_trigger: "Status = Approved"
  publishing_destinations:
    blog: "Framer CMS API"
    linkedin: "LinkedIn API"
    twitter: "Twitter API"
    instagram: "Instagram Graph API"
    facebook: "Facebook Pages API"
    email: "ConvertKit API"
weekly_output_target:
  pillar_posts: 1
  platform_packages: 6    # LinkedIn + Twitter + Instagram + Facebook + Email + Reddit (blog is the pillar)
constraints: >
  Never position as "cheap" — frame as high-ROI and "95% less than a full
  team." Do not use competitor names negatively. Avoid AI hype language
  (disruptive, revolutionary, game-changing). Every claim should be
  supportable with a specific number or case study. Reference the 47 startup
  case study and 14-day guarantee where relevant.
review_contact: "Dylan Angloher — dylan@orchidea.digital"
```

---

## Benchmarks

> Cycle 1 uses these as starting targets. Update after 4 weeks with real data.

```yaml
blog:
  organic_sessions_per_post_monthly: 200   # conservative for new domain
  avg_time_on_page_seconds: 150
  keyword_ranking_target: top_20           # page 2 → page 1 by cycle 8

linkedin:
  carousel_save_rate_pct: 3.0              # document carousel saves — primary quality signal
  post_engagement_rate_pct: 3.0           # company page posts
  executive_post_engagement_rate_pct: 6.0 # Dylan's personal brand posts
  article_views_30d: 500
  follower_growth_monthly_pct: 8.0
  impressions_per_post: 1000

twitter:
  engagement_rate_pct: 2.0
  thread_retweets: 15
  link_clicks_per_post: 30

instagram:
  save_rate_pct: 3.0
  reach_per_post: 800
  reel_completion_rate_pct: 35

facebook:
  engagement_rate_pct: 2.0
  reach_per_post: 500

email:
  open_rate_pct: 35.0                  # industry B2B SaaS avg ~25% — target above
  click_through_rate_pct: 4.0
  unsubscribe_rate_pct: 0.3            # flag if any send exceeds this
  list_growth_monthly_pct: 10.0

# FILL IN current metrics if you have them — these override the defaults above
current_actuals:
  blog_monthly_organic_sessions: "[FILL IN or leave blank]"
  linkedin_avg_engagement_rate: "[FILL IN or leave blank]"
  twitter_avg_engagement_rate: "[FILL IN or leave blank]"
  domain_authority: "[FILL IN — check ahrefs.com/website-checker/ free tool]"
```

---

## Priority Keyword Clusters

> Pre-seeded based on brand positioning. SEO Specialist will refine each cycle.

```yaml
cluster_1_pillar: "marketing automation"
  primary: "automated marketing platform"
  supporting:
    - "marketing automation for startups"
    - "replace marketing team with AI"
    - "automated content marketing"
    - "AI marketing tools for small business"

cluster_2_pillar: "growth without hiring"
  primary: "scale marketing without hiring"
  supporting:
    - "fractional marketing team"
    - "outsource content marketing"
    - "marketing team alternative"
    - "marketing on a startup budget"

cluster_3_pillar: "AI in marketing"
  primary: "AI content marketing"
  supporting:
    - "AI SEO articles"
    - "AI social media management"
    - "AI marketing strategy"
    - "how AI is changing content marketing"

cluster_4_pillar: "performance measurement"
  primary: "content marketing ROI"
  supporting:
    - "how to measure content marketing"
    - "marketing attribution for startups"
    - "content performance tracking"
```

---

## Optimization Memory

> Runner writes to this section automatically each cycle.

### Cycle Log

<!-- CYCLE LOG START -->

<!-- CYCLE LOG END -->

### Cumulative Learnings

> Updated automatically every 4 cycles.

<!-- LEARNINGS START -->
- [ Initial learnings will populate after Cycle 1 ]
<!-- LEARNINGS END -->

### Content Cluster Progress

| Pillar | Target Keyword | Blog Ranking | LinkedIn Article | First Published | Last Updated |
|--------|---------------|-------------|-----------------|-----------------|--------------|
| Marketing Automation | automated marketing platform | — | — | — | — |
| Growth Without Hiring | scale marketing without hiring | — | — | — | — |
| AI in Marketing | AI content marketing | — | — | — | — |
| Performance & Measurement | content marketing ROI | — | — | — | — |
| Digital Transformation | AI marketing roadmap | — | — | — | — |

---

## Approval History

| Cycle | Date | Decision | Changes Requested |
|-------|------|----------|-------------------|
| | | | |
