# 🏦 The Agency Platform — AI Agents + Autonomous Trading, One Repo

> **Four projects, one platform.** A full roster of specialist AI agents, a production-grade personal trading agent, and two multi-agent LLM trading research frameworks — unified so each one makes the others more valuable.

| Component | What it is | License | Docs |
|---|---|---|---|
| **[Agents roster](AGENTS.md)** | 100+ specialist AI agent personas (engineering, finance, marketing, security, …) installable into Claude Code, Cursor, Codex, Gemini CLI, and more | MIT | [AGENTS.md](AGENTS.md) |
| **[Vibe-Trading](trading/vibe-trading/)** | Personal trading agent platform: CLI + Web UI + REST/MCP API, 18 market-data sources, backtesting, Alpha Zoo (456 factors), broker connectors, swarm presets | MIT | [trading/vibe-trading/README.md](trading/vibe-trading/README.md) |
| **[TradingAgents](trading/tradingagents/)** | Multi-agent LLM financial trading research framework (analyst → researcher → trader → risk → portfolio manager pipeline), backed by the [arXiv paper](https://arxiv.org/abs/2412.20138) | Apache-2.0 | [trading/tradingagents/README.md](trading/tradingagents/README.md) |
| **[TradingAgents-CN](trading/tradingagents-cn/)** | China-market edition: A-share/HK data sources (tushare, AkShare), Chinese LLM providers (Qwen, GLM, DeepSeek), localized pipeline | Apache-2.0 core¹ | [trading/tradingagents-cn/README.md](trading/tradingagents-cn/README.md) |

¹ Only the Apache-2.0 components of TradingAgents-CN are vendored here. Its proprietary FastAPI backend (`app/`) and Vue frontend are **excluded** — see [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

---

## Why one repo?

Each project alone is a tool. Together they're a **stack**:

```
┌─────────────────────────────────────────────────────────┐
│  The Agency roster (AGENTS.md)                          │
│  finance/, strategy/, marketing/, engineering/ personas │
│  → your "staff": analysts, researchers, growth, ops     │
├─────────────────────────────────────────────────────────┤
│  Vibe-Trading (trading/vibe-trading)                    │
│  → the PRODUCT: Web UI, API/MCP server, backtests,      │
│    live broker connectors, shadow accounts              │
├─────────────────────────────────────────────────────────┤
│  TradingAgents / TradingAgents-CN (trading/…)           │
│  → the RESEARCH ENGINES: multi-agent debate pipelines   │
│    for US and China markets                             │
└─────────────────────────────────────────────────────────┘
```

- Use **agency finance agents** (`finance/finance-investment-researcher.md`, `finance/finance-financial-analyst.md`) inside Claude Code/Cursor to develop and review strategies for the trading stacks.
- Use **TradingAgents'** analyst-debate pipeline to generate trade theses; validate them with **Vibe-Trading's** backtester and Alpha Zoo; execute via Vibe-Trading's broker connectors.
- Ship **one product** (Vibe-Trading's Web UI/API) with **two research brains** (US + CN markets) behind it.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the integration map and [docs/MONETIZATION.md](docs/MONETIZATION.md) for the business plan built on this structure.

## Quick start

### 1. Install the agent roster (any AI coding tool)

```bash
./scripts/install.sh --tool claude-code            # or cursor, codex, gemini-cli, …
./scripts/install.sh --tool claude-code --division finance,strategy
```

### 2. Run Vibe-Trading (the product)

```bash
cd trading/vibe-trading
pip install -e .          # or: pip install vibe-trading-ai
vibe-trading              # interactive CLI
# Web UI + API: see trading/vibe-trading/README.md (docker compose up)
```

### 3. Run a TradingAgents research pipeline

```bash
cd trading/tradingagents
pip install -r requirements.txt
python main.py            # US markets
```

```bash
cd trading/tradingagents-cn
pip install -r requirements.txt
python main.py            # A-share / HK markets
```

> ⚠️ Each trading stack keeps its own Python dependencies — use a separate virtualenv per stack (they pin different LangChain/provider versions).

## Repository layout

```
├── AGENTS.md                  # the full agent roster & install guide (formerly README)
├── <division>/                # agent personas: engineering/, finance/, marketing/, …
├── scripts/                   # roster install/convert tooling
├── trading/
│   ├── vibe-trading/          # personal trading agent platform (MIT)
│   ├── tradingagents/         # multi-agent trading research framework (Apache-2.0)
│   ├── tradingagents-cn/      # China-market edition, Apache-2.0 core only
│   └── bridge/                # HTTP bridge exposing the research engines to the product layer
├── docs/
│   ├── ARCHITECTURE.md        # how the pieces fit together
│   └── MONETIZATION.md        # revenue strategy for the unified platform
└── THIRD_PARTY_LICENSES.md    # provenance & license map
```

## Provenance

The `trading/` directory vendors code from upstream open-source projects (snapshot date 2026-07-06); original attribution, licenses, and exclusions are documented in [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md). Nothing in this repo is financial advice; live trading is at your own risk.
