# Monetization Strategy for the Unified Platform

The unified repo exists to support one thesis: **sell the product surface (Vibe-Trading) while the research engines and agent roster differentiate it.** Everything here is MIT/Apache-licensed and safe to commercialize — with one carve-out documented in THIRD_PARTY_LICENSES.md (TradingAgents-CN's proprietary web app is excluded and must stay excluded).

## Priority 1 — Hosted trading copilot (SaaS)

Vibe-Trading already has the full product shape: Web UI, REST + MCP API, auth hooks (`API_AUTH_KEY`), Docker deployment, persistent run library. The gap to SaaS is multi-tenancy and billing, not features.

- **Free:** research chat, backtests on delayed data, 3 saved strategies, community alphas.
- **Pro ($29–49/mo):** live data sources, Research Autopilot, Shadow Accounts, scheduled research, full Alpha Zoo + `alpha compare`, unlimited run library.
- **Desk ($199+/mo):** broker connectors / live execution, swarm presets (investment committee, risk committee), multi-seat, priority support.
- **Metering levers already in the code:** per-run `llm_usage.json` token accounting, scheduler opt-in flag, connector authorization flow.

## Priority 2 — Research-as-a-Service API

Sell the *combined* engine output as an API product: one endpoint that runs a TradingAgents debate pipeline (US) or the CN core (A-share/HK) and returns the decision + reasoning trail + a Vibe-Trading backtest validation.

- Price per research run (token-cost-plus) or via monthly run quotas.
- The auditable multi-agent reasoning trail is the differentiator vs. "GPT wrapper" signal services — and the arXiv paper behind TradingAgents is the credibility asset.
- Target buyers: fintech apps, newsletters, prop-trading educators, quant hobbyist platforms.

## Priority 3 — B2B / white-label

- **White-label the platform** for prop firms, RIAs, and trading educators: their brand on the Vibe-Trading UI, your infrastructure underneath. Setup fee + monthly platform fee.
- **China market angle:** TradingAgents-CN's Apache core + Vibe-Trading's MIT frontend is a legally clean localized offering (the upstream CN project's own web app is proprietary — you're offering what it charges for, on your own MIT stack).
- **Enterprise support contracts:** deployment, custom data connectors, custom swarm presets.

## Priority 4 — The roster as growth engine (not the revenue line)

Keep the agent roster free and MIT. It's the top-of-funnel: installable in every AI coding tool, each persona a shareable artifact. Monetize adjacently:

- Premium *finance* agent packs tuned to drive the trading platform via MCP (the pattern in ARCHITECTURE.md §C).
- Paid "build your own trading copilot" course/bootcamp using this repo as the curriculum.
- Sponsorships/featured listings if the roster app gains distribution.

## Sequencing (90 days)

1. **Weeks 1–4:** Deploy hosted Vibe-Trading (single-tenant per customer is fine initially — Docker compose per customer). Add Stripe + signup in front. Charge from day one.
2. **Weeks 5–8:** Wire TradingAgents behind the API as the "Deep Research" premium feature; publish 2–3 public research reports weekly as marketing.
3. **Weeks 9–12:** First white-label pilot (one educator or small prop firm), and launch the research API with per-run pricing.

## Compliance guardrails (non-optional)

- Position everything as **research/analysis tooling**, not investment advice; consult counsel before marketing auto-execution to retail (jurisdiction-dependent: RIA/broker-dealer rules in the US, CSRC rules for CN-market services).
- Broker connector revenue-shares and data-vendor redistribution each require partner agreements.
- Keep upstream attribution intact (THIRD_PARTY_LICENSES.md) and rebrand the commercial offering under your own trademark.
