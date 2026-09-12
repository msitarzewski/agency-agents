# Zipcode Market Opportunity Operator Design

## Overview

This design adds a specialized agent that identifies realistic, AI-solvable business opportunities by ZIP code using public signals first, with an optional extension point for internal sales or delivery data later.

The agent is intended to do more than rank ZIP codes. It should extract local and digitally concentrated market needs, infer the jobs buyers need done, estimate budget and urgency, identify who the likely buyer is, and enrich top opportunities with public contact paths and work intake clues.

## Problem

The repository currently lacks an agent focused on turning local market signals into actionable opportunity intelligence for AI-enabled products and services. Existing research and analytics agents can analyze trends, but they do not produce a field-ready list of:

- what the need is
- what job the buyer needs done
- who the buyer is
- what they are likely asking for
- how much they may pay
- how quickly they need it
- how AI can solve it
- how to reach named businesses publicly

## Goals

- Add one specialized operator agent for ZIP-level and locality-aware market opportunity discovery
- Default to public-signal analysis
- Support both productized services and product/SaaS opportunities
- Optimize for realistic opportunities with a mix of revenue and speed
- Return actionable dossiers, not abstract market summaries
- Include public contact paths and work intake clues for named business targets
- Leave a defined hook for internal CRM, lead, and close-rate data later

## Non-Goals

- Private or invasive contact scraping
- Fully automated outbound execution
- Full go-to-market sequence generation in the first version
- Replacing human judgment on legal, compliance, or sales qualification

## Recommended Placement

Place the agent in `specialized/` because it blends market intelligence, opportunity scoring, lead enrichment, and operational sales readiness.

Recommended filename:

- `specialized/zipcode-market-opportunity-operator.md`

## Agent Concept

### Name

Zipcode Market Opportunity Operator

### Core Role

An opportunity-intelligence operator that uses public market signals to identify unmet needs by ZIP code, infer the jobs buyers need done, estimate budgets and timing, recommend AI-enabled offers, and enrich top opportunities with public business contact paths and intake clues.

### Distinguishing Behavior

- treats ZIP code as a market signal, not a simplistic filter
- handles both local service businesses and digitally concentrated businesses
- scores both service-first and product-first opportunity paths
- separates pain from the solution a buyer would recognize
- attaches public business identity and outreach clues to top opportunities
- defaults to auditable outputs with signal links and confidence labels

## Core Output Shape

Each output row should represent a real opportunity dossier with these fields:

- `ZIP code`
- `Need category`
- `Pain statement`
- `Solution they'd buy`
- `What the job is`
- `Who it is for`
- `Likely buyer role`
- `Estimated budget`
- `Urgency / expected timeline`
- `AI-fit`
- `Offer type`
- `Competition density`
- `Confidence`
- `Public signals used`
- `Signal links`
- `Named businesses`
- `Public contact paths`
- `Work intake clues`
- `What you need to deliver the job`
- `Suggested pitch angle`
- `Suggested next action`

## Data Inputs

### Public Signals First

The initial version should prioritize:

- job boards and local hiring signals
- Google Maps, Yelp, and local business directories
- review text and complaint clusters
- service marketplaces and request boards
- search demand proxies and trend signals
- demographic and business concentration data
- ad density, listings quality, and visible competition signals

### Internal Data Hook Later

Future re-ranking inputs may include:

- CRM lead sources
- close rates
- ACV
- churn data
- referral data
- support logs

This internal layer should refine rankings rather than replace the public-signal base.

## Scoring Model

Each opportunity should be scored on:

- demand evidence
- buyer clarity
- budget realism
- urgency
- AI solvability
- speed to offer
- competition density
- confidence based on corroboration

The final ranking should favor realistic opportunities that balance revenue potential and speed to close.

## Lead Enrichment Boundary

The agent should enrich top opportunities with public business contact routes only:

- company website
- phone number
- public email or contact form
- booking page
- directory listing
- LinkedIn company or public decision-maker context where available

It should not be framed as a private-data scraping or invasive contact-harvesting agent.

## Workflow

1. Scan a ZIP code or ZIP set
2. Gather public market, business, review, and hiring signals
3. Infer recurring pains and buyer jobs
4. Score opportunities for realism, urgency, budget, and AI fit
5. Split recommendations into service-first, product-first, and combined views
6. Enrich top opportunities with named public business targets and contact paths
7. Return an action-ready dossier

## Acceptance Criteria

- A new specialized agent exists for ZIP-level opportunity discovery
- The prompt clearly distinguishes pain, buyer, ask, budget, urgency, and AI-fit
- The prompt includes competition density and auditable signal links
- The prompt includes named-business enrichment using public contact paths
- README includes the new agent in the Specialized Division roster

## Notes

This agent is intentionally an operator, not just an analyst. The success condition is not merely “interesting trends by ZIP,” but “a realistic list of opportunities you can actually sell or build against.”
