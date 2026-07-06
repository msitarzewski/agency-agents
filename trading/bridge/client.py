"""Client for the Research Bridge — usable from Vibe-Trading or any Python code.

Routes a research request to the right engine by market and returns the
bridge's JSON response. Uses only the stdlib so it can be dropped into any
of the platform's virtualenvs without dependency changes.

    from client import deep_research
    result = deep_research("NVDA")                      # US engine
    result = deep_research("600519.SH", market="cn")    # CN engine
    print(result["decision"])
"""

import json
import os
import urllib.request

DEFAULT_ENDPOINTS = {
    "us": os.environ.get("RESEARCH_BRIDGE_US", "http://127.0.0.1:8801"),
    "cn": os.environ.get("RESEARCH_BRIDGE_CN", "http://127.0.0.1:8802"),
}

# A full multi-agent debate pipeline takes minutes, not seconds.
DEFAULT_TIMEOUT_S = float(os.environ.get("RESEARCH_BRIDGE_TIMEOUT_S", "1800"))


def deep_research(ticker: str, date: str | None = None, market: str = "us",
                  timeout_s: float = DEFAULT_TIMEOUT_S) -> dict:
    """Run a multi-agent research pipeline and return decision + reasoning trail."""
    base = DEFAULT_ENDPOINTS.get(market)
    if base is None:
        raise ValueError(f"unknown market {market!r}; expected one of {sorted(DEFAULT_ENDPOINTS)}")

    payload = {"ticker": ticker}
    if date:
        payload["date"] = date

    req = urllib.request.Request(
        f"{base}/research",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        return json.load(resp)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Query the research bridge from the CLI")
    parser.add_argument("ticker")
    parser.add_argument("--date", default=None)
    parser.add_argument("--market", choices=sorted(DEFAULT_ENDPOINTS), default="us")
    args = parser.parse_args()
    print(json.dumps(deep_research(args.ticker, args.date, args.market), indent=2, ensure_ascii=False))
