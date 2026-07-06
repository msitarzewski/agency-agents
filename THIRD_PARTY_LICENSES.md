# Third-Party Licenses & Provenance

This repository unifies four codebases. The umbrella repository and the agent roster are MIT-licensed (see [LICENSE](LICENSE)). Vendored components under `trading/` retain their original licenses, which govern those directories.

| Directory | Upstream | License | Notes |
|---|---|---|---|
| `/` (agent roster, scripts) | [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents) | MIT | Root LICENSE applies |
| `trading/vibe-trading/` | [HKUDS/Vibe-Trading](https://github.com/HKUDS/Vibe-Trading) | MIT | `assets/`, `wiki/`, and translated READMEs omitted for size; code complete. See its bundled `LICENSE` and `NOTICE`. |
| `trading/tradingagents/` | [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) | Apache-2.0 | `assets/` (images) omitted; code complete. See its bundled `LICENSE`. |
| `trading/tradingagents-cn/` | [hsliuping/TradingAgents-CN](https://github.com/hsliuping/TradingAgents-CN) | Apache-2.0 (**partial vendor**) | See below. |

## TradingAgents-CN — what is and isn't included

TradingAgents-CN is a **mixed-license** project (see its `LICENSING.md`, vendored at `trading/tradingagents-cn/LICENSING.md`):

- **Included (Apache-2.0):** `tradingagents/` core library, `cli/`, `scripts/`, `examples/`, `tests/`, `config/`, root Python files and docs. These are free for commercial use, modification, and redistribution.
- **Deliberately excluded (proprietary):** the `app/` FastAPI backend and the Vue.js `frontend/`. Upstream prohibits their redistribution and commercial use without a commercial license (contact: hsliup@163.com per upstream `LICENSING.md`).

**Do not copy the upstream `app/` or `frontend/` directories into this repository.** If you need a web UI over the CN pipeline, use Vibe-Trading's MIT-licensed frontend/API layer instead, or build your own.

## Apache-2.0 obligations

For `trading/tradingagents/` and `trading/tradingagents-cn/`: retain the bundled `LICENSE` files and this attribution notice in redistributions, and state significant changes. Modifications made in this repo are tracked in git history.

## Trademark note

"TradingAgents", "Vibe-Trading", and upstream project names/logos belong to their respective owners. If you commercialize this platform, brand it under your own name.
