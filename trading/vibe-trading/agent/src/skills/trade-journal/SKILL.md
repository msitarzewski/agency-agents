---
name: trade-journal
description: Analyze a user's trade journal (CSV/Excel broker export). Parses 同花顺/东方财富/富途/generic formats, produces a trading profile and 4 behavior diagnostics (disposition effect, overtrading, chasing, anchoring). Use the `analyze_trade_journal` tool.
category: tool
---
# Trade Journal Analysis

## Purpose

Users upload broker exports (交割单) and get an honest, data-grounded portrait
of their own trading. Two layers are live:

- **Profile** — holding days, frequency, win rate, PnL ratio, cumulative PnL,
  max drawdown, top symbols, market/hourly distribution.
- **Behavior diagnostics** — 4 biases, each with severity (low/medium/high)
  and numeric evidence: disposition effect, overtrading, chasing momentum,
  anchoring.

Strategy extraction → backtest bridge lands in Phase 4c.

Supported formats (auto-detected):
- **同花顺** (Tonghuashun) — A-share CSV, typically GBK-encoded
- **东方财富** (Eastmoney) — A-share CSV, typically GBK-encoded
- **富途** (Futu) — HK/US CSV, UTF-8
- **Generic** — any CSV with columns like `datetime/symbol/side/qty/price`

## Usage

**Call the `analyze_trade_journal` tool directly. Never run Python from bash.**

```
analyze_trade_journal(file_path="uploads/xxx.csv")
analyze_trade_journal(file_path="uploads/xxx.csv", analysis_type="profile")
analyze_trade_journal(file_path="uploads/xxx.csv", filter_expr="2026-01 to 2026-03")
analyze_trade_journal(file_path="uploads/xxx.csv", filter_expr="symbol=600519.SH")
analyze_trade_journal(file_path="uploads/xxx.csv", filter_expr="market=china_a")
```

`analysis_type`:
- `full` (default) — profile + behavior (strategy still placeholder)
- `profile` — profile metrics only (fastest)
- `behavior` — 4 behavior diagnostics only
- `strategy` — Phase 4c placeholder

`filter_expr` (optional):
- Date range: `"YYYY-MM to YYYY-MM"` or `"YYYY-MM-DD to YYYY-MM-DD"`
- Symbol: `"symbol=600519.SH"` (exact match on qualified symbol)
- Market: `"market=china_a|us|hk|crypto"`

## Return shape (profile subset)

```json
{
  "status": "ok",
  "file": "xxx.csv",
  "format_detected": "tonghuashun",
  "total_records": 326,
  "date_range": "2026-01-06 ~ 2026-03-28",
  "symbols_count": 42,
  "market": "china_a",
  "profile": {
    "total_trades": 326,
    "total_roundtrips": 118,
    "avg_holding_days": 3.2,
    "trade_frequency_per_week": 4.1,
    "win_rate": 0.48,
    "profit_loss_ratio": 1.35,
    "total_pnl": 18240.55,
    "max_drawdown": -9820.10,
    "top_symbols": [{"symbol": "600519.SH", "trades": 14, "total_amount": 1.02e6}, ...],
    "market_distribution": {"china_a": 326},
    "hourly_distribution": {9: 52, 10: 84, ...},
    "roundtrips_sample": [{"symbol": "600519.SH", "buy_dt": "...", "sell_dt": "...", "pnl": 3400.1, "pnl_pct": 0.021, "hold_days": 2.5}, ...]
  }
}
```

Note: PnL uses FIFO lot matching; unmatched open positions are excluded from
win rate / PnL ratio (only closed round-trips count).

## Presenting results to the user

Produce a **single markdown report** in the user's language. Lead with the
top-line numbers, then section-by-section. Keep it dense — this is retail
readers skimming on a phone.

### Report template

```
## 你的交易画像 — {date_range}

**总体**
- 交易笔数：{total_trades}（完整来回 {total_roundtrips} 次）
- 平均持仓：{avg_holding_days} 天
- 交易频率：{trade_frequency_per_week} 次/周
- 胜率：{win_rate:.0%}
- 盈亏比：{profit_loss_ratio}
- 累计盈亏：{total_pnl}
- 最大回撤：{max_drawdown}

**最常交易的标的**（前 5 名）
| 标的 | 笔数 | 成交额 |
|------|------|--------|
| ... | ... | ... |

**市场分布**
{market_distribution}

**交易时段**
{hourly_distribution — highlight peak hours}

**一句话观察**
（根据数据写 1-2 句：过度交易？只做窄范围标的？集中在某时段？）
```

