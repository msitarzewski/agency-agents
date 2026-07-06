# Platform Architecture — How the Four Projects Fit Together

## The three layers

### 1. Product layer — Vibe-Trading (`trading/vibe-trading/`)

The only component with a shippable end-user surface, and therefore the platform's front door:

- **Interfaces:** interactive CLI (`vibe-trading`), React Web UI (`frontend/`), FastAPI REST server (`agent/api_server.py`), MCP server (`agent/mcp_server.py`).
- **Capabilities:** 18 market-data loaders (US/A-share/HK/crypto), backtesting with layered attribution, Alpha Zoo (456 factors) with `alpha compare`, Research Autopilot (hypothesis → signal engine → backtest), Shadow Accounts (learn rules from your real fills), 10 broker connectors, multi-agent swarm presets (investment committee, quant desk, risk committee).
- **Persistence:** sessions, run library (`/reports`), per-run token usage, Docker volumes.

### 2. Research-engine layer — TradingAgents & TradingAgents-CN (`trading/tradingagents*/`)

Structured multi-agent debate pipelines that produce a trading decision with an auditable reasoning trail:

- **Pipeline:** market/sentiment/news/fundamentals analysts → bull vs. bear researcher debate → trader proposal → risk-management debate → portfolio-manager verdict.
- **TradingAgents** targets US markets; v0.3.0 adds a verified data-access contract, FRED and Polymarket vendors, and a broad LLM provider registry (OpenAI-compatible, NVIDIA, Kimi, Groq, Mistral, Bedrock).
- **TradingAgents-CN** (Apache core only — see THIRD_PARTY_LICENSES.md) adds A-share/HK data (tushare, AkShare), Chinese LLM providers (Qwen, GLM, DeepSeek), and localized prompts.

### 3. Workforce layer — the agent roster (`AGENTS.md`, division directories)

Personas installed into your AI coding tool that act as the platform's *staff* while you build and operate it:

- `finance/` — investment researcher, financial analyst, FP&A: strategy design and review.
- `engineering/`, `security/` — build and harden the platform itself.
- `marketing/`, `sales/`, `paid-media/`, `strategy/` — the go-to-market side of docs/MONETIZATION.md.

## Integration patterns

### A. Thesis → validation → execution
1. Run a **TradingAgents** pipeline on a ticker to produce a researched thesis (BUY/HOLD/SELL + reasoning trail).
2. Encode the thesis as a hypothesis in **Vibe-Trading's Research Autopilot** (`run_research_autopilot`), which scaffolds a SignalEngine and backtests it.
3. If validated, paper-trade or go live through Vibe-Trading's broker connectors; track it as a Shadow Account.

### B. One product, two brains
Expose both research engines behind Vibe-Trading's API/MCP surface: US requests route to `tradingagents`, A-share/HK requests to `tradingagents-cn`'s core library. Vibe-Trading's loader registry already covers both regions' market data, so the engines share one data plane.

**Implemented:** [`trading/bridge/`](../trading/bridge/README.md) runs one small HTTP service per engine (`research_bridge.py --engine … --port …`) and returns the decision plus the full reasoning trail; `client.py` is a stdlib-only client that routes by market and works from inside any of the platform's virtualenvs, including a Vibe-Trading session.

### C. MCP-first composition
Vibe-Trading ships an MCP server; the roster installs into MCP-capable clients (Claude Code, Cursor, …). A finance persona in your editor can therefore *directly drive* the trading platform — run backtests, compare alphas, pull fund-flow data — without custom glue.

## Dependency isolation

The three trading stacks pin conflicting dependency versions (different LangChain generations, provider SDKs). Keep them in **separate virtualenvs**; compose at the process/API boundary (REST/MCP), not the import boundary. This is deliberate: it keeps each stack upgradable from upstream via a simple re-vendor.

## Re-vendoring from upstream

Each `trading/<name>/` directory is a snapshot. To refresh one: pull the upstream repo, re-apply the exclusion list in THIRD_PARTY_LICENSES.md (notably TradingAgents-CN's proprietary `app/` and `frontend/`), and replace the directory in a single commit titled `vendor: bump <name> to <upstream ref>`.
