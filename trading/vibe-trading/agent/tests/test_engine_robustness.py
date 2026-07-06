"""E2E tests for engine robustness fixes:

1. ffill(limit=5) — long suspensions stay NaN instead of using stale prices
2. All-NaN symbol detection — symbols with no data are dropped with warning
3. Single symbol exception isolation — one symbol crash doesn't kill the backtest
4. Config schema validation — invalid config gets clear pydantic error
5. Date range validation — start > end raises ValueError in all loaders
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Dict
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from backtest.engines.base import _align
from backtest.engines import base as base_engine
from backtest.engines.china_a import ChinaAEngine
from backtest.loaders.base import validate_date_range
from backtest.runner import BacktestConfigSchema


# ---------------------------------------------------------------------------
# 1. ffill(limit=5) — long gaps stay NaN
# ---------------------------------------------------------------------------


class TestFfillLimit:
    def test_short_gap_filled(self) -> None:
        """Gaps <= 5 bars should be forward-filled."""
        dates = pd.bdate_range("2025-01-01", periods=10)
        close = [100, 101, np.nan, np.nan, np.nan, 105, 106, 107, 108, 109]
        df = pd.DataFrame({"close": close, "open": close}, index=dates)
        sig = pd.Series(1.0, index=dates)

        _, close_df, _, _ = _align({"A": df}, {"A": sig}, ["A"])
        # 3-bar gap should be filled — no NaN in close
        assert close_df["A"].isna().sum() == 0

    def test_long_gap_not_filled(self) -> None:
        """Gaps > 5 bars should remain NaN (not masked by stale price)."""
        dates = pd.bdate_range("2025-01-01", periods=15)
        close = [100.0] + [np.nan] * 8 + [110.0] * 6
        df = pd.DataFrame({"close": close, "open": close}, index=dates)
        sig = pd.Series(1.0, index=dates)

        _, close_df, _, _ = _align({"A": df}, {"A": sig}, ["A"])
        # 8-bar gap: ffill covers first 5, remaining 3 should be NaN
        nan_count = close_df["A"].isna().sum()
        assert nan_count == 3, f"Expected 3 NaN bars after ffill limit=5, got {nan_count}"

    def test_all_nan_symbol_dropped(self) -> None:
        """Symbol with entirely NaN data should be dropped from alignment."""
        dates = pd.bdate_range("2025-01-01", periods=10)
        df_good = pd.DataFrame(
            {"close": np.linspace(100, 110, 10), "open": np.linspace(100, 110, 10)},
            index=dates,
        )
        df_bad = pd.DataFrame(
            {"close": [np.nan] * 10, "open": [np.nan] * 10},
            index=dates,
        )
        data_map = {"GOOD": df_good, "BAD": df_bad}
        signal_map = {
            "GOOD": pd.Series(1.0, index=dates),
            "BAD": pd.Series(1.0, index=dates),
        }

        _, close_df, pos_df, _ = _align(data_map, signal_map, ["GOOD", "BAD"])
        assert "BAD" not in close_df.columns, "All-NaN symbol should be dropped"
        assert "GOOD" in close_df.columns
        assert "BAD" not in pos_df.columns

    def test_all_symbols_nan_raises(self) -> None:
        """If ALL symbols are NaN, _align should raise ValueError."""
        dates = pd.bdate_range("2025-01-01", periods=5)
        df = pd.DataFrame({"close": [np.nan] * 5, "open": [np.nan] * 5}, index=dates)
        data_map = {"X": df}
        signal_map = {"X": pd.Series(1.0, index=dates)}

        with pytest.raises(ValueError, match="All symbols have no data"):
            _align(data_map, signal_map, ["X"])


# ---------------------------------------------------------------------------
# 2. Single symbol exception isolation
# ---------------------------------------------------------------------------


class TestSymbolIsolation:
    def test_one_symbol_error_doesnt_crash_backtest(self) -> None:
        """If rebalance fails for one symbol, other symbols still execute."""
        dates = pd.bdate_range("2025-01-01", periods=10)
        df_good = pd.DataFrame(
            {
                "close": np.linspace(10, 20, 10),
                "open": np.linspace(10, 20, 10),
                "high": np.linspace(10, 21, 10),
                "low": np.linspace(9, 19, 10),
                "volume": [1000] * 10,
            },
            index=dates,
        )
        df_bad = df_good.copy()
        data_map: Dict[str, pd.DataFrame] = {"GOOD": df_good, "BAD": df_bad}

        sig = pd.Series(0.0, index=dates)
        sig.iloc[2:] = 1.0
        signal_map = {"GOOD": sig.copy(), "BAD": sig.copy()}
        valid_codes = ["GOOD", "BAD"]

        _, close_df, target_pos, _ = _align(data_map, signal_map, valid_codes)

        engine = ChinaAEngine({"initial_cash": 1_000_000})

        # Patch _rebalance to throw for BAD only
        original_rebalance = ChinaAEngine._rebalance

        def _exploding_rebalance(self, symbol, target_weight, df, ts, equity):
            if symbol == "BAD":
                raise RuntimeError("Simulated failure for BAD")
            return original_rebalance(self, symbol, target_weight, df, ts, equity)

        with patch.object(ChinaAEngine, "_rebalance", _exploding_rebalance):
            # Should NOT raise — exception is caught internally
            engine._execute_bars(dates, data_map, close_df, target_pos, valid_codes)

        # GOOD should have traded despite BAD exploding
        assert len(engine.trades) > 0
        assert all(t.symbol == "GOOD" for t in engine.trades)

    def test_backtest_enriches_data_map_with_configured_fundamental_fields(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """A-share backtests should expose configured statement fields to strategies."""
        dates = pd.bdate_range("2024-04-01", periods=3)
        bars = pd.DataFrame(
            {
                "open": [10.0, 11.0, 12.0],
                "high": [10.5, 11.5, 12.5],
                "low": [9.5, 10.5, 11.5],
                "close": [10.2, 11.2, 12.2],
                "volume": [1000, 1100, 1200],
            },
            index=dates,
        )

        class FakeLoader:
            def fetch(self, *args, **kwargs):
                return {"000001.SZ": bars.copy()}

        class SignalEngine:
            def generate(self, data_map):
                frame = data_map["000001.SZ"]
                assert "income_total_revenue" in frame.columns
                assert frame["income_total_revenue"].iloc[-1] == 120.0
                return {"000001.SZ": pd.Series(0.0, index=frame.index)}

        def fake_enrich(data_map, provider, fields_by_table, *, as_of, periods=None):
            assert fields_by_table == {"income": ["total_revenue"]}
            assert as_of == "2024-04-30"
            enriched = {code: frame.copy() for code, frame in data_map.items()}
            enriched["000001.SZ"]["income_total_revenue"] = [None, 80.0, 120.0]
            return enriched

        monkeypatch.setattr(base_engine, "TushareFundamentalProvider", lambda: object(), raising=False)
        monkeypatch.setattr(base_engine, "enrich_price_frames_with_fundamentals", fake_enrich, raising=False)

        engine = ChinaAEngine({"initial_cash": 1_000_000})
        engine.run_backtest(
            {
                "codes": ["000001.SZ"],
                "start_date": "2024-04-01",
                "end_date": "2024-04-30",
                "source": "tushare",
                "fundamental_fields": {"income": ["total_revenue"]},
                "initial_cash": 1_000_000,
            },
            FakeLoader(),
            SignalEngine(),
            tmp_path,
        )

    def test_backtest_records_explicit_benchmark_metadata(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Explicit benchmark metadata should be added after metrics are computed."""
        dates = pd.bdate_range("2024-04-01", periods=3)
        bars = pd.DataFrame(
            {
                "open": [10.0, 11.0, 12.0],
                "high": [10.5, 11.5, 12.5],
                "low": [9.5, 10.5, 11.5],
                "close": [10.2, 11.2, 12.2],
                "volume": [1000, 1100, 1200],
            },
            index=dates,
        )

        class FakeLoader:
            def fetch(self, *args, **kwargs):
                return {"000001.SZ": bars.copy()}

        class SignalEngine:
            def generate(self, data_map):
                return {"000001.SZ": pd.Series(0.0, index=data_map["000001.SZ"].index)}

        def fake_resolve_benchmark(**kwargs):
            return SimpleNamespace(
                ticker="000300.SH",
                ret_series=pd.Series([0.0, 0.01, -0.005], index=dates),
                total_ret=0.00495,
            )

        monkeypatch.setattr("backtest.benchmark.resolve_benchmark", fake_resolve_benchmark)

        engine = ChinaAEngine({"initial_cash": 1_000_000})
        metrics = engine.run_backtest(
            {
                "codes": ["000001.SZ"],
                "start_date": "2024-04-01",
                "end_date": "2024-04-30",
                "source": "tushare",
                "benchmark": "000300.SH",
                "initial_cash": 1_000_000,
            },
            FakeLoader(),
            SignalEngine(),
            tmp_path,
        )

        assert metrics["benchmark_ticker"] == "000300.SH"
        assert metrics["benchmark_return"] == 0.00495

        run_card_path = tmp_path / "run_card.json"
        assert run_card_path.exists()
        run_card = json.loads(run_card_path.read_text(encoding="utf-8"))
        assert run_card["schema_version"] == "0.1"
        assert run_card["backtest"]["codes"] == ["000001.SZ"]
        assert run_card["data_sources"] == ["tushare"]
        assert run_card["metrics"]["benchmark_return"] == 0.00495
        assert (tmp_path / "run_card.md").exists()

    def test_configured_fundamental_enrichment_failure_is_not_silent(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Explicit statement-field requests should fail rather than degrade silently."""
        dates = pd.bdate_range("2024-04-01", periods=1)
        bars = pd.DataFrame({"close": [10.0]}, index=dates)

        def fake_enrich(*args, **kwargs):
            raise RuntimeError("provider failed")

        monkeypatch.setattr(base_engine, "TushareFundamentalProvider", lambda: object(), raising=False)
        monkeypatch.setattr(base_engine, "enrich_price_frames_with_fundamentals", fake_enrich, raising=False)

        with pytest.raises(RuntimeError, match="fundamental_fields.*provider failed"):
            base_engine._maybe_enrich_fundamentals(
                {"000001.SZ": bars},
                {
                    "end_date": "2024-04-30",
                    "fundamental_fields": {"income": ["total_revenue"]},
                },
            )


# ---------------------------------------------------------------------------
# 3. Config schema validation (pydantic)
# ---------------------------------------------------------------------------


class TestBacktestConfigSchema:
    def test_valid_config(self) -> None:
        c = BacktestConfigSchema(
            codes=["AAPL.US"],
            start_date="2025-01-01",
            end_date="2025-06-01",
        )
        assert c.codes == ["AAPL.US"]
        assert c.interval == "1D"
        assert c.engine == "daily"

    def test_fundamental_fields_must_be_table_to_field_list_mapping(self) -> None:
        with pytest.raises(ValueError, match="fundamental_fields"):
            BacktestConfigSchema(
                codes=["000001.SZ"],
                start_date="2025-01-01",
                end_date="2025-06-01",
                fundamental_fields={"income": "total_revenue"},
            )

    def test_empty_codes_rejected(self) -> None:
        with pytest.raises(Exception, match="codes must be a non-empty list"):
            BacktestConfigSchema(
                codes=[], start_date="2025-01-01", end_date="2025-06-01"
            )

    def test_empty_string_code_rejected(self) -> None:
        with pytest.raises(Exception, match="codes must not contain empty strings"):
            BacktestConfigSchema(
                codes=["AAPL.US", ""], start_date="2025-01-01", end_date="2025-06-01"
            )

    def test_reversed_dates_rejected(self) -> None:
        with pytest.raises(Exception, match="start_date.*must be <= end_date"):
            BacktestConfigSchema(
                codes=["AAPL.US"],
                start_date="2025-06-01",
                end_date="2025-01-01",
            )

    def test_invalid_date_format_rejected(self) -> None:
        with pytest.raises(Exception, match="invalid date format"):
            BacktestConfigSchema(
                codes=["AAPL.US"],
                start_date="not-a-date",
                end_date="2025-06-01",
            )

    def test_invalid_interval_rejected(self) -> None:
        with pytest.raises(Exception, match="unsupported interval"):
            BacktestConfigSchema(
                codes=["AAPL.US"],
                start_date="2025-01-01",
                end_date="2025-06-01",
                interval="3D",
            )

    def test_invalid_engine_rejected(self) -> None:
        with pytest.raises(Exception, match="unsupported engine"):
            BacktestConfigSchema(
                codes=["AAPL.US"],
                start_date="2025-01-01",
                end_date="2025-06-01",
                engine="invalid",
            )

    def test_invalid_source_rejected(self) -> None:
        with pytest.raises(Exception, match="unsupported source"):
            BacktestConfigSchema(
                codes=["AAPL.US"],
                start_date="2025-01-01",
                end_date="2025-06-01",
                source="bloomberg",
            )

    def test_mootdx_and_futu_sources_accepted(self) -> None:
        """mootdx and futu are registered loaders, so config validation must
        accept them. Regression: ``_VALID_SOURCES`` drifted and rejected both
        even though the agent-facing backtest tool already allowed them."""
        for src in ("mootdx", "futu"):
            c = BacktestConfigSchema(
                codes=["000001.SZ"],
                start_date="2025-01-01",
                end_date="2025-06-01",
                source=src,
            )
            assert c.source == src

    def test_valid_sources_covers_all_registered_loaders(self) -> None:
        """Every registered loader name must be an accepted config source, so a
        new loader can never be silently rejected by the config schema."""
        from backtest.loaders.registry import (
            LOADER_REGISTRY,
            VALID_SOURCES,
            _ensure_registered,
        )

        _ensure_registered()
        missing = set(LOADER_REGISTRY) - VALID_SOURCES
        assert not missing, f"loaders missing from VALID_SOURCES: {missing}"

    def test_extra_fields_allowed(self) -> None:
        """Config may contain engine-specific fields not in the schema."""
        c = BacktestConfigSchema(
            codes=["AAPL.US"],
            start_date="2025-01-01",
            end_date="2025-06-01",
            initial_cash=500_000,
            custom_field="whatever",
        )
        assert c.codes == ["AAPL.US"]

    def test_same_start_end_allowed(self) -> None:
        """start_date == end_date is valid (single-day backtest)."""
        c = BacktestConfigSchema(
            codes=["AAPL.US"],
            start_date="2025-03-15",
            end_date="2025-03-15",
        )
        assert c.start_date == c.end_date


# ---------------------------------------------------------------------------
# 4. Date range validation in loaders
# ---------------------------------------------------------------------------


class TestDateRangeValidation:
    def test_valid_range(self) -> None:
        validate_date_range("2025-01-01", "2025-06-01")

    def test_same_date_valid(self) -> None:
        validate_date_range("2025-03-15", "2025-03-15")

    def test_reversed_dates_raise(self) -> None:
        with pytest.raises(ValueError, match="start_date.*>.*end_date"):
            validate_date_range("2025-06-01", "2025-01-01")

    def test_invalid_date_format_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid date format"):
            validate_date_range("not-a-date", "2025-06-01")

    def test_yfinance_loader_validates_dates(self) -> None:
        """yfinance loader should raise on reversed dates before fetching."""
        from backtest.loaders.yfinance_loader import DataLoader

        loader = DataLoader()
        with pytest.raises(ValueError):
            loader.fetch(["AAPL"], "2025-06-01", "2025-01-01")

    def test_okx_loader_validates_dates(self) -> None:
        """OKX loader should raise on reversed dates before fetching."""
        from backtest.loaders.okx import DataLoader

        loader = DataLoader()
        with pytest.raises(ValueError):
            loader.fetch(["BTC-USDT"], "2025-06-01", "2025-01-01")

    def test_ccxt_loader_validates_dates(self) -> None:
        """CCXT loader should raise on reversed dates before fetching."""
        from backtest.loaders.ccxt_loader import DataLoader

        loader = DataLoader()
        with pytest.raises(ValueError):
            loader.fetch(["BTC-USDT"], "2025-06-01", "2025-01-01")

    def test_akshare_loader_validates_dates(self) -> None:
        """AKShare loader should raise on reversed dates before fetching."""
        from backtest.loaders.akshare_loader import DataLoader

        loader = DataLoader()
        with pytest.raises(ValueError):
            loader.fetch(["000001.SZ"], "2025-06-01", "2025-01-01")

    def test_tushare_loader_validates_dates(self) -> None:
        """Tushare loader should raise on reversed dates before fetching."""
        from backtest.loaders.tushare import DataLoader

        # Tushare requires TUSHARE_TOKEN at init; skip if unavailable
        import os
        if not os.getenv("TUSHARE_TOKEN"):
            pytest.skip("TUSHARE_TOKEN not set")
        loader = DataLoader()
        with pytest.raises(ValueError):
            loader.fetch(["000001.SZ"], "2025-06-01", "2025-01-01")


# ---------------------------------------------------------------------------
# 5. Integration: full backtest with bad data doesn't crash
# ---------------------------------------------------------------------------


class TestFullBacktestRobustness:
    def test_backtest_with_suspension_gap(self) -> None:
        """A stock suspended for >5 bars should not produce fake flat equity."""
        dates = pd.bdate_range("2025-01-01", periods=20)
        # Normal stock
        df_normal = pd.DataFrame(
            {
                "close": np.linspace(100, 120, 20),
                "open": np.linspace(100, 120, 20),
                "high": np.linspace(101, 121, 20),
                "low": np.linspace(99, 119, 20),
                "volume": [10000] * 20,
            },
            index=dates,
        )
        # Suspended stock: data only at start and end
        close_suspended = [50.0] * 3 + [np.nan] * 14 + [60.0] * 3
        df_suspended = pd.DataFrame(
            {
                "close": close_suspended,
                "open": close_suspended,
                "high": close_suspended,
                "low": close_suspended,
                "volume": [1000] * 3 + [0] * 14 + [1000] * 3,
            },
            index=dates,
        )
        data_map = {"NORMAL": df_normal, "SUSPENDED": df_suspended}

        sig = pd.Series(1.0, index=dates)
        signal_map = {"NORMAL": sig.copy(), "SUSPENDED": sig.copy()}
        valid_codes = ["NORMAL", "SUSPENDED"]

        _, close_df, target_pos, _ = _align(data_map, signal_map, valid_codes)

        # The 14-bar gap should not be fully filled
        suspended_nan_count = close_df["SUSPENDED"].isna().sum()
        assert suspended_nan_count >= 9, (
            f"14-bar gap with ffill(limit=5) should leave >=9 NaN, got {suspended_nan_count}"
        )

        # Engine should still complete without crashing
        engine = ChinaAEngine({"initial_cash": 1_000_000})
        engine._execute_bars(dates, data_map, close_df, target_pos, valid_codes)
        assert len(engine.equity_snapshots) == 20
