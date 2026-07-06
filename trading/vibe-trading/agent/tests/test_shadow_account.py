"""Tests for src.shadow_account (Phase 4c — M1).

Fixtures are synthesized in-test via tmp_path; no binary fixtures on disk.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

pytestmark = pytest.mark.filterwarnings(
    "ignore:Number of distinct clusters.*:UserWarning",
)

from src.shadow_account import (
    AttributionBreakdown,
    ShadowBacktestResult,
    ShadowProfile,
    ShadowRule,
    extract_shadow_profile,
    find_by_journal_hash,
    load_profile,
    render_config,
    render_shadow_report,
    render_signal_engine,
    run_shadow_backtest,
    save_profile,
    select_multi_market_codes,
    validate_generated,
    write_run_dir,
)
from src.shadow_account.models import AttributionBreakdown as _AttrCls
from src.shadow_account.extractor import MIN_PROFITABLE_ROUNDTRIPS


# ---------------- Helpers ----------------

@pytest.fixture(autouse=True)
def _offline_prices(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default every test to an offline price source.

    `_compute_features` now reaches the loader registry for price-context
    features. Without this, the suite could make real network calls in a
    connected environment (auth-free loaders like stooq/yahoo). Forcing
    `resolve_loader` to raise keeps the suite deterministic and network-free;
    extraction degrades to NaN price features exactly as in production offline.
    Tests that exercise the price path override this with a fixture loader.
    """
    from backtest.loaders.base import NoAvailableSourceError

    def _no_source(market: str):
        raise NoAvailableSourceError(f"offline test: no source for {market}")

    # Patch at the source module: `_fetch_price_history` imports `resolve_loader`
    # locally at call time, so the binding to override lives in the registry.
    monkeypatch.setattr(
        "backtest.loaders.registry.resolve_loader", _no_source,
    )


def _write_journal(path: Path, rows: list[dict]) -> Path:
    """Write a plain-utf8 Tonghuashun-style CSV the parser can ingest."""
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False, encoding="utf-8")
    return path


def _make_tonghuashun_rows(trades: list[tuple[str, str, str, float, float]]) -> list[dict]:
    """Build Tonghuashun-format rows from (datetime, symbol, side, qty, price).

    Tonghuashun requires columns: 成交时间 / 证券代码 / 操作 (see
    `trade_journal_parsers.parse_tonghuashun`).
    """
    out: list[dict] = []
    for dt_str, symbol, side, qty, price in trades:
        amount = qty * price
        out.append({
            "成交时间": dt_str,
            "证券代码": symbol,
            "证券名称": f"标的{symbol}",
            "操作": "买入" if side == "buy" else "卖出",
            "成交数量": qty,
            "成交价格": price,
            "成交金额": round(amount, 2),
            "手续费": round(amount * 0.00025, 2),
            "印花税": round(amount * 0.001, 2) if side == "sell" else 0.0,
            "过户费": 0.0,
        })
    return out


# ---------------- Fixtures ----------------

@pytest.fixture
def profitable_journal(tmp_path: Path) -> Path:
    """15 roundtrips across 5 symbols, all profitable (2% gain each)."""
    trades: list[tuple[str, str, str, float, float]] = []
    symbols = ["600519", "000001", "300750", "600036", "000858"]
    start_day = 1
    for sym in symbols:
        for i in range(3):
            buy_day = start_day + i * 4
            sell_day = buy_day + 2
            trades.append((f"2026-01-{buy_day:02d} 10:30:00", sym, "buy", 100.0, 10.0))
            trades.append((f"2026-01-{sell_day:02d} 14:15:00", sym, "sell", 100.0, 10.2))
    return _write_journal(tmp_path / "journal_profitable.csv", _make_tonghuashun_rows(trades))


@pytest.fixture
def insufficient_journal(tmp_path: Path) -> Path:
    """Only 2 profitable roundtrips — below MIN_PROFITABLE_ROUNDTRIPS."""
    trades = [
        ("2026-01-02 10:30:00", "600519", "buy", 100.0, 10.0),
        ("2026-01-04 14:15:00", "600519", "sell", 100.0, 10.5),
        ("2026-01-06 10:30:00", "000001", "buy", 100.0, 20.0),
        ("2026-01-08 14:15:00", "000001", "sell", 100.0, 20.5),
    ]
    return _write_journal(tmp_path / "journal_few.csv", _make_tonghuashun_rows(trades))


@pytest.fixture
def no_roundtrips_journal(tmp_path: Path) -> Path:
    """Only buys, no sells — zero roundtrips."""
    trades = [
        ("2026-01-02 10:30:00", "600519", "buy", 100.0, 10.0),
        ("2026-01-04 10:30:00", "000001", "buy", 50.0, 20.0),
    ]
    return _write_journal(tmp_path / "journal_nort.csv", _make_tonghuashun_rows(trades))


# ---------------- extract_shadow_profile ----------------

@pytest.mark.unit
def test_extract_profile_happy_path(profitable_journal: Path) -> None:
    profile = extract_shadow_profile(profitable_journal)
    assert isinstance(profile, ShadowProfile)
    assert profile.profitable_roundtrips >= MIN_PROFITABLE_ROUNDTRIPS
    assert profile.total_roundtrips == profile.profitable_roundtrips  # all profitable
    assert profile.source_market == "china_a"
    assert profile.shadow_id.startswith("shadow_")
    assert profile.journal_hash and len(profile.journal_hash) == 40
    assert profile.typical_holding_days[0] > 0
    assert profile.profile_text  # non-empty portrait


@pytest.mark.unit
def test_extract_profile_yields_rules(profitable_journal: Path) -> None:
    from src.shadow_account.extractor import RULE_TEXT_MAX

    profile = extract_shadow_profile(profitable_journal, min_support=2, max_rules=5)
    assert 1 <= len(profile.rules) <= 5
    for rule in profile.rules:
        assert isinstance(rule, ShadowRule)
        assert rule.rule_id.startswith("R")
        assert rule.human_text  # non-empty natural language
        assert len(rule.human_text) <= RULE_TEXT_MAX
        assert rule.human_text.isascii(), f"rule text must be English-only: {rule.human_text!r}"
        assert rule.support_count >= 2
        assert 0.0 < rule.coverage_rate <= 1.0
        lo, hi = rule.holding_days_range
        assert lo >= 1 and hi >= lo


@pytest.mark.unit
def test_extract_profile_rejects_insufficient_sample(insufficient_journal: Path) -> None:
    with pytest.raises(ValueError, match="Insufficient profitable roundtrips"):
        extract_shadow_profile(insufficient_journal)


@pytest.mark.unit
def test_extract_profile_rejects_no_roundtrips(no_roundtrips_journal: Path) -> None:
    with pytest.raises(ValueError, match="No complete buy"):
        extract_shadow_profile(no_roundtrips_journal)


@pytest.mark.unit
def test_extract_profile_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        extract_shadow_profile(tmp_path / "does_not_exist.csv")


@pytest.mark.unit
def test_custom_llm_translator_is_used(profitable_journal: Path) -> None:
    calls: list[dict] = []

    def fake_translator(ctx: dict) -> str:
        calls.append(ctx)
        return "Custom shadow rule text"

    profile = extract_shadow_profile(profitable_journal, llm_translator=fake_translator)
    assert calls, "translator should be invoked at least once"
    assert all(rule.human_text == "Custom shadow rule text" for rule in profile.rules)


# ---------------- Storage round-trip ----------------

@pytest.mark.unit
def test_profile_roundtrip_persistence(
    profitable_journal: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))  # Windows
    profile = extract_shadow_profile(profitable_journal)

    saved_path = save_profile(profile)
    assert saved_path.exists()

    loaded = load_profile(profile.shadow_id)
    assert loaded.shadow_id == profile.shadow_id
    assert loaded.journal_hash == profile.journal_hash
    assert len(loaded.rules) == len(profile.rules)
    assert loaded.rules[0].rule_id == profile.rules[0].rule_id
    assert loaded.preferred_markets == profile.preferred_markets


