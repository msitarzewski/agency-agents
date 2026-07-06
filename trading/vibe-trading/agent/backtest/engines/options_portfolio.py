"""Options portfolio backtest engine (v2).

Supports European and American options via Black-Scholes model with
IV smile approximation.  Synthesises theoretical option prices from
underlying prices; supports multi-leg strategies.

v2 enhancements over v1:
  - American option support (early exercise heuristic for calls on dividends,
    always-exercise check for deep ITM puts)
  - IV smile model: skew adjustment based on moneyness (log(K/S))
  - Portfolio-level Greeks aggregation

Signal interface: OptionsSignalEngine.generate(data_map) returns a list of trade instructions.
Artifacts: equity.csv, metrics.csv, trades.csv, greeks.csv.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from scipy.stats import norm


# --- Black-Scholes pricing ---


def bs_price(S: float, K: float, T: float, r: float, sigma: float,
             option_type: str = "call") -> float:
    """Black-Scholes European option pricing.

    Args:
        S: Underlying spot price.
        K: Strike price.
        T: Time to expiry in years.
        r: Risk-free rate (annualised).
        sigma: Annualised volatility.
        option_type: Option type, "call" or "put".

    Returns:
        Theoretical option price.

    Example:
        >>> round(bs_price(100, 100, 1.0, 0.05, 0.2, "call"), 2)
        10.45
    """
    if T <= 0 or sigma <= 0:
        # Expired: return intrinsic value
        if option_type == "call":
            return max(S - K, 0.0)
        return max(K - S, 0.0)

    d1 = (np.log(S / K) + (r + sigma ** 2 / 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == "call":
        return float(S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2))
    return float(K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1))


# --- Greeks ---


def bs_greeks(S: float, K: float, T: float, r: float, sigma: float,
              option_type: str = "call") -> Dict[str, float]:
    """Calculate Black-Scholes Greeks.

    Args:
        S: Underlying spot price.
        K: Strike price.
        T: Time to expiry in years.
        r: Risk-free rate (annualised).
        sigma: Annualised volatility.
        option_type: Option type, "call" or "put".

    Returns:
        Dict containing delta, gamma, theta, vega.
    """
    if T <= 0 or sigma <= 0:
        intrinsic_call = 1.0 if S > K else 0.0
        delta = intrinsic_call if option_type == "call" else intrinsic_call - 1.0
        return {"delta": delta, "gamma": 0.0, "theta": 0.0, "vega": 0.0}

    sqrt_T = np.sqrt(T)
    d1 = (np.log(S / K) + (r + sigma ** 2 / 2) * T) / (sigma * sqrt_T)
    d2 = d1 - sigma * sqrt_T
    nd1_pdf = float(norm.pdf(d1))

    # Delta
    if option_type == "call":
        delta = float(norm.cdf(d1))
    else:
        delta = float(norm.cdf(d1) - 1.0)

    # Gamma (same for call and put)
    gamma = float(nd1_pdf / (S * sigma * sqrt_T))

    # Theta (daily)
    theta_common = -(S * nd1_pdf * sigma) / (2 * sqrt_T)
    if option_type == "call":
        theta = theta_common - r * K * np.exp(-r * T) * norm.cdf(d2)
    else:
        theta = theta_common + r * K * np.exp(-r * T) * norm.cdf(-d2)
    theta = float(theta / 365.0)  # convert to daily

    # Vega (per 1% change in volatility)
    vega = float(S * nd1_pdf * sqrt_T / 100.0)

    return {"delta": delta, "gamma": gamma, "theta": theta, "vega": vega}


# --- Historical volatility ---


def historical_volatility(close: pd.Series, window: int = 30) -> pd.Series:
    """Calculate annualised historical volatility from a close price series.

    Args:
        close: Close price Series.
        window: Rolling window in days.

    Returns:
        Annualised historical volatility Series.
    """
    log_ret = np.log(close / close.shift(1))
    hv = log_ret.rolling(window=window).std() * np.sqrt(252)
    return hv.fillna(hv.dropna().iloc[0] if len(hv.dropna()) > 0 else 0.3)


# --- IV Smile model (v2) ---


def iv_smile_adjustment(S: float, K: float, base_iv: float,
                        skew: float = -0.15, curvature: float = 0.05) -> float:
    """Adjust IV for moneyness using a quadratic smile model.

    IV(K) = base_iv + skew * log(K/S) + curvature * log(K/S)^2

    Args:
        S: Spot price.
        K: Strike price.
        base_iv: At-the-money implied volatility.
        skew: Slope of the smile (negative = put skew). Default -0.15.
        curvature: Curvature of the smile (always positive). Default 0.05.

    Returns:
        Adjusted implied volatility, floored at 0.01.
    """
    if S <= 0 or K <= 0:
        return max(base_iv, 0.01)
    log_moneyness = np.log(K / S)
    adj = base_iv + skew * log_moneyness + curvature * log_moneyness ** 2
    return max(adj, 0.01)


# --- Option positions ---


class OptionPosition:
    """A single option leg position.

    Attributes:
        option_type: "call" or "put".
        strike: Strike price.
        expiry: Expiry date.
        qty: Quantity (positive = long, negative = short).
        entry_price: Theoretical option price at entry.
        entry_date: Entry date string.
        underlying_code: Underlying instrument code.
    """

    def __init__(self, option_type: str, strike: float, expiry: str,
                 qty: int, entry_price: float, entry_date: str,
                 underlying_code: str):
        self.option_type = option_type
        self.strike = strike
        self.expiry = pd.Timestamp(expiry)
        self.qty = qty
        self.entry_price = entry_price
        self.entry_date = entry_date
        self.underlying_code = underlying_code

    def time_to_expiry(self, current_date: pd.Timestamp) -> float:
        """Calculate time remaining to expiry in years.

        Args:
            current_date: Current date.

        Returns:
            Time to expiry in years.
        """
        days = (self.expiry - current_date).days
        return max(days / 365.0, 0.0)

    def is_expired(self, current_date: pd.Timestamp) -> bool:
        """Check whether the option has expired.

        Args:
            current_date: Current date.

        Returns:
            True if expired.
        """
        return current_date >= self.expiry

    def intrinsic_value(self, spot: float) -> float:
        """Calculate intrinsic value.

        Args:
            spot: Underlying spot price.

        Returns:
            Intrinsic value.
        """
        if self.option_type == "call":
            return max(spot - self.strike, 0.0)
        return max(self.strike - spot, 0.0)


# --- Backtest driver ---


def run_options_backtest(
    config: Dict[str, Any],
    loader: Any,
    engine: Any,
    run_dir: Path,
    bars_per_year: int = 252,
) -> Dict[str, Any]:
    """Options backtest entry point.

    Day-by-day simulation:
    1. Read underlying price for the current day
    2. Mark all open option positions to market (BS)
    3. Execute trade instructions from the signal (open/close)
    4. Automatically exercise ITM options or expire OTM options at maturity
    5. Record P&L and Greeks

    Args:
        config: Backtest config; must include codes, start_date, end_date, initial_cash,
                and options_config (risk_free_rate, iv_source).
        loader: DataLoader instance (must have a fetch method).
        engine: OptionsSignalEngine instance (generate method returns a list of trade instructions).
        run_dir: Run directory path.
        bars_per_year: Bars per year.

    Returns:
        Metrics dictionary.

    Raises:
        SystemExit: When no data is fetched.
    """
    codes = config.get("codes", [])
    start_date = config.get("start_date", "")
    end_date = config.get("end_date", "")
    initial_cash = config.get("initial_cash", 1_000_000)
    commission = config.get("commission", 0.001)
    options_cfg = config.get("options_config", {})
    risk_free_rate = options_cfg.get("risk_free_rate", 0.05)
    contract_multiplier = options_cfg.get("contract_multiplier", 1.0)
    exercise_style = options_cfg.get("exercise_style", "european")  # v2: "european" or "american"
    iv_skew = options_cfg.get("iv_skew", 0.0)         # v2: smile skew param (0 = flat)
    iv_curvature = options_cfg.get("iv_curvature", 0.0)  # v2: smile curvature

    # Load underlying data
    data_map = loader.fetch(codes, start_date, end_date)
    if not data_map:
        print(json.dumps({"error": "No data fetched"}))
        sys.exit(1)

    # Compute implied volatility (approximated by historical volatility)
    iv_map: Dict[str, pd.Series] = {}
    for code, df in data_map.items():
        iv_map[code] = historical_volatility(df["close"])

    # Generate trade signals
    signals = engine.generate(data_map)

    # Build trading date sequence
    all_dates = set()
    for df in data_map.values():
        all_dates.update(df.index)
    dates = sorted(all_dates)

    # Index signals by date
    signal_by_date: Dict[str, List[Dict[str, Any]]] = {}
    for sig in signals:
        d = sig.get("date", "")
        signal_by_date.setdefault(d, []).append(sig)

    # Day-by-day simulation
    cash = float(initial_cash)
    positions: List[OptionPosition] = []
    trade_records: List[Dict[str, Any]] = []
    greeks_records: List[Dict[str, Any]] = []
    equity_records: List[Dict[str, Any]] = []

    for current_date in dates:
        ts = pd.Timestamp(current_date)
        date_str = str(ts.date()) if hasattr(ts, "date") else str(ts)

        # 1. Get underlying price and IV for the current day
        spot_prices: Dict[str, float] = {}
        ivs: Dict[str, float] = {}
        for code, df in data_map.items():
            if ts in df.index:
                spot_prices[code] = float(df.at[ts, "close"])
                ivs[code] = float(iv_map[code].at[ts]) if ts in iv_map[code].index else 0.3
            else:
                # Use the last available price
                before = df.index[df.index <= ts]
                if len(before) > 0:
                    last = before[-1]
                    spot_prices[code] = float(df.at[last, "close"])
                    ivs[code] = float(iv_map[code].at[last]) if last in iv_map[code].index else 0.3

        # 2a. American early exercise (v2): exercise if intrinsic > continuation
        if exercise_style == "american":
            for pos in list(positions):
                if pos.is_expired(ts):
                    continue  # handled below
                spot = spot_prices.get(pos.underlying_code, 0.0)
                iv_val_ex = ivs.get(pos.underlying_code, 0.3)
                T_ex = pos.time_to_expiry(ts)
                if T_ex <= 0:
                    continue
                intrinsic = pos.intrinsic_value(spot)
                continuation = bs_price(spot, pos.strike, T_ex, risk_free_rate, iv_val_ex, pos.option_type)
                if intrinsic > 0 and intrinsic > continuation * 1.02:
                    # Early exercise is optimal
                    settlement = intrinsic * pos.qty * contract_multiplier
                    cash += settlement
                    pnl = (intrinsic - pos.entry_price) * pos.qty * contract_multiplier
                    trade_records.append({
                        "timestamp": date_str,
                        "code": pos.underlying_code,
                        "option_type": pos.option_type,
                        "strike": pos.strike,
                        "expiry": str(pos.expiry.date()),
                        "side": "early_exercise",
                        "price": round(intrinsic, 4),
                        "qty": pos.qty,
                        "pnl": round(pnl, 4),
                        "entry_date": pos.entry_date,
                    })
                    positions.remove(pos)

        # 2b. Handle expiry
        expired = [p for p in positions if p.is_expired(ts)]
        for pos in expired:
            spot = spot_prices.get(pos.underlying_code, 0.0)
            intrinsic = pos.intrinsic_value(spot)

            # Expiry: recover intrinsic value (entry_price already deducted at open)
            settlement = intrinsic * pos.qty * contract_multiplier
            cash += settlement
            pnl = (intrinsic - pos.entry_price) * pos.qty * contract_multiplier

            side = "exercise" if intrinsic > 0 else "expire"
            trade_records.append({
                "timestamp": date_str,
                "code": pos.underlying_code,
                "option_type": pos.option_type,
                "strike": pos.strike,
                "expiry": str(pos.expiry.date()),
                "side": side,
                "price": round(intrinsic, 4),
                "qty": pos.qty,
                "pnl": round(pnl, 4),
                "entry_date": pos.entry_date,
            })
            positions.remove(pos)

        # 3. Execute today's signals
        day_signals = signal_by_date.get(date_str, [])
        for sig in day_signals:
            action = sig.get("action", "")
            legs = sig.get("legs", [])
            underlying = sig.get("underlying", codes[0] if codes else "")

            spot = spot_prices.get(underlying, 0.0)
            iv_val = ivs.get(underlying, 0.3)

            for leg in legs:
                leg_type = leg.get("type", "call")
                strike = leg.get("strike", spot)
                expiry = leg.get("expiry", "")
                qty = leg.get("qty", 1)

                expiry_ts = pd.Timestamp(expiry)
                T = max((expiry_ts - ts).days / 365.0, 0.001)

                # Apply IV smile adjustment (v2) if configured
                adj_iv = iv_val
                if iv_skew != 0 or iv_curvature != 0:
                    adj_iv = iv_smile_adjustment(spot, strike, iv_val, iv_skew, iv_curvature)

                # Black-Scholes price (with smile-adjusted IV if enabled)
                opt_price = bs_price(spot, strike, T, risk_free_rate, adj_iv, leg_type)

                if action == "open":
                    # Open: long pays premium, short receives premium
                    abs_cost = opt_price * abs(qty) * contract_multiplier
                    if qty > 0:
                        cash -= abs_cost * (1 + commission)
                    else:
                        cash += abs_cost * (1 - commission)

                    positions.append(OptionPosition(
                        option_type=leg_type,
                        strike=strike,
                        expiry=expiry,
                        qty=qty,
                        entry_price=opt_price,
                        entry_date=date_str,
                        underlying_code=underlying,
                    ))

                    trade_records.append({
                        "timestamp": date_str,
                        "code": underlying,
                        "option_type": leg_type,
                        "strike": strike,
                        "expiry": expiry,
                        "side": "buy" if qty > 0 else "sell",
                        "price": round(opt_price, 4),
                        "qty": qty,
                        "pnl": 0.0,
                        "entry_date": date_str,
                    })

                elif action == "close":
                    # Close: find matching position
                    matched = _find_matching_position(
                        positions, underlying, leg_type, strike, expiry)
                    if matched:
                        pnl = (opt_price - matched.entry_price) * matched.qty * contract_multiplier
                        abs_close = opt_price * abs(matched.qty) * contract_multiplier
                        if matched.qty > 0:
                            # Long close: sell to recover
                            cash += abs_close * (1 - commission)
                        else:
                            # Short close: buy back
                            cash -= abs_close * (1 + commission)

                        trade_records.append({
                            "timestamp": date_str,
                            "code": underlying,
                            "option_type": leg_type,
                            "strike": strike,
                            "expiry": expiry,
                            "side": "close",
                            "price": round(opt_price, 4),
                            "qty": matched.qty,
                            "pnl": round(pnl, 4),
                            "entry_date": matched.entry_date,
                        })
                        positions.remove(matched)

        # 4. Compute portfolio mark-to-market value and Greeks
        portfolio_value = cash
        total_delta = 0.0
        total_gamma = 0.0
        total_theta = 0.0
        total_vega = 0.0

        for pos in positions:
            spot = spot_prices.get(pos.underlying_code, 0.0)
            iv_val = ivs.get(pos.underlying_code, 0.3)
            T = pos.time_to_expiry(ts)

            mark_price = bs_price(spot, pos.strike, T, risk_free_rate, iv_val, pos.option_type)
            portfolio_value += mark_price * pos.qty * contract_multiplier

            greeks = bs_greeks(spot, pos.strike, T, risk_free_rate, iv_val, pos.option_type)
            total_delta += greeks["delta"] * pos.qty * contract_multiplier
            total_gamma += greeks["gamma"] * pos.qty * contract_multiplier
            total_theta += greeks["theta"] * pos.qty * contract_multiplier
            total_vega += greeks["vega"] * pos.qty * contract_multiplier

        equity_records.append({
            "timestamp": date_str,
            "equity": round(portfolio_value, 4),
            "cash": round(cash, 4),
            "positions_value": round(portfolio_value - cash, 4),
        })

        greeks_records.append({
            "timestamp": date_str,
            "delta": round(total_delta, 6),
            "gamma": round(total_gamma, 6),
            "theta": round(total_theta, 6),
            "vega": round(total_vega, 6),
            "num_positions": len(positions),
        })

    # Compute metrics
    equity_df = pd.DataFrame(equity_records)
    if equity_df.empty:
        print(json.dumps({"error": "No equity data generated"}))
        sys.exit(1)

    equity_series = equity_df.set_index("timestamp")["equity"]
    metrics = _calc_options_metrics(equity_series, initial_cash, trade_records, bars_per_year)

    # Write artifacts
    out = run_dir / "artifacts"
    out.mkdir(parents=True, exist_ok=True)

    for code, df in data_map.items():
        df.to_csv(out / f"ohlcv_{code}.csv")

    equity_df.to_csv(out / "equity.csv", index=False)

    trade_cols = ["timestamp", "code", "option_type", "strike", "expiry",
                  "side", "price", "qty", "pnl", "entry_date"]
    pd.DataFrame(trade_records or [], columns=trade_cols).to_csv(
        out / "trades.csv", index=False)

    pd.DataFrame(greeks_records).to_csv(out / "greeks.csv", index=False)
    pd.DataFrame([metrics]).to_csv(out / "metrics.csv", index=False)

    from backtest.run_card import write_run_card
    write_run_card(
        run_dir,
        config,
        metrics,
        data_sources=[str(getattr(loader, "name", config.get("source", "")))],
        strategy_path=run_dir / "code" / "signal_engine.py",
        warnings=config.get("content_filter_warnings") or None,
    )

    print(json.dumps(metrics, indent=2))
    return metrics


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _find_matching_position(
    positions: List[OptionPosition],
    underlying: str,
    option_type: str,
    strike: float,
    expiry: str,
) -> Optional[OptionPosition]:
    """Find a matching open position.

    Args:
        positions: Current open positions.
        underlying: Underlying instrument code.
        option_type: Option type.
        strike: Strike price.
        expiry: Expiry date string.

    Returns:
        Matching position, or None if not found.
    """
    expiry_ts = pd.Timestamp(expiry)
    for pos in positions:
        if (pos.underlying_code == underlying
                and pos.option_type == option_type
                and abs(pos.strike - strike) < 1e-6
                and pos.expiry == expiry_ts):
            return pos
    return None


def _calc_options_metrics(
    equity: pd.Series,
    initial_cash: float,
    trades: List[Dict[str, Any]],
    bars_per_year: int = 252,
) -> Dict[str, Any]:
    """Calculate options backtest metrics.

    Args:
        equity: Equity series.
        initial_cash: Initial capital.
        trades: List of trade records.
        bars_per_year: Bars per year.

    Returns:
        Metrics dictionary.
    """
    n = len(equity)
    if n < 2:
        return {
            "final_value": initial_cash, "total_return": 0, "annual_return": 0,
            "max_drawdown": 0, "sharpe": 0, "calmar": 0, "sortino": 0,
            "trade_count": len(trades), "win_rate": 0, "profit_loss_ratio": 0,
        }

    equity_vals = equity.astype(float)
    returns = equity_vals.pct_change().fillna(0.0)

    total_ret = float(equity_vals.iloc[-1] / initial_cash - 1)
    ann_ret = float((1 + total_ret) ** (bars_per_year / max(n, 1)) - 1)

    vol = float(returns.std())
    sharpe = float(returns.mean() / (vol + 1e-10) * np.sqrt(bars_per_year))

    peak = equity_vals.cummax()
    dd = (equity_vals - peak) / peak.replace(0, 1)
    max_dd = float(dd.min())
    calmar = ann_ret / abs(max_dd) if abs(max_dd) > 1e-10 else 0.0

    downside = returns[returns < 0]
    downside_std = float(downside.std()) if len(downside) > 1 else 1e-10
    sortino = float(returns.mean() / (downside_std + 1e-10) * np.sqrt(bars_per_year))

    # Trade statistics
    closed_pnl = [t["pnl"] for t in trades if t.get("pnl", 0) != 0]
    wins = [p for p in closed_pnl if p > 0]
    losses = [p for p in closed_pnl if p < 0]
    win_rate = len(wins) / len(closed_pnl) if closed_pnl else 0.0
    avg_win = np.mean(wins) if wins else 0.0
    avg_loss = abs(np.mean(losses)) if losses else 1e-10
    pl_ratio = avg_win / avg_loss if avg_loss > 1e-10 else 0.0

    return {
        "final_value": round(float(equity_vals.iloc[-1]), 2),
        "total_return": round(total_ret, 6),
        "annual_return": round(ann_ret, 6),
        "max_drawdown": round(max_dd, 6),
        "sharpe": round(sharpe, 4),
        "calmar": round(calmar, 4),
        "sortino": round(sortino, 4),
        "trade_count": len(trades),
        "win_rate": round(win_rate, 4),
        "profit_loss_ratio": round(pl_ratio, 4),
    }
