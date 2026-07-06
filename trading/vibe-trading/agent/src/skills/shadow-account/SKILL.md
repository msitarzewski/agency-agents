---
name: shadow-account
description: "Shadow Account — 从用户交割单提炼盈利模式（3-5 条人话规则）→ 跨 A股/港股/美股/crypto 多市场回测 → 差值归因 → 8-section PDF 报告。叙事：你的影子，没有情绪噪音。"
category: analysis
---

# Shadow Account — 影子账户

## 何时触发

当用户说 "提炼我的策略" / "训练影子" / "我的打法回测一下" / "我能多赚多少" / "我的盈利模式" 时，加载此 skill。

**前提**：用户已上传交割单且 `analyze_trade_journal` 已跑过。若没有，先跑 Phase 4a 工具。

## 工作流（四步）

1. `extract_shadow_strategy(journal_path=...)`
   - 返回 `shadow_id` + 3-5 条人话规则
   - 向用户 confirm："这些规则像你本人吗？" 如果用户说"不像"，提高 `min_support` 重跑
2. `run_shadow_backtest(shadow_id=..., journal_path=...)`
   - 返回 per-market 指标 + `delta_pnl` + attribution breakdown
   - 默认四市场并跑（china_a/hk/us/crypto）
3. `render_shadow_report(shadow_id=...)`
   - 生成 HTML + PDF（weasyprint 失败时自动降级成 HTML-only）
   - 返回 `html_path` / `pdf_path` / `delta_pnl`
4. （可选）`scan_shadow_signals(shadow_id=...)` — 今日落在影子入场窗口的标的列表（研究用）

## 产出解读

### 规则卡
每条规则含：`rule_id`、`human_text`（≤30 字）、`support_count`、`coverage_rate`、`holding_days_range`。规则不是"必赚公式"，而是"用户盈利时的共性画像"。

### 回测矩阵
- `per_market`：四市场的 Sharpe/年化/最大回撤
- `combined`：合并池表现
- `equity_curve`：净值时序（进入 PDF Section 3）

### 差值归因（PDF Section 5 — gut punch）
所有数值 signed，正值=影子相对赚更多：
- `noise_trades_pnl`：不命中任何规则的真实交易累计 PnL（用户的情绪单）
- `early_exit_pnl`：赢单但持仓 < 规则下限，按不足比例折算的机会成本
- `late_exit_pnl`：亏单但持仓 > 规则上限，按超额比例折算的放大损失
- `overtrading_pnl`：超出规则频率的真实交易 PnL
- `missed_signals_pnl`：残差（shadow_pnl − real_pnl − 上面四项之和）

### 反事实 Top 5
按 `|impact|` 排序，列出 5 条"最该做没做 / 最不该做却做了"的交易，带具体日期、原因。

## 对话模板

**确认规则**：
> 从你 {profitable_roundtrips} 笔盈利回合中提炼出这些规则：{rules}。这些看起来像你本人的打法吗？

**展示差值**（Section 5）：
> 影子 PnL **{shadow_pnl:+.0f}** / 你真实 **{real_pnl:+.0f}** / 差值 **{delta_pnl:+.0f}**。其中 **{noise_trades_pnl:+.0f}** 来自不符合你任何盈利规则的"情绪单"。

**今日扫描**（强制附带免责）：
> 今日落在你影子入场节奏的标的：{symbols}。**仅研究用，不是买入建议。**

## 规则翻译 Prompt 模板

当 `extract_shadow_strategy` 被调用时，可以注入一个 `llm_translator` callable 以把结构化 entry_condition 翻译成中文自然语言：

```
[上下文] 一位散户的盈利回合中，{N} 笔满足同一组条件：
  market = {market}
  entry_hour ∈ [{hour_min}, {hour_max}]
  持有 {hold_lo}-{hold_hi} 天
[任务] 用 ≤30 字的中文写一条规则，口吻像用户自述的交易习惯，不要堆术语。
[输出] 只返回一行规则文本，不要解释。
```

不注入时走 f-string 模板（见 `extractor._translate_rule`）。

## 红线

- **不落单**：这些工具永远不会对接任何下单通道，仅研究输出
- **不复制他人策略**：Shadow Account 是"用户自己"的影子，不从社区/公开策略提取规则
- **样本不足必报错**：profitable roundtrips < 5 → 直接 raise，不编造
