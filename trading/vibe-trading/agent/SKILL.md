---
name: vibe-trading
version: 0.1.10
description: Professional finance research toolkit — backtesting (7 engines + benchmark comparison panel), factor analysis, Alpha Zoo (452 pre-built alphas across qlib158/alpha101/gtja191/academic), options pricing, 79 finance skills, 29 multi-agent swarm teams, Trade Journal analyzer, and Shadow Account (extract → backtest → render) across 18 market-data sources (tushare, yfinance, okx, akshare, baostock, tencent, mootdx, ccxt, futu, local, eastmoney, sina, stooq, yahoo, plus optional-key finnhub/alphavantage/tiingo/fmp).
dependencies:
  python: ">=3.11"
  pip:
    - vibe-trading-ai
env:
  - name: TUSHARE_TOKEN
    description: "Tushare API token for China A-share data (optional — HK/US/crypto work without any key)"
    required: false
  - name: OPENAI_API_KEY
    description: "OpenAI-compatible API key — only needed for run_swarm (multi-agent teams). All other tools work without it."
    required: false
  - name: LANGCHAIN_MODEL_NAME
    description: "LLM model name for run_swarm (e.g. deepseek/deepseek-v4-pro). Only needed if using run_swarm."
    required: false
mcp:
  command: vibe-trading-mcp
  args: []
---

# Vibe-Trading

Professional finance research toolkit with AI-powered backtesting (7 engines), multi-agent teams, 79 specialized skills, the **Alpha Zoo** (452 pre-built quantitative alphas across qlib158 / alpha101 / gtja191 / academic with one-line CLI benchmarking), and the Shadow Account loop — extract your implicit trading rules from a journal, backtest them across A股/港股/美股/crypto, then see where they would have served you better.

## Setup

```bash
pip install vibe-trading-ai
```

> **Package name vs commands:** The PyPI package is `vibe-trading-ai`. Once installed, you get:
>
> | Command | Purpose |
> |---------|---------|
> | `vibe-trading` | Interactive CLI / TUI |
> | `vibe-trading serve` | Launch FastAPI web server |
> | `vibe-trading-mcp` | Start MCP server (for Claude Desktop, OpenClaw, Cursor, etc.) |

Add to your agent's MCP config:

```json
{
  "mcpServers": {
    "vibe-trading": {
      "command": "vibe-trading-mcp"
    }
  }
}
```

### API Key Requirements

Core research MCP tools work with zero API keys for HK/US/crypto. After `pip install`, backtesting, market data, factor analysis, options pricing, chart patterns, web search, document reading, trade journal analysis, shadow-account extraction/backtest/report, the Alpha Zoo (452 pre-built alphas), and all 79 skills are ready to use. IBKR tools require a local TWS / IB Gateway session; `run_swarm` requires an LLM key.

| Feature | Key needed | When |
|---------|-----------|------|
| HK/US equities & crypto | None | Always free (yfinance / stooq / yahoo + OKX) |
| China A-share data | None | Free via akshare / baostock / tencent / sina / eastmoney / mootdx fallback (`TUSHARE_TOKEN` optional for premium quality) |
| Premium US fundamentals/quotes | `FINNHUB_API_KEY` / `ALPHAVANTAGE_API_KEY` / `TIINGO_API_KEY` / `FMP_API_KEY` | Only for optional-key providers (graceful fallback to free sources) |
| Multi-agent swarm (`run_swarm`) | `OPENAI_API_KEY` + `LANGCHAIN_MODEL_NAME` | Swarm spawns internal LLM workers |

## What You Can Do

### Shadow Account — flagship loop

Feed a CSV broker export (同花顺 / 东财 / 富途 / generic), and the agent will:
1. `analyze_trade_journal` — profile your behavior (holding period, win rate, disposition effect, chasing, overtrading, anchoring).
2. `extract_shadow_strategy` — distill 3-5 if-then rules that describe your profitable roundtrips.
3. `run_shadow_backtest` — backtest those rules across A/HK/US/crypto and compute delta-PnL vs your realized trades.
4. `render_shadow_report` — produce an HTML/PDF report (8 sections + charts) with today's matching signals.
5. `scan_shadow_signals` — list today's symbols that match your shadow's entry cadence (research only).

