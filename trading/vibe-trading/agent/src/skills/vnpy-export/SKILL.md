---
name: vnpy-export
description: Export a Vibe-Trading backtest strategy to a runnable vnpy CtaTemplate Python class — supports A-share equities, futures, and crypto via BarGenerator + ArrayManager.
category: tool
---

## Overview

This skill translates a Vibe-Trading strategy into a **vnpy `CtaTemplate` subclass** `.py` file
that can be loaded directly into the vnpy CTA Strategy App for live trading or vnpy backtesting.

Output file: `artifacts/vnpy_strategy/<StrategyName>Strategy.py` (inside the run directory).

vnpy is the most widely-used open-source quant framework in mainland China (39k+ GitHub stars).
Use this skill when the user asks to export to vnpy, requests a `/vnpy` command, or wants to
run a Vibe-Trading strategy inside vnpy's CTA backtester or live trading engine.

---

## Workflow: Export from Backtest Run

1. `load_skill("vnpy-export")` — read this guide
2. `read_file("config.json")` — extract instrument, dates, parameters, interval
3. `read_file("code/signal_engine.py")` — understand the Python signal logic
4. Determine asset class from `config.json` → choose correct CtaTemplate convention (see below)
5. Translate signal logic to CtaTemplate using the reference tables
6. `write_file("artifacts/vnpy_strategy/<StrategyName>Strategy.py")` — save the output
7. Return the class in a code block with setup instructions

## Workflow: Generate from Description

1. `load_skill("vnpy-export")` — read this guide
2. Write a CtaTemplate class from the user's strategy description
3. `write_file("artifacts/vnpy_strategy/<StrategyName>Strategy.py")` — save the output
4. Return the class with setup and usage instructions

---

## Asset Class Conventions

vnpy uses the same `CtaTemplate` base class for all asset types, but parameter conventions differ:

| Asset Class | Instrument Example | `vt_symbol` Format | Position Unit |
|-------------|-------------------|---------------------|---------------|
| A-share stock | Ping An Bank | `000001.SZSE` | shares (整手, min 100) |
| Futures | IF2406 | `IF2406.CFFEX` | lots |
| Crypto | BTC/USDT | `BTC/USDT.BINANCE` | coin units |

For **stocks**: use `buy` / `sell` only (no short selling unless margin account).
For **futures / crypto**: use all four directions — `buy`, `sell`, `short`, `cover`.

---

## CtaTemplate Structure

Every strategy must subclass `CtaTemplate` and implement these methods:

| Method | Purpose |
|--------|---------|
| `__init__` | Declare parameters, variables, BarGenerator, ArrayManager |
| `on_init` | Called once at startup; call `load_bar(n)` to warm up indicators |
| `on_start` | Called when strategy is started by user |
| `on_stop` | Called when strategy is stopped |
| `on_tick` | Receives live tick data; forward to BarGenerator |
| `on_bar` | Main logic — called once per bar by BarGenerator |
| `on_order` | Order status updates |
| `on_trade` | Fill notifications |
| `on_stop_order` | Stop-order status (if using stop orders) |

**Always call** `self.cancel_all()` at the start of `on_bar` to avoid stale orders.
**Always call** `self.put_event()` at the end of `on_bar` to refresh the UI.

---

## Full Template

See `scripts/cta_template.py` for a complete, runnable example (MA crossover).
The template below is the canonical skeleton — replace the `# SIGNAL LOGIC` section:

