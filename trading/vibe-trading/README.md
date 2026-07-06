<p align="center">
  <b>English</b> | <a href="README_zh.md">中文</a> | <a href="README_ja.md">日本語</a> | <a href="README_ko.md">한국어</a> | <a href="README_ar.md">العربية</a>
</p>

<p align="center">
  <img src="assets/icon.png" width="120" alt="Vibe-Trading Logo"/>
</p>

<h1 align="center">Vibe-Trading: Your Personal Trading Agent</h1>

<p align="center">
  <b>One Command to Empower Your Agent with Comprehensive Trading Capabilities</b>
</p>

<p align="center">
  <a href="https://trendshift.io/repositories/25527" target="_blank"><img src="https://trendshift.io/api/badge/repositories/25527" alt="HKUDS%2FVibe-Trading | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=flat" alt="FastAPI">
  <img src="https://img.shields.io/badge/Frontend-React%2019-61DAFB?style=flat&logo=react&logoColor=white" alt="React">
  <a href="https://pypi.org/project/vibe-trading-ai/"><img src="https://img.shields.io/pypi/v/vibe-trading-ai?style=flat&logo=pypi&logoColor=white" alt="PyPI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow?style=flat" alt="License"></a>
  <br>
  <a href="https://github.com/HKUDS/.github/blob/main/profile/README.md"><img src="https://img.shields.io/badge/Feishu-Group-E9DBFC?style=flat-square&logo=feishu&logoColor=white" alt="Feishu"></a>
  <a href="https://github.com/HKUDS/.github/blob/main/profile/README.md"><img src="https://img.shields.io/badge/WeChat-Group-C5EAB4?style=flat-square&logo=wechat&logoColor=white" alt="WeChat"></a>
  <a href="https://discord.gg/6TdQnT5xcF"><img src="https://img.shields.io/badge/Discord-Join-7289DA?style=flat-square&logo=discord&logoColor=white" alt="Discord"></a>
</p>

<p align="center">
  <a href="https://vibetrading.wiki/">Website</a> &nbsp;&middot;&nbsp;
  <a href="https://vibetrading.wiki/docs/">Docs</a> &nbsp;&middot;&nbsp;
  <a href="#-news">News</a> &nbsp;&middot;&nbsp;
  <a href="#-key-features">Features</a> &nbsp;&middot;&nbsp;
  <a href="#-shadow-account">Shadow Account</a> &nbsp;&middot;&nbsp;
  <a href="#-demo">Demo</a> &nbsp;&middot;&nbsp;
  <a href="#-quick-start">Quick Start</a> &nbsp;&middot;&nbsp;
  <a href="#-examples">Examples</a> &nbsp;&middot;&nbsp;
  <a href="#-api-server">API / MCP</a> &nbsp;&middot;&nbsp;
  <a href="#-roadmap">Roadmap</a> &nbsp;&middot;&nbsp;
  <a href="#-contributing">Contributing</a>
</p>

<p align="center">
  <a href="#-quick-start"><img src="assets/pip-install.svg" height="45" alt="pip install vibe-trading-ai"></a>
</p>

---

## 📰 News