### Backtesting
Create and run quantitative strategies across 7 engines (ChinaA, GlobalEquity, Crypto, ChinaFutures, GlobalFutures, Forex + options) with 18 market-data sources (auto-detect + ordered fallback):
- **HK/US equities** via yfinance / stooq / yahoo (free, no API key)
- **Cryptocurrency** via OKX or CCXT/100+ exchanges (free, no API key)
- **China A-shares** via AKShare / baostock / tencent / sina / eastmoney / mootdx (free, no API key) — `TUSHARE_TOKEN` optional for premium quality
- **Futures, forex, macro** via AKShare (free, no API key)
- **HK & A-share equities** via Futu (broker login required, optional)
- **Local CSV/parquet bars** via the `local` loader (offline, no network)
- **Premium US data** via optional-key finnhub / alphavantage / tiingo / fmp (graceful fallback to free sources)

Example workflow:
1. Use `list_skills()` to discover strategy patterns
2. Use `load_skill("strategy-generate")` for the strategy creation guide
3. Use `write_file()` to create `config.json` and `code/signal_engine.py`
4. Use `backtest()` to run and get metrics (Sharpe, return, drawdown, etc.)

### Multi-Agent Swarm Teams
29 pre-built agent teams for complex research:
- **Investment Committee**: bull/bear debate → risk review → PM decision
- **Global Equities Desk**: A-share + HK/US + crypto → global strategist
- **Crypto Trading Desk**: funding/basis + liquidation + flow → risk manager
- **Earnings Research Desk**: fundamentals + revisions + options → earnings strategist
- **Macro/Rates/FX Desk**: rates + FX + commodities → macro PM
- **Quant Strategy Desk**: screening → factor research → backtest → risk audit
- **Risk Committee**: drawdown, tail risk, regime analysis
- And 22 more specialized teams

Use `list_swarm_presets()` to see all teams, then `run_swarm()` to execute.

### Alpha Zoo (452 pre-built alphas)
One-line cross-sectional IC / IR / alive-reversed-dead categorisation across four bundled zoos:
- **qlib158** (154 alphas) — Microsoft Qlib's `Alpha158` feature handler, Apache-2.0 with pinned commit SHA.
- **alpha101** (101 alphas) — Kakushadze (2015) "101 Formulaic Alphas" (arXiv:1601.00991), written from the paper appendix.
- **gtja191** (191 alphas) — Guotai Junan 2014 "191 Short-period Trading Alpha Factors" research report.
- **academic** (6 factors) — Fama-French 5 + Carhart momentum (honest price-based proxies).

Each alpha ships with `__alpha_meta__` (formula LaTeX + theme + universe + warmup + columns required), guarded by an AST purity gate + 300-row lookahead sentinel test. Use the `vibe-trading alpha {list,show,bench,compare,export-manifest}` CLI, the `/alpha/*` REST routes (browser at `/alpha-zoo`), or compose multi-factor signals via `ZooSignalEngine.from_zoo(...)`.

### Finance Skills (79)
Comprehensive knowledge base covering:
- Technical analysis (candlestick, Elliott wave, Ichimoku, SMC, harmonic, chanlun)
- Quantitative methods (factor research, ML strategy, pair trading, multi-factor)
- Risk management (VaR/CVaR, stress testing, hedging)
- Options (Black-Scholes, Greeks, multi-leg strategies, payoff diagrams)
- HK/US equities (SEC filings, earnings revisions, ETF flows, ADR/H-share arbitrage)
- Crypto trading desk (funding rates, liquidation heatmaps, stablecoin flows, token unlocks, DeFi yields)
- Behavioral finance, trade journal diagnostics, shadow account
- Macro analysis, credit research, sector rotation, and more

Use `load_skill(name)` to access full methodology docs with code templates.

## Available MCP Tools (54)