@pytest.mark.unit
def test_find_by_journal_hash_returns_latest(
    profitable_journal: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    first = extract_shadow_profile(profitable_journal)
    save_profile(first)

    found = find_by_journal_hash(first.journal_hash)
    assert found is not None
    assert found.shadow_id == first.shadow_id
    assert find_by_journal_hash("nonexistent-hash") is None


# ---------------- M2: Codegen ----------------

@pytest.mark.unit
def test_render_signal_engine_produces_valid_python(profitable_journal: Path) -> None:
    profile = extract_shadow_profile(profitable_journal)
    source = render_signal_engine(profile)

    ok, err = validate_generated(source)
    assert ok, f"generated source failed validation: {err}"
    assert "class SignalEngine" in source
    assert profile.shadow_id in source
    assert "def generate" in source


@pytest.mark.unit
def test_validate_generated_rejects_missing_class() -> None:
    ok, err = validate_generated("x = 1\n")
    assert not ok
    assert "SignalEngine" in err


@pytest.mark.unit
def test_validate_generated_rejects_syntax_error() -> None:
    ok, err = validate_generated("class SignalEngine\n  def generate(self, d): pass\n")
    assert not ok
    assert "SyntaxError" in err


@pytest.mark.unit
def test_generated_engine_runs_on_mock_data_map(profitable_journal: Path) -> None:
    """The rendered engine must execute cleanly against a minimal data_map."""
    import importlib.util

    profile = extract_shadow_profile(profitable_journal)
    source = render_signal_engine(profile)

    module_path = Path("./_shadow_test_engine.py").resolve()
    # Use tmp via test's temp dir proxy — write + exec.
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "signal_engine.py"
        path.write_text(source, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("gen_signal_engine", path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        engine = module.SignalEngine()

        idx = pd.date_range("2026-01-02", periods=30, freq="B")
        data_map = {
            "600519.SH": pd.DataFrame({"close": range(30)}, index=idx),
            "AAPL": pd.DataFrame({"close": range(30)}, index=idx),
        }
        signals = engine.generate(data_map)
        assert set(signals.keys()) == set(data_map.keys())
        for code, series in signals.items():
            assert isinstance(series, pd.Series)
            assert len(series) == len(idx)
            assert (series >= 0).all()


@pytest.mark.unit
def test_render_config_shape(profitable_journal: Path) -> None:
    profile = extract_shadow_profile(profitable_journal)
    cfg = render_config(
        profile,
        codes=["600519.SH", "AAPL"],
        start_date="2026-01-01",
        end_date="2026-06-30",
    )
    assert cfg["source"] == "auto"
    assert cfg["engine"] == "daily"
    assert cfg["codes"] == ["600519.SH", "AAPL"]
    assert cfg["shadow_id"] == profile.shadow_id


@pytest.mark.unit
def test_write_run_dir_materializes_files(
    profitable_journal: Path, tmp_path: Path,
) -> None:
    profile = extract_shadow_profile(profitable_journal)
    run_dir = write_run_dir(
        profile,
        tmp_path / "run",
        codes=["600519.SH"],
        start_date="2026-01-01",
        end_date="2026-06-30",
    )
    assert (run_dir / "code" / "signal_engine.py").exists()
    assert (run_dir / "config.json").exists()
    cfg = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    assert cfg["shadow_id"] == profile.shadow_id


# ---------------- M3: Backtester + Attribution ----------------

@pytest.mark.unit
def test_select_multi_market_codes_covers_all_markets(profitable_journal: Path) -> None:
    profile = extract_shadow_profile(profitable_journal)
    selection = select_multi_market_codes(profile, per_market_count=3)
    assert set(selection.keys()) == {"china_a", "hk", "us", "crypto"}
    for market, codes in selection.items():
        assert 1 <= len(codes) <= 3
        assert all(codes)


@pytest.mark.unit
def test_run_shadow_backtest_with_mocked_runner(
    profitable_journal: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Inject a stub run_backtest_fn that writes artifacts the parser can read."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    profile = extract_shadow_profile(profitable_journal)

    def stub_run_backtest(run_dir_str: str) -> str:
        run_path = Path(run_dir_str)
        artifacts_dir = run_path / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        metrics_path = artifacts_dir / "metrics.json"
        metrics_path.write_text(json.dumps({
            "total_return_abs": 12_345.0,
            "sharpe": 1.5,
            "max_drawdown": -0.12,
            "win_rate": 0.55,
        }), encoding="utf-8")
        equity_path = artifacts_dir / "equity.csv"
        equity_path.write_text(
            "date,equity\n2026-01-02,1000000\n2026-06-30,1012345\n",
            encoding="utf-8",
        )
        return json.dumps({
            "status": "ok",
            "exit_code": 0,
            "artifacts": {
                "metrics.json": str(metrics_path),
                "equity.csv": str(equity_path),
            },
        })

    result = run_shadow_backtest(
        profile,
        window_start="2026-01-01",
        window_end="2026-06-30",
        journal_path=profitable_journal,
        run_backtest_fn=stub_run_backtest,
    )
    assert isinstance(result, ShadowBacktestResult)
    assert result.shadow_id == profile.shadow_id
    assert set(result.per_market.keys()) == {"china_a", "hk", "us", "crypto"}
    assert result.combined["total_return_abs"] == 12_345.0
    assert result.combined["sharpe"] == 1.5
    assert result.shadow_total_pnl == 12_345.0
    assert result.real_total_pnl > 0  # all profitable test data
    assert result.delta_pnl == round(result.shadow_total_pnl - result.real_total_pnl, 2)
    assert isinstance(result.attribution, AttributionBreakdown)
    assert len(result.equity_curves["combined"]) == 2


@pytest.mark.unit
def test_run_shadow_backtest_handles_runner_failure(
    profitable_journal: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    profile = extract_shadow_profile(profitable_journal)

    def failing_runner(run_dir_str: str) -> str:
        return json.dumps({
            "status": "error",
            "exit_code": 1,
            "stderr": "No data fetched",
            "artifacts": {},
        })

    result = run_shadow_backtest(
        profile,
        window_start="2026-01-01",
        window_end="2026-06-30",
        run_backtest_fn=failing_runner,
    )
    assert result.combined.get("error")
    assert result.shadow_total_pnl == 0.0
    assert result.equity_curves == {}


# ---------------- M4: Reporter ----------------

def _stub_backtest_result(profile: ShadowProfile) -> ShadowBacktestResult:
    return ShadowBacktestResult(
        shadow_id=profile.shadow_id,
        per_market={
            "china_a": {"sharpe": 1.2, "annual_return": 0.15, "max_drawdown": -0.08},
            "us": {"sharpe": 0.9, "annual_return": 0.11, "max_drawdown": -0.10},
        },
        combined={"sharpe": 1.05, "annual_return": 0.13, "max_drawdown": -0.09},
        equity_curves={"combined": [("2026-01-02", 1_000_000.0), ("2026-06-30", 1_130_000.0)]},
        attribution=AttributionBreakdown(
            missed_signals_pnl=50.0,
            noise_trades_pnl=-120.0,
            early_exit_pnl=80.0,
            late_exit_pnl=-20.0,
            overtrading_pnl=10.0,
            counterfactual_trades=(
                {
                    "symbol": "600519.SH", "buy_dt": "2026-02-01", "sell_dt": "2026-02-02",
                    "hold_days": 1.0, "pnl": 100.0, "impact": 50.0, "reason": "early_exit",
                },
            ),
        ),
        shadow_total_pnl=1500.0,
        real_total_pnl=1200.0,
        delta_pnl=300.0,
    )


@pytest.mark.unit
def test_render_shadow_report_emits_html(profitable_journal: Path, tmp_path: Path) -> None:
    profile = extract_shadow_profile(profitable_journal)
    result = _stub_backtest_result(profile)

    out = render_shadow_report(profile, result, output_dir=tmp_path)
    html_path = Path(out["html_path"])
    assert html_path.exists()
    content = html_path.read_text(encoding="utf-8")
    assert "Shadow Account" in content
    assert profile.shadow_id in content
    assert "Delta Attribution" in content  # Section 5
    assert "Counterfactual" in content      # Section 6
    assert out["engine"] in ("weasyprint", "html-only")


@pytest.mark.unit
def test_render_shadow_report_includes_today_signals(
    profitable_journal: Path, tmp_path: Path,
) -> None:
    profile = extract_shadow_profile(profitable_journal)
    result = _stub_backtest_result(profile)
    signals = [
        {"symbol": "NVDA", "market": "us", "rule_id": "R1", "reason": "匹配影子规则"},
    ]
    out = render_shadow_report(profile, result, today_signals=signals, output_dir=tmp_path)
    content = Path(out["html_path"]).read_text(encoding="utf-8")
    assert "NVDA" in content
    assert out["sections"]["today_signals"] == signals


@pytest.mark.unit
def test_render_shadow_report_handles_empty_equity(
    profitable_journal: Path, tmp_path: Path,
) -> None:
    profile = extract_shadow_profile(profitable_journal)
    result = ShadowBacktestResult(
        shadow_id=profile.shadow_id,
        per_market={}, combined={}, equity_curves={},
        attribution=AttributionBreakdown(
            missed_signals_pnl=0.0, noise_trades_pnl=0.0, early_exit_pnl=0.0,
            late_exit_pnl=0.0, overtrading_pnl=0.0, counterfactual_trades=(),
        ),
        shadow_total_pnl=0.0, real_total_pnl=0.0, delta_pnl=0.0,
    )
    out = render_shadow_report(profile, result, output_dir=tmp_path)
    assert Path(out["html_path"]).exists()
    # Section 6 should degrade gracefully when no counterfactuals exist.
    assert "No material counterfactual" in Path(out["html_path"]).read_text(encoding="utf-8")


# ---------------- M5/M6: Tool wrappers + scanner ----------------

@pytest.mark.unit
def test_shadow_tools_are_auto_discovered() -> None:
    from src.tools import build_registry

    registry = build_registry()
    for expected in (
        "extract_shadow_strategy",
        "run_shadow_backtest",
        "render_shadow_report",
        "scan_shadow_signals",
    ):
        assert expected in registry.tool_names, f"{expected} missing from registry"


@pytest.mark.unit
def test_extract_shadow_strategy_tool(
    profitable_journal: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.tools.shadow_account_tool import ExtractShadowStrategyTool

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("VIBE_TRADING_ALLOWED_FILE_ROOTS", str(tmp_path))
    tool = ExtractShadowStrategyTool()
    out = json.loads(tool.execute(journal_path=str(profitable_journal)))
    assert out["status"] == "ok"
    assert out["shadow_id"].startswith("shadow_")
    assert len(out["rules"]) >= 1
    from src.shadow_account.extractor import RULE_TEXT_MAX
    assert 1 <= len(out["rules"][0]["human_text"]) <= RULE_TEXT_MAX

    # Persistence happened — we can load it back.
    loaded = load_profile(out["shadow_id"])
    assert loaded.shadow_id == out["shadow_id"]


@pytest.mark.unit
def test_extract_shadow_strategy_tool_reports_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.tools.shadow_account_tool import ExtractShadowStrategyTool

    monkeypatch.setenv("VIBE_TRADING_ALLOWED_FILE_ROOTS", str(tmp_path))
    tool = ExtractShadowStrategyTool()
    out = json.loads(tool.execute(journal_path=str(tmp_path / "missing.csv")))
    assert out["status"] == "error"
    assert "error" in out


@pytest.mark.unit
def test_scan_shadow_signals_tool(
    profitable_journal: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.tools.shadow_account_tool import ScanShadowSignalsTool

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    profile = extract_shadow_profile(profitable_journal)
    save_profile(profile)
    tool = ScanShadowSignalsTool()
    out = json.loads(tool.execute(shadow_id=profile.shadow_id, date="2026-04-18"))
    assert out["status"] == "ok"
    assert out["disclaimer"]
    assert isinstance(out["matches"], list)


@pytest.mark.unit
def test_run_shadow_backtest_tool_handles_missing_id() -> None:
    from src.tools.shadow_account_tool import RunShadowBacktestTool

    out = json.loads(RunShadowBacktestTool().execute(shadow_id="shadow_unknown"))
    assert out["status"] == "error"


@pytest.mark.unit
def test_shadow_account_skill_shipped() -> None:
    skill = Path(__file__).resolve().parents[1] / "src" / "skills" / "shadow-account" / "SKILL.md"
    assert skill.exists()
    body = skill.read_text(encoding="utf-8")
    for needle in ("shadow-account", "extract_shadow_strategy", "run_shadow_backtest", "render_shadow_report", "scan_shadow_signals"):
        assert needle in body, f"skill missing reference to {needle}"


@pytest.mark.unit
def test_context_prompt_references_shadow_account() -> None:
    from src.agent.context import _SYSTEM_PROMPT  # noqa: SLF001 — intentional peek

    assert "Shadow Account" in _SYSTEM_PROMPT
    assert "extract_shadow_strategy" in _SYSTEM_PROMPT
    assert "Phase 4b" not in _SYSTEM_PROMPT  # stale note should be gone


@pytest.mark.unit
def test_attribution_is_zero_without_journal(
    profitable_journal: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    profile = extract_shadow_profile(profitable_journal)

    def stub_runner(run_dir_str: str) -> str:
        metrics_path = Path(run_dir_str) / "metrics.json"
        metrics_path.write_text(json.dumps({"total_return_abs": 0.0}), encoding="utf-8")
        return json.dumps({
            "status": "ok",
            "exit_code": 0,
            "artifacts": {"metrics.json": str(metrics_path)},
        })

    result = run_shadow_backtest(
        profile,
        window_start="2026-01-01",
        window_end="2026-06-30",
        journal_path=None,  # disable attribution
        run_backtest_fn=stub_runner,
    )
    assert result.attribution.noise_trades_pnl == 0.0
    assert result.real_total_pnl == 0.0
    assert result.attribution.counterfactual_trades == ()


# ---------------- Price-context features (as-of buy_dt) ----------------

from src.shadow_account.extractor import (  # noqa: E402
    _MARKET_KEY_MAP,
    _attach_price_features,
    _compute_rsi,
    _price_features_as_of,
    _promoted_numeric_features,
)


def _price_frame(dates: list[str], closes: list[float]) -> pd.DataFrame:
    """Build a tz-naive trade_date-indexed OHLCV frame like a loader returns."""
    idx = pd.to_datetime(dates)
    return pd.DataFrame(
        {
            "open": closes,
            "high": [c * 1.01 for c in closes],
            "low": [c * 0.99 for c in closes],
            "close": closes,
            "volume": [1_000_000] * len(closes),
        },
        index=pd.DatetimeIndex(idx, name="trade_date"),
    )


class _FixtureLoader:
    """Minimal loader returning a fixed frame for any requested symbol."""

    def __init__(self, frame: pd.DataFrame) -> None:
        self._frame = frame

    def fetch(self, codes, start_date, end_date, *, interval="1D", fields=None):
        # Mirror real loaders: only return bars within [start, end].
        lo, hi = pd.Timestamp(start_date), pd.Timestamp(end_date)
        sliced = self._frame.loc[lo:hi]
        return {code: sliced.copy() for code in codes}


@pytest.fixture
def with_price_loader(monkeypatch: pytest.MonkeyPatch):
    """Override the offline default with a fixture loader the test controls."""

    def _install(frame: pd.DataFrame) -> None:
        loader = _FixtureLoader(frame)
        monkeypatch.setattr(
            "backtest.loaders.registry.resolve_loader", lambda market: loader,
        )

    return _install


@pytest.mark.unit
def test_compute_rsi_is_causal_and_bounded() -> None:
    rising = pd.Series(range(1, 40), dtype=float)
    rsi = _compute_rsi(rising)
    assert rsi.isna().sum() == 14  # warmup window
    assert 99.0 <= float(rsi.iloc[-1]) <= 100.0  # monotonic up → RSI ~100
    # Causality: truncating future bars does not change an earlier RSI value.
    at_20_full = float(_compute_rsi(rising).iloc[20])
    at_20_trunc = float(_compute_rsi(rising.iloc[:21]).iloc[-1])
    assert at_20_full == pytest.approx(at_20_trunc)


@pytest.mark.unit
def test_price_features_as_of_reads_only_past_bars() -> None:
    dates = [f"2026-02-{d:02d}" for d in range(1, 21)]
    closes = [10.0 + 0.1 * i for i in range(20)]  # steadily rising
    frame = _price_frame(dates, closes)
    buy_dt = pd.Timestamp("2026-02-20 10:30:00")

    feats = _price_features_as_of(frame, buy_dt)
    assert not pd.isna(feats["entry_rsi14"])
    # prior_5d_return over a +0.1/step ramp ending at 11.9 vs 5 steps back (11.4)
    assert feats["prior_5d_return"] == pytest.approx((11.9 - 11.4) / 11.4, rel=1e-6)


@pytest.mark.unit
def test_price_features_no_lookahead_past_buy_dt() -> None:
    """Appending bars dated after buy_dt must not change feature values."""
    dates = [f"2026-02-{d:02d}" for d in range(1, 21)]
    closes = [10.0 + 0.1 * i for i in range(20)]
    buy_dt = pd.Timestamp("2026-02-20 10:30:00")

    base = _price_features_as_of(_price_frame(dates, closes), buy_dt)

    future_dates = dates + [f"2026-02-{d:02d}" for d in range(21, 26)]
    future_closes = closes + [99.0, 1.0, 99.0, 1.0, 99.0]  # wild future moves
    extended = _price_features_as_of(_price_frame(future_dates, future_closes), buy_dt)

    assert extended["entry_rsi14"] == pytest.approx(base["entry_rsi14"])
    assert extended["prior_5d_return"] == pytest.approx(base["prior_5d_return"])


@pytest.mark.unit
def test_price_features_tz_aware_buy_dt_does_not_raise() -> None:
    dates = [f"2026-02-{d:02d}" for d in range(1, 21)]
    closes = [10.0 + 0.1 * i for i in range(20)]
    frame = _price_frame(dates, closes)

    naive = _price_features_as_of(frame, pd.Timestamp("2026-02-20 10:30:00"))
    aware = _price_features_as_of(
        frame, pd.Timestamp("2026-02-20 10:30:00", tz="Asia/Shanghai"),
    )
    assert aware["entry_rsi14"] == pytest.approx(naive["entry_rsi14"])
    assert aware["prior_5d_return"] == pytest.approx(naive["prior_5d_return"])


@pytest.mark.unit
def test_price_features_insufficient_history_is_nan() -> None:
    frame = _price_frame(["2026-02-01", "2026-02-02", "2026-02-03"], [10.0, 10.1, 10.2])
    feats = _price_features_as_of(frame, pd.Timestamp("2026-02-03"))
    assert pd.isna(feats["entry_rsi14"])  # <14 closes
    assert pd.isna(feats["prior_5d_return"])  # <6 closes


@pytest.mark.unit
def test_attach_price_features_unmapped_market_is_nan() -> None:
    rows = [{"symbol": "X", "market": "other", "buy_dt": pd.Timestamp("2026-02-20")}]
    _attach_price_features(rows)  # "other" has no registry mapping → no fetch
    assert pd.isna(rows[0]["entry_rsi14"])
    assert pd.isna(rows[0]["prior_5d_return"])


@pytest.mark.unit
def test_extract_with_price_features_promotes_into_clustering(
    profitable_journal: Path, with_price_loader, monkeypatch: pytest.MonkeyPatch,
) -> None:
    # 60 daily bars so RSI(14) + prior-5d are well-defined as-of every buy_dt.
    dates = pd.bdate_range("2025-12-01", periods=60).strftime("%Y-%m-%d").tolist()
    closes = [10.0 + 0.05 * i for i in range(60)]
    with_price_loader(_price_frame(dates, closes))

    # Capture what `_compute_features` produced and which numeric features the
    # clusterer was actually handed — a rule count alone can't prove promotion.
    import src.shadow_account.extractor as extractor

    captured: dict[str, object] = {}
    orig_features = extractor._compute_features
    orig_cluster = extractor._auto_cluster

    def spy_features(roundtrips, trades_df):
        df = orig_features(roundtrips, trades_df)
        captured["features_df"] = df
        return df

    def spy_cluster(features_df, *, max_k, numeric_features=extractor._NUMERIC_FEATURES):
        captured["numeric_features"] = numeric_features
        return orig_cluster(
            features_df, max_k=max_k, numeric_features=numeric_features,
        )

    monkeypatch.setattr(extractor, "_compute_features", spy_features)
    monkeypatch.setattr(extractor, "_auto_cluster", spy_cluster)

    profile = extract_shadow_profile(profitable_journal, min_support=2)
    assert isinstance(profile, ShadowProfile)
    assert len(profile.rules) >= 1

    # Price columns were actually attached and populated (not all-NaN)...
    fdf = captured["features_df"]
    assert "entry_rsi14" in fdf.columns and "prior_5d_return" in fdf.columns
    assert fdf["entry_rsi14"].notna().any()
    assert fdf["prior_5d_return"].notna().any()
    # ...and both were promoted into the clustering feature set.
    numeric = captured["numeric_features"]
    assert "entry_rsi14" in numeric
    assert "prior_5d_return" in numeric


@pytest.mark.unit
def test_sparse_price_features_fall_back_to_journal_only(
    profitable_journal: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With prices offline (autouse), promotion is skipped and rules still form."""
    import src.shadow_account.extractor as extractor

    captured: dict[str, object] = {}
    orig_cluster = extractor._auto_cluster

    def spy_cluster(features_df, *, max_k, numeric_features=extractor._NUMERIC_FEATURES):
        captured["numeric_features"] = numeric_features
        return orig_cluster(
            features_df, max_k=max_k, numeric_features=numeric_features,
        )

    monkeypatch.setattr(extractor, "_auto_cluster", spy_cluster)

    profile = extract_shadow_profile(profitable_journal, min_support=2)
    assert len(profile.rules) >= 1
    # No price source → no price feature promoted → journal-only clustering.
    assert tuple(captured["numeric_features"]) == extractor._NUMERIC_FEATURES


@pytest.mark.unit
def test_promoted_features_threshold() -> None:
    df = pd.DataFrame({
        "holding_days": [1.0, 2.0, 3.0, 4.0],
        "pnl_pct": [0.1, 0.2, 0.1, 0.2],
        "entry_hour": [10, 11, 10, 11],
        "entry_weekday": [1, 2, 3, 4],
        "entry_rsi14": [55.0, 60.0, float("nan"), float("nan")],  # 2 present
        "prior_5d_return": [0.01, 0.02, 0.03, 0.04],  # 4 present
    })
    promoted = _promoted_numeric_features(df, min_support=3)
    assert "prior_5d_return" in promoted  # 4 >= 3
    assert "entry_rsi14" not in promoted  # 2 < 3
    assert set(_MARKET_KEY_MAP) == {"china_a", "us", "hk", "crypto"}


@pytest.mark.unit
def test_single_cluster_fallback_carries_price_bounds() -> None:
    """The degenerate single-rule path must still emit RSI/return bounds.

    Regression for PR #314 review: ``_heuristic_single_rule`` previously called
    ``_cluster_to_rule`` without ``price_features``, so small/homogeneous
    journals (len < min_support) silently produced behavior-only rules even
    when price data was present.
    """
    from src.shadow_account.extractor import _extract_rules

    df = pd.DataFrame({
        "market": ["us", "us", "us"],
        "holding_days": [3.0, 4.0, 5.0],
        "entry_hour": [10, 11, 10],
        "symbol": ["AAPL", "MSFT", "NVDA"],
        "buy_dt": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03"]),
        "entry_rsi14": [55.0, 60.0, 65.0],
        "prior_5d_return": [0.01, 0.02, 0.03],
    })

    # min_support above len(df) forces the len < min_support fallback branch.
    rules = _extract_rules(df, min_support=10, max_rules=3, llm_translator=None)

    assert len(rules) == 1
    entry = rules[0].entry_condition
    assert isinstance(entry.get("entry_rsi14"), dict)
    assert isinstance(entry.get("prior_5d_return"), dict)
    assert entry["entry_rsi14"]["min"] <= entry["entry_rsi14"]["max"]


@pytest.mark.unit
def test_codegen_and_extractor_share_price_feature_names() -> None:
    """codegen must read the same price-feature names the extractor writes.

    Both now source ``PRICE_FEATURES`` from ``models`` instead of repeating a
    literal tuple, so a single edit cannot leave one side stale.
    """
    from src.shadow_account import codegen, extractor
    from src.shadow_account.models import PRICE_FEATURES

    assert extractor._PRICE_FEATURES is PRICE_FEATURES
    # codegen flattens exactly these features' bounds — guard against drift.
    rule = ShadowRule(
        rule_id="R1",
        human_text="x",
        entry_condition={
            "market": "us",
            "entry_hour": {"min": 9, "max": 11},
            **{f: {"min": 1.0, "max": 2.0} for f in PRICE_FEATURES},
        },
        exit_condition={"holding_days": {"min": 2, "max": 5}},
        holding_days_range=(2, 5),
        support_count=5,
        coverage_rate=0.5,
        sample_trades=("AAPL@2026-01-01",),
    )
    ctx = codegen._rule_to_context(rule)
    for feature in PRICE_FEATURES:
        assert f"{feature}_min" in ctx and f"{feature}_max" in ctx


@pytest.mark.unit
def test_price_bounds_keep_four_decimal_precision() -> None:
    """Small ``prior_5d_return`` bounds must survive rounding.

    Regression for PR #314 review nit: ``round(.,2)`` collapsed return-type
    bounds (e.g. 0.0123 → 0.01); the extractor now rounds price-feature bounds
    to 4 decimals.
    """
    from src.shadow_account.extractor import _extract_rules

    df = pd.DataFrame({
        "market": ["us"] * 4,
        "holding_days": [3.0, 4.0, 5.0, 6.0],
        "entry_hour": [10, 11, 10, 11],
        "symbol": ["AAPL", "MSFT", "NVDA", "AMZN"],
        "buy_dt": pd.to_datetime(
            ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"]
        ),
        "prior_5d_return": [0.0123, 0.0156, 0.0188, 0.0211],
    })

    rules = _extract_rules(df, min_support=10, max_rules=1, llm_translator=None)
    bounds = rules[0].entry_condition["prior_5d_return"]
    # At 2 decimals both would round to 0.01/0.02; 4-decimal keeps them distinct.
    assert bounds["min"] != round(bounds["min"], 2) or bounds["max"] != round(bounds["max"], 2)
    assert bounds["min"] == round(bounds["min"], 4)
    assert bounds["max"] == round(bounds["max"], 4)


# ---- Degradation branches in the price-fetch / attach path ----

from src.shadow_account.extractor import (  # noqa: E402
    _auto_cluster,
    _fetch_price_history,
)


@pytest.mark.unit
def test_fetch_price_history_symbol_absent_from_map(monkeypatch: pytest.MonkeyPatch) -> None:
    """Loader available but returns no entry for the requested symbol → None."""

    class _EmptyMapLoader:
        def fetch(self, codes, start_date, end_date, *, interval="1D", fields=None):
            return {}  # symbol not present

    monkeypatch.setattr(
        "backtest.loaders.registry.resolve_loader", lambda market: _EmptyMapLoader(),
    )
    out = _fetch_price_history(
        "600519", "china_a",
        start=pd.Timestamp("2026-01-01"), end=pd.Timestamp("2026-02-01"),
    )
    assert out is None


@pytest.mark.unit
def test_fetch_price_history_empty_frame(monkeypatch: pytest.MonkeyPatch) -> None:
    """Loader returns an empty frame for the symbol → None."""

    class _EmptyFrameLoader:
        def fetch(self, codes, start_date, end_date, *, interval="1D", fields=None):
            return {c: pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
                    for c in codes}

    monkeypatch.setattr(
        "backtest.loaders.registry.resolve_loader", lambda market: _EmptyFrameLoader(),
    )
    out = _fetch_price_history(
        "600519", "china_a",
        start=pd.Timestamp("2026-01-01"), end=pd.Timestamp("2026-02-01"),
    )
    assert out is None


@pytest.mark.unit
def test_fetch_price_history_loader_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """A loader that raises mid-fetch degrades to None, never propagates."""

    class _BoomLoader:
        def fetch(self, codes, start_date, end_date, *, interval="1D", fields=None):
            raise RuntimeError("network down")

    monkeypatch.setattr(
        "backtest.loaders.registry.resolve_loader", lambda market: _BoomLoader(),
    )
    out = _fetch_price_history(
        "600519", "china_a",
        start=pd.Timestamp("2026-01-01"), end=pd.Timestamp("2026-02-01"),
    )
    assert out is None


@pytest.mark.unit
def test_attach_price_features_batches_one_fetch_per_symbol(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two roundtrips on the same symbol trigger exactly one loader fetch."""
    dates = pd.bdate_range("2025-12-01", periods=60).strftime("%Y-%m-%d").tolist()
    frame = _price_frame(dates, [10.0 + 0.05 * i for i in range(60)])

    calls: list[list[str]] = []

    class _CountingLoader:
        def fetch(self, codes, start_date, end_date, *, interval="1D", fields=None):
            calls.append(list(codes))
            lo, hi = pd.Timestamp(start_date), pd.Timestamp(end_date)
            return {c: frame.loc[lo:hi].copy() for c in codes}

    monkeypatch.setattr(
        "backtest.loaders.registry.resolve_loader", lambda market: _CountingLoader(),
    )
    rows = [
        {"symbol": "600519", "market": "china_a", "buy_dt": pd.Timestamp("2026-02-10")},
        {"symbol": "600519", "market": "china_a", "buy_dt": pd.Timestamp("2026-02-20")},
    ]
    _attach_price_features(rows)
    assert len(calls) == 1  # one symbol → one fetch despite two roundtrips
    assert all(not pd.isna(r["entry_rsi14"]) for r in rows)


@pytest.mark.unit
def test_auto_cluster_median_imputes_partial_nan() -> None:
    """A promoted feature with some NaN rows is median-imputed, not crashed."""
    df = pd.DataFrame({
        "holding_days": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        "pnl_pct": [0.1, 0.2, 0.1, 0.2, 0.1, 0.2],
        "entry_hour": [10, 11, 10, 11, 10, 11],
        "entry_weekday": [1, 2, 3, 4, 0, 1],
        "prior_5d_return": [0.01, 0.02, float("nan"), 0.04, 0.05, float("nan")],
    })
    labels = _auto_cluster(
        df, max_k=3,
        numeric_features=("holding_days", "pnl_pct", "entry_hour",
                          "entry_weekday", "prior_5d_return"),
    )
    # No exception (NaN would crash StandardScaler/KMeans); one label per row.
    assert len(labels) == len(df)


@pytest.mark.unit
def test_auto_cluster_all_nan_feature_is_dropped() -> None:
    """An all-NaN promoted column is dropped, leaving journal features to cluster."""
    df = pd.DataFrame({
        "holding_days": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        "pnl_pct": [0.1, 0.2, 0.1, 0.2, 0.1, 0.2],
        "entry_hour": [10, 11, 10, 11, 10, 11],
        "entry_weekday": [1, 2, 3, 4, 0, 1],
        "entry_rsi14": [float("nan")] * 6,  # all NaN
    })
    labels = _auto_cluster(
        df, max_k=3,
        numeric_features=("holding_days", "pnl_pct", "entry_hour",
                          "entry_weekday", "entry_rsi14"),
    )
    assert len(labels) == len(df)


# ---- M4: Price conditions in extracted rules ----


@pytest.mark.unit
def test_extracted_rules_carry_price_condition_bounds(
    profitable_journal: Path, with_price_loader,
) -> None:
    """When price features are promoted, each rule's entry_condition carries bounds."""
    dates = pd.bdate_range("2025-12-01", periods=60).strftime("%Y-%m-%d").tolist()
    closes = [10.0 + 0.05 * i for i in range(60)]
    with_price_loader(_price_frame(dates, closes))

    profile = extract_shadow_profile(profitable_journal, min_support=2)
    assert len(profile.rules) >= 1

    for rule in profile.rules:
        ec = rule.entry_condition
        assert "market" in ec
        assert "entry_hour" in ec
        # Price features were promoted → should appear in every rule.
        assert "entry_rsi14" in ec, f"rule {rule.rule_id} missing entry_rsi14 bounds"
        assert isinstance(ec["entry_rsi14"], dict)
        assert "min" in ec["entry_rsi14"] and "max" in ec["entry_rsi14"]
        assert "prior_5d_return" in ec, f"rule {rule.rule_id} missing prior_5d_return bounds"
        assert isinstance(ec["prior_5d_return"], dict)


@pytest.mark.unit
def test_extracted_rules_no_price_conditions_when_sparse(
    profitable_journal: Path,
) -> None:
    """With prices offline (autouse), rules carry only behavioral conditions."""
    profile = extract_shadow_profile(profitable_journal, min_support=2)
    assert len(profile.rules) >= 1

    for rule in profile.rules:
        ec = rule.entry_condition
        assert "market" in ec
        assert "entry_hour" in ec
        assert "entry_rsi14" not in ec
        assert "prior_5d_return" not in ec


@pytest.mark.unit
def test_price_condition_bounds_are_p10_p90() -> None:
    """The p10/p90 values are the actual quantiles of the cluster."""
    from src.shadow_account.extractor import _cluster_to_rule

    cluster_df = pd.DataFrame({
        "symbol": ["A"] * 4,
        "market": ["china_a"] * 4,
        "holding_days": [3.0, 4.0, 3.0, 4.0],
        "pnl_pct": [0.1, 0.2, 0.1, 0.2],
        "entry_hour": [10, 10, 10, 10],
        "entry_weekday": [1, 1, 1, 1],
        "entry_rsi14": [25.0, 30.0, 35.0, 45.0],
        "buy_dt": [pd.Timestamp("2026-01-10")] * 4,
        "sell_dt": [pd.Timestamp("2026-01-14")] * 4,
    })
    rule = _cluster_to_rule(
        cluster_df=cluster_df,
        rule_index=1,
        total_profitable=4,
        llm_translator=None,
        price_features=("entry_rsi14",),
    )
    bounds = rule.entry_condition["entry_rsi14"]
    # p10 of [25, 30, 35, 45] = 25 + 0.3*5 = 26.5; p90 = 30 + 0.9*10 = 39.0
    # Actually with 4 data points, p10 is between 1st and 2nd:
    # With default linear interpolation: p10 ~ 26.5, p90 ~ 42.0
    assert "min" in bounds and "max" in bounds
    assert bounds["min"] > 24.0  # roughly p10
    assert bounds["max"] < 46.0  # roughly p90
    assert bounds["min"] < bounds["max"]


@pytest.mark.unit
def test_price_condition_nan_rows_excluded_from_bounds() -> None:
    """NaN rows in the cluster do not shift p10/p90 quantiles."""
    from src.shadow_account.extractor import _cluster_to_rule

    cluster_df = pd.DataFrame({
        "symbol": ["A"] * 4,
        "market": ["china_a"] * 4,
        "holding_days": [3.0, 4.0, 3.0, 4.0],
        "pnl_pct": [0.1, 0.2, 0.1, 0.2],
        "entry_hour": [10, 10, 10, 10],
        "entry_weekday": [1, 1, 1, 1],
        "entry_rsi14": [30.0, float("nan"), 40.0, float("nan")],
        "buy_dt": [pd.Timestamp("2026-01-10")] * 4,
        "sell_dt": [pd.Timestamp("2026-01-14")] * 4,
    })
    rule = _cluster_to_rule(
        cluster_df=cluster_df,
        rule_index=1,
        total_profitable=4,
        llm_translator=None,
        price_features=("entry_rsi14",),
    )
    # Only two non-NaN values (30, 40) — bounds from those.
    bounds = rule.entry_condition["entry_rsi14"]
    assert bounds["min"] == pytest.approx(30.0, abs=2.0)
    assert bounds["max"] == pytest.approx(40.0, abs=2.0)


# ---- M5: Codegen with price conditions ----


from src.shadow_account.codegen import _rule_to_context  # noqa: E402


@pytest.mark.unit
def test_rule_to_context_with_price_conditions() -> None:
    rule = ShadowRule(
        rule_id="R1",
        human_text="Enter when RSI 25-45",
        entry_condition={
            "market": "china_a",
            "entry_hour": {"min": 9, "max": 11},
            "entry_rsi14": {"min": 25.0, "max": 45.0},
            "prior_5d_return": {"min": -0.05, "max": 0.02},
        },
        exit_condition={"holding_days": {"min": 2, "max": 5}},
        holding_days_range=(2, 5),
        support_count=10,
        coverage_rate=0.5,
        sample_trades=("600519@2026-01-10",),
    )
    ctx = _rule_to_context(rule)
    assert ctx["entry_rsi14_min"] == 25.0
    assert ctx["entry_rsi14_max"] == 45.0
    assert ctx["prior_5d_return_min"] == -0.05
    assert ctx["prior_5d_return_max"] == 0.02


@pytest.mark.unit
def test_rule_to_context_without_price_conditions() -> None:
    rule = ShadowRule(
        rule_id="R1",
        human_text="Enter at 9-11am",
        entry_condition={
            "market": "china_a",
            "entry_hour": {"min": 9, "max": 11},
        },
        exit_condition={"holding_days": {"min": 2, "max": 5}},
        holding_days_range=(2, 5),
        support_count=10,
        coverage_rate=0.5,
        sample_trades=("600519@2026-01-10",),
    )
    ctx = _rule_to_context(rule)
    assert "entry_rsi14_min" not in ctx
    assert "entry_rsi14_max" not in ctx
    assert "prior_5d_return_min" not in ctx
    assert "prior_5d_return_max" not in ctx


@pytest.mark.unit
def test_render_signal_engine_with_price_conditions() -> None:
    rule = ShadowRule(
        rule_id="R1",
        human_text="Enter when RSI 25-45",
        entry_condition={
            "market": "china_a",
            "entry_hour": {"min": 9, "max": 11},
            "entry_rsi14": {"min": 25.0, "max": 45.0},
        },
        exit_condition={"holding_days": {"min": 2, "max": 5}},
        holding_days_range=(2, 5),
        support_count=10,
        coverage_rate=0.5,
        sample_trades=("600519@2026-01-10",),
    )
    profile = ShadowProfile(
        shadow_id="shadow_test123",
        created_at="2026-01-01T00:00:00",
        journal_hash="abc",
        source_market="china_a",
        profitable_roundtrips=10,
        total_roundtrips=20,
        date_range=("2025-01-01", "2026-01-01"),
        profile_text="test",
        rules=(rule,),
        preferred_markets=("china_a",),
        typical_holding_days=(3.0, 5.0),
    )
    source = render_signal_engine(profile)
    ok, err = validate_generated(source)
    assert ok, f"validation failed: {err}"
    assert "_compute_rsi" in source
    assert "_compute_prior_return" in source
    assert "_conditional_entry" in source
    assert "entry_rsi14_min" in source
    assert "entry_rsi14_max" in source
    assert "class SignalEngine" in source
    assert "def generate" in source


@pytest.mark.unit
def test_render_signal_engine_without_price_conditions_still_valid() -> None:
    rule = ShadowRule(
        rule_id="R1",
        human_text="Enter at 9-11am",
        entry_condition={
            "market": "china_a",
            "entry_hour": {"min": 9, "max": 11},
        },
        exit_condition={"holding_days": {"min": 2, "max": 5}},
        holding_days_range=(2, 5),
        support_count=10,
        coverage_rate=0.5,
        sample_trades=("600519@2026-01-10",),
    )
    profile = ShadowProfile(
        shadow_id="shadow_test456",
        created_at="2026-01-01T00:00:00",
        journal_hash="def",
        source_market="china_a",
        profitable_roundtrips=10,
        total_roundtrips=20,
        date_range=("2025-01-01", "2026-01-01"),
        profile_text="test",
        rules=(rule,),
        preferred_markets=("china_a",),
        typical_holding_days=(3.0, 5.0),
    )
    source = render_signal_engine(profile)
    ok, err = validate_generated(source)
    assert ok, f"validation failed: {err}"
    # Conditional entry method still present (uses runtime checks)
    assert "_conditional_entry" in source
    # Rule dict in RULES literal has only behavioral keys, no price keys.
    import ast
    tree = ast.parse(source)
    rules_found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "RULES":
            rules_found = True
            val = node.value
            if isinstance(val, ast.List) and val.elts:
                first_rule = ast.literal_eval(val.elts[0])
                assert "entry_rsi14_min" not in first_rule
                assert "prior_5d_return_min" not in first_rule
    assert rules_found


# ---- M6: Template behavior — conditional entry logic ----


def _generate_signals(profile: ShadowProfile, data_map: dict) -> dict:
    """Render + load + execute a SignalEngine against a data_map."""
    import importlib.util
    import tempfile

    source = render_signal_engine(profile)
    ok, err = validate_generated(source)
    assert ok, f"generated source failed validation: {err}"

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "signal_engine.py"
        path.write_text(source, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("gen_se", path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        engine = module.SignalEngine()
        return engine.generate(data_map)


def _rule_with_rsi(
    rsi_min: float, rsi_max: float, hour_min: int = 0, hour_max: int = 23,
) -> ShadowRule:
    return ShadowRule(
        rule_id="R1",
        human_text="RSI rule",
        entry_condition={
            "market": "china_a",
            "entry_hour": {"min": hour_min, "max": hour_max},
            "entry_rsi14": {"min": rsi_min, "max": rsi_max},
        },
        exit_condition={"holding_days": {"min": 2, "max": 5}},
        holding_days_range=(3, 3),
        support_count=10,
        coverage_rate=0.5,
        sample_trades=("600519@2026-01-10",),
    )


def _rule_without_price() -> ShadowRule:
    return ShadowRule(
        rule_id="R1",
        human_text="Time-only rule",
        entry_condition={
            "market": "china_a",
            "entry_hour": {"min": 0, "max": 23},
        },
        exit_condition={"holding_days": {"min": 2, "max": 5}},
        holding_days_range=(3, 3),
        support_count=10,
        coverage_rate=0.5,
        sample_trades=("600519@2026-01-10",),
    )


def _profile(rule: ShadowRule) -> ShadowProfile:
    return ShadowProfile(
        shadow_id="shadow_test",
        created_at="2026-01-01T00:00:00",
        journal_hash="test",
        source_market="china_a",
        profitable_roundtrips=10,
        total_roundtrips=20,
        date_range=("2025-01-01", "2026-01-01"),
        profile_text="test",
        rules=(rule,),
        preferred_markets=("china_a",),
        typical_holding_days=(3.0, 5.0),
    )


def _hourly_index(start: str = "2026-01-02", periods: int = 24) -> pd.DatetimeIndex:
    return pd.date_range(start, periods=periods, freq="h")


def _daily_index(start: str = "2026-01-02", periods: int = 30) -> pd.DatetimeIndex:
    return pd.date_range(start, periods=periods, freq="B")


@pytest.mark.unit
def test_conditional_entry_emits_signal_when_rsi_in_range() -> None:
    """RSI in [25, 45] → signal fires."""
    rule = _rule_with_rsi(25.0, 45.0)
    idx = _hourly_index(periods=40)
    sideways = pd.Series(
        [10.0 + (i % 6) * 0.5 for i in range(40)], index=idx, dtype=float,
    )
    s2 = _generate_signals(
        _profile(rule),
        {"600519.SH": pd.DataFrame({"close": sideways}, index=idx)},
    )["600519.SH"]
    assert (s2 >= 0).all()
    # With a 3-day hold, at least some 4-hour entry windows should fire.
    assert (s2 > 0).any(), "signal should fire when RSI is in range"


@pytest.mark.unit
def test_conditional_entry_skips_when_rsi_out_of_range() -> None:
    """RSI strictly below min → no entry. Use a steep uptrend to push RSI high."""
    rule = _rule_with_rsi(5.0, 15.0)  # very low range
    idx = _hourly_index(periods=40)
    # Steep uptrend → RSI very high (well above 15)
    close = pd.Series(
        [10.0 + 0.5 * i for i in range(40)], index=idx, dtype=float,
    )
    signals = _generate_signals(
        _profile(rule),
        {"600519.SH": pd.DataFrame({"close": close}, index=idx)},
    )
    series = signals["600519.SH"]
    # RSI should be far above the 5-15 range → zero entries.
    assert (series == 0.0).all()


@pytest.mark.unit
def test_conditional_entry_respects_hour_window() -> None:
    """Entry only allowed when bar hour is in [9, 11]; outside → zero."""
    rule = _rule_with_rsi(0.0, 100.0, hour_min=9, hour_max=11)
    idx = _hourly_index(periods=48)  # 2 full days of hours
    close = pd.Series(
        [10.0 + (i % 6) * 0.5 for i in range(48)], index=idx, dtype=float,
    )
    signals = _generate_signals(
        _profile(rule),
        {"600519.SH": pd.DataFrame({"close": close}, index=idx)},
    )
    series = signals["600519.SH"]
    for i, ts in enumerate(idx):
        h = pd.Timestamp(ts).hour
        if h < 9 or h > 11:
            assert series.iloc[i] == 0.0, f"signal at hour {h} should be zero"


@pytest.mark.unit
def test_conditional_entry_holds_for_full_duration() -> None:
    """Once entered, signal persists for hold_days bars."""
    rule = _rule_with_rsi(0.0, 100.0)  # always passes RSI check
    idx = _hourly_index(periods=24)
    close = pd.Series(
        [10.0 + (i % 6) * 0.5 for i in range(24)], index=idx, dtype=float,
    )
    signals = _generate_signals(
        _profile(rule),
        {"600519.SH": pd.DataFrame({"close": close}, index=idx)},
    )
    series = signals["600519.SH"]

    # Find first entry bar.
    entry_idx = None
    for i in range(len(series)):
        if series.iloc[i] > 0:
            entry_idx = i
            break
    assert entry_idx is not None
    # Signal should persist for hold_days (3) consecutive bars.
    for j in range(entry_idx, min(entry_idx + 3, len(series))):
        assert series.iloc[j] == 1.0, f"hold broken at bar {j}"


@pytest.mark.unit
def test_conditional_entry_no_reentry_while_holding() -> None:
    """remaining_hold > 0 must prevent re-entry during a hold."""
    # Use daily bars with all-hours window so RSI warmup is the only gate.
    rule = _rule_with_rsi(0.0, 100.0, hour_min=0, hour_max=23)
    idx = _daily_index(periods=30)
    # A price series that yields a moderate RSI value (not extreme).
    close = pd.Series(
        [10.0 + (i % 6) * 0.5 for i in range(30)], index=idx, dtype=float,
    )
    signals = _generate_signals(
        _profile(rule),
        {"600519.SH": pd.DataFrame({"close": close}, index=idx)},
    )
    series = signals["600519.SH"]

    # Find the first entry bar.
    entry_bar = None
    for i in range(len(series)):
        if series.iloc[i] > 0:
            entry_bar = i
            break
    assert entry_bar is not None, "expected at least one entry"
    # The first hold run after entry should last hold_days=3 consecutive bars.
    for j in range(entry_bar, min(entry_bar + 3, len(series))):
        assert series.iloc[j] == 1.0, f"hold broken at bar {j} (entry at {entry_bar})"


@pytest.mark.unit
def test_conditional_entry_falls_back_to_time_only_when_no_price_keys() -> None:
    """Rule without price conditions uses time-window-only entry."""
    rule = _rule_without_price()
    idx = _hourly_index(periods=24)
    close = pd.Series(
        [10.0 + (i % 6) * 0.5 for i in range(24)], index=idx, dtype=float,
    )
    signals = _generate_signals(
        _profile(rule),
        {"600519.SH": pd.DataFrame({"close": close}, index=idx)},
    )
    series = signals["600519.SH"]
    assert isinstance(series, pd.Series)
    assert len(series) == len(idx)
    # With hour_min=0, hour_max=23 and no price gates, at least first bar enters.
    assert (series > 0).any()


@pytest.mark.unit
def test_conditional_entry_prior_return_gates_entry() -> None:
    """Prior return outside bounds → no entry."""
    rule = ShadowRule(
        rule_id="R1",
        human_text="Return rule",
        entry_condition={
            "market": "china_a",
            "entry_hour": {"min": 0, "max": 23},
            "prior_5d_return": {"min": -0.03, "max": 0.03},
        },
        exit_condition={"holding_days": {"min": 2, "max": 5}},
        holding_days_range=(3, 3),
        support_count=10,
        coverage_rate=0.5,
        sample_trades=("600519@2026-01-10",),
    )
    idx = _daily_index(periods=40)
    # Very large returns (+50% over 5 bars) → well outside [-0.03, 0.03]
    close = pd.Series(
        [10.0 + 0.5 * i for i in range(40)], index=idx, dtype=float,
    )
    signals = _generate_signals(
        _profile(rule),
        {"600519.SH": pd.DataFrame({"close": close}, index=idx)},
    )
    series = signals["600519.SH"]
    # Strong trend → prior_5d_return far outside narrow [-3%, 3%] → all zero.
    assert (series == 0.0).all()


@pytest.mark.unit
def test_conditional_entry_both_rsi_and_return_must_pass() -> None:
    """Both RSI and prior-return conditions must pass (AND logic)."""
    rule = ShadowRule(
        rule_id="R1",
        human_text="Both rule",
        entry_condition={
            "market": "china_a",
            "entry_hour": {"min": 0, "max": 23},
            "entry_rsi14": {"min": 0.0, "max": 100.0},  # always passes
            "prior_5d_return": {"min": -0.02, "max": 0.02},  # very narrow
        },
        exit_condition={"holding_days": {"min": 2, "max": 5}},
        holding_days_range=(3, 3),
        support_count=10,
        coverage_rate=0.5,
        sample_trades=("600519@2026-01-10",),
    )
    idx = _daily_index(periods=40)
    # Strong uptrend → prior_5d_return >> 2%.
    close = pd.Series(
        [10.0 + 1.0 * i for i in range(40)], index=idx, dtype=float,
    )
    signals = _generate_signals(
        _profile(rule),
        {"600519.SH": pd.DataFrame({"close": close}, index=idx)},
    )
    series = signals["600519.SH"]
    # RSI passes, but prior_5d_return fails (too positive) → no entry.
    assert (series == 0.0).all()


@pytest.mark.unit
def test_conditional_entry_only_prior_return_condition() -> None:
    """Rule with only prior_5d_return (no RSI) gates on return alone."""
    rule = ShadowRule(
        rule_id="R1",
        human_text="Return-only rule",
        entry_condition={
            "market": "china_a",
            "entry_hour": {"min": 0, "max": 23},
            "prior_5d_return": {"min": -0.02, "max": 0.02},
        },
        exit_condition={"holding_days": {"min": 2, "max": 5}},
        holding_days_range=(3, 3),
        support_count=10,
        coverage_rate=0.5,
        sample_trades=("600519@2026-01-10",),
    )
    idx = _daily_index(periods=40)
    # Sideways prices → prior_5d_return ~0, within [-0.02, 0.02].
    close = pd.Series(
        [10.0 + (i % 3) * 0.005 for i in range(40)], index=idx, dtype=float,
    )
    signals = _generate_signals(
        _profile(rule),
        {"600519.SH": pd.DataFrame({"close": close}, index=idx)},
    )
    series = signals["600519.SH"]
    assert (series >= 0).all()
    assert (series > 0).any(), "entry should fire when return in range"


@pytest.mark.unit
def test_cluster_to_rule_skips_all_nan_price_feature() -> None:
    """When a promoted price feature is all-NaN in the cluster, it is skipped."""
    from src.shadow_account.extractor import _cluster_to_rule

    cluster_df = pd.DataFrame({
        "symbol": ["A"] * 4,
        "market": ["china_a"] * 4,
        "holding_days": [3.0, 4.0, 3.0, 4.0],
        "pnl_pct": [0.1, 0.2, 0.1, 0.2],
        "entry_hour": [10, 10, 10, 10],
        "entry_weekday": [1, 1, 1, 1],
        "entry_rsi14": [float("nan")] * 4,  # all NaN
        "buy_dt": [pd.Timestamp("2026-01-10")] * 4,
        "sell_dt": [pd.Timestamp("2026-01-14")] * 4,
    })
    rule = _cluster_to_rule(
        cluster_df=cluster_df,
        rule_index=1,
        total_profitable=4,
        llm_translator=None,
        price_features=("entry_rsi14",),
    )
    # All-NaN → dropna() leaves < 2 values → feature not added to entry_condition.
    assert "entry_rsi14" not in rule.entry_condition
    assert "market" in rule.entry_condition
    assert "entry_hour" in rule.entry_condition


@pytest.mark.unit
def test_conditional_entry_rsi_nan_bars_are_skipped() -> None:
    """Bars where RSI is NaN (warmup) are skipped, then entry fires after warmup."""
    rule = _rule_with_rsi(0.0, 100.0)
    idx = _daily_index(periods=30)
    close = pd.Series(
        [10.0 + (i % 6) * 0.5 for i in range(30)], index=idx, dtype=float,
    )
    signals = _generate_signals(
        _profile(rule),
        {"600519.SH": pd.DataFrame({"close": close}, index=idx)},
    )
    series = signals["600519.SH"]
    # First 14 bars have NaN RSI → must be zero.
    for i in range(14):
        assert series.iloc[i] == 0.0, f"bar {i} should be zero (RSI warmup)"
    # At least one entry after warmup.
    assert (series.iloc[14:] > 0).any(), "no entry after RSI warmup"


