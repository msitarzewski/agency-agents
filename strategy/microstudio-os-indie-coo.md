# Microstudio OS — AI Executive Producer for Solo Game Devs

> Product brief & MVP audit. Category: **AI Studio Operator / Executive Producer** for commercial solo indie game developers. **Not** an AI game generator.

## 0. Thesis (and the Polsia lesson)

The product helps a **solo / 1–3 person commercial game dev operate like a small studio** — it does not make the game. It runs the *studio around the game*: market/Steam research, scope governance, production planning, build audits, playtest synthesis, wishlist growth, store positioning, community ops, and a daily operating report.

"Polsia" (the autonomous "AI runs your company while you sleep" operator) is the cautionary reference: strong fantasy, real funding/virality, but a documented **trust gap** — failed/credit-burning tasks, "complete" outputs that don't deploy, weak control/auditability, and "slop at scale." The durable lesson is the inverse of its pitch:

> **Autonomy sells, but control retains.** Human directs; AI operates the studio scaffolding.

Every recommendation this product makes must be **grounded, cited, reversible, human-gated, and auditable** (opinion vs. fact labeled, source-linked, exportable). We reject: full game generation, autonomous publishing, asset-slop, opaque credits, secret repo edits, false market certainty, and "one-click success."

### The two wedges, and which we build first

| | **Wedge A — Demand/Steam Operator** | **Wedge B — Production/Scope Operator** |
|---|---|---|
| Job | Page audit, comparables, wishlist actions, review mining, launch ops | Concept→market validation, solo-feasibility scope scoring, vertical-slice plan, build/playtest audits |
| Best customer | Page-live, pre-launch, wishlist-anxious | Idea/prototype-stage, "am I building the wrong thing?" |
| Data | Public Steam/SteamSpy (easy, defensible) | Mostly user-provided artifacts (builds, videos, docs) |
| AI risk | Low — synthesis over structured public data | Higher — taste-level judgment is where LLMs bluff |
| Pain | High *near launch* (seasonal) | High *and earlier* (prevents months of wrong work; less seasonal) |

**Decision: build Wedge B first** — the Scope/Concept Operator (Concept Lab + Scope Governor) — with the vision branded **"never build blind again,"** and keep the free **Steam Page audit** (Wedge A) as the cheap, shareable acquisition hook on top.