| Tool | Description | API Key |
|------|-------------|---------|
| `list_skills` | List all 79 finance skills | None |
| `load_skill` | Load full skill documentation | None |
| `start_research_goal` | Create an auditable research goal | None |
| `get_research_goal` | Read the current research goal | None |
| `add_goal_evidence` | Attach evidence to a research goal | None |
| `update_research_goal_status` | Update goal lifecycle status | None |
| `backtest` | Run vectorized backtest engine | None* |
| `factor_analysis` | IC/IR analysis + layered backtest | None* |
| `analyze_options` | Black-Scholes price + Greeks | None |
| `pattern_recognition` | Detect chart patterns (H&S, double top, etc.) | None |
| `get_market_data` | Fetch OHLCV data (auto-detect + ordered fallback across 18 sources) | None* |
| `get_fund_flow` | Capital fund-flow (main/retail net inflow) | None* |
| `get_dragon_tiger` | Dragon-tiger list (龙虎榜) top buyer/seller seats | None* |
| `get_northbound_flow` | Northbound (Stock Connect) net flow | None* |
| `get_margin_trading` | Margin trading & short-selling balances | None* |
| `get_block_trades` | Block-trade (大宗交易) records | None* |
| `get_shareholder_count` | Shareholder-count history per symbol | None* |
| `get_lockup_expiry` | Restricted-share lockup release schedule | None* |
| `get_sector_info` | Sector / industry constituents & performance | None* |
| `get_research_reports` | Sell-side analyst research reports | None* |
| `get_stock_news` | Market & company news headlines | None* |
| `get_sec_filings` | SEC EDGAR filings (10-K/10-Q/8-K, etc.) | None |
| `get_financial_statements` | Income / balance / cash-flow statements | None* |
| `get_options_chain` | Options chain (strikes, IV, OI, Greeks) | None* |
| `get_stock_profile` | Valuation, analyst estimates & institutional holdings (US/HK) | None |
| `screen_market` | Market screener with fundamental/technical filters | None* |
| `search_symbol` | Symbol / ticker search across markets | None |
| `get_macro_series` | FRED macroeconomic series | FRED_API_KEY |
| `iwencai_search` | A-share natural-language research search | IWENCAI_KEY |
| `web_search` | Search the web via DuckDuckGo | None |
| `read_url` | Fetch web page as Markdown | None |
| `read_document` | Extract text from PDF/DOCX/XLSX/PPTX/images | None |
| `write_file` | Write files (config, strategy code) | None |
| `read_file` | Read file contents | None |
| `analyze_trade_journal` | Parse broker CSV → profile + behavior diagnostics | None |
| `extract_shadow_strategy` | Distill 3-5 if-then rules from profitable roundtrips | None |
| `run_shadow_backtest` | Multi-market backtest + delta-PnL attribution | None* |
| `render_shadow_report` | HTML/PDF shadow report (8 sections + charts) | None |
| `scan_shadow_signals` | Today's symbols matching the shadow's cadence | None |
| `list_swarm_presets` | List multi-agent team presets | None |
| `run_swarm` | Execute a multi-agent research team | LLM key |
| `get_swarm_status` | Poll swarm run status without blocking | None |
| `get_run_result` | Get final report and task summaries | None |
| `list_runs` | List recent swarm runs with metadata | None |
| `reap_stale_runs` | Finalize stale swarm runs | None |
| `retry_run` | Re-run a failed/stale swarm run | LLM key |
| `trading_connections` | List selectable connector profiles | None |
| `trading_select_connection` | Select the default connector profile | None |
| `trading_check` | Check connector readiness | Connector app/OAuth |
| `trading_account` | Read account summary from selected connector | Connector app/OAuth |
| `trading_positions` | Read positions from selected connector | Connector app/OAuth |
| `trading_orders` | Read open orders from selected connector | Connector app/OAuth |
| `trading_quote` | Read a quote snapshot from selected connector | Connector app/OAuth |
| `trading_history` | Read historical bars from selected connector | Connector app/OAuth |

<sub>*A-share symbols require `TUSHARE_TOKEN`. HK/US/crypto are free. Trading connector rows use the selected connector profile, e.g. IBKR local TWS/Gateway or Robinhood MCP OAuth.</sub>

## Quick Start

```bash
pip install vibe-trading-ai
```

That's it — no API keys needed for HK/US/crypto markets. Start using `backtest`, `get_market_data`, `analyze_options`, `analyze_trade_journal`, `extract_shadow_strategy`, `web_search`, the **Alpha Zoo** (`vibe-trading alpha bench --zoo gtja191 --universe csi300 --period 2018-2025`), and all 79 skills immediately.

## Loading Tools from External MCP Servers

The built-in agent can load tools from your own external MCP servers in addition to its local toolset.

> **Note:** This is the *MCP client* path — the opposite of the MCP plugin listed above. The plugin above makes Vibe-Trading's tools available to your agents. This section lets Vibe-Trading's own agent call tools from *your* servers.

### Setup

