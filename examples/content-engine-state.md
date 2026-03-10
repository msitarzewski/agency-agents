# Content Engine State

> This file is the single source of truth for your content engine. The weekly runner agent reads it at the start of each cycle and writes results back at the end. Keep it in your project root or wherever you run Claude Code from.

---

## Brand Configuration

```yaml
brand_name: "[Your Brand Name]"
brand_description: "[1-2 sentence description of what you do and who you serve]"
primary_audience: "[Persona description — job title, company size, pain points]"
brand_voice: "[e.g. Direct, technical, no fluff. Dry humor welcome. Never corporate-speak.]"
content_goals:
  - "[primary goal: SEO authority / brand awareness / lead generation / retention]"
  - "[secondary goal]"
content_pillars:
  - "[Pillar 1 — e.g. Team productivity]"
  - "[Pillar 2 — e.g. Developer workflows]"
  - "[Pillar 3 — e.g. Remote collaboration]"
active_platforms:
  - twitter
  - instagram
  - tiktok
  - reddit
  - blog
weekly_output_target:
  pillar_posts: 1
  platform_packages: 4        # one per active platform
constraints: "[Brand guidelines, off-limits topics, legal/regulatory notes]"
review_contact: "[Your name or email — for the weekly plan and results reports]"
```

---

## Benchmarks

> Update these after your first 4 weeks once you have real baselines.

```yaml
blog:
  organic_sessions_per_post_monthly: 300
  avg_time_on_page_seconds: 180
  keyword_ranking_target: top_10

twitter:
  engagement_rate_pct: 2.0
  thread_retweets: 25
  link_clicks_per_post: 40

instagram:
  save_rate_pct: 3.0
  reach_per_post: 1000
  reel_completion_rate_pct: 35

tiktok:
  view_completion_rate_pct: 40
  shares_per_video: 10
  follower_gain_per_video: 20

reddit:
  upvotes_per_post: 40
  comments_per_post: 5
  outbound_clicks_per_post: 30
```

---

## Optimization Memory

> The weekly runner writes to this section automatically. Do not edit manually.

### Cycle Log

<!-- CYCLE LOG START — runner appends here each week -->

<!-- CYCLE LOG END -->

### Cumulative Learnings

> Patterns the engine has learned across all cycles. Runner updates after every 4 cycles.

<!-- LEARNINGS START -->
- [ Initial learnings will be written here after Cycle 1 ]
<!-- LEARNINGS END -->

### Current Content Cluster Progress

> Tracks topical authority building across keyword clusters over time.

| Pillar | Target Keyword | Current Ranking | First Published | Last Updated |
|--------|---------------|-----------------|-----------------|--------------|
| | | | | |

---

## Approval History

> Log of user approvals, rejections, and direction changes for weekly plans.

| Cycle | Date | Decision | Changes Requested |
|-------|------|----------|-------------------|
| | | | |