**De-risking the taste-level weakness (critical):**
- Ground every judgment in **named, real comparable Steam games**, never vibes. "Solo-feasibility score" derives from analogous titles' scope, team-size signals, dev time, and system count. Always show the evidence; always label it an *estimate*.
- Prefer **rules/heuristics for numeric scoring** (feature-count → system-dependency → risk weighting); use the LLM for synthesis and explanation, not for inventing numbers.
- **Human gates everywhere:** AI proposes Must/Should/Could/**Kill**; the dev decides. Tag each item *opinion vs. fact* and *reversible vs. costly*.
- **Concierge the first cohort** (~15 reports) to learn what "credible" looks like before automating.

---

## 1. Market Audit

**Target user:** the commercially-minded **solo / 1–3 person PC indie dev shipping on Steam** who can *make* a game but is overwhelmed or allergic to the *business/ops* half. Steam is the center of gravity. Best genres: cozy, roguelite, survival-craft, automation, horror, narrative, simulation, deckbuilder. **Anti-persona:** AAA/mid studios (have marketing staff), pure mobile/hypercasual (UA-driven), pure hobbyists (won't pay).

**Painful jobs (ranked by real anguish in r/gamedev, GDC talks, post-mortems):**
1. "Nobody knows my game exists." Wishlist growth is existential and unsystematized.
2. "Is my capsule / tags / short description costing me wishlists?" Suspected underperformance, no diagnosis.
3. "Who are my real competitors and what worked for them?" Tedious manual SteamDB/SteamSpy spelunking.
4. "I have 400 Discord messages, 60 reviews, 30 Reddit replies — what do I actually fix?" Feedback firehose, no synthesis.
5. "Who do I email to cover my game, and what do I say?" Cold, ad hoc outreach.
6. "When do I launch / demo / hit Next Fest / price it?" Decisions on vibes.
7. "I context-switch between coding and business and business always loses." No operating cadence.
8. *(Earlier in the lifecycle)* "Am I building the wrong game, at the wrong scope, for an audience that won't care?" — the most expensive mistake of all.

**Competitive landscape:**

| Category | Examples | Gap they leave |
|---|---|---|
| Steam data/analytics | SteamDB, SteamSpy, VG Insights, Gamalytic | Data, not *decisions or actions* |
| Market intelligence / education | GameDiscoverCo (Simon Carless), Chris Zukowski / HowToMarketAGame | Best knowledge, but manual & generic — not personalized to *your* page/week |
| Wishlist/launch tooling | Keymailer, Woovit, Lurkit | Key-distribution logistics only; no strategy/synthesis |
| PM / ops | Notion, Trello, Linear | Empty boxes; no game intelligence |
| AI game-gen | Ludo.ai, Rosebud, Inworld | Solve the *wrong half* for commercial solo devs |

**Key finding:** there is **no incumbent "operator/producer" layer.** The market splits into *data tools* (no decisions) and *education* (no personalization/execution). The opening is the **synthesis → recommendation → recurring-cadence layer on top of public data**, plus the **production-discipline layer** earlier in the lifecycle.

**Real pain or wrapper?** Real — but with a thin-wrapper trap. If it's "paste URL → generic GPT tips," it churns in month 2. Defensibility = (a) proprietary structured benchmarks from real Steam data, (b) recurring cadence that compounds, (c) closing the loop recommendation → action → measured result.

**What makes someone pay monthly:** it tells them the 3 highest-leverage things to do this week, grounded in *their* comparables; it does tedious work they'd never do; it produces artifacts they'd otherwise sweat over; it gives a calm operating rhythm; and it keeps delivering fresh value (a one-time audit is a one-time payment).

---

## 2. Category Positioning

- **One-line pitch:** *"An AI Executive Producer for solo game devs — it runs the studio around your game so you can stay in the engine."*
- **Category name:** **AI Studio Operator / Executive Producer** (avoid "marketing tool" and "analytics" — both passive/commoditized).
- **vs. AI game generators:** they help you *make* the game (saturated supply side); we help the game *succeed and ship right* (the actual bottleneck — production discipline + distribution). Complementary, not competitive.
- **vs. PM tools:** Notion/Trello are empty boxes; we're a **filled box with a brain** that generates the work and tells you which tasks matter.
- **vs. marketing automation:** Mailchimp/HubSpot blast messages through funnels you build; we provide **research + judgment + artifacts** for a non-marketer who needs to be *told what's worth doing* in a domain those tools know nothing about.

The defensible framing: not a tool the dev *operates* — an **operator that works for the dev**.

---

## 3. Customer Segments (ranked)

| Segment | Urgency | WTP | MVP fit | Verdict |
|---|---|---|---|---|
| **Prototype / scope-stage** | 🔥🔥 | Med | ★★★★☆ | **PRIMARY for Wedge B** — "am I building the wrong thing?"; prevents months of wrong work; less seasonal retention. |
| **Steam page live / wishlist-stage** | 🔥🔥🔥 | High | ★★★★★ | **PRIMARY for the free hook + Wedge A** — data to audit, deadline urgency, wishlists as a legible metric. |
| **Demo-stage (Next Fest)** | 🔥🔥🔥 | High | ★★★★☆ | Strong secondary; great time-boxed "launch campaign" SKU. |
| **Post-launch** | 🔥🔥 | Med-High | ★★★★☆ | Best long-term retention (reviews, patches, roadmap, updates-as-marketing). |
| **Small 2–5 person teams** | 🔥🔥 | Highest $ | ★★★☆☆ | Pay most but more demanding; expansion, not beachhead. |
| **Pre-game-idea** | 💤 | Low | ★☆☆☆☆ | Tourists. Avoid for MVP. |

**Beachhead:** the same dev moving through the lifecycle (idea → prototype → page → demo → launch → post-launch) = built-in retention. Land on the scope/concept pain; hook with the free Steam audit.

---

## 4. Core Workflows (ranked)

Scoring 1–5 (higher = better/easier).

| Workflow | Pain | Feasibility | Data ease | MVP value | Monetization | Priority |
|---|---|---|---|---|---|---|
| **Solo-feasibility / scope governance** | 5 | 3 | 3 | 5 | 5 | **#1 (Wedge B core)** |
| **Concept → market validation** | 4 | 3 | 4 | 5 | 4 | **#2 (Wedge B core)** |
| **Steam page audit** | 5 | 5 | 5 | 5 | 5 | **#3 — free hook** |
| **Competitor & tag research** | 5 | 4 | 4 | 5 | 5 | **#4** |
| **Wishlist growth recommendations** | 5 | 4 | 4 | 5 | 5 | **#5** |
| **Daily/weekly studio report** | 4 | 4 | 4 | 4 | 5 | **#6 — retention engine** |
| **Review mining** | 4 | 5 | 5 | 4 | 4 | #7 (post-launch) |
| **Build/screenshot audit** | 4 | 3 | 3 | 4 | 4 | #8 (v1.5) |
| **Playtest synthesis** | 4 | 3 | 3 | 4 | 4 | #9 (v1.5) |
| **Influencer/outreach list** | 5 | 3 | 2 | 4 | 5 | #10 (v1.5) |
| **Patch-note drafting** | 3 | 5 | 4 | 3 | 3 | #11 |
| **Discord/community summarization** | 4 | 3 | 2 (ToS) | 4 | 4 | **defer** |

**Read:** Scope governance and concept validation are the highest-leverage, least-seasonal, most-defensible jobs (Wedge B). The Steam page audit is the cheapest thing to make *demonstrably non-slop* and is the shareable acquisition hook. Discord summarization sounds appealing but is a ToS/data swamp — deliberately deferred.

---

## 5. MVP Scope (buildable in ~2–4 weeks, concierge-first)

**MVP thesis:** *"Describe your game (or paste your Steam page). Get an AI executive producer that benchmarks you against 8–10 real comparables, scores your solo-feasibility, hands you a Must/Should/Could/Kill scope plan and a vertical-slice roadmap — plus a free, shareable Steam page audit — refreshed weekly."*

**User journey:** Land ("free AI audit / studio plan") → Intake (game concept + constraints, or Steam URL) → **Output** (solo-feasibility score + scope plan + comparables brief; or scored page audit with 2–3 specific fixes) → Convert ("get a weekly producer report + scope watch") → Operate (Monday report: top 3 moves, scope risks, competitor changes, one generated artifact).

**Screens:** (1) Landing + intake; (2) **Report page** (the money screen — scored, specific, shareable); (3) Auth + onboarding (genre, stage, goal, time budget, art capability); (4) **Operator dashboard / weekly report**; (5) Stripe billing; (6) internal concierge/admin view.

**Backend services:** intake parser; **comparables engine** (tag/genre similarity → 8–10 peers + public metrics); **scope-scoring service** (rules/heuristics); LLM synthesis (`claude-opus-4-8` for the high-stakes report, cheaper tier for digests); report generator (JSON → page + email); scheduler/queue; persistence.

**Data sources (public only):** Steam store pages (HTML), Steam Web API / `appdetails`, **Steam review API** (official, great); SteamSpy/VGI/Gamalytic (label as *estimates*; respect ToS); YouTube/Reddit later. **Defer Discord.**

**Automate vs. manual:** automate scraping, comparables, scoring, report generation, scheduling, email. Keep human-in-loop early: final tone/credibility pass, scope-kill calls, outreach curation. Sell the outcome; hand-finish the first ~15–20 customers.

**Do NOT build yet:** Discord bot; influencer auto-send CRM; revenue-share mechanics; mobile app; multi-game studio dashboards; AI game-content generation; deep Steamworks OAuth.

---

## 6. Technical Architecture

- **Frontend:** Next.js (App Router) + Tailwind + shadcn/ui on Vercel; SSR the public report (each report is a marketing/SEO asset).
- **Backend:** Next.js route handlers / serverless + a small worker (Node or Python) for scraping & scheduled jobs.
- **DB/Auth:** Supabase (Postgres + Auth + storage + RLS); magic-link/Google auth.
- **AI:** Anthropic Claude — `claude-opus-4-8` for high-stakes synthesis (quality sells the subscription), Haiku/Sonnet for routine digests; strict JSON/tool-use schemas so the UI is deterministic.
- **Scraping/API:** prefer official Steam endpoints over HTML scraping; cache comparables daily; respect rate limits.
- **Queue/jobs:** Supabase cron / Upstash QStash; idempotent.
- **Reports:** JSON-from-LLM → React render; email via Resend/Postmark; optional PDF.
- **Integrations roadmap:** Steam (public now; Steamworks OAuth later for real wishlist data — big trust/value unlock), GitHub (commits → patch notes), YouTube (creators), Reddit (mentions), Discord (last, ToS-careful).

**Legal/platform risks:** no official public wishlist-count API (store-page scraping is grey — prefer official endpoints + cached/light scraping + eventual Steamworks OAuth for the user's own data); third-party revenue numbers are *estimates* with ToS limits — label as such; Discord self-bots are a real risk (official opt-in bot only); position all outputs as *recommendations, not guarantees*; over-index on specific, grounded, cited outputs to counter the "AI slop" allergy.

---

## 7. Research Plan

- **Read:** Chris Zukowski (HowToMarketAGame), GameDiscoverCo (Simon Carless); "Steam wishlist conversion benchmarks," "Next Fest results post-mortem," "store page best practices," "capsule A/B test"; sold-X-copies post-mortems.
- **Communities:** r/gamedev, r/IndieDev, r/IndieGaming, r/playmygame; HowToMarketAGame Discord, TIGSource, indie Discords; #screenshotsaturday / #indiedev; Steam discussion boards.
- **Competitors:** GameDiscoverCo Plus, VG Insights / Gamalytic, HowToMarketAGame products, Keymailer/Lurkit/Woovit, Ludo.ai (to contrast positioning).
- **Steam dataset (the moat):** for 50 recent indie launches across 3 target genres — tags, capsule style, short-desc patterns, screenshot count/order, price, review count/score, demo presence, Next Fest participation, (estimated) wishlist→sale conversion.
- **Pain validation:** search "wishlist," "not selling," "no one sees my game," "scope creep," "too ambitious" threads; tag recurring complaints and map each to a workflow.
- **Dev interview questions:** current wishlist count + feeling; walk me through last week's marketing/ops; what you avoid/hate and why; what you've paid for and whether it was worth it; what a weekly producer report would be worth/month; what would make you *not* trust an AI to do this.

---

## 8. Validation Plan (before building)

- **Landing test / fake-door:** free-audit form collecting concept/URL + email; "your audit is being prepared." Headline A: "AI Executive Producer for solo game devs." B: "Is your solo game shippable? Free scope + Steam audit." Drive from Reddit/Discord/Twitter; measure capture + "notify me."
- **Concierge MVP:** for 10–20 devs, hand-produce the scope plan + audit; **charge $19–29** to test willingness to pay (payment > praise).
- **Cold outreach:** devs who just posted a Steam page or a "too ambitious / scope" thread; Next Fest participants; #screenshotsaturday posters. ~50 personalized DMs offering a free hand-made audit.
- **Pricing tests:** same value at $9 / $19 / $39 to different cohorts; measure conversion *and* week-2 retention.
- **Kill/Go:** if you can't get ~10 devs to pay even $19 for a concierge weekly operator within a few weeks, the monthly thesis is weak — pivot toward one-time reports.

---

## 9. Pricing

| Model | Verdict |
|---|---|
| **Free audit (Steam page + scope snapshot)** | **Always free** — acquisition / viral hook / fake-door. |
| **One-time report** ($19–49) | Yes as entry SKU, but a transaction, not a business. |
| **Monthly Studio Operator** ($19–39/mo) | **PRIMARY recurring product** — weekly actions, scope watch, competitor watch, artifacts. |
| **Premium launch campaign** ($99–199 one-time) | Yes — high-margin SKU around the demo/launch deadline. |
| **Revenue-share / publisher-like** | Not yet — attribution unprovable, trust bar too high. Revisit at scale. |

**Recommended start:** Free audit → **$29/mo "Studio Operator"** (with a $19 intro/annual lever) + a **$149 one-time "Launch Campaign."** Stay under GameDiscoverCo Plus on price; differentiate on *action over data*. Sub-$30/mo is the solo-dev psychological zone; the launch SKU captures the spend spike.

---

## 10. Risks (brutally honest)

- **Thin-wrapper death:** generic output → brutal churn + hostile word-of-mouth. *Mitigation: grounded, cited, comparable-benchmarked specificity; proprietary benchmark dataset.*
- **AI weakest where it matters:** taste calls (capsule art, "is it fun," positioning) and quantified predictions are things LLMs bluff. *Mitigation: recommendations + rationale, not guarantees; rules for numbers; concierge-tune; always show the comparables.*
- **Data access is the existential blocker:** real wishlist/conversion numbers live behind Steamworks login. *Mitigation: opt-in Steamworks OAuth as a premium unlock; until then, label public proxies as estimates.*
- **"AI slop" allergy:** indie devs are vocally skeptical. Branding as "AI makes your game" is poison — stay "operator that does the boring ops you hate."
- **Toy vs. business:** a one-shot audit with generic tips is a toy. A recurring operator with a compounding dataset and a visible before/after on a metric the dev cares about is a business.
- **Small TAM realism:** commercially-serious solo Steam devs number in the low hundreds-of-thousands with thin wallets — a lean/indie SaaS, not obviously VC-scale without expanding to teams/publishers.
- **Seasonality:** value spikes around launch. *Mitigation: production-side (scope, builds, playtests) + post-launch ops to retain across the lifecycle.*
- **Platform dependence:** built on Steam's grace; diversify signal sources over time.

---

## 11. Sharpened Concept

- **Names:** company **Microstudio OS**; the free Steam-audit surface ships as **"Greenlit."** (Alts: SoloForge, Tiny Studio Operator, Market Familiar.)
- **Tagline (vision):** *"Your solo game needs a producer before it needs more ideas."* **(Hook):** *"You make the game. We run the studio."*
- **Core promise:** *"Never build blind again — keep your solo game commercially legible, production-safe, and continuously validated."* A **studio-function compressor** (producer + market analyst + scope police + QA reader + Steam strategist + launch operator) under explicit human gates. Human owns fantasy, taste, and final calls; AI proposes, researches, drafts, audits — never decides.
- **ICP:** solo / 1–3 person dev building a commercial PC game for Steam within 6–18 months; can build, weak on market read / scope discipline / launch; willing to spend <$30/mo (solo) to ~$99–149/mo (microstudio).
- **Feature architecture:** (1) **Concept Lab** → hook, core loop, tag cluster, comparables, solo-feasibility score, vertical-slice target, feature cutline. (2) **Market Scout** → Steam cluster/tags/capsules/price-bands/review-complaints. (3) **Scope Governor** *(killer feature)* → Must/Should/Could/Kill + solo-risk forecast. (4) **Steam Page Operator** → capsule/desc/tags/trailer-beats/wishlist plan (starts before production). (5) **Build Auditor** → readability/clarity/onboarding/market-promise audit. (6) **Playtest Synthesizer** → observed-behavior vs. player-claim vs. design-inference vs. action. (7) **Devlog/Community Operator** → human-approved drafts. Surfaced as an auditable **Daily Studio Feed**.
- **MVP feature set (ship first):** free Steam page audit (scored, benchmarked, shareable); solo-feasibility score + Must/Should/Could/Kill scope plan; comparables brief (8–10 real peers); weekly ranked action plan; one generated artifact/week; Monday email report. *(Concierge-finished for the first cohort.)*
- **North-star metric:** a **solo-feasibility / shippability health** trend on the production side, with **wishlist growth attributable to acted-on recommendations** as the demand-side proxy (leading: % of weekly recommendations marked "done"; weekly active-operator retention).
- **First 10 users:** hand-made free audits DM'd to devs who just posted a Steam page or a "too ambitious / scope creep" thread (Reddit + Next Fest list + #screenshotsaturday); convert the delighted to a $19 concierge month. Be a present human in 2–3 indie Discords first.
- **30-day build plan:** **Wk1** — 30 interviews/DMs; ship free-audit fake-door; stand up Next.js+Supabase; build Steam fetch + comparables; hand-make 5 reports. **Wk2** — automate scored audit + comparables + scope scoring + Claude synthesis; ship shareable report; get 20+ reports into devs' hands. **Wk3** — weekly action plan + Monday email + Stripe; onboard 5–10 concierge subscribers at $19–29; instrument "mark done" + retention. **Wk4** — add review mining + first outreach draft; measure paid conversion + week-2 retention vs. the kill/go bar; decide automate-more vs. pivot-to-one-time.

---

## Companion agent personas

This brief is paired with a network of agent personas under [`game-development/microstudio-os/`](../game-development/microstudio-os/) that operationalize the feature architecture above: **Studio Operator** (orchestrator), **Concept Lab**, **Scope Governor**, **Market Scout**, **Steam Page Operator**, **Build Auditor**, and **Playtest Synthesizer**.
</content>
</invoke>