Create `~/.vibe-trading/agent.json`:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "uvx",
      "args": ["my-mcp-server"],
      "toolTimeout": 30,
      "enabledTools": ["*"]
    }
  }
}
```

Ordinary external MCP tools appear automatically in every `vibe-trading run` / `vibe-trading chat` call. They are injected after local tools under stable names: `mcp_<server>_<tool>`. Live-broker MCP servers are consumed through the connector-scoped `trading_*` tools instead of exposing raw `mcp_<broker>_*` tools to the agent.

### Official IBKR MCP read-only probe

Add Interactive Brokers' official MCP endpoint as a read-only external server:

```json
{
  "mcpServers": {
    "ibkr": {
      "type": "streamableHttp",
      "url": "https://api.ibkr.com/v1/api/mcp",
      "auth": {
        "type": "oauth",
        "scopes": ["mcp.read"],
        "clientName": "Vibe-Trading",
        "cacheDir": "~/.vibe-trading/live/ibkr/oauth"
      },
      "enabledTools": ["*"]
    }
  }
}
```

Authorize it with `vibe-trading connector authorize ibkr-live-official-mcp-readonly`. The wildcard is accepted
only for this `mcp.read` probe. Generic `trading_account` and `trading_positions`
calls stay disabled until IBKR publishes stable read tool names that Vibe-Trading
can map safely; `mcp.write` requires an explicit tool allowlist and live
order-guard handling. If IBKR issues a pre-registered OAuth client, add
`clientId` and `clientSecret` inside `auth`.

### Trading connector profiles

The public trading surface is connector-first. Choose a connector profile, then
paper/live is just an attribute under that connector.

```bash
pip install "vibe-trading-ai[ibkr]"
vibe-trading connector list
vibe-trading connector use ibkr-paper-local
vibe-trading connector configure ibkr-paper-local --yes
vibe-trading connector check
vibe-trading connector account
vibe-trading connector positions
vibe-trading connector orders
vibe-trading connector quote AAPL
vibe-trading connector history AAPL --duration "30 D" --bar-size "1 day"
```

Default ports are TWS paper `7497`, IB Gateway paper `4002`, TWS live-readonly
`7496`, and IB Gateway live-readonly `4001`.

### Config fields

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `type` | stdio: no, HTTP: yes | inferred only for stdio | Transport type. Use `sse` or `streamableHttp` for URL-based servers. |
| `command` | stdio: yes | — | Executable to launch |
| `args` | no | `[]` | Command arguments |
| `env` | no | `{}` | Extra env vars for the subprocess |
| `url` | HTTP: yes | — | Remote SSE / streamable HTTP endpoint URL |
| `headers` | no | `{}` | Extra HTTP headers for SSE / streamable HTTP servers |
| `toolTimeout` | no | `30` | Seconds before a tool call is cancelled |
| `enabledTools` | no | `["*"]` | Allowlist of remote tool names. `["*"]` enables all |

For URL-based transports, `type` is required. The agent no longer guesses between SSE and streamable HTTP from the URL suffix.

### Per-session override (API)

> **Security — disabled by default.** `mcpServers` defines subprocess `command`/`args`/`env` and is therefore restricted to operator-level trust. API callers **cannot** inject MCP server definitions through `POST /sessions` unless the server operator explicitly opts in.

To enable session-level MCP injection, set the environment variable on the server before starting the agent:

```bash
export ALLOW_SESSION_MCP_SERVERS=1
```

With the opt-in active, pass `mcpServers` inside `session.config` to extend or replace the global config for that session only:

```json
{
  "config": {
    "mcpServers": {
      "research": {
        "command": "uvx",
        "args": ["research-mcp"],
        "enabledTools": ["search"]
      }
    }
  }
}
```

Without `ALLOW_SESSION_MCP_SERVERS=1`, any `mcpServers` key in `session.config` is silently stripped before config loading. The global operator config on disk (`~/.vibe-trading/agent.json`) is always respected regardless of this flag.

### v1 limits

- **Transport:** stdio, SSE, and streamable HTTP.
- **Execution:** serial only. MCP tools never enter the parallel readonly path.
- **Surfaces:** tools only. Resources and prompts are not exposed.
- **Swarm:** MCP tools are excluded from Swarm worker registries in v1.
- **Hot reload:** not supported. Restart the process to pick up config changes.

### Failure handling

| Case | Behavior |
|------|----------|
| Missing config file | falls back to empty config — no MCP servers loaded |
| Invalid config file | logs a warning and falls back to empty config |
| Server fails to start | that server is skipped; local tools and other servers still load |
| Tool call times out | returns a normalized error payload instead of raising |
| Two server names collide after sanitization | deterministic hash suffix appended; operator warning emitted |



## Examples

**Backtest a MACD strategy on Apple:**
> Backtest AAPL with MACD crossover strategy (fast=12, slow=26, signal=9) for 2024

**Analyze my trade journal and build a Shadow Account:**
> Call analyze_trade_journal on ~/Downloads/tonghuashun.csv, then extract_shadow_strategy with min_support=3, then run_shadow_backtest for the last year, then render_shadow_report.

**Run an investment committee review:**
> Use run_swarm with investment_committee preset to evaluate NVDA. Variables: target=NVDA.US, market=US

**Factor analysis on CSI 300:**
> Run factor_analysis on CSI 300 stocks using pe_ttm factor from 2023 to 2024

**Options analysis:**
> Use analyze_options: spot=100, strike=105, 90 days, vol=25%, rate=3%
