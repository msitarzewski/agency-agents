# Private Client Acquisition OS

This directory is a private operator layer around the existing Agency Agents repository. It is for local use by the owner, not a new agent marketplace or SaaS product.

## What we are building

```text
Prospect list
  -> public web evidence collection
  -> company research
  -> qualification
  -> pain detection
  -> personalized audit angle
  -> outreach draft
  -> HUMAN APPROVAL
  -> manual/approved sending
  -> reply/discovery
  -> proposal
  -> won client
```

The existing specialist markdown files remain the workforce. This layer supplies state, contracts, execution, tracing, local lead intake, evidence collection and approval boundaries.

## Current status

- Phase 1 foundation: complete
- Phase 2 executable deterministic runner: complete
- Phase 3 real model adapter + CSV lead intake: complete
- Phase 3 public web research evidence layer: complete
- Network side effects: still disabled by default

## Local setup

No Python packages are required for the core runner or public research layer. Use Python 3.10+.

Copy `.env.example` to `.env` and set an OpenAI-compatible provider if you want real model execution. The adapter expects a `/chat/completions` endpoint.

Required values:

```text
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-key
LLM_MODEL=your-model
```

Do not commit `.env` or API keys.

## Research one prospect

Public research uses a local HTTP client and DuckDuckGo's public HTML search endpoint. It does not log in, access private profiles, send messages, or perform outbound actions.

```bash
python client-acquisition/cli.py research-lead --company "Hyppy" --name "Sawni Gupta"
```

The command returns search queries, public source URLs, page text excerpts and fetch errors. Treat search results as evidence to review, not automatically verified facts.

## Run a lead with live public research

```bash
python client-acquisition/cli.py run-lead \
  --name "Sawni Gupta" \
  --company "Hyppy" \
  --provider llm \
  --web-research
```

The web evidence is inserted into the same evidence-first context used by the existing research, qualification, pain and outreach agents. The LLM is still instructed not to invent facts, and outreach remains `send=false` behind human approval.

You can cap research sources:

```bash
python client-acquisition/cli.py run-lead --company "Hyppy" --name "Sawni Gupta" --provider llm --web-research --max-sources 5
```

## Run a lead CSV with research

Use `client-acquisition/data/leads.example.csv` as the template. Important columns are:

`company_name,contact_name,contact_email,website,source,evidence`

Run:

```bash
python client-acquisition/cli.py run-csv client-acquisition/data/leads.example.csv --provider llm --web-research
```

The CSV runner prints one JSON result per lead and never sends outreach.

## Evidence-first rule

The model must not invent company facts. Every research claim should be tied to supplied evidence. Public-web research adds source URLs and page excerpts to the same evidence context. A source being discovered by search does not by itself prove that every claim on the page is current, accurate or attributable to the company, so the workflow preserves source URLs and uncertainty for review.

## Client strategy

The first offer is intentionally narrow: ecommerce/D2C operations automation. We look for businesses showing operational complexity (multiple channels, large catalogs, manual reporting, support/order workload, spreadsheet-heavy processes, or similar public signals) and sell a concrete business outcome rather than "AI agents".

The acquisition system should help create a small number of high-quality, evidence-backed conversations. Human approval remains mandatory before outbound communication.