Guidance:
- If `win_rate < 0.4` AND `profit_loss_ratio < 1.0` → explicit warning: losing
  on both win rate and payoff. Ask whether they want behavior diagnostics
  (Phase 4b) or a cooling-off reality check.
- If `avg_holding_days < 1` AND `trade_frequency_per_week > 15` → flag
  intraday-heavy pattern, note that minute-level backtest would be better.
- If `symbols_count <= 3` → concentration risk; ask if they want a sector-
  diversification check.

## Follow-up dialogue

After the initial report, users typically ask:
- **Time-slice**: "3 月份表现怎么样" → re-call with `filter_expr="2026-03-01 to 2026-03-31"`.
- **Symbol deep-dive**: "茅台这只赚了多少" → `filter_expr="symbol=600519.SH"`.
- **Market split**: "港股和美股分开看" → two calls, `market=hk` and `market=us`.
- **Hypothetical** ("如果我严格止损 -5%") → Phase 4b feature; for now tell the
  user this is on the roadmap.

Do NOT re-upload — the file path is still valid for subsequent tool calls
in the same session.

## Error handling

- `File not found` / `Unsupported extension` — ask user to re-upload.
- `Unrecognized trade journal format` — share the detected columns back to
  the user and ask them to rename the key columns to: `datetime, symbol,
  side, quantity, price, amount, fee` (generic fallback).
- `No trade records parsed` — likely empty file or header-only; ask user to
  confirm the export contains actual fills.

## Behavior diagnostics (shape)

Under `result["behavior"]`:

```json
{
  "disposition_effect": {
    "severity": "high",
    "ratio_loss_to_win_hold": 1.69,
    "avg_winner_hold_days": 7.4,
    "avg_loser_hold_days": 12.5,
    "evidence": "Losing roundtrips held 12.5d vs winning 7.4d (ratio 1.69). Classic disposition pattern."
  },
  "overtrading": {
    "severity": "high",
    "busy_day_avg_pnl": -2632,
    "quiet_day_avg_pnl": 759,
    "evidence": "On busy days (≥3 trades) avg PnL -2632; on quiet days (≤1) avg PnL +759. High activity hurts returns."
  },
  "chasing_momentum": {
    "severity": "medium",
    "chase_ratio": 0.5,
    "buys_evaluated": 4,
    "evidence": "2/4 buys (50%) came after a >3% price run-up in the same symbol. Some chasing tendency."
  },
  "anchoring": {
    "severity": "high",
    "anchored_symbol_ratio": 0.83,
    "symbols_evaluated": 6,
    "anchored_symbols": [...],
    "evidence": "5/6 frequently-traded symbols stayed in a narrow price band (CV<5%). Strong anchoring."
  }
}
```

### Detection logic (for user-facing explanation)

| Bias | Metric | Medium | High |
|------|--------|--------|------|
| **Disposition effect** | avg_loser_hold / avg_winner_hold | ≥ 1.2 | ≥ 1.5 |
| **Overtrading** | (quiet − busy) / \|quiet\| day-PnL gap | ≥ 0.3 | ≥ 1.0 |
| **Chasing** | fraction of buys after 3-trade rolling +3% move | ≥ 40% | ≥ 60% |
| **Anchoring** | fraction of ≥5-trade symbols with price CV < 5% | ≥ 33% | ≥ 66% |

### Report section (Chinese)

```
## 行为偏差诊断

| 偏差 | 严重程度 | 核心证据 |
|------|----------|----------|
| 处置效应 | {high/medium/low} | {evidence} |
| 过度交易 | {...} | {...} |
| 追涨杀跌 | {...} | {...} |
| 锚定效应 | {...} | {...} |

**改进建议**（根据检测到的 high/medium 项生成）：
- 处置效应 high → 写死止损（例如 -8%），盈利持仓不要过早兑现
- 过度交易 high → 每日交易次数 <= N 的硬约束
- 追涨杀跌 high → 改买回调而不是新高，设置"涨幅 X% 以上当日不追"规则
- 锚定效应 high → 扩宽价格带，不要死守某个"心理价"
```

## Phase 4c preview (not yet implemented)

Strategy extraction → SignalEngine code gen → auto-backtest lands in Phase 4c.
When the user asks for it, respond honestly and offer the behavior diagnostics
instead (they're live).
