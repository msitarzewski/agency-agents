# Research Bridge

Exposes the TradingAgents research engines as HTTP services so the rest of the platform — Vibe-Trading, MCP clients, or paying API customers — can request a full multi-agent research run (analysts → researcher debate → trader → risk → portfolio manager) and get back a **decision plus its reasoning trail**.

This implements integration pattern **B ("one product, two brains")** from [docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md): composition happens at the process boundary because the two engines pin conflicting dependencies and both import as `tradingagents`.

## Setup — one virtualenv per engine

```bash
# US engine
python -m venv ~/.venvs/ta-us && source ~/.venvs/ta-us/bin/activate
pip install -r ../tradingagents/requirements.txt -r requirements.txt
export TRADINGAGENTS_LLM_PROVIDER=openai OPENAI_API_KEY=...   # per engine docs
python research_bridge.py --engine ../tradingagents --port 8801
```

```bash
# CN engine (separate shell / venv)
python -m venv ~/.venvs/ta-cn && source ~/.venvs/ta-cn/bin/activate
pip install -r ../tradingagents-cn/requirements.txt -r requirements.txt
export DASHSCOPE_API_KEY=... TUSHARE_TOKEN=...                # per engine docs
python research_bridge.py --engine ../tradingagents-cn --port 8802
```

Each engine reads its provider/model configuration from its own environment variables (see the engine READMEs); the bridge adds none of its own.

## API

```bash
curl -s localhost:8801/health
# {"status": "ok", "engine": "tradingagents"}

curl -s -X POST localhost:8801/research \
  -H 'Content-Type: application/json' \
  -d '{"ticker": "NVDA", "date": "2026-07-03"}'
```

Response shape:

```json
{
  "engine": "tradingagents",
  "ticker": "NVDA",
  "date": "2026-07-03",
  "decision": "BUY",
  "reasoning_trail": {
    "market_report": "…",
    "sentiment_report": "…",
    "news_report": "…",
    "fundamentals_report": "…",
    "investment_debate_state": { "...bull vs bear..." : "…" },
    "trader_investment_plan": "…",
    "risk_debate_state": { "…" : "…" },
    "final_trade_decision": "…"
  }
}
```

Notes:
- A run takes **minutes** (it is a full LLM debate pipeline) and runs are serialized per bridge instance.
- Engine failures return a structured `502` with the exception type and message.
- The bridge binds to `127.0.0.1` by default. Put real auth (or Vibe-Trading's `API_AUTH_KEY`-protected API) in front of it before exposing it beyond localhost.

## Calling it from Python / Vibe-Trading

[`client.py`](client.py) is stdlib-only, so it works inside any of the platform's virtualenvs:

```python
from client import deep_research
result = deep_research("NVDA")                    # US engine on :8801
result = deep_research("600519.SH", market="cn")  # CN engine on :8802
```

Endpoints are overridable with `RESEARCH_BRIDGE_US` / `RESEARCH_BRIDGE_CN`; the request timeout with `RESEARCH_BRIDGE_TIMEOUT_S` (default 1800s).

From a **Vibe-Trading chat session**, the shortest path is the CLI form (requires Vibe-Trading's shell tools opt-in, `VIBE_TRADING_ENABLE_SHELL_TOOLS=1`):

```
python trading/bridge/client.py NVDA --market us
```

which the agent can run itself and then feed the thesis into `run_research_autopilot` for backtest validation — the full pattern-A loop from the architecture doc.