```python
from vnpy.app.cta_strategy import (
    CtaTemplate,
    StopOrder,
    TickData,
    BarData,
    TradeData,
    OrderData,
    BarGenerator,
    ArrayManager,
)


class {{StrategyName}}Strategy(CtaTemplate):
    """
    Vibe-Trading export — {{StrategyName}}
    Generated from run: {{run_id}}
    Instrument: {{vt_symbol}}
    """

    author = "Vibe-Trading"

    # ── Parameters (editable in vnpy UI) ──────────────────────────────────
    {{param_name}} = {{param_default}}   # add one line per parameter

    parameters = [{{param_list_as_strings}}]

    # ── Variables (displayed in vnpy UI, reset on strategy restart) ────────
    {{var_name}} = 0.0   # add one line per runtime variable

    variables = [{{var_list_as_strings}}]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)
        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager()

        # initialise variable attributes to match class-level defaults
        # (vnpy requires instance attributes for variables declared above)

    def on_init(self):
        self.write_log("Strategy initialised")
        self.load_bar({{warmup_bars}})   # load enough bars to warm up all indicators

    def on_start(self):
        self.write_log("Strategy started")
        self.put_event()

    def on_stop(self):
        self.write_log("Strategy stopped")

    def on_tick(self, tick: TickData):
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        self.cancel_all()

        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        # ── INDICATOR CALCULATIONS ──────────────────────────────────────────
        # translate indicators from signal_engine.py using the mapping table

        # ── SIGNAL LOGIC ───────────────────────────────────────────────────
        # set cross_over / cross_under (or long_signal / short_signal) here

        # ── ORDER EXECUTION ────────────────────────────────────────────────
        if cross_over:
            if self.pos == 0:
                self.buy(bar.close_price, 1)
            elif self.pos < 0:
                self.cover(bar.close_price, 1)
                self.buy(bar.close_price, 1)
        elif cross_under:
            if self.pos == 0:
                self.short(bar.close_price, 1)
            elif self.pos > 0:
                self.sell(bar.close_price, 1)
                self.short(bar.close_price, 1)

        self.put_event()

    def on_order(self, order: OrderData):
        pass

    def on_trade(self, trade: TradeData):
        self.put_event()

    def on_stop_order(self, stop_order: StopOrder):
        pass
```

---

## Python → ArrayManager Indicator Mapping

`ArrayManager` is vnpy's built-in vectorised indicator library. Always prefer it over pandas
when the equivalent method exists — it is faster and avoids look-ahead bias.

| Python (Vibe-Trading / pandas / ta-lib) | vnpy ArrayManager |
|----------------------------------------|-------------------|
| `df['close'].rolling(n).mean()` | `am.sma(n)` |
| `df['close'].ewm(span=n).mean()` | `am.ema(n)` |
| `ta.RSI(close, n)` | `am.rsi(n)` |
| `ta.MACD(close, 12, 26, 9)` | `am.macd(12, 26, 9)` → `(macd, signal, hist)` |
| Bollinger Bands | `am.boll(n, dev)` → `(mid, upper, lower)` |
| ATR | `am.atr(n)` |
| ADX | `am.adx(n)` |
| `df['close'].rolling(n).std()` | `am.std(n)` |
| Stochastic K, D | `am.kd(n, m)` → `(k, d)` |
| `df['high'].rolling(n).max()` | `am.high_array[-n:].max()` |
| `df['low'].rolling(n).min()` | `am.low_array[-n:].min()` |
| Donchian channel | `am.donchian(n)` → `(upper, lower)` |
| `df['close'].shift(1)` (previous bar) | `am.close_array[-2]` |
| Last N bars as array | `am.sma(n, array=True)` (returns full array) |

**Using arrays**: pass `array=True` to get the full history array (e.g. for crossover detection):

```python
fast_ma = am.sma(self.fast_window, array=True)
cross_over = fast_ma[-1] > slow_ma[-1] and fast_ma[-2] <= slow_ma[-2]
```

---

## Signal → Order Mapping

| Vibe-Trading signal | Position check | vnpy call |
|---------------------|---------------|-----------|
| Long entry | `self.pos == 0` | `self.buy(price, volume)` |
| Long entry (reverse from short) | `self.pos < 0` | `self.cover(price, vol); self.buy(price, vol)` |
| Long exit | `self.pos > 0` | `self.sell(price, volume)` |
| Short entry | `self.pos == 0` | `self.short(price, volume)` |
| Short entry (reverse from long) | `self.pos > 0` | `self.sell(price, vol); self.short(price, vol)` |
| Short exit | `self.pos < 0` | `self.cover(price, volume)` |
| Close all (stop signal) | any | `self.cancel_all()` then `sell` / `cover` as needed |