- **2026-06-27** 🧯 **Content-filter resilience + Shadow Account feature contract cleanup**: event-driven and swarm runs now skip individual LLM content-moderation hits, warn in run cards when filter rates are high, and recognize Gemini safety finish reasons instead of aborting an entire analysis ([#308](https://github.com/HKUDS/Vibe-Trading/pull/308), closes [#307](https://github.com/HKUDS/Vibe-Trading/issues/307), thanks @shadowinlife). Shadow Account extraction/codegen now share one `PRICE_FEATURES` contract and keep four-decimal return bounds, preventing rule/codegen drift and precision loss on `prior_5d_return` ([#316](https://github.com/HKUDS/Vibe-Trading/pull/316), thanks @Robin1987China).
- **2026-06-26** 🎯 **Shadow Account conditional entry + tushare ETF/index/HK routing**: extracted Shadow Account rules now carry RSI / prior-return bounds, so the generated SignalEngine enters on real conditions (RSI in range, prior-return in range) instead of blindly replaying the holding cadence ([#314](https://github.com/HKUDS/Vibe-Trading/pull/314), follows [#302](https://github.com/HKUDS/Vibe-Trading/pull/302), thanks @Robin1987China). The tushare loader also routes ETF/LOF → `fund_daily()`, indices → `index_daily()`, and HK equities → `hk_daily()` instead of always calling `daily()` (which silently returns empty for non-stocks), with per-symbol empty-result + partial-fetch warnings ([#315](https://github.com/HKUDS/Vibe-Trading/pull/315), closes [#310](https://github.com/HKUDS/Vibe-Trading/issues/310), thanks @shadowinlife).
- **2026-06-25** 🧪 **Strict validation JSON + calmer agent context**: standalone backtest validation now normalizes nested `NaN` / `Infinity` values before writing `artifacts/validation.json` or CLI stdout, so strict JSON parsers no longer choke on validation payloads ([#306](https://github.com/HKUDS/Vibe-Trading/pull/306), thanks @gyx09212214-prog). The agent prompt also derives the current data-source count from the loader registry, and `_microcompact()` now waits for real token pressure instead of clearing older tool results during short runs ([#296](https://github.com/HKUDS/Vibe-Trading/pull/296), closes [#282](https://github.com/HKUDS/Vibe-Trading/issues/282), thanks @MarkfuGod).
<details>
<summary>Earlier news</summary>

- **2026-06-24** 🎯 **Shadow Account price context + reactive Chinese UI + LAN auth fix**: Shadow Account rule extraction now sees PIT-safe entry context — `entry_rsi14` and `prior_5d_return` fetched through the loader registry as of `buy_dt`, with graceful offline/no-data degradation ([#302](https://github.com/HKUDS/Vibe-Trading/pull/302), follows [#295](https://github.com/HKUDS/Vibe-Trading/issues/295), thanks @Robin1987China). The main Web UI panels now use reactive English / zh-CN translations across charts, chat, Alpha Library, Correlation, and Run Detail ([#301](https://github.com/HKUDS/Vibe-Trading/pull/301), thanks @skloxo). Remote same-origin Web UI deployments with `API_AUTH_KEY` can post and upload again after the CSRF hardening, while mismatched cross-site origins remain blocked ([#304](https://github.com/HKUDS/Vibe-Trading/pull/304), thanks @Hinotoi-agent).
- **2026-06-23** 🛡️ **Local API CSRF hardening**: a malicious web page can no longer drive unsafe cross-site requests (POST/PUT/DELETE) against the loopback API — CORS blocks reading the response but not the side effect, so loopback dev-mode trust now applies the existing cross-site guard to unsafe methods *before* honoring it. Safe methods and local CLI / non-browser uploads are unaffected ([#293](https://github.com/HKUDS/Vibe-Trading/pull/293), thanks @Hinotoi-agent).
- **2026-06-22** 🔧 **Live-authorize OAuth fix + Alpha Zoo headline fix**: `connector authorize` now holds the OAuth handshake open through a multi-minute broker sign-in (tunable via `VIBE_LIVE_AUTHORIZE_TIMEOUT_SECONDS`) and no longer spawns a competing callback server on retry, so the token actually persists ([#281](https://github.com/HKUDS/Vibe-Trading/pull/281), closes [#259](https://github.com/HKUDS/Vibe-Trading/issues/259), thanks @Robin1987China). The Alpha Zoo page no longer prints its alpha count twice ([#287](https://github.com/HKUDS/Vibe-Trading/pull/287), closes [#286](https://github.com/HKUDS/Vibe-Trading/issues/286), thanks @digger-yu). Scheduled research also picked up end-to-end usage docs ([#288](https://github.com/HKUDS/Vibe-Trading/pull/288)).
- **2026-06-21** ⏰ **Scheduled-research executor + Reports library + post-backtest attribution**: scheduled research now runs **end to end** — a default-off background executor (`VIBE_TRADING_ENABLE_SCHEDULER`) fires due interval/cron jobs through the session runtime ([#278](https://github.com/HKUDS/Vibe-Trading/pull/278), thanks @mvanhorn, closing [#254](https://github.com/HKUDS/Vibe-Trading/issues/254)). A new **`/reports` Run Library** page lists, searches, and filters report-worthy runs with links into Run Detail + Compare ([#224](https://github.com/HKUDS/Vibe-Trading/pull/224), thanks @LemonCANDY42). And after every backtest the agent now runs **layered attribution** — trade-level winners/losers, beta regression, market-regime analysis, and a Monte Carlo permutation test, gated by data availability and routing ([#280](https://github.com/HKUDS/Vibe-Trading/pull/280), thanks @shadowinlife).
- **2026-06-20** 🔬 **Research Autopilot loop closes (Phase 3) + loader OHLC integrity guard + 4 academic alphas**: **Research Autopilot** now runs **hypothesis → signal-engine → backtest** end to end — `scaffold_signal_engine` writes a contract-correct engine and `link_autopilot_backtest` feeds run metrics back to the hypothesis (**68 tools**) ([#267](https://github.com/HKUDS/Vibe-Trading/pull/267)). A structural **OHLC sanity check** drops dirty bars (`high < low`, non-positive prices, bad bracketing) centrally at the loader boundary, guarding every data source ([#274](https://github.com/HKUDS/Vibe-Trading/pull/274), thanks @Shizoqua). And the **academic alpha family grows 6 → 10** — Jegadeesh reversal, George-Hwang 52-week-high, Amihud illiquidity, Harvey-Siddique skew (**456 factors**) ([#277](https://github.com/HKUDS/Vibe-Trading/pull/277), thanks @Robin1987China).
- **2026-06-19** 🚀 **v0.1.10 — Global data layer**: market-data sources grow 10 → 18 (free **Eastmoney / Sina / Stooq / Yahoo** + key-gated **Finnhub / Alpha Vantage / Tiingo / FMP**, ban-risk fallback) plus **18 read-only data tools** (fund flow, dragon-tiger, northbound, margin, block trades, SEC EDGAR + XBRL, financials, options chains, full-market screening…) across A-share / US / HK, all over MCP. Also bundles everything since 0.1.9 — 10 broker connectors, `alpha compare`, the provider-reliability overhaul, and the opt-in data cache. `pip install -U vibe-trading-ai`
- **2026-06-18** 🔬 **Research Autopilot Phase 1 + a local Data Bridge loader, + a Discord security notice**: new `run_research_autopilot` + `generate_backtest_config` wire **Hypothesis → Research Goal → backtest** end to end (now **50 tools**), and a **`local`** loader reads OHLCV straight from your own **CSV / Parquet / DuckDB** files ([#260](https://github.com/HKUDS/Vibe-Trading/pull/260), [#252](https://github.com/HKUDS/Vibe-Trading/pull/252), thanks @Robin1987China), alongside DeepSeek `DSML` tool-call parsing and an identifier-containment hardening wave. ⚠️ **Security:** the old community Discord invite now points to a server we don't control running a fake Collab.Land wallet-"verification" phishing scam — removed everywhere; the **only** official Discord is the HKUDS server ([discord.gg/6TdQnT5xcF](https://discord.gg/6TdQnT5xcF)), and we'll never ask you to connect a wallet.
- **2026-06-17** 🧩 **Install compatibility + Opus/Kimi provider fixes**: Baseline `pip install vibe-trading-ai` no longer pulls the optional `pyharmonics` / `ta` dependency chain; harmonic detection now lives behind `vibe-trading-ai[harmonic]` while the bundled detector remains available ([#250](https://github.com/HKUDS/Vibe-Trading/pull/250), closes [#249](https://github.com/HKUDS/Vibe-Trading/issues/249)). The agent loop also avoids assistant-prefill handoff messages rejected by Opus 4.8+, and Kimi/Moonshot can override the client `User-Agent` with `MOONSHOT_USER_AGENT` ([#248](https://github.com/HKUDS/Vibe-Trading/pull/248), closes [#246](https://github.com/HKUDS/Vibe-Trading/issues/246) and [#204](https://github.com/HKUDS/Vibe-Trading/issues/204)); follow-up tests now directly cover background-result and auto-compact handoff paths ([#251](https://github.com/HKUDS/Vibe-Trading/pull/251)).
- **2026-06-16** 🛡️ **Security/API hardening + GLM/Zhipu alias**: Settings writes require auth when configured ([#245](https://github.com/HKUDS/Vibe-Trading/pull/245)); API shell-capable tools require explicit `VIBE_TRADING_ENABLE_SHELL_TOOLS=1` opt-in ([#243](https://github.com/HKUDS/Vibe-Trading/pull/243)); local shutdown requires auth when an API key is configured ([#241](https://github.com/HKUDS/Vibe-Trading/pull/241)); and untrusted loopback-looking hosts are rejected instead of treated as local ([#242](https://github.com/HKUDS/Vibe-Trading/pull/242)). Runtime edges also got cleaned up: Web chat syncs completed attempts ([#236](https://github.com/HKUDS/Vibe-Trading/pull/236)), run cards emit strict JSON for non-finite metrics ([#238](https://github.com/HKUDS/Vibe-Trading/pull/238)), malformed `RSSHUB_TIMEOUT_S` / `RSSHUB_FETCH_BUDGET_S` falls back safely ([#240](https://github.com/HKUDS/Vibe-Trading/pull/240)), and ddgs retry fallback is regression-covered ([#239](https://github.com/HKUDS/Vibe-Trading/pull/239)). GLM/Zhipu is now a first-class provider alias with model-name inference ([#247](https://github.com/HKUDS/Vibe-Trading/pull/247), closes [#237](https://github.com/HKUDS/Vibe-Trading/issues/237)).

- **2026-06-15** 🧭 **Web-search resilience + Web UI run-continuity fixes**: `web_search` no longer fails when a single engine is rate-limited — it now queries several free, no-key engines in order (DuckDuckGo, Google, Bing, Brave, Mojeek, Yahoo) with retry/backoff, treats "no results" as an empty answer rather than an error, and returns an actionable message instead of a bare ❌ when every engine is throttled (override the engine list with `VIBE_TRADING_SEARCH_BACKENDS`) ([#232](https://github.com/HKUDS/Vibe-Trading/pull/232), closes [#231](https://github.com/HKUDS/Vibe-Trading/issues/231), thanks @Ethan-sun01). In the Web UI, switching pages during a run no longer freezes it — the chat re-subscribes to the live stream and replays missed progress on return ([#234](https://github.com/HKUDS/Vibe-Trading/pull/234)) — and the Stop button now takes effect mid-stream and between tools instead of only at iteration boundaries ([#235](https://github.com/HKUDS/Vibe-Trading/pull/235)), closing both halves of [#229](https://github.com/HKUDS/Vibe-Trading/issues/229) (thanks @kalkinj). The baostock loader also accepts native `sh.601398` / `sz.000001` codes alongside tushare-style `601398.SH` ([#230](https://github.com/HKUDS/Vibe-Trading/pull/230), thanks @bhlt).

- **2026-06-14** 📊 **Per-run token usage + progressive Run Detail charts**: Every agent run now persists provider-reported token usage as a run-scoped `llm_usage.json` — provider/model, aggregate totals, and per-iteration counts — surfaced additively on `/runs/{id}`, so a finished run's token cost stays auditable after the live stream is gone (provider-reported only; no prompt/content capture, no price estimation) ([#223](https://github.com/HKUDS/Vibe-Trading/pull/223), thanks @LemonCANDY42). The Run Detail page no longer loads every symbol's candlesticks up front: the default `/runs/{id}` response is unchanged, but the UI now renders the run summary first and loads each symbol's chart on demand through opt-in `?chart_payload=summary` / `?chart_symbol=` modes, with per-symbol loading state and a load-all-with-progress control ([#225](https://github.com/HKUDS/Vibe-Trading/pull/225), thanks @LemonCANDY42). Two loader fixes close the cycle: yfinance's exclusive `end` boundary no longer drops the final requested trading day — the download now passes `end + 1 day` while cache keys keep the original range ([#226](https://github.com/HKUDS/Vibe-Trading/pull/226), thanks @gyx09212214-prog) — and a malformed `CCXT_TIMEOUT_MS` / `OKX_TIMEOUT_S` value now warns and falls back to its default instead of raising at import and blocking startup ([#227](https://github.com/HKUDS/Vibe-Trading/pull/227), thanks @gyx09212214-prog).
- **2026-06-13** ↩️ **Resume a past session by ID from the CLI**: The interactive CLI now prints the session-id on exit, with a copy-paste `vibe-trading resume <session-id>` hint — so locating the trace for a finished run no longer means guessing which folder under `agent/sessions/` is newest by timestamp. The new `vibe-trading resume <session-id>` subcommand reopens that exact session and replays its recent turns into the loop; an unknown id fails fast instead of silently starting a blank session ([#218](https://github.com/HKUDS/Vibe-Trading/pull/218), thanks @zwrong).
- **2026-06-12** 🩺 **Provider reliability overhaul — DeepSeek hangs, Kimi access, streaming liveness**: A cluster of provider reports — DeepSeek runs stuck on "Agent is working…" ([#208](https://github.com/HKUDS/Vibe-Trading/issues/208), thanks @XYWOX), `reached max iterations` masking empty model responses ([#203](https://github.com/HKUDS/Vibe-Trading/issues/203), thanks @mojianliang), the UI never recovering after a stall ([#195](https://github.com/HKUDS/Vibe-Trading/issues/195), thanks @mafia23), and Kimi rejecting the client ([#204](https://github.com/HKUDS/Vibe-Trading/issues/204), thanks @liao497) — shared one root: every OpenAI-compatible provider ran through a single shim that applied DeepSeek/Kimi/Gemini quirks globally and silently swallowed stream failures. Provider-specific behavior now lives in an explicit **capability layer** — reasoning capture/replay, Gemini thought signatures, the Kimi `User-Agent`, OpenRouter's reasoning body are each gated to their own provider instead of cross-contaminating. Reasoning-only streams show a live **"Reasoning…"** indicator instead of dead air; a stream failure raises a contextual `provider_stream_error` with one automatic retry for transient resets (deterministic 4xx fail fast) instead of silently falling back to a slow non-streaming call; an empty model response is reported as `empty_model_response` instead of "max iterations"; SSE heartbeats no longer break reconnect replay; and a stuck read-only tool times out instead of hiding behind heartbeats forever. A new **`vibe-trading provider doctor`** prints a redacted provider/model/package/proxy snapshot for one-command triage of environment-side hangs. DeepSeek users can opt into the official native adapter with `pip install "vibe-trading-ai[deepseek]"`, and kimi-k2.x's `temperature=1` requirement is applied automatically — the Kimi path is verified end-to-end against the live API (tool calls + strict multi-turn reasoning replay on `kimi-k2.6`).

- **2026-06-11** 🐝 **Swarm workers now pull market data through the loader layer**: An investment-committee run on NVDA exposed a chain of gaps — workers wrote ad-hoc yfinance scripts, trusted a malformed latest bar (volume present, OHLC empty), leaked `NaN` into non-strict JSON, and a context-free continuation prompt re-routed to the wrong preset ([#198](https://github.com/HKUDS/Vibe-Trading/issues/198), thanks @BillDin for an exceptional diagnosis plus both fixes). Swarm workers now get a local `get_market_data` tool backed by the same normalized loader registry as MCP — strict JSON, non-finite floats serialize as `null` — wired into **every market-data preset** (21 workers across 13 presets) with a prompt policy that steers OHLCV work tool-first ([#199](https://github.com/HKUDS/Vibe-Trading/pull/199)); `run_swarm` takes an explicit `preset_name` and refuses ambiguous continuation fragments instead of silently falling back to `equity_research_team` ([#200](https://github.com/HKUDS/Vibe-Trading/pull/200)). Grounding got smarter too: a bare US ticker like `NVDA` in a swarm prompt is promoted to `NVDA.US` (stopword-guarded), so workers start from authoritative pre-fetched prices. The tool joins the main agent registry as well — **48 tools** now. Also: **your Docker data now survives updates** — persistent memory, the session search index, user-created skills, shadow accounts and broker config live in named volumes, so `docker compose up --build` no longer wipes them ([#197](https://github.com/HKUDS/Vibe-Trading/issues/197), thanks @FlyerJ).
- **2026-06-10** 🐳 **Docker reaches a host-side Ollama out of the box**: Inside the container `localhost` is the container itself, so the shipped `OLLAMA_BASE_URL=http://localhost:11434` failed the LLM preflight for every Dockerized Ollama setup. `docker-compose.yml` now defaults to `http://host.docker.internal:11434` (export `OLLAMA_BASE_URL` to point elsewhere) and adds the `host-gateway` `extra_hosts` mapping so the same file works on Linux as well as Docker Desktop ([#196](https://github.com/HKUDS/Vibe-Trading/pull/196), thanks @ShahNewazKhan).
- **2026-06-09** 🔑 **Clearer error when the Web UI is opened from another machine**: Reaching the chat from a non-loopback client (another machine, a VM host, a phone on your LAN) without `API_AUTH_KEY` set returned `403` on every sensitive endpoint — sending a message, listing sessions, live status — but the chat only showed a generic "Failed to send message, please retry." The send path now surfaces the real reason — *"Remote API access requires an API key. Add it in Settings, or run the backend on localhost for local-only use."* — and the README's web-UI setup spells out the localhost-vs-LAN rule plus the three fixes (browse via `localhost` on the same machine; set `API_AUTH_KEY` and enter it once in Settings; or `VIBE_TRADING_TRUST_DOCKER_LOOPBACK=1` for Docker Desktop's host gateway) ([#191](https://github.com/HKUDS/Vibe-Trading/issues/191), thanks @mafia23).
- **2026-06-08** 🔧 **Gemini 3.x multi-turn tool-calling fix**: This completes the Gemini 3.x thinking-model fix. The 6/05 round-trip ([#176](https://github.com/HKUDS/Vibe-Trading/pull/176)) only covered in-memory history, but the real agent loop replays history as OpenAI-format dicts where LangChain dropped the per-tool-call `thought_signature` before the request was built — so multi-turn tool calling still 400'd with `missing thought_signature`. It is now re-attached at the single `_convert_input` chokepoint both `invoke` and `stream` pass through (parallel calls, where only the first of N is signed, included) ([#184](https://github.com/HKUDS/Vibe-Trading/pull/184), thanks @ngoanpv).
- **2026-06-07** 🐝 **Live swarm status in the chat timeline**: When the agent launches a multi-agent swarm (investment committee, quant desk, risk committee, …), the chat now renders an inline **status card** that streams each worker's state — waiting / running / done / failed / blocked / retrying — in real time, the same per-agent visibility the standalone swarm dashboard already had. Runtime events are bridged into the session SSE stream without changing the existing `/swarm/runs` API, and a finished card rehydrates from the final `run_swarm` result on reconnect or history replay ([#188](https://github.com/HKUDS/Vibe-Trading/pull/188), thanks @BillDin). Preset routing also got sharper: an explicitly named preset (e.g. `investment_committee`, with or without underscores) now wins over keyword scoring, and the bare `IV` derivatives keyword no longer false-matches inside ordinary words like "g**iv**en" ([#189](https://github.com/HKUDS/Vibe-Trading/pull/189), thanks @BillDin).
- **2026-06-06** ⚖️ **Alpha compare — head-to-head across CLI, Web UI, REST & agent**: A new `alpha compare` benches a hand-picked shortlist of Alpha Zoo alphas against each other on a universe and period, then ranks them by IC mean/std, IR, IC-positive ratio or sample count — each with its gap to the leader. Unlike a full-zoo bench it evaluates **only the alphas you name** (a new `run_bench(only=…)` subset filter), so comparing three alphas no longer scores all 191 in their zoo. One shared core powers every surface: `vibe-trading alpha compare <id1> <id2> … --sort ir` (CLI), a **Compare view** in the Alpha Zoo Web UI (tick alphas in the catalogue → one-click compare with a streamed ranking table), `POST /alpha/compare` + SSE (REST), and a read-only `alpha_compare` agent tool (**47 tools** now).
- **2026-06-05** 🇮🇳 **Dhan + Shoonya connectors (India) — 10 brokers total**: The connector-first trading layer adds **Dhan** and **Shoonya** for the Indian market (NSE/BSE equities + F&O), bringing the roster to ten brokers. Both are **paper + read-only** — like Longbridge, their APIs expose no runtime paper/live discriminator, so their `place_order` / `cancel_order` hard-refuse any non-paper config at the first line (the rule: a broker with no structural paper/live guard is capped at paper + read-only) ([#181](https://github.com/HKUDS/Vibe-Trading/pull/181), closes [#174](https://github.com/HKUDS/Vibe-Trading/issues/174)). This cycle also fixes **Gemini 2.5 / 3.x thinking models**: their per-tool-call `thoughtSignature` now round-trips through the OpenAI-compatible path, so multi-turn function calling no longer fails with `INVALID_ARGUMENT` ([#176](https://github.com/HKUDS/Vibe-Trading/pull/176), closes [#170](https://github.com/HKUDS/Vibe-Trading/issues/170), thanks @mvanhorn & @jliu6789). Chinese docstrings landed on all **452 Alpha Zoo factors** ([#180](https://github.com/HKUDS/Vibe-Trading/pull/180), thanks @LeeCQiang), and a **frontend test suite (197 vitest tests)** plus backend auth / path-traversal / CORS security tests joined CI ([#175](https://github.com/HKUDS/Vibe-Trading/pull/175), thanks @sambazhu).
- **2026-06-04** 🗃️ **Opt-in local data cache for all 7 data sources**: A new `VIBE_TRADING_DATA_CACHE` switch lets every backtest loader — tushare, okx, ccxt, akshare, mootdx, yfinance, futu — cache settled historical bars under `~/.vibe-trading/cache` (user home, never the repo), so repeated and long-horizon / cross-market backtests skip the network and avoid provider rate limits. Off by default. Batch and connection loaders (yfinance, futu) skip the bulk download / FutuOpenD connection entirely on a full cache hit, a staleness guard never caches a range ending today (its last bar is still forming), and cached frames round-trip byte-identical to freshly fetched ones ([#177](https://github.com/HKUDS/Vibe-Trading/pull/177), thanks @mvanhorn). A new contributor guide for AI / automation-assisted PRs also landed, mapping safe local checks and high-risk broker/MCP/credential surfaces ([#173](https://github.com/HKUDS/Vibe-Trading/pull/173)).
- **2026-06-03** 🧹 **Community triage + trace correlation**: Tool-call trace entries now carry the originating `call_id`, so a `tool_result` can be matched back to its `tool_call` when replaying a run trace — arg previews stay truncated to keep trace files small ([#168](https://github.com/HKUDS/Vibe-Trading/pull/168), thanks @zwrong). Source comments no longer point at an internal-only docs path that external contributors couldn't find ([#166](https://github.com/HKUDS/Vibe-Trading/issues/166), thanks @jaleelpersonal). Also clarified that the `langchain-community` resolver warning on install is a harmless leftover-package notice, not a failure ([#167](https://github.com/HKUDS/Vibe-Trading/issues/167)), and scoped Gemini 2.5/3.0 `thoughtSignature` round-tripping for function calls as a `help wanted` task with a full fix plan ([#170](https://github.com/HKUDS/Vibe-Trading/issues/170), thanks @jliu6789).
- **2026-06-02** 🔌 **Six new broker connectors (Tiger / Longbridge / Alpaca / OKX / Binance / Futu)**: The connector-first trading layer gains a direct-SDK transport alongside IBKR (local) and Robinhood (MCP). Each connector exposes read-only account / positions / orders / quote / history **plus paper-account order placement** — test your strategies across these broker paper accounts. Five of them (Tiger, Alpaca, OKX, Binance, Futu) also support **bounded, mandate-gated order placement** behind the same safety model as Robinhood: a user-committed mandate (symbol universe / order size / exposure / leverage / daily cap), a filesystem kill switch, a fail-closed pre-trade gate, and a full audit ledger. **Longbridge is paper + read-only only** (its API exposes no runtime paper/live discriminator). Every paper/live distinction is a structural per-broker guard — account-id format, host separation, demo flag, or trade environment. New `trading_place_order` / `trading_cancel_order` tools; HK and A-share asset classes added to the mandate universe. Experimental / use at your own risk.
- **2026-06-01** 🚀 **v0.1.9 released** (`pip install -U vibe-trading-ai`): Rolls up everything since 0.1.8. Connector-first broker profiles (IBKR local read-only TWS / IB Gateway + Robinhood Agentic Trading behind OAuth, a committed mandate, order guard, audit ledger, and instant halt). Research Goal runtime across CLI / REST / MCP / Web. A swarm pass — live reconcile + MCP keepalive, operator-configured worker MCP tools, a strict alpha-bench random control, and a new `retry_run` to relaunch failed/stale runs (**36 MCP tools** now). The `agent/cli/` package refactor with a refreshed terminal UI, the `mootdx` no-token A-share loader, and a robustness pass across backtest / agent loop / sessions. `--version` now always matches the installed package, fixing the 0.1.8 drift ([#156](https://github.com/HKUDS/Vibe-Trading/issues/156)).
- **2026-05-31** 🔌 **Connector-first broker architecture (IBKR + Robinhood)**: Trading access now starts from a selectable connector profile instead of separate broker/live entry points. `vibe-trading connector list/use/check/account/positions/orders/quote/history` and the MCP `trading_*` tools share the same selected profile, where paper/live is an attribute of the connector. IBKR can be used immediately through a local read-only TWS / IB Gateway profile, while the official IBKR remote MCP path is seeded as an OAuth `mcp.read` probe until stable read tool names are available. Robinhood Agentic Trading remains the bounded live MCP connector behind OAuth, a committed mandate, order guard, audit ledger, and instant halt.
- **2026-05-30** 🧰 **Robustness pass — backtest, agent loop, sessions**: LLM-generated signal engines now pass pre-flight interface validation before instantiation, catching circular self-imports, a missing `generate()`, non-defaulted `__init__` args, and wrong return types with actionable JSON errors instead of raw tracebacks ([#149](https://github.com/HKUDS/Vibe-Trading/pull/149)); a follow-up routes source-level AST validation errors through the same clean JSON envelope. The agent loop no longer burns all 50 iterations into a `failed` status with no output — it mirrors the swarm worker's wrap-up nudge at 80% of the iteration budget and drops tool definitions on the last iteration to force a final text answer ([#148](https://github.com/HKUDS/Vibe-Trading/pull/148)), guarded to fire only mid-run so it never displaces research-goal context. Session message writes now `flush + fsync` each append so expensive AI responses survive a mid-write crash, and the read path skips corrupted JSONL lines (logging the first 200 chars for recovery) instead of 500-ing the whole `/messages` endpoint ([#147](https://github.com/HKUDS/Vibe-Trading/pull/147)). The Web composer also fixes IME Enter handling so a composition-confirming Enter no longer submits mid-word ([#146](https://github.com/HKUDS/Vibe-Trading/pull/146)).
- **2026-05-29** 🔐 **Robinhood Agentic Trading support (opt-in, bounded autonomy)**: Adds support for Robinhood Agentic Trading (remote MCP, OAuth). Off and read-only by default; the agent acts only inside a user-committed mandate (symbols / order size / exposure / leverage / daily cap), with a filesystem-level instant kill switch, preemptive flatten, mandate auto-expiry, a full audit ledger, and a persistent autonomous runner. No custody, no venue — the broker holds funds and executes; we only relay intent. Experimental / use at your own risk.
- **2026-05-28** 🧪 **Swarm safety + strict alpha gate + worker MCP**: Swarm DAG blocks downstream tasks when upstream fails ([#145](https://github.com/HKUDS/Vibe-Trading/pull/145)). New `run_bench_strict()` adds a same-universe random control + OOS split to catch factors that just track market beta ([#143](https://github.com/HKUDS/Vibe-Trading/pull/143), thanks @Soli22de). Swarm workers can call operator-configured external MCP servers, with trust boundary pinned ([#142](https://github.com/HKUDS/Vibe-Trading/pull/142), thanks @shadowinlife).
- **2026-05-27** 📊 **mootdx A-share data source + output polish**: New `mootdx` loader speaks the native 通达信 TCP protocol for A-share OHLCV (no auth, no IP rate-limit, daily + intraday with 25-page walk-back pagination), slotting between tushare and akshare in the fallback chain ([#107](https://github.com/HKUDS/Vibe-Trading/issues/107)). CCXT loader now reads `HTTP_PROXY/HTTPS_PROXY/ALL_PROXY` so Binance/OKX public data works from restricted networks ([#126](https://github.com/HKUDS/Vibe-Trading/pull/126), thanks @ruok808). Final-answer rendering also dropped the ugly full-width `---` horizontal separators on CLI and Web: the system prompt now nudges the agent toward markdown tables and `##` headings, the CLI renderer strips standalone HRs as defense-in-depth, and the chat bubble hides any `<hr>` that slips through ([#139](https://github.com/HKUDS/Vibe-Trading/issues/139), thanks @sdwxm188).
- **2026-05-26** ✅ **Research Goal lifecycle closure**: Goal mode now behaves like a real task runner: Web UI goal creation creates or binds the session and immediately sends the kickoff turn; active goals can be continued, edited, cancelled, and completed across Web/API/CLI/MCP; and the agent advances from the current goal snapshot (criteria, evidence, claims, open items) instead of only the original prompt. Covered-but-still-active goals now enter an audit/status update instead of stopping silently, with regression coverage across backend, CLI, MCP, and frontend events.

- **2026-05-25** 🧼 **Cleaner chat UI + composer workflow**: The Web UI keeps chat focused on the next action: upload, swarm, and research-goal modes now live behind the composer `+` menu instead of floating panels. Active context appears above the input as compact chips, and goal details expand inline only when needed. The UI also drops the old custom i18n layer in favor of direct English copy, gates Full Report cards to report-worthy runs, and hardens local dev startup/status reporting for reliable browser smoke tests.
- **2026-05-24** 🎯 **Research Goal runtime**: Added a session-scoped Research Goal layer across backend, CLI, API/MCP, SSE, and Web UI. Goals persist claims, acceptance criteria, evidence rows, budgets, and completion policy; agent tools can create goals and attach evidence; `/goal` gives the CLI a direct entry point; REST/MCP expose goal snapshots and evidence writes; SSE keeps chat clients fresh. Follow-up audit fixes locked down verified evidence, blocked live-trading risk tiers through agent tools, wired CLI-created goals into later turns, cleaned goal ledgers on session deletion, enabled replay-all, and fixed cross-session frontend races.
- **2026-05-23** 🖥️ **Interactive CLI refresh**: The terminal front door now opens with a larger Vibe-Trading banner, a cleaner prompt divider, prior-turn recap, post-run timing, and a Claude Code-style activity rail for live agent work. Tool calls, web/data fetches, shell-style actions, Markdown answers, and pipe tables render in a more readable transcript, while piped or non-TTY runs keep plain-text output for automation. Generated CLI screenshots are now treated as local artifacts instead of committed docs files, keeping the repository lighter.
- **2026-05-22** 🧭 **Swarm recovery + MCP keepalive**: Swarm status now reconciles from live task files on every read, so API/MCP/SSE/list views recover crashed or stale runs instead of showing permanent `running` snapshots. `run_swarm` sends MCP progress heartbeats while it polls, with a fixed first frame of `swarm_started run_id=<id>` for clients that reconnect after transport drops; workers now heartbeat through LLM streaming, grounding fetches, and tool execution. The stale-run reaper uses per-run thresholds and derives terminal status from task states, `SwarmTool` no longer cancels a still-running team just because its wait budget elapsed, and MCP clients can call `reap_stale_runs()` for explicit cleanup. Today's DX pass also refreshed provider default models and aligned CI syntax checks with the new `agent/cli/` package. 22 new regressions cover hydration, terminal recovery, stale reaping, keepalive cadence, env parsing, and heartbeat wiring; the full swarm/MCP suite is at 169 passed, 4 skipped.
- **2026-05-21** 🧱 **CLI package refactor**: `agent/cli.py` (3216 LOC) split into the `agent/cli/` package — interactive front door, slash router, Rich components, plus a `_legacy.py` shim that preserves every subcommand and re-exports every public symbol so `cli.cmd_*` / `cli._INIT_ENV_PATH` / `cli.Confirm` keep working. New FastAPI middleware serves the SPA shell when a browser opens `/runs/{id}` or `/correlation` directly; same narrowing landed in the Vite dev proxy. Version unified via `cli/_version.py` (no more drift between `--version` and the banner), `python -m cli` restored via `__main__.py`, and the chat-gate narrowed so `chat --help` / `chat extra` reach legacy argparse instead of being swallowed by the REPL.
- **2026-05-20** 🔬 **Hypothesis Registry CLI**: Closes the CLI side of the Hypothesis Registry shipped backend-only on 2026-05-16. `vibe-trading hypothesis list` prints a Rich table or JSON (`--status` filter, `--limit`); `show <id>` renders a detail panel including linked run cards; `invalidate <id> --note "..."` flips status to `rejected` while preserving prior invalidation notes when `--note` is omitted. Honors the existing `VIBE_TRADING_HYPOTHESES_PATH` env override and adds a per-invocation `--path`. 22 new tests cover wiring, JSON output, status filter, limit, missing-id errors, and note persistence.
- **2026-05-19** ✨ **Live tool feedback + graceful cancel**: Long-running tools (backtests, large PDFs, swarm workers) no longer look frozen. Each tool call now emits a 3-second heartbeat plus structured per-stage progress — `run_backtest` shows phase markers (`validate` / `simulate` / `finalize`), `read_document` ticks per page on PDF or per sheet on Excel, `read_url` marks `fetch` / `parse`. The CLI Rich Live dashboard renders a Unicode spinner, ASCII progress bar, ETA, and stacks up to 3 parallel tools keyed by name; the frontend chat ships a new `ToolProgressIndicator` with rAF-coalesced renders, ARIA `role="status"` + hidden native `<progress>` for screen readers, and a determinate `ProgressRing` SVG when total is known. First `Ctrl+C` during a CLI run now calls `agent.cancel()` for graceful exit (current step finishes, trace closes cleanly); a second within 2s force-quits. Reusable primitives extracted along the way: `ProgressBar.tsx` and `lib/tools.ts` (shared tool-name i18n).
- **2026-05-18** 🧹 **Cleanup pass + three latent bug fixes**: `CompositeEngine` no longer misroutes bare Chinese-futures codes like `RB2410` to `GlobalFuturesEngine` — `_is_china_futures` moved into a shared `_market_hooks` module with a case-normalized product table and a non-CN exchange guard, plus 9 new regression cases. Session FTS5 indexes now persist timestamps so cross-session search can sort by date; the same path also fixed a re-upsert that was wall-clocking every session's `started_at`. The Vite dev-mode proxy gained the missing `/alpha` entry so the AlphaZoo page resolves on `npm run dev`. `tests/test_e2e_harness_v2.py` (real-LLM e2e suite) is now gated behind `VIBE_TRADING_RUN_LIVE_E2E=1` so CI no longer changes shape based on env-key presence. Ruff `per-file-ignores` added for the factor zoo (3783 → 0 F401 noise), frontend tsconfig enables `noUnusedLocals` / `noUnusedParameters` as regression guards, and 76 unused `vw = vwap(...)` boilerplate lines were dropped from `gtja191` alphas. Net **-918 LOC**.
- **2026-05-17** 🧬 **Alpha Zoo v1 (0.1.8)**: 452 pre-built quant alphas across 4 zoos — `qlib158` (Microsoft Qlib, Apache-2 attribution), `alpha101` (Kakushadze 101 Formulaic Alphas, paper rewrite from arXiv:1601.00991), `gtja191` (Guotai Junan 2014 short-horizon factor report), and `academic` (Fama-French 5 + Carhart price-based proxies). One-line CLI to bench any zoo on your universe: `vibe-trading alpha bench --zoo gtja191 --universe csi300 --period 2018-2025`. Ships with AST purity gate, lookahead-guard test, `pytest-socket` network kill-switch, per-zoo LICENSE.md, and a Developer Certificate of Origin (DCO) workflow for community PRs. Auto-rendered Alpha Library at [vibetrading.wiki/alpha-library/](https://vibetrading.wiki/alpha-library/) + research-lab post [Which of the 191 GTJA alphas still work in 2026?](https://vibetrading.wiki/research-lab/posts/alpha-191-in-2026.html).
- **2026-05-16** 🧪 **Research spine update**: Added a backend Hypothesis Registry with `create_hypothesis`, `update_hypothesis`, `link_backtest`, and `search_hypotheses`; external-content readers now attach warning-only `security_warnings`; and Shadow Account scanning now uses deterministic OHLCV feature evaluation instead of the old calendar-phase stub.
- **2026-05-15** 🪪 The run detail page now surfaces the Trust Layer run card alongside metrics and artifacts, completing the UI side of the `run_card.json` work landed on 2026-05-12. `PersistentMemory.add()` was also hardened on length, empty/whitespace-only names, and C0/C1 control bytes from the #108/#109/#110 triage ([#112](https://github.com/HKUDS/Vibe-Trading/pull/112), thanks @Teerapat-Vatpitak).
- **2026-05-14** 🌐 the public wiki is now live at [vibetrading.wiki](https://vibetrading.wiki/) with docs, tutorials, Research Lab, and Alpha Library sections deployed through Cloudflare Pages. Persistent memory is also inspectable from the CLI via `vibe-trading memory list/show/search/forget` ([#102](https://github.com/HKUDS/Vibe-Trading/pull/102), thanks @Teerapat-Vatpitak), and memory tokenization/slugs now support Thai, Arabic, Hebrew, and Cyrillic text ([#104](https://github.com/HKUDS/Vibe-Trading/pull/104)).
- **2026-05-13** 🧭 Swarm runs now ground workers with fetched market data and cleaner persisted reports ([#93](https://github.com/HKUDS/Vibe-Trading/pull/93), [#84](https://github.com/HKUDS/Vibe-Trading/pull/84)).
- **2026-05-12** 🧾 Backtests now emit `run_card.json` and `run_card.md` alongside artifacts for reproducible research runs.
- **2026-05-11** 🧭 **Memory slugs, swarm accounting, and CLI preflight**: Persistent memory now preserves CJK characters when generating file slugs, preventing silent filename collisions for Chinese/Japanese/Korean notes ([#95](https://github.com/HKUDS/Vibe-Trading/pull/95), thanks @voidborne-d). Swarm run totals now prefer provider-reported token usage with the existing estimate fallback ([#94](https://github.com/HKUDS/Vibe-Trading/pull/94), thanks @Teerapat-Vatpitak), and the CLI run UI gained a startup preflight check for common environment issues ([#96](https://github.com/HKUDS/Vibe-Trading/pull/96), thanks @ykykj).
- **2026-05-10** 🧱 **Regression guardrails + run metadata**: Memory recall now treats underscores as token boundaries, so snake_case saved memories such as `mcp_wiring_test` match natural-language queries like "mcp wiring" ([#87](https://github.com/HKUDS/Vibe-Trading/pull/87), thanks @hp083625). The MCP server has a subprocess smoke test covering initialize → `tools/list` → `tools/call` to guard the first-call deadlock path ([#86](https://github.com/HKUDS/Vibe-Trading/pull/86)), while low-risk hardening landed for Windows path-sensitive tests, API best-effort exception handling, backtest `run_dir` allowed-root validation, and SwarmRun provider/model metadata ([#88](https://github.com/HKUDS/Vibe-Trading/pull/88), [#90](https://github.com/HKUDS/Vibe-Trading/pull/90), [#91](https://github.com/HKUDS/Vibe-Trading/pull/91), [#92](https://github.com/HKUDS/Vibe-Trading/pull/92), thanks @Teerapat-Vatpitak).
- **2026-05-09** 🛡️ **API path hardening + MCP server stability**: API run/session routes now validate path IDs before lookup, rejecting malformed newline-containing parameters and pinning the behavior in the auth/security regression suite ([#80](https://github.com/HKUDS/Vibe-Trading/pull/80), thanks @SJoon99). The MCP server now pre-warms the tool registry on the main thread before serving `tools/call`, avoiding a first-call deadlock in lazy tool discovery ([#85](https://github.com/HKUDS/Vibe-Trading/pull/85), thanks @Teerapat-Vatpitak). The Vite dev proxy also honors `VITE_API_URL` for non-default backend targets ([#82](https://github.com/HKUDS/Vibe-Trading/pull/82), thanks @voidborne-d).
- **2026-05-08** 🧾 **Tushare statement fields in filters**: A-share daily backtests can now request PIT-safe financial statement fields through `fundamental_fields`, so signal engines can screen on `income_total_revenue`, `income_n_income`, `balancesheet_total_hldr_eqy_exc_min_int`, `fina_indicator_roe`, and similar table-prefixed columns after their announcement/disclosure dates ([#76](https://github.com/HKUDS/Vibe-Trading/pull/76), thanks @mrbob-git). Follow-up hardening makes explicit statement-field requests fail fast if Tushare enrichment cannot run, instead of silently falling back to raw price bars ([#77](https://github.com/HKUDS/Vibe-Trading/pull/77)).
- **2026-05-07** 📈 **Tushare fundamentals + community triage**: Added a point-in-time `TushareFundamentalProvider` contract for fundamental research workflows, with regression coverage for the project `TUSHARE_TOKEN` environment path ([#74](https://github.com/HKUDS/Vibe-Trading/pull/74)). Community triage also clarified that Vibe-Trading keeps rapid iteration focused on one UI language for now, avoids adding redundant search dependencies while DuckDuckGo-backed `web_search` is already bundled, and treats unofficial hosted deployments as untrusted places for API keys or data-source tokens.
- **2026-05-06** 🚀 **v0.1.7 released** ([Release notes](https://github.com/HKUDS/Vibe-Trading/releases/tag/v0.1.7), `pip install -U vibe-trading-ai`): Security-boundary hardening is now published on PyPI and ClawHub, covering safer API/read/upload/file/URL/generated-code/shell-tool/Docker defaults while keeping localhost CLI/Web UI workflows low-friction. This cycle also includes Web UI Settings, correlation heatmap, OpenAI Codex OAuth, A-share pre-ST filtering, interactive CLI UX, swarm preset inspection, dividend analysis, dev workflow polish, and audited frontend build-dependency floors. Thanks to the 0.1.7 contributors and to lemi9090 (S2W) for coordinated security validation.
- **2026-05-05** 🛡️ **Security boundary follow-up**: Completes the remaining security-boundary hardening around explicit CORS origins, Settings credential indicators, web URL reading, and Shadow Account code generation, with regression tests added for each path. Normal localhost CLI/Web UI workflows stay the same; remote deployments should continue using `API_AUTH_KEY` and explicit trusted origins.
- **2026-05-04** 🖥️ **Interactive CLI UX + CI cleanup**: Interactive mode now has a live bottom status bar showing provider/model, session duration, last-run latency, and cumulative tool-call stats, plus prompt history navigation and cursor editing with arrow keys via `prompt_toolkit` ([#69](https://github.com/HKUDS/Vibe-Trading/pull/69)). The CLI still falls back to Rich prompts when `prompt_toolkit` or a TTY is unavailable. CI path expectations were also aligned with the hardened file-import sandbox and cross-platform `/tmp` resolution, returning main to green ([`bb67dc7`](https://github.com/HKUDS/Vibe-Trading/commit/bb67dc7cfcc11553c57d8962bee56381dca43758)).
- **2026-05-03** 🛡️ **Security hardening patch**: Tightens default API authentication for non-local deployments, protects sensitive run/session/swarm reads, restricts upload and local file-reading boundaries, gates shell-capable tools by entry point, validates generated strategy loading before import, and runs the Docker image as a non-root user with a localhost-only published port by default. Local CLI and localhost Web UI workflows remain low-friction; remote API/Web deployments should set `API_AUTH_KEY`.
- **2026-05-02** 🧭 **Dividend analysis + sharper roadmap**: Added the `dividend-analysis` skill for income stocks, payout sustainability, dividend growth, shareholder yield, ex-dividend mechanics, and yield-trap checks, pinned by bundled-skill regression tests. The public roadmap now focuses on upcoming work: Research Autopilot, Data Bridge, Options Lab, Portfolio Studio, Alpha Zoo, Research Delivery, Trust Layer, and Community sharing.
- **2026-05-01** 🔥 **Correlation heatmap + OpenAI Codex OAuth + A-share pre-ST filter**: New correlation dashboard/API computes rolling return correlations and renders an ECharts heatmap for portfolio and symbol analysis ([#64](https://github.com/HKUDS/Vibe-Trading/pull/64)). OpenAI Codex provider support now uses ChatGPT OAuth via `vibe-trading provider login openai-codex`, with Settings metadata and adapter regression tests ([#65](https://github.com/HKUDS/Vibe-Trading/pull/65)). Added and hardened the `ashare-pre-st-filter` skill for A-share ST/*ST risk screening, including Sina penalty relevance filtering so securities-account mentions do not inflate E2 counts ([#63](https://github.com/HKUDS/Vibe-Trading/pull/63)).
- **2026-04-30** ⚙️ **Web UI Settings + validation CLI hardening**: New Settings page for LLM provider/model, base URL, reasoning effort, and data source credentials, backed by local/auth-protected settings APIs and data-driven provider metadata ([#57](https://github.com/HKUDS/Vibe-Trading/pull/57)). Also hardens `python -m backtest.validation <run_dir>` so missing, blank, malformed, non-existent, and non-directory inputs fail with clear operator-facing messages before validation starts ([#60](https://github.com/HKUDS/Vibe-Trading/pull/60)).
- **2026-04-28** 🚀 **v0.1.6 released** (`pip install -U vibe-trading-ai`): Fixes `vibe-trading --swarm-presets` returning empty after `pip install` / `uv tool install` ([#55](https://github.com/HKUDS/Vibe-Trading/issues/55)) — preset YAMLs now bundled inside the `src.swarm` package and pinned by a 6-test regression suite. Plus AKShare loader correctly routes ETFs (`510300.SH`) and forex (`USDCNH`) to the right endpoints with hardened registry fallback. Rolls up everything since v0.1.5: benchmark comparison panel, `/upload` streaming + size limits, Futu loader (HK + A-share), vnpy export skill, security hardening, frontend lazy loading (688KB → 262KB).
- **2026-04-27** 📊 **Benchmark panel + upload safety**: Backtest output now ships a benchmark comparison panel (ticker / benchmark return / excess return / information ratio) with yfinance-backed resolution for SPY, CSI 300, etc. ([#48](https://github.com/HKUDS/Vibe-Trading/issues/48)). Plus `/upload` streams the request body in 1 MB chunks and aborts past `MAX_UPLOAD_SIZE`, bounding memory under oversized/malformed clients ([#53](https://github.com/HKUDS/Vibe-Trading/pull/53)) — pinned by a 4-case regression suite.
- **2026-04-22** 🛡️ **Hardening + new integrations**: Path containment enforced in `safe_path` + journal/shadow tool sandbox, `MANIFEST.in` ships `.env.example` / tests / Docker files in sdist, route-level lazy loading shrinks frontend initial bundle 688KB → 262KB. Plus Futu data loader for HK & A-share equities ([#47](https://github.com/HKUDS/Vibe-Trading/pull/47)) and vnpy CtaTemplate export skill ([#46](https://github.com/HKUDS/Vibe-Trading/pull/46)).
- **2026-04-21** 🛡️ **Workspace + docs**: Relative `run_dir` normalized to active run dir ([#43](https://github.com/HKUDS/Vibe-Trading/pull/43)). README usage examples ([#45](https://github.com/HKUDS/Vibe-Trading/pull/45)).
- **2026-04-20** 🔌 **Reasoning + Swarm**: `reasoning_content` preserved across all `ChatOpenAI` paths — Kimi / DeepSeek / Qwen thinking work end-to-end ([#39](https://github.com/HKUDS/Vibe-Trading/issues/39)). Swarm streaming + clean Ctrl+C ([#42](https://github.com/HKUDS/Vibe-Trading/issues/42)).
- **2026-04-19** 📦 **v0.1.5**: Published to PyPI & ClawHub. `python-multipart` CVE floor bump, 5 new MCP tools wired (`analyze_trade_journal` + 4 shadow-account tools), `pattern_recognition` → `pattern` registry fix, Docker dep parity, SKILL manifest synced (22 MCP tools / 71 skills).
- **2026-04-18** 👥 **Shadow Account**: Extract your strategy rules from a broker journal → backtest the shadow across markets → 8-section HTML/PDF report showing exactly how much you leave on the table (rule violations, early exits, missed signals, counterfactual trades). 4 new tools, 1 skill, 32 tools total. Trade Journal + Shadow Account samples now live in the web UI welcome screen.
- **2026-04-17** 📊 **Trade Journal Analyzer + Universal File Reader**: Upload broker exports (同花顺/东财/富途/generic CSV) → auto trading profile (holding days, win rate, PnL ratio, drawdown) + 4 bias diagnostics (disposition effect, overtrading, chasing momentum, anchoring). `read_document` now dispatches PDF, Word, Excel, PowerPoint, images (OCR), and 40+ text formats behind one unified call.
- **2026-04-16** 🧠 **Agent Harness**: Persistent cross-session memory, FTS5 session search, self-evolving skills (full CRUD), 5-layer context compression, read/write tool batching. 27 tools, 107 new tests.
- **2026-04-15** 🤖 **Z.ai + MiniMax**: Z.ai provider ([#35](https://github.com/HKUDS/Vibe-Trading/pull/35)), MiniMax temperature fix + model update ([#33](https://github.com/HKUDS/Vibe-Trading/pull/33)). 13 providers.
- **2026-04-14** 🔧 **MCP Stability**: Fixed backtest tool `Connection closed` error on stdio transport ([#32](https://github.com/HKUDS/Vibe-Trading/pull/32)).
- **2026-04-13** 🌐 **Cross-Market Composite Backtest**: New `CompositeEngine` backtests mixed-market portfolios (e.g. A-shares + crypto) with shared capital pool and per-market rules. Also fixed swarm template variable fallback and frontend timeout.
- **2026-04-12** 🌍 **Multi-Platform Export**: `/pine` exports strategies to TradingView (Pine Script v6), TDX (通达信/同花顺/东方财富), and MetaTrader 5 (MQL5) in one command.
- **2026-04-11** 🛡️ **Reliability & DX**: `vibe-trading init` .env bootstrap ([#19](https://github.com/HKUDS/Vibe-Trading/pull/19)), preflight checks, runtime data-source fallback, hardened backtest engine. Multi-language README ([#21](https://github.com/HKUDS/Vibe-Trading/pull/21)).
- **2026-04-10** 📦 **v0.1.4**: Docker fix ([#8](https://github.com/HKUDS/Vibe-Trading/issues/8)), `web_search` MCP tool, 12 LLM providers, `akshare`/`ccxt` deps. Published to PyPI and ClawHub.
- **2026-04-09** 📊 **Backtest Wave 2**: ChinaFutures, GlobalFutures, Forex, Options v2 engines. Monte Carlo, Bootstrap CI, Walk-Forward validation.
- **2026-04-08** 🔧 **Multi-market backtest** with per-market rules, Pine Script v6 export, 5 data sources with auto-fallback.

</details>

---

## ✨ Key Features

<div align="center">
<table align="center" width="94%" style="width:94%; margin-left:auto; margin-right:auto;">
  <tr>
    <td align="center" width="50%" valign="top">
      <img src="assets/feature-self-improving-trading-agent.png" height="130" alt="Self-improving trading agent"/><br>
      <h3>🔍 Self-Improving Trading Agent</h3>
      <div align="left">
        • Natural-language market research<br>
        • Strategy drafts and file/web analysis<br>
        • Memory-backed workflows
      </div>
    </td>
    <td align="center" width="50%" valign="top">
      <img src="assets/feature-multi-agent-trading-teams.png" height="130" alt="Multi-agent trading teams"/><br>
      <h3>🐝 Multi-Agent Trading Teams</h3>
      <div align="left">
        • Investment, quant, crypto, and risk teams<br>
        • Streaming progress and persisted reports<br>
        • Workers grounded with fetched market data
      </div>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%" valign="top">
      <img src="assets/feature-cross-market-data-backtesting.png" height="130" alt="Cross-market data and backtesting"/><br>
      <h3>📊 Cross-Market Data & Backtesting</h3>
      <div align="left">
        • A/HK/US equities, crypto, futures, and forex<br>
        • Data fallback and composite backtests<br>
        • PIT data, validation, and run cards
      </div>
    </td>
    <td align="center" width="50%" valign="top">
      <img src="assets/feature-shadow-account.png" height="130" alt="Shadow Account"/><br>
      <h3>👥 Shadow Account</h3>
      <div align="left">
        • Broker-journal behavior diagnostics<br>
        • Rule-based Shadow Account comparisons<br>
        • Exportable audit reports and strategy code
      </div>
    </td>
  </tr>
</table>
</div>

## 💡 What Is Vibe-Trading?

Vibe-Trading is an open-source research workspace for turning finance questions into runnable analysis. It connects natural-language prompts to market-data loaders, strategy generation, backtest engines, reports, exports, and persistent research memory.

It is designed for research, simulation, and backtesting — and, when you choose, autonomous trading through a broker you authorize yourself (e.g. Robinhood Agentic Trading). It holds no funds and never trades outside the limits you set, and you can halt it instantly.

---

## ✨ What You Can Do

| Task | Output |
|------|--------|
| **Ask a trading question** | Market research with tools, data, documents, and reusable session context. |
| **Backtest a strategy idea** | Strategy code, metrics, benchmark context, validation artifacts, and run cards. |
| **Review your own trades** | Broker-journal parsing, behavior diagnostics, rule extraction, and Shadow Account comparisons. |
| **Improve repeated research** | Persistent memory and editable skills turn useful routines into reusable workflows. |
| **Run analyst teams** | Multi-agent research reviews for investment, quant, crypto, macro, and risk workflows. |
| **Ship usable artifacts** | Reports, TradingView Pine Script, TDX, MetaTrader 5, MCP tools, and later research sessions. |
| **Bench a pre-built alpha zoo** | One-line IC + alive/reversed/dead categorisation across 456 alphas (Qlib 158 + Kakushadze 101 + GTJA 191 + FF5 + Carhart) on your universe. |

---

## ⚡ Quick Example

```bash
pip install vibe-trading-ai

# Natural-language research
vibe-trading run -p "Backtest a BTC-USDT 20/50 moving-average strategy for 2024, summarize return and drawdown, then export the report"

# Bench a pre-built alpha zoo (one line)
vibe-trading alpha bench --zoo gtja191 --universe csi300 --period 2018-2025 --top 20
```

```bash
vibe-trading --upload trades_export.csv
vibe-trading run -p "Analyze my trading behavior, extract my shadow strategy, and compare it with my actual trades"
```

---

## 👥 Shadow Account

Shadow Account starts from your own trading records instead of a generic strategy template.

Upload a broker export, let the agent summarize your behavior, then compare the actual trading path with a rule-based shadow strategy.

| Step | Agent output |
|------|--------------|
| **1. Read your journal** | Parses broker exports from 同花顺, 东方财富, 富途, and generic CSV formats. |
| **2. Profile your behavior** | Holding days, win rate, PnL ratio, drawdown, disposition effect, overtrading, momentum chasing, and anchoring checks. |
| **3. Extract your rules** | Turns recurring entries/exits into an explicit strategy profile instead of a hand-wavy summary. |
| **4. Run the shadow** | Backtests the extracted rules and highlights rule breaks, early exits, missed signals, and alternative trade paths. |
| **5. Deliver the report** | Produces an HTML/PDF report that can be inspected, archived, or refined in a later session. |

```bash
vibe-trading --upload trades_export.csv
vibe-trading run -p "Analyze my trading behavior, extract my shadow strategy, and compare it with my actual trades"
```

---

## 🧪 Research Workflow

Most runs follow the same evidence path: route the request, load the right market context, execute tools, validate outputs, and keep the artifacts inspectable.

| Layer | What happens |
|-------|--------------|
| **Plan** | Selects the relevant finance skills, tools, data sources, and swarm preset when useful. |
| **Ground** | Pulls A-shares, HK/US equities, crypto, futures, forex, documents, or web context through the available loaders. |
| **Execute** | Generates testable strategy code, runs tools, and uses the matching backtest engine or analysis workflow. |
| **Validate** | Adds metrics, benchmark comparison, Monte Carlo, Bootstrap, Walk-Forward, run cards, and warnings where applicable. |
| **Deliver** | Returns reports, artifacts, tool traces, and exports for TradingView, TDX, MetaTrader 5, MCP clients, or later sessions. |

---

## 📡 Data Sources & Smart Fallback

One `get_market_data` call, **18 market-data sources**. Set `source: "auto"` — the loader picks by symbol, then walks a per-market chain ordered by **IP-ban risk**: never-banned public sources first, throttled / key-gated ones last. Zero config, no single point of failure.

| Source | Markets | Auth | Role |
|--------|---------|------|------|
| `tencent` · `mootdx` | A-share | none | never IP-banned (`mootdx` = 通达信 TCP) |
| `eastmoney` | A / US / HK | none | OHLCV + deep fundamentals & flow tools (throttled) |
| `baostock` · `akshare` | A (+ US/HK/futures/macro/fx) | none | free fallbacks |
| `tushare` | A / futures / fund / macro | token | richest A-share |
| `yahoo` · `sina` · `stooq` | US (/HK) | none | direct chart/quotes/options · K-line to 1984 · EOD CSV |
| `yfinance` | US / HK | none | wrapper |
| `finnhub` · `alphavantage` · `tiingo` · `fmp` | US | key | optional providers |
| `okx` · `ccxt` | crypto | none | OKX + 100+ exchanges |
| `futu` | HK / A | OpenD | optional local FutuOpenD |
| `local` | any | none | your own CSV / Parquet / DuckDB via `local:` prefix |

**Fallback chains (by IP-ban risk):**

- **A-share** → `tencent` · `mootdx` · `eastmoney` · `baostock` · `akshare` · `tushare` · `local`
- **US** → `yahoo` · `stooq` · `sina` · `eastmoney` · `yfinance` · `tiingo` · `fmp` · `finnhub` · `alphavantage` · `akshare` · `local`
- **HK** → `eastmoney` · `yahoo` · `futu` · `yfinance` · `akshare` · `local`
- **Crypto** → `okx` · `ccxt` · `yfinance` · `local` &nbsp;·&nbsp; *(futures / fund / macro / forex → `tushare`/`akshare` → `local`)*

Beyond OHLCV, **18 read-only data tools** reach into fundamentals & flow — fund flow, dragon-tiger, northbound, margin, block trades, shareholder count, lockup, sector, research reports, news, SEC filings, financial statements, options chains, institutional holdings, market screening, symbol search, and macro — all exposed over MCP. An explicit `local:` symbol never silently falls back to a network source.

---

## 🔩 Detailed Capabilities

Detailed inventories are folded below to keep the main README scannable. Open them when you want to inspect the available building blocks.

<details>
<summary><b>Finance Skill Library</b> <sub>79 skills across 8 categories</sub></summary>

- 📊 79 specialized finance skills organized into 8 categories
- 🌐 Complete coverage from traditional markets to crypto & DeFi
- 🔬 Comprehensive capabilities spanning data sourcing to quantitative research

| Category | Skills | Examples |
|----------|--------|----------|
| Data Source | 9 | `data-routing`, `tushare`, `yfinance`, `okx-market`, `akshare`, `mootdx`, `ccxt`, `eastmoney`, `sec-edgar` |
| Strategy | 17 | `strategy-generate`, `cross-market-strategy`, `technical-basic`, `candlestick`, `ichimoku`, `elliott-wave`, `smc`, `multi-factor`, `ml-strategy` |
| Analysis | 17 | `factor-research`, `macro-analysis`, `global-macro`, `valuation-model`, `earnings-forecast`, `credit-analysis`, `dividend-analysis` |
| Asset Class | 9 | `options-strategy`, `options-advanced`, `convertible-bond`, `etf-analysis`, `asset-allocation`, `sector-rotation` |
| Crypto | 7 | `perp-funding-basis`, `liquidation-heatmap`, `stablecoin-flow`, `defi-yield`, `onchain-analysis` |
| Flow | 7 | `hk-connect-flow`, `us-etf-flow`, `edgar-sec-filings`, `financial-statement`, `adr-hshare` |
| Tool | 11 | `backtest-diagnose`, `report-generate`, `pine-script`, `doc-reader`, `web-reader`, `vnpy-export`, `alpha-zoo` |
| Risk Analysis | 1 | `ashare-pre-st-filter` |

</details>

<details>
<summary><b>Custom Data Source</b> <sub>register your own historical OHLCV loader</sub></summary>

Need a market or vendor we don't ship a loader for? Add your own historical-bar
loader and select it with `source="<name>"`. The steps edit package source, so
run from a clone (`pip install -e .`).

1. **Write the loader** — create `agent/backtest/loaders/<name>_loader.py` with a
   class that satisfies `DataLoaderProtocol` (duck-typed, no base class needed)
   and is tagged with `@register`:

   ```python
   import pandas as pd
   from backtest.loaders.registry import register

   @register
   class DataLoader:
       name = "mysource"            # the value you pass as source=
       markets = {"us_equity"}      # a_share/us_equity/hk_equity/crypto/futures/fund/macro/forex
       requires_auth = False

       def is_available(self) -> bool:
           return True              # token present? network reachable?

       def fetch(self, codes, start_date, end_date, *, interval="1D", fields=None):
           # return {symbol: DataFrame indexed by trade_date,
           #         columns: open, high, low, close, volume}
           ...
   ```

2. **Register the module** so `@register` fires — add
   `"backtest.loaders.<name>_loader"` to `_loader_modules` in
   `agent/backtest/loaders/registry.py`.
3. **Allow the name** through config validation — add `"mysource"` to
   `_VALID_SOURCES` in `agent/backtest/runner.py`.
4. *(Optional)* slot it into a market's `FALLBACK_CHAINS` in `registry.py` so
   `source="auto"` can reach it.
5. **Use it** — `source="mysource"` in a backtest config, or via the CLI / agent.

> **Real-time ticks / order-book depth are out of scope for loaders** — the
> loader layer is point-in-time historical bars only. Live market data flows
> through the broker connectors instead: `okx` / `binance` / `ccxt` for crypto,
> `futu` / `tiger` for equities.

</details>

<details>
<summary><b>Preset Trading Teams</b> <sub>29 swarm presets</sub></summary>

- 🏢 29 ready-to-use agent teams
- ⚡ Pre-configured finance workflows
- 🎯 Investment, trading & risk management presets

| Preset | Workflow |
|--------|----------|
| `investment_committee` | Bull/bear debate → risk review → PM final call |
| `global_equities_desk` | A-share + HK/US + crypto researcher → global strategist |
| `crypto_trading_desk` | Funding/basis + liquidation + flow → risk manager |
| `earnings_research_desk` | Fundamental + revision + options → earnings strategist |
| `macro_rates_fx_desk` | Rates + FX + commodity → macro PM |
| `quant_strategy_desk` | Screening + factor research → backtest → risk audit |
| `technical_analysis_panel` | Classic TA + Ichimoku + harmonic + Elliott + SMC → consensus |
| `risk_committee` | Drawdown + tail risk + regime review → sign-off |
| `global_allocation_committee` | A-shares + crypto + HK/US → cross-market allocation |

<sub>Plus 20+ additional specialist presets — run vibe-trading --swarm-presets to explore all.

</sub>

</details>

<details>
<summary><b>Alpha Zoo</b> <sub>456 pre-built quant alphas across 4 zoos</sub></summary>

- 🧬 456 cross-sectional alphas, lookahead-banned at the operator layer
- 📈 IC + IR + alive/reversed/dead categorisation in one CLI command
- 🔬 AST purity gate + 300-row lookahead sentinel test + `pytest-socket` network kill-switch
- 📦 Apache-2 attribution for Qlib; per-zoo `LICENSE.md` declaring formulas as mathematical content
- 🤝 Developer Certificate of Origin (DCO) sign-off workflow for community PRs

| Zoo | Count | Source | License |
|-----|-------|--------|---------|
| **qlib158** | 154 | Microsoft Qlib `Alpha158` (Apache-2.0, commit-pinned) | Apache-2.0 |
| **alpha101** | 101 | Kakushadze (2015), "101 Formulaic Alphas", arXiv:1601.00991 | Formulas are mathematical content |
| **gtja191** | 191 | Guotai Junan (2014), "191 Short-period Trading Alpha Factors" | Formulas are mathematical content |
| **academic** | 10 | Fama-French 5 + Carhart momentum + Jegadeesh reversal + George-Hwang 52-week-high + Amihud illiquidity + Harvey-Siddique skew (price-based proxies) | Public academic literature |

Run `vibe-trading alpha list` to browse, `vibe-trading alpha show <id>` for formulas + source, `vibe-trading alpha bench --zoo X --universe Y --period Z` to score a whole zoo.

</details>

## 🎬 Demo

<div align="center">
<table>
<tr>
<td width="50%">

https://github.com/user-attachments/assets/4e4dcb80-7358-4b9a-92f0-1e29612e6e86

</td>
<td width="50%">

https://github.com/user-attachments/assets/3754a414-c3ee-464f-b1e8-78e1a74fbd30

</td>
</tr>
<tr>
<td colspan="2" align="center"><sub>☝️ Natural-language backtest & multi-agent swarm debate — Web UI + CLI</sub></td>
</tr>
</table>
</div>

---

## 🚀 Quick Start

### One-line install (PyPI)

```bash
pip install vibe-trading-ai
```

Then run a first research task:

```bash
vibe-trading init
vibe-trading run -p "Backtest a BTC-USDT 20/50 moving-average strategy for 2024 and summarize return and drawdown"
```

> **Upgrading from an older version?** 0.1.10 moved to LangChain 1.x. If imports break after `pip install -U vibe-trading-ai` over a pre-0.1.10 install (e.g. langgraph fails to import), recreate the venv or run `pip install --force-reinstall vibe-trading-ai`. A fresh install is unaffected.

> **Package name vs commands:** The PyPI package is `vibe-trading-ai`. Once installed, you get three commands:
>
> | Command | Purpose |
> |---------|---------|
> | `vibe-trading` | Interactive CLI / TUI |
> | `vibe-trading serve` | Launch FastAPI web server |
> | `vibe-trading-mcp` | Start MCP server (for Claude Desktop, OpenClaw, Cursor, etc.) |

```bash
vibe-trading init              # interactive .env setup
vibe-trading                   # launch CLI
vibe-trading serve --port 8899 # launch web UI
vibe-trading-mcp               # start MCP server (stdio)
```

### Or choose a path

| Path | Best for | Time |
|------|----------|------|
| **A. Docker** | Try it now, zero local setup | 2 min |
| **B. Local install** | Development, full CLI access | 5 min |
| **C. MCP plugin** | Plug into your existing agent | 3 min |
| **D. ClawHub** | One command, no cloning | 1 min |

### Prerequisites

- An **LLM API key** from any supported provider — or run locally with **Ollama** (no key needed)
- **Python 3.11+** for Path B
- **Docker** for Path A
- OpenAI Codex can also be used with ChatGPT OAuth: set `LANGCHAIN_PROVIDER=openai-codex`, then run `vibe-trading provider login openai-codex`. This does not use `OPENAI_API_KEY`.

> **Supported LLM providers:** OpenRouter, OpenAI, DeepSeek, Gemini, Groq, DashScope/Qwen, Zhipu, Moonshot/Kimi, MiniMax, Xiaomi MIMO, Z.ai, Ollama (local). See `.env.example` for config.

> **Tip:** All markets work without any API keys thanks to automatic fallback. yfinance (HK/US), OKX (crypto), mootdx (A-shares, TCP-direct, no IP throttle), and AKShare (A-shares, US, HK, futures, forex) are all free. Tushare token is optional — mootdx is the preferred no-token A-share fallback, with AKShare as a broader backup.

### Path A: Docker (zero setup)

```bash
git clone https://github.com/HKUDS/Vibe-Trading.git
cd Vibe-Trading
cp agent/.env.example agent/.env
# Edit agent/.env — uncomment your LLM provider and set API key
docker compose up --build
```

Open `http://localhost:8899`. Backend + frontend in one container.

Docker publishes the backend on `127.0.0.1:8899` by default and runs the app as a non-root container user. If you intentionally expose the API beyond your own machine, set a strong `API_AUTH_KEY` and send `Authorization: Bearer <key>` from clients.

> [!NOTE]
> **Using Ollama with Docker:** the container reaches a host-side Ollama via `host.docker.internal`, not `localhost` (inside the container `localhost` is the container itself). `docker-compose.yml` defaults `OLLAMA_BASE_URL` to `http://host.docker.internal:11434`; export `OLLAMA_BASE_URL` (or set it in a top-level `.env`) to point elsewhere. This relies on the `host-gateway` mapping in `extra_hosts`, which requires **Docker Engine ≥ 20.10 / Compose v2** (provided automatically on Docker Desktop).

Your data survives updates: persistent memory, the cross-session search index, user-created skills, shadow accounts, broker connector config, web sessions, backtest runs, swarm history, and uploads all live in named Docker volumes, so `git pull && docker compose up --build` keeps them. They are deleted only by `docker compose down -v`.

### Path B: Local install

```bash
git clone https://github.com/HKUDS/Vibe-Trading.git
cd Vibe-Trading
python -m venv .venv

# Activate
source .venv/bin/activate          # Linux / macOS
# .venv\Scripts\Activate.ps1       # Windows PowerShell

pip install -e .
cp agent/.env.example agent/.env   # Edit — set your LLM provider API key
vibe-trading                       # Launch interactive TUI
```

<details>
<summary><b>Start web UI (optional)</b></summary>

```bash
# Terminal 1: API server
vibe-trading serve --port 8899

# Terminal 2: Frontend dev server
cd frontend && npm install && npm run dev
```

Open `http://localhost:5899`. The frontend proxies API calls to `localhost:8899`.

**Production mode (single server):**

```bash
cd frontend && npm run build && cd ..
vibe-trading serve --port 8899     # FastAPI serves dist/ as static files
```

> [!NOTE]
> `vibe-trading serve` binds `0.0.0.0` and is loopback-only by default: opening the UI on the **same machine** (`http://localhost:8899`) works with zero config. If you browse from **another machine, a VM host, or a phone on your LAN**, sensitive endpoints return `403` and the chat shows "Remote API access requires an API key" — set a strong `API_AUTH_KEY` in `agent/.env`, restart, and enter the same key once in **Settings**. (Docker Desktop's host gateway: set `VIBE_TRADING_TRUST_DOCKER_LOOPBACK=1` with the default `127.0.0.1` port bind.)

</details>

### Path C: MCP plugin

See [MCP Plugin](#-mcp-plugin) section below.

### Path D: ClawHub (one command)

```bash
npx clawhub@latest install vibe-trading --force
```

The skill + MCP config is downloaded into your agent's skills directory. See [ClawHub install](#-mcp-plugin) for details.

---

## 🧠 Environment Variables

Copy `agent/.env.example` to `agent/.env` and uncomment the provider block you want. Each provider needs 3-4 variables:

| Variable | Required | Description |
|----------|:--------:|-------------|
| `LANGCHAIN_PROVIDER` | Yes | Provider name (`openrouter`, `deepseek`, `groq`, `ollama`, etc.) |
| `<PROVIDER>_API_KEY` | Yes* | API key (`OPENROUTER_API_KEY`, `DEEPSEEK_API_KEY`, etc.) |
| `<PROVIDER>_BASE_URL` | Yes | API endpoint URL |
| `LANGCHAIN_MODEL_NAME` | Yes | Model name (e.g. `deepseek-v4-pro`) |
| `TUSHARE_TOKEN` | No | Tushare Pro token for A-share data (falls back to AKShare) |
| `TIMEOUT_SECONDS` | No | LLM call timeout, default 120s |
| `API_AUTH_KEY` | Recommended for network deployments | Bearer token required when the API is reachable from non-local clients |
| `VIBE_TRADING_ENABLE_SHELL_TOOLS` | No | Explicit opt-in for shell-capable tools in remote API/MCP-SSE style deployments |
| `VIBE_TRADING_ALLOWED_FILE_ROOTS` | No | Extra comma-separated roots for document and broker-journal imports |
| `VIBE_TRADING_ALLOWED_RUN_ROOTS` | No | Extra comma-separated roots for generated-code run directories |
| `CONTENT_FILTER_WARNING_THRESHOLD` | No | Content-filter warning ratio threshold (default 0.05 = 5%). When the ratio of LLM responses blocked by content moderation exceeds this, the run card warns you to switch providers. |

<sub>* Ollama does not require an API key. OpenAI Codex uses ChatGPT OAuth and stores tokens via `oauth-cli-kit`, not in `agent/.env`.</sub>

**Free data (no key needed):** A-shares via AKShare, HK/US equities via yfinance, crypto via OKX, 100+ crypto exchanges via CCXT. The system automatically selects the best available source for each market.

### 🎯 Recommended Models

Vibe-Trading is a tool-heavy agent — skills, backtests, memory, and swarms all flow through tool calls. Model choice directly decides whether the agent *uses* its tools or fabricates answers from training data.

| Tier | Examples | When to use |
|------|----------|-------------|
| **Best** | `anthropic/claude-opus-4.7`, `anthropic/claude-sonnet-4.6`, `openai/gpt-5.5-pro`, `google/gemini-3.5-flash` | Complex swarms (3+ agents), long research sessions, paper-grade analysis |
| **Sweet spot** (default) | `deepseek-v4-pro`, `deepseek/deepseek-v4-pro`, `x-ai/grok-4.20`, `z-ai/glm-5.1`, `moonshotai/kimi-k2.6`, `qwen/qwen3-max-thinking` | Daily driver — reliable tool-calling at ~1/10 the cost |
| **Avoid for agent use** | `*-nano`, `*-flash-lite`, `*-coder-next`, small / distilled variants | Tool-calling is unreliable — the agent will appear to "answer from memory" instead of loading skills or running backtests |

The default `agent/.env.example` ships with DeepSeek official API + `deepseek-v4-pro`; OpenRouter users can use `deepseek/deepseek-v4-pro`.

---

## 🖥 CLI Reference

The interactive TUI (`vibe-trading`) now uses a terminal-native transcript: a startup banner, prompt rule, previous-turn recap, live activity rail, Markdown/table rendering, and run timing all stay in the CLI. Non-interactive invocations such as `vibe-trading run`, pipes, and `--json` remain script-friendly.

```bash
vibe-trading               # interactive TUI
vibe-trading run -p "..."  # single run
vibe-trading serve         # API server
vibe-trading alpha list    # browse 456 pre-built alphas; show / bench / compare / export-manifest sub-commands available
vibe-trading provider doctor  # print redacted provider/proxy/package diagnostics
```

<details>
<summary><b>Slash commands inside TUI</b></summary>

| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/skills` | List all 79 finance skills |
| `/swarm` | List 29 swarm team presets |
| `/swarm run <preset> [vars_json]` | Run a swarm team with live streaming |
| `/swarm list` | Swarm run history |
| `/swarm show <run_id>` | Swarm run details |
| `/swarm cancel <run_id>` | Cancel a running swarm |
| `/list` | Recent runs |
| `/show <run_id>` | Run details + metrics |
| `/code <run_id>` | Generated strategy code |
| `/pine <run_id>` | Export indicators (TradingView + TDX + MT5) |
| `/trace <run_id>` | Full execution replay |
| `/continue <run_id> <prompt>` | Continue a run with new instructions |
| `/sessions` | List chat sessions |
| `/settings` | Show runtime config |
| `/clear` | Clear screen |
| `/quit` | Exit |

</details>

<details>
<summary><b>Single run & flags</b></summary>

```bash
vibe-trading run -p "Backtest BTC-USDT MACD strategy, last 30 days"
vibe-trading run -p "Analyze AAPL momentum" --json
vibe-trading run -f strategy.txt
echo "Backtest 000001.SZ RSI" | vibe-trading run
```

```bash
vibe-trading -p "your prompt"
vibe-trading --skills
vibe-trading --swarm-presets
vibe-trading --swarm-run investment_committee '{"topic":"BTC outlook"}'
vibe-trading --list
vibe-trading --show <run_id>
vibe-trading --code <run_id>
vibe-trading --pine <run_id>           # Export indicators (TradingView + TDX + MT5)
vibe-trading --trace <run_id>
vibe-trading --continue <run_id> "refine the strategy"
vibe-trading --upload report.pdf
```

```bash
vibe-trading alpha list --zoo gtja191 --limit 10
vibe-trading alpha show gtja191_171
vibe-trading alpha bench --zoo gtja191 --universe csi300 --period 2018-2025 --top 20
```

</details>

---

## 💡 Examples

### Strategy & Backtesting

```bash
# Moving average crossover on US equities
vibe-trading run -p "Backtest a 20/50-day moving average crossover on AAPL for the past year, show Sharpe ratio and max drawdown"

# RSI mean-reversion on crypto
vibe-trading run -p "Test RSI(14) mean-reversion on BTC-USDT: buy below 30, sell above 70, last 6 months"

# Multi-factor strategy on A-shares
vibe-trading run -p "Backtest a momentum + value + quality multi-factor strategy on CSI 300 constituents over 2 years"

# After backtesting, export to TradingView / TDX / MetaTrader 5
vibe-trading --pine <run_id>
```

**Bench a pre-built alpha zoo** (one line):
```bash
vibe-trading alpha bench --zoo gtja191 --universe csi300 --period 2018-2025 --top 20
```

**Browse the catalogue** and inspect a single alpha:
```bash
vibe-trading alpha list --zoo gtja191 --theme reversal --limit 10
vibe-trading alpha show gtja191_171
```

**Compose a multi-factor signal** from the zoo (Python):
```python
from src.skills.multi_factor.zoo_signal_engine import ZooSignalEngine
engine = ZooSignalEngine.from_zoo(["gtja191_171", "gtja191_111", "gtja191_163"])
panel = ...  # your wide OHLCV panel
signal = engine.compute_signal(panel)
```

### Market Research

```bash
# Equity deep-dive
vibe-trading run -p "Research NVDA: earnings trend, analyst consensus, option flow, and key risks for next quarter"

# Macro analysis
vibe-trading run -p "Analyze the current Fed rate path, USD strength, and impact on EM equities and gold"

# Crypto on-chain
vibe-trading run -p "Deep dive BTC on-chain: whale flows, exchange balances, miner activity, and funding rates"
```

### Swarm Workflows

```bash
# Bull/bear debate on a stock
vibe-trading --swarm-run investment_committee '{"topic": "Is TSLA a buy at current levels?"}'

# Quant strategy from screening to backtest
vibe-trading --swarm-run quant_strategy_desk '{"universe": "S&P 500", "horizon": "3 months"}'

# Crypto desk: funding + liquidation + flow → risk manager
vibe-trading --swarm-run crypto_trading_desk '{"asset": "ETH-USDT", "timeframe": "1w"}'

# Global macro portfolio allocation
vibe-trading --swarm-run macro_rates_fx_desk '{"focus": "Fed pivot impact on EM bonds"}'
```

### Cross-Session Memory

```bash
# Save your preferences once
vibe-trading run -p "Remember: I prefer RSI-based strategies, max 10% drawdown, hold period 5–20 days"

# The agent recalls them in future sessions automatically
vibe-trading run -p "Build a crypto strategy that fits my risk profile"
```

### Upload & Analyze Documents

```bash
# Analyze a broker export or earnings report
vibe-trading --upload trades_export.csv
vibe-trading run -p "Profile my trading behavior and identify any biases"

vibe-trading --upload NVDA_Q1_earnings.pdf
vibe-trading run -p "Summarize the key risks and beats/misses from this earnings report"
```

---

## 🌐 API Server

```bash
vibe-trading serve --port 8899
```

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/runs` | List runs |
| `GET` | `/runs/{run_id}` | Run details |
| `GET` | `/runs/{run_id}/pine` | Multi-platform indicator export |
| `POST` | `/sessions` | Create session |
| `POST` | `/sessions/{id}/messages` | Send message |
| `GET` | `/sessions/{id}/events` | SSE event stream |
| `POST` | `/upload` | Upload PDF/file |
| `GET` | `/swarm/presets` | List swarm presets |
| `POST` | `/swarm/runs` | Start swarm run |
| `GET` | `/swarm/runs/{id}/events` | Swarm SSE stream |
| `GET` | `/alpha/list` | List alphas (filter by zoo/theme/universe) |
| `GET` | `/alpha/{alpha_id}` | Alpha metadata + source code |
| `POST` | `/alpha/bench` | Start a bench job (returns `job_id`) |
| `GET` | `/alpha/bench/{job_id}/stream` | SSE progress stream |
| `GET` | `/settings/llm` | Read Web UI LLM settings |
| `PUT` | `/settings/llm` | Update local LLM settings |
| `GET` | `/settings/data-sources` | Read local data source settings |
| `PUT` | `/settings/data-sources` | Update local data source settings |
| `POST` | `/scheduled-runs` | Create a scheduled research job (interval-ms or cron) |
| `GET` | `/scheduled-runs` | List scheduled jobs |
| `DELETE` | `/scheduled-runs/{job_id}` | Cancel a scheduled job |

Interactive docs: `http://localhost:8899/docs`

### Security defaults

For localhost development, `vibe-trading serve` keeps the browser workflow simple. For any non-local client, sensitive API endpoints require `API_AUTH_KEY`; use `Authorization: Bearer <key>` for JSON/upload requests. Browser EventSource streams are handled by the Web UI after you enter the same key once in Settings.

Shell-capable tools are available to local CLI and trusted localhost workflows, but are not exposed to remote API sessions unless you explicitly set `VIBE_TRADING_ENABLE_SHELL_TOOLS=1`. Document and journal readers are limited to upload/import roots by default; place files under `agent/uploads`, `agent/runs`, `./uploads`, `./data`, `~/.vibe-trading/uploads`, or `~/.vibe-trading/imports`, or add a dedicated directory through `VIBE_TRADING_ALLOWED_FILE_ROOTS`.

### Web UI Settings

The Web UI Settings page lets local users update the LLM provider/model, base URL, generation parameters, reasoning effort, and optional market data credentials such as the Tushare token. Settings are persisted to `agent/.env`; provider defaults are loaded from `agent/src/providers/llm_providers.json`.

Settings reads are side-effect free: `GET /settings/llm` and `GET /settings/data-sources` never create `agent/.env`, and they only return project-relative paths. Settings reads and writes can expose credential state or update credentials/runtime environment, so they require `API_AUTH_KEY` when configured. If `API_AUTH_KEY` is unset for dev mode, settings access is accepted only from loopback clients.

### Scheduled research

Run a research prompt or backtest on a repeating schedule. The background executor is **off by default** — start the server with `VIBE_TRADING_ENABLE_SCHEDULER=1` to enable it:

```bash
VIBE_TRADING_ENABLE_SCHEDULER=1 vibe-trading serve --port 8899
```

Then create jobs over REST. `schedule` is either a bare integer (interval in **milliseconds**) or a 5-field cron expression (`min hour dom mon dow`):

```bash
# every 6 hours (cron)
curl -X POST http://localhost:8899/scheduled-runs \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Scan CSI300 for momentum breakouts and backtest the top 5","schedule":"0 */6 * * *"}'

# list / cancel
curl http://localhost:8899/scheduled-runs
curl -X DELETE http://localhost:8899/scheduled-runs/<job_id>
```

Each fire runs the `prompt` through a fresh agent session (optional backtest parameters go in `config`), and jobs persist under `~/.vibe-trading/` so they survive restarts. Without the flag, the `/scheduled-runs` endpoints still record jobs but nothing fires. Add `-H "Authorization: Bearer <key>"` to each call when `API_AUTH_KEY` is set.

---

## 🔌 MCP Plugin

Vibe-Trading exposes 54 MCP tools for any MCP-compatible client. Runs as a stdio subprocess — no server setup needed. Core research tools work with zero API keys for HK/US/crypto; trading connector tools use the selected connector profile, and `run_swarm` needs an LLM key.

<details>
<summary><b>Claude Desktop</b></summary>

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "vibe-trading": {
      "command": "vibe-trading-mcp"
    }
  }
}
```

</details>

<details>
<summary><b>OpenClaw</b></summary>

Add to `~/.openclaw/config.yaml`:

```yaml
skills:
  - name: vibe-trading
    command: vibe-trading-mcp
```

For a first research-only smoke test, confirm tool discovery and run a market
data or backtest request before selecting a trading connector profile. Core
research tools can run without broker credentials; connector-backed `trading_*`
tools should be used only after you intentionally select and check a connector
profile. `run_swarm` requires an LLM key.

</details>

<details>
<summary><b>Cursor / Windsurf / other MCP clients</b></summary>

```bash
vibe-trading-mcp                  # stdio (default)
vibe-trading-mcp --transport sse  # SSE for web clients
```

</details>

**MCP tools exposed (54):** `list_skills`, `load_skill`, `start_research_goal`, `get_research_goal`, `add_goal_evidence`, `update_research_goal_status`, `backtest`, `factor_analysis`, `analyze_options`, `pattern_recognition`, `read_url`, `read_document`, `web_search`, `write_file`, `read_file`, `trading_connections`, `trading_select_connection`, `trading_check`, `trading_account`, `trading_positions`, `trading_orders`, `trading_quote`, `trading_history`, `list_swarm_presets`, `run_swarm`, `get_market_data`, `get_fund_flow`, `get_dragon_tiger`, `get_northbound_flow`, `get_margin_trading`, `get_block_trades`, `get_shareholder_count`, `get_lockup_expiry`, `get_sector_info`, `get_research_reports`, `get_stock_news`, `get_sec_filings`, `get_financial_statements`, `get_options_chain`, `get_stock_profile`, `screen_market`, `search_symbol`, `get_macro_series`, `iwencai_search`, `get_swarm_status`, `get_run_result`, `list_runs`, `reap_stale_runs`, `retry_run`, `analyze_trade_journal`, `extract_shadow_strategy`, `run_shadow_backtest`, `render_shadow_report`, `scan_shadow_signals`.

### SWARM external MCP tools

`run_swarm` workers can call operator-approved tools from external MCP servers. Configure the server-side allowlist in `VIBE_TRADING_SWARM_AGENT_CONFIG`, `~/.vibe-trading/swarm-agent.json`, or the fallback `~/.vibe-trading/agent.json`; then list remote tools in a swarm preset using the local MCP wrapper name, such as `mcp_internal_kb_search`. Caller-provided `variables` stay template data only and cannot inject MCP URLs, commands, environment variables, or allowlist overrides.

<details>
<summary><b>Install from ClawHub (one command)</b></summary>

```bash
npx clawhub@latest install vibe-trading --force
```

> `--force` is required because the skill references external APIs, which triggers VirusTotal's automated scan. The code is fully open-source and safe to inspect.

This downloads the skill + MCP config into your agent's skills directory. No cloning needed.

Browse on ClawHub: [clawhub.ai/skills/vibe-trading](https://clawhub.ai/skills/vibe-trading)

</details>

<details>
<summary><b>OpenSpace — self-evolving skills</b></summary>

All 79 finance skills are published on [open-space.cloud](https://open-space.cloud) and evolve autonomously through OpenSpace's self-evolution engine.

To use with OpenSpace, add both MCP servers to your agent config:

```json
{
  "mcpServers": {
    "openspace": {
      "command": "openspace-mcp",
      "toolTimeout": 600,
      "env": {
        "OPENSPACE_HOST_SKILL_DIRS": "/path/to/vibe-trading/agent/src/skills",
        "OPENSPACE_WORKSPACE": "/path/to/OpenSpace"
      }
    },
    "vibe-trading": {
      "command": "vibe-trading-mcp"
    }
  }
}
```

OpenSpace will auto-discover all 79 skills, enabling auto-fix, auto-improve, and community sharing. Search for Vibe-Trading skills via `search_skills("finance backtest")` in any OpenSpace-connected agent.

</details>

---

## 🔌 Loading Tools from External MCP Servers (MCP Client Mode)

> **This is the opposite direction from the MCP Plugin above.**
> The MCP Plugin lets *other* agents call Vibe-Trading tools.
> This section lets the *built-in* Vibe-Trading agent call tools from *your* external MCP servers.

### Quick start

Create `~/.vibe-trading/agent.json`:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "uvx",
      "args": ["my-mcp-server"]
    }
  }
}
```

Run any CLI command — tools from ordinary external servers are automatically injected into the agent's registry after local tools:

```bash
vibe-trading run "use my-server to do X"
```

### Official IBKR MCP read-only probe

Vibe-Trading can connect directly to Interactive Brokers' official remote MCP
endpoint in read-only mode. Add this to `~/.vibe-trading/agent.json`:

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

Then start the browser OAuth flow:

```bash
vibe-trading connector authorize ibkr-live-official-mcp-readonly
```

The wildcard is accepted only for IBKR's `mcp.read` probe. Authorizing this
profile confirms access to IBKR's official read scope; generic `trading_account`
and `trading_positions` calls stay disabled until IBKR publishes stable read
tool names that Vibe-Trading can map safely. A config that adds `mcp.write` must
pin an explicit tool allowlist and still passes through the live order guard.

If IBKR issues a pre-registered OAuth client, add `clientId` and `clientSecret`
inside `auth`.

### Trading connectors: fastest path

For users who cannot wait for IBKR OAuth client approval, connect to a local
TWS or IB Gateway session. Credentials stay inside IBKR's desktop app; Vibe-
Trading only connects to `127.0.0.1` and exposes it as a connector profile.

Install the optional SDK:

```bash
pip install "vibe-trading-ai[ibkr]"
```

Open TWS paper trading or IB Gateway paper, enable API socket clients, then run:

```bash
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

Default local ports:

| App | Paper | Live read-only |
|-----|-------|----------------|
| TWS | `7497` | `7496` |
| IB Gateway | `4002` | `4001` |

The agent exposes connector-scoped tools named `trading_connections`,
`trading_select_connection`, `trading_check`, `trading_account`,
`trading_positions`, `trading_orders`, `trading_quote`, and `trading_history`.
Live-broker raw MCP tools are not registered directly as `mcp_<broker>_*`.
No IBKR order-placement tool is registered.

### Config reference

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `type` | string | inferred for stdio; required for HTTP | Omit for stdio, or set to `sse` / `streamableHttp` for URL-based servers. |
| `command` | string | required for stdio | Executable to spawn for stdio servers. Invalid for `sse` / `streamableHttp` servers. |
| `args` | array | `[]` | Command-line arguments for stdio servers only. |
| `env` | object | `{}` | Extra environment variables merged into the subprocess env for stdio servers only. |
| `url` | string | required for `sse` / `streamableHttp` | Remote SSE / streamable HTTP endpoint URL. Not used for stdio servers. |
| `headers` | object | `{}` | Extra HTTP headers for `sse` / `streamableHttp` servers only. |
| `toolTimeout` | number | `30` | Per-tool call timeout in seconds |
| `initTimeout` | number | unset (`max(toolTimeout, 30)`) | MCP initialize / OAuth authorization timeout in seconds. Use this for slow browser authorization without widening ordinary tool calls. |
| `enabledTools` | array | `["*"]` | Tool allowlist. Use `["*"]` to expose all tools from the server |

Config file location: `~/.vibe-trading/agent.json` (JSON or YAML).

For URL-based transports, `type` is required. The agent no longer guesses between SSE and streamable HTTP from the URL suffix.

### Per-session overrides (API)

When creating a session via the API you can pass `mcpServers` inside `session.config` to extend or override the global config for that session only:

```json
{
  "config": {
    "mcpServers": {
      "research-server": {
        "command": "uvx",
        "args": ["research-mcp"],
        "enabledTools": ["search", "fetch"]
      }
    }
  }
}
```

### Tool naming

Ordinary remote tools are exposed with stable names: `mcp_<server>_<tool>`.
Live-broker MCP servers stay behind the `trading_*` connector surface.

If two server names produce the same ASCII-safe local prefix (e.g. `foo-bar` and `foo_bar` both become `foo_bar`), a deterministic hash suffix is appended at the server-segment level so names remain unique. The operator receives a warning:

```
WARNING: Configured MCP server 'foo-bar' collides with another server after local name
normalization. Using local tool prefix 'mcp_foo_bar_<hash>_<tool>' to keep generated
tool names unique. Rename the server in agent config if you want a different prefix.
```

### v1 limits

| Limit | Detail |
|-------|--------|
| Transport | stdio, SSE, and streamable HTTP |
| Execution | serial only — MCP tools never enter the parallel readonly path |
| Surfaces | tools only (resources and prompts excluded in v1) |
| Hot reload | not supported — restart the process to pick up config changes |
| Swarm path | MCP tools are not available inside Swarm worker registries in v1 |

---

## 📁 Project Structure

<details>
<summary><b>Click to expand</b></summary>

```
Vibe-Trading/
├── agent/                          # Backend (Python)
│   ├── cli/                        # CLI package — interactive TUI + subcommands
│   ├── api_server.py               # FastAPI server — runs, sessions, upload, swarm, SSE
│   ├── mcp_server.py               # MCP server — 54 tools for OpenClaw / Claude Desktop
│   │
│   ├── src/
│   │   ├── agent/                  # ReAct agent core
│   │   │   ├── loop.py             #   5-layer compression + read/write tool batching
│   │   │   ├── context.py          #   system prompt + auto-recall from persistent memory
│   │   │   ├── skills.py           #   skill loader (79 bundled + user-created via CRUD)
│   │   │   ├── tools.py            #   tool base class + registry
│   │   │   ├── memory.py           #   lightweight workspace state per run
│   │   │   ├── frontmatter.py      #   shared YAML frontmatter parser
│   │   │   └── trace.py            #   execution trace writer
│   │   │
│   │   ├── memory/                 # Cross-session persistent memory
│   │   │   └── persistent.py       #   file-based memory (~/.vibe-trading/memory/)
│   │   │
│   │   ├── tools/                  # 68 auto-discovered agent tools
│   │   │   ├── backtest_tool.py    #   run backtests
│   │   │   ├── remember_tool.py    #   cross-session memory (save/recall/forget)
│   │   │   ├── skill_writer_tool.py #  skill CRUD (save/patch/delete/file)
│   │   │   ├── session_search_tool.py # FTS5 cross-session search
│   │   │   ├── swarm_tool.py       #   launch swarm teams
│   │   │   ├── web_search_tool.py  #   DuckDuckGo web search
│   │   │   └── ...                 #   bash, file I/O, factor analysis, options, alpha browser + bench, etc.
│   │   │
│   │   ├── factors/                # Alpha Zoo — 456 alphas across 4 zoos
│   │   │   ├── base.py             #   19 operators (rank/scale/ts_*/delta/decay_linear/safe_div/vwap)
│   │   │   ├── registry.py         #   AST-only metadata load + lazy compute + sanity gates
│   │   │   ├── bench_runner.py     #   IC + alive/reversed/dead categorisation
│   │   │   └── zoo/                #   qlib158 (154) + alpha101 (101) + gtja191 (191) + academic (10)
│   │   │
│   │   ├── api/                    # FastAPI route modules
│   │   │   └── alpha_routes.py     #   /alpha/list, /alpha/{id}, /alpha/bench, SSE stream
│   │   │
│   │   ├── skills/                 # 79 finance skills in 8 categories (SKILL.md each)
│   │   ├── swarm/                  # Swarm DAG execution engine
│   │   │   └── presets/            #   29 swarm preset YAML definitions
│   │   ├── session/                # Multi-turn chat + FTS5 session search
│   │   └── providers/              # LLM provider abstraction
│   │
│   └── backtest/                   # Backtest engines
│       ├── engines/                #   7 engines + composite cross-market engine + options_portfolio
│       ├── loaders/                #   18 sources: tushare, okx, yfinance, akshare, baostock, tencent, mootdx, ccxt, futu, local, eastmoney, sina, stooq, yahoo, finnhub, alphavantage, tiingo, fmp
│       │   ├── base.py             #   DataLoader Protocol
│       │   └── registry.py         #   Registry + auto-fallback chains
│       └── optimizers/             #   MVO, equal vol, max div, risk parity
│
├── frontend/                       # Web UI (React 19 + Vite + TypeScript)
│   └── src/
│       ├── pages/                  #   Home, Agent, AlphaZoo, RunDetail, Compare, Correlation, Settings
│       ├── components/             #   chat, charts, layout
│       └── stores/                 #   Zustand state management
│
├── Dockerfile                      # Multi-stage build
├── docker-compose.yml              # One-command deploy
├── pyproject.toml                  # Package config + CLI entrypoint
├── tools/                          # Repo-level CI helpers
│   └── ci_grep_gates.sh            # rejects yaml.load / trademark / per-stock-data leaks
└── LICENSE                         # MIT
```

</details>

---

## 🏛 Ecosystem

Vibe-Trading is part of the **[HKUDS](https://github.com/HKUDS)** agent ecosystem:

<table>
  <tr>
    <td align="center" width="20%">
      <a href="https://github.com/HKUDS/nanobot"><b>NanoBot</b></a><br>
      <sub>Ultra-Lightweight Personal AI Assistant</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/HKUDS/AI-Trader"><b>AI-Trader</b></a><br>
      <sub>Agent-Native Signal &amp; Copy Trading Platform</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/HKUDS/CLI-Anything"><b>CLI-Anything</b></a><br>
      <sub>Making All Software Agent-Native</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/HKUDS/OpenSpace"><b>OpenSpace</b></a><br>
      <sub>Self-Evolving AI Agent Skills</sub>
    </td>
    <td align="center" width="20%">
      <a href="https://github.com/HKUDS/ClawTeam"><b>ClawTeam</b></a><br>
      <sub>Agent Swarm Intelligence</sub>
    </td>
  </tr>
</table>

---

## 🗺 Roadmap

> We ship in phases. Items move to [Issues](https://github.com/HKUDS/Vibe-Trading/issues) when work begins.

| Phase | Feature | Status |
|-------|---------|--------|
| **Trust Layer** | Reproducible run cards are emitted and shown in Run Detail; v1 adds tool traces and citations | v0 Shipped |
| **Hypothesis Registry** | Durable research hypotheses with lifecycle status, data sources, skills, run-card links, and invalidation notes | Backend MVP Shipped |
| **Research Autopilot** | Manual-first research loop: hypothesis → deterministic backtest → evidence report | Phase 1–3 Shipped |
| **Data Bridge** | Bring-your-own data: local CSV/Parquet/SQL connectors with schema mapping | Local loader Shipped |
| **Options Lab** | Vol surface, Greeks dashboard, payoff/scenario explorer | Planned |
| **Portfolio Studio** | Risk x-ray, constraints, turnover-aware optimizer, rebalance notes | Planned |
| **Alpha Zoo** | 452 pre-built alphas (Qlib 158 + Kakushadze 101 + GTJA 191 + FF5 + Carhart) with one-line bench, agent integration, and Web UI | **Shipped 0.1.8** |
| **Research Delivery** | Scheduled briefs to Slack / Telegram / email-style channels | Scheduler Shipped |
| **Community** | Shareable skills, presets, and strategy cards | Exploring |

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Good first issues** are tagged with [`good first issue`](https://github.com/HKUDS/Vibe-Trading/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) — pick one and get started.

Want to contribute something bigger? Check the [Roadmap](#-roadmap) above and open an issue to discuss before starting.

---

## Contributors

Thanks to everyone who has contributed to Vibe-Trading!

Recent v0.1.10 cycle contributors and credits:

- @Hinotoi-agent — a security-hardening wave: local-shutdown auth (#241), loopback-host rebinding rejection (#242), agent shell-tool opt-in (#243), settings-write auth (#245), mandate proposal-id containment (#256), persistent-memory type validation (#257), and MCP swarm run-id containment (#258)
- @mvanhorn — the opt-in local data cache (#177), Gemini thoughtSignature round-trip over OpenAI-compat tool calls (#176), the custom data loader guide (#194), and the glm/zhipu provider alias + model-name inference (#247)
- @gyx09212214-prog — loader robustness for malformed crypto/RSSHub timeout env vars (#227, #240), requested yfinance end-date inclusion (#226), strict run-card JSON for non-finite metrics (#238), and ddgs retry-fallback coverage (#239)
- @BillDin — swarm agent status in the chat UI (#188), explicit preset-name handling (#189), the loader-backed market-data tool for swarm workers (#199), and preset-context continuations (#200)
- @Robin1987China — the Research Autopilot goal-hypothesis bridge (#260), the local CSV/Parquet/DuckDB data loader (#252), and an assistant-prefill fix + configurable Kimi User-Agent (#248)
- @LemonCANDY42 — the read-only runtime status dashboard (#210), persisted AgentLoop usage artifacts (#223), and opt-in Run Detail chart payloads (#225)
- @zwrong — the trace.jsonl overhaul with zero truncation + offload (#206) and session-id on exit + `resume <session-id>` (#218)
- @forge-builder — the AI contributor guide (#173) and the OpenClaw MCP research-only smoke-test docs (#165)
- @skloxo — Chinese (zh-CN) frontend localization (adopted from #217)
- @LeeCQiang — Chinese docstrings across all 452 Alpha Zoo factors (#180)
- @KaiLuettmann — GHCR pre-built image publishing on release (#187)
- @ngoanpv — Gemini thought_signature preservation through the AgentLoop dict path (#184)
- @ShahNewazKhan — Docker host-Ollama reachability via host.docker.internal (#196)
- @sambazhu — frontend sync of completed chat attempts (#236)
- @bhlt — baostock-native code format support (#230)
- @octo-patch — MiniMax M3 default model upgrade (#162)
- @warren618 / Haozhe Wu — the global data layer (8 sources + 18 read-only data tools), the 10 broker SDK connectors, the alpha-compare full stack, the provider-reliability overhaul, multi-engine web_search fallback, responsive Stop + SSE reconnect, and release integration

<a href="https://github.com/HKUDS/Vibe-Trading/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=HKUDS/Vibe-Trading" />
</a>

---

## Disclaimer

Vibe-Trading is research and trading software. It is not investment advice, holds no funds, and runs no execution venue. Trading through a broker channel you explicitly authorize (e.g. Robinhood Agentic Trading) happens only within the limits you set and which you can halt at any time. This broker-trading capability is experimental and not verified by us against a real broker account — use it at your own risk. Past performance does not guarantee future results.

## License

MIT License — see [LICENSE](LICENSE)

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=HKUDS/Vibe-Trading&type=Date)](https://star-history.com/#HKUDS/Vibe-Trading&Date)

<p align="center">
  ⭐ If <b>Vibe-Trading</b> helps your research, a star helps more people find it.
</p>

---

<p align="center">
  Thanks for visiting <b>Vibe-Trading</b> ✨
</p>
<p align="center">
  <img src="https://visitor-badge.laobi.icu/badge?page_id=HKUDS.Vibe-Trading&style=flat" alt="visitors"/>
</p>
