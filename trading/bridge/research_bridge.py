"""Research Bridge — expose a TradingAgents engine as a small HTTP service.

One bridge process serves exactly one engine (US `trading/tradingagents`
or CN `trading/tradingagents-cn`). The two engines pin conflicting
dependencies and both import as the `tradingagents` package, so they must
never share a virtualenv or a process. Run one instance per engine:

    # venv A (US engine deps + this file's requirements.txt)
    python research_bridge.py --engine ../tradingagents --port 8801

    # venv B (CN engine deps + this file's requirements.txt)
    python research_bridge.py --engine ../tradingagents-cn --port 8802

Then:

    curl -X POST localhost:8801/research \
         -H 'Content-Type: application/json' \
         -d '{"ticker": "NVDA", "date": "2026-07-03"}'

The response carries the pipeline's final decision plus the reasoning
trail (analyst reports, researcher debate, trader plan, risk debate) so
callers — Vibe-Trading, an MCP client, or a paying API customer — get an
auditable answer, not a bare signal.
"""

import argparse
import json
import logging
import os
import sys
import threading
from datetime import date as _date

logger = logging.getLogger("research_bridge")

# Keys of TradingAgentsGraph's final state that make up the reasoning
# trail. Both engines populate a subset of these; missing keys are simply
# omitted from the response.
TRAIL_KEYS = (
    "market_report",
    "sentiment_report",
    "news_report",
    "fundamentals_report",
    "investment_debate_state",
    "trader_investment_plan",
    "investment_plan",
    "risk_debate_state",
    "final_trade_decision",
)

_graph = None
_graph_lock = threading.Lock()
_engine_name = "unknown"


def _jsonable(value):
    """Best-effort conversion of graph state values to JSON-safe data."""
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return str(value)


def _load_engine(engine_dir: str):
    """Import TradingAgentsGraph from the given engine checkout."""
    engine_dir = os.path.abspath(engine_dir)
    if not os.path.isdir(os.path.join(engine_dir, "tradingagents")):
        raise SystemExit(
            f"--engine {engine_dir} does not contain a tradingagents/ package"
        )
    # The engine dir must win over any installed package of the same name.
    sys.path.insert(0, engine_dir)
    os.chdir(engine_dir)  # both engines resolve data/result dirs relative to cwd

    from tradingagents.default_config import DEFAULT_CONFIG
    from tradingagents.graph.trading_graph import TradingAgentsGraph

    config = DEFAULT_CONFIG.copy()
    # Providers/models come from each engine's own TRADINGAGENTS_* /
    # provider env vars; the bridge deliberately adds no config of its own.
    return TradingAgentsGraph(debug=False, config=config)


def run_research(ticker: str, trade_date: str) -> dict:
    """Run one pipeline pass; serialized because the graph is stateful."""
    with _graph_lock:
        result = _graph.propagate(ticker, trade_date)

    final_state, decision = (result if isinstance(result, tuple) else (result, None))
    trail = {}
    if isinstance(final_state, dict):
        trail = {k: _jsonable(final_state[k]) for k in TRAIL_KEYS if final_state.get(k)}
    return {
        "engine": _engine_name,
        "ticker": ticker,
        "date": trade_date,
        "decision": _jsonable(decision),
        "reasoning_trail": trail,
    }


def build_app():
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, Field

    class ResearchRequest(BaseModel):
        ticker: str = Field(..., min_length=1, max_length=20)
        date: str = Field(default_factory=lambda: _date.today().isoformat())

    app = FastAPI(title="Agency Platform Research Bridge", version="0.1.0")

    @app.get("/health")
    def health():
        return {"status": "ok", "engine": _engine_name}

    @app.post("/research")
    def research(req: ResearchRequest):
        try:
            return run_research(req.ticker.strip().upper(), req.date)
        except Exception as exc:  # surface engine failures as structured 502s
            logger.exception("research run failed for %s", req.ticker)
            raise HTTPException(status_code=502, detail=f"{type(exc).__name__}: {exc}")

    return app


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--engine", required=True,
                        help="path to the engine checkout (trading/tradingagents or trading/tradingagents-cn)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8801)
    parser.add_argument("--name", default=None,
                        help="engine label reported in responses (defaults to the engine dir name)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    global _graph, _engine_name
    _engine_name = args.name or os.path.basename(os.path.abspath(args.engine))
    _graph = _load_engine(args.engine)
    logger.info("engine %s loaded from %s", _engine_name, args.engine)

    import uvicorn
    uvicorn.run(build_app(), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