**Price conventions**:
- For backtesting: use `bar.close_price` (market order equivalent)
- For live trading with limit orders: use `bar.close_price` ± a small offset (e.g. `* 1.001`)
- For stop orders: use `self.buy_stop(trigger, volume)` / `self.short_stop(trigger, volume)`

**Volume conventions**:
- Stocks: volume in shares; must be a multiple of 100 (round lots)
- Futures: volume in lots (usually 1 for CtaTemplate strategies)
- Crypto: volume in base-currency units (e.g., BTC)

---

## Multi-Timeframe Strategies

When the Vibe-Trading strategy uses multiple timeframes (e.g., daily signal, hourly entry):

```python
def __init__(self, ...):
    super().__init__(...)
    self.bg = BarGenerator(self.on_bar, 5, self.on_5min_bar)   # 5-min bars
    self.bg_d = BarGenerator(self.on_bar, window=1, on_window_bar=self.on_daily_bar,
                              interval=Interval.DAILY)          # daily bars
    self.am = ArrayManager()
    self.am_d = ArrayManager(size=100)                          # daily ArrayManager

def on_bar(self, bar: BarData):
    self.bg.update_bar(bar)    # feeds 5-min generator

def on_5min_bar(self, bar: BarData):
    self.bg_d.update_bar(bar)  # feeds daily generator
    # put intraday entry logic here

def on_daily_bar(self, bar: BarData):
    self.am_d.update_bar(bar)
    # put daily trend-filter logic here
```

---

## Output File Instructions

Save the generated file to: `artifacts/vnpy_strategy/<StrategyName>Strategy.py`

To load in vnpy:

1. Copy the file to your vnpy project's `strategies/` folder (or any folder on `sys.path`)
2. Open the vnpy Trader → CTA Strategy App
3. Click **Add Strategy** → select `<StrategyName>Strategy` from the dropdown
4. Set `vt_symbol` (e.g. `IF2406.CFFEX`) and adjust parameters
5. Click **Init** → **Start** to begin

To run the vnpy backtester:

```python
from vnpy.app.cta_backtester import BacktestingEngine
from vnpy.trader.constant import Interval

engine = BacktestingEngine()
engine.set_parameters(
    vt_symbol="000001.SZSE",
    interval=Interval.DAILY,
    start=datetime(2020, 1, 1),
    end=datetime(2024, 1, 1),
    rate=0.0003,
    slippage=0.02,
    size=1,
    pricetick=0.01,
    capital=1_000_000,
)
engine.add_strategy({{StrategyName}}Strategy, {})
engine.load_data()
engine.run_backtesting()
df = engine.calculate_result()
engine.calculate_statistics()
engine.show_chart()
```

---

## Quality Checklist

Before saving the output file:

- [ ] Class name ends with `Strategy` and matches the filename
- [ ] All `parameters` entries have matching class-level defaults and `__init__` instance attributes
- [ ] All `variables` entries have matching instance attributes initialised in `__init__`
- [ ] `on_bar` calls `self.cancel_all()` at the start
- [ ] `on_bar` calls `self.put_event()` at the end
- [ ] `on_bar` returns early if `not am.inited`
- [ ] Position direction checked with `self.pos` before every order call
- [ ] Stocks: no `short` / `cover` calls unless margin trading is explicitly requested
- [ ] `load_bar(n)` warmup in `on_init` is at least `max(all indicator windows) + 2`
- [ ] Comment block at top of file notes the original Vibe-Trading `run_id` and instrument

---

## References

- vnpy CtaTemplate source: `vnpy/app/cta_strategy/template.py`
- ArrayManager source: `vnpy/app/cta_strategy/base.py`
- Official docs: https://www.vnpy.com/docs/cn/cta_strategy.html
- Example strategies (official): `vnpy/app/cta_strategy/strategies/`
