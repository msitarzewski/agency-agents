# Keyword Cannibalization Audit

## With Search Console access

```markdown
# Cannibalization Audit: [Target Keyword Cluster]

## Step 1: Cross-Page Query Map
Query GSC with dimensions=[page, query] for all pages matching the target topic.

| Query | Page A (URL) | Page A Pos | Page A Clicks | Page B (URL) | Page B Pos | Page B Clicks | Conflict? |
|-------|-------------|------------|---------------|-------------|------------|---------------|-----------|
| [kw1] | /page-a     | X.X        | XX            | /page-b     | X.X        | XX            | YES/NO    |

## Step 2: Ownership Assignment
For each conflicting query, assign ONE owner page based on:
- Which page has the most clicks/impressions on that query
- Which page's topic is the closest semantic match
- Which page is the designated satellite/pillar for that topic

| Query | Current Winner | Designated Owner | Action Required |
|-------|---------------|-----------------|-----------------|
| [kw1] | /page-a       | /page-b          | [consolidate/redirect/rewrite] |

## Step 3: Resolution Plan
For each conflict:
- [ ] Remove/reduce competing content from non-owner pages
- [ ] Add internal links FROM non-owner TO owner page for the conflicting query
- [ ] Ensure title tags and H1s do not overlap on primary keywords
- [ ] Verify canonical tags are self-referencing (no cross-canonicals unless merging)
```

## Without GSC access (fallback)

Use this sitemap + query-intent method when Search Console access isn't available yet — new
site, client hasn't granted access, or auditing a competitor. Battle-tested on a
single-page-anchor + sub-page architecture (e.g. a homepage with anchor sections for multiple
entities where each entity also has a dedicated `/guides/entity-build` sub-page).

```markdown
# Pre-GSC Cannibalization Audit: [Topic Cluster]

## Step 1: Inventory Every URL Touching the Topic
Pull the full sitemap.xml and list every URL whose <title>, H1, or body mentions the target
entity. Flag the homepage/anchor page separately — it is the #1 silent cannibal because it
usually wins by raw authority and starves the dedicated sub-page.

| URL | Mentions Topic? | Primary Role | Current Title/H1 Keyword |
|-----|-----------------|--------------|--------------------------|
| / (homepage)        | YES (anchor section) | Hub   | [keyword in hero?] |
| /guides/entity-build | YES              | Dedicated | [entity] build     |

## Step 2: Query-Intent Overlap Check
For each URL pair, ask: "If a user searches [primary keyword], which ONE page should win?"
- Homepage + sub-page both targeting the same primary keyword = CONFLICT (homepage wins,
  sub-page starves).
- Resolution: the homepage anchor should LINK OUT to the dedicated page and NOT try to rank for
  the sub-page's primary keyword. Give the homepage its own distinct primary keyword.

## Step 3: Title/H1 Deconfliction (no GSC needed)
Grep every page's <title> and H1 for the target primary keyword. Two pages sharing the same
primary keyword in title+H1 = guaranteed internal competition. Assign one owner, rewrite the
other's title/H1 to a distinct long-tail modifier (e.g. "...build" vs "...best team comps 2026").

## Step 4: Canonical & Language Hygiene
- Verify each dedicated page has a self-referencing canonical.
- If a URL mixes languages (e.g. Chinese + English in one page with no `lang` attribute and no
  hreflang), Google treats it as one ambiguous document — split into per-language URLs or add
  `lang` + hreflang before expecting clean rankings.
```
