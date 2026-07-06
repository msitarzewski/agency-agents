"""Tests for the trade journal analyzer and its broker-format parsers.

Covers ``src.tools.trade_journal_parsers`` (format detection, side/symbol
normalization, market inference, end-to-end parse) and
``src.tools.trade_journal_tool`` (FIFO pairing, profile/behavior metrics,
filtering, and the analyze_trade_journal error/dispatch paths).
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.tools.trade_journal_parsers import (
    TradeRecord,
    _infer_market_from_symbol,
    _normalize_side,
    _qualify_a_share,
    detect_format,
    parse_file,
    records_to_dataframe,
)
from src.tools.trade_journal_tool import (
    _apply_filter,
    _compute_behavior,
    _compute_profile,
    _disposition_effect,
    analyze_trade_journal,
    pair_trades_fifo,
)


def _rec(dt: str, symbol: str, side: str, qty: float, price: float, fee: float = 0.0) -> TradeRecord:
    return TradeRecord(
        datetime=dt,
        symbol=symbol,
        name="",
        side=side,
        quantity=qty,
        price=price,
        amount=qty * price,
        fee=fee,
        market="china_a",
    )


def _df(records: list[TradeRecord]) -> pd.DataFrame:
    return records_to_dataframe(records)


@pytest.fixture()
def allow_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Allow analyze_trade_journal to read files under tmp_path."""
    monkeypatch.setenv("VIBE_TRADING_ALLOWED_FILE_ROOTS", str(tmp_path))
    return tmp_path


# --------------------------------------------------------------------------
# Parser pure helpers
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "code,expected",
    [
        ("600519", "600519.SH"),  # Shanghai main
        ("688981", "688981.SH"),  # STAR
        ("000001", "000001.SZ"),  # Shenzhen main
        ("300750", "300750.SZ"),  # ChiNext
        ("430139", "430139.BJ"),  # BSE (4-prefix)
        ("830799", "830799.BJ"),  # BSE (8-prefix)
        ("600519.SH", "600519.SH"),  # already qualified -> passthrough
        ("1", "000001.SZ"),  # zero-padded to 6 then mapped
    ],
)
def test_qualify_a_share(code: str, expected: str) -> None:
    assert _qualify_a_share(code) == expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("买入", "buy"),
        ("证券买入", "buy"),
        ("B", "buy"),
        ("long", "buy"),
        ("卖出", "sell"),
        ("证券卖出", "sell"),
        ("融券卖出", "sell"),
        ("S", "sell"),
        ("short", "sell"),
        ("hold", "buy"),  # no buy/sell token substring -> documented fallback
    ],
)
def test_normalize_side(raw: str, expected: str) -> None:
    assert _normalize_side(raw) == expected


@pytest.mark.parametrize(
    "symbol,expected",
    [
        ("00700.HK", "hk"),
        ("600519.SH", "china_a"),
        ("000001.SZ", "china_a"),
        ("AAPL", "us"),
        ("BTC-USDT", "crypto"),
        ("ETH-USD", "crypto"),
        ("123456", "other"),
    ],
)
def test_infer_market_from_symbol(symbol: str, expected: str) -> None:
    assert _infer_market_from_symbol(symbol) == expected


def test_detect_format_signatures() -> None:
    ths = pd.DataFrame(columns=["成交时间", "证券代码", "操作", "成交数量"])
    assert detect_format(ths) == "tonghuashun"

    em = pd.DataFrame(columns=["成交日期", "买卖标志", "股票代码"])
    assert detect_format(em) == "eastmoney"

    futu = pd.DataFrame(columns=["Date", "Symbol", "Side", "Quantity"])
    assert detect_format(futu) == "futu"

    generic = pd.DataFrame(columns=["datetime", "ticker", "side"])
    assert detect_format(generic) == "generic"

    unknown = pd.DataFrame(columns=["foo", "bar"])
    assert detect_format(unknown) == "unknown"


def test_records_to_dataframe_sorts_and_handles_empty() -> None:
    empty = records_to_dataframe([])
    assert empty.empty
    assert "datetime" in empty.columns

    out = _df(
        [
            _rec("2026-01-03 10:00:00", "600519.SH", "buy", 100, 10),
            _rec("2026-01-01 10:00:00", "600519.SH", "buy", 100, 9),
        ]
    )
    # Sorted ascending by datetime.
    assert list(out["price"]) == [9, 10]


# --------------------------------------------------------------------------
# parse_file end-to-end (CSV fixtures)
# --------------------------------------------------------------------------


def test_parse_file_generic_csv(tmp_path: Path) -> None:
    csv = tmp_path / "generic.csv"
    csv.write_text(
        "datetime,symbol,side,quantity,price\n"
        "2026-01-02 09:35:00,AAPL,buy,10,180\n"
        "2026-01-05 14:00:00,AAPL,sell,10,190\n",
        encoding="utf-8",
    )
    fmt, records = parse_file(csv)
    assert fmt == "generic"
    assert len(records) == 2
    assert records[0].symbol == "AAPL"
    assert records[0].side == "buy"
    assert records[0].market == "us"


def test_parse_file_tonghuashun_csv(tmp_path: Path) -> None:
    csv = tmp_path / "ths.csv"
    csv.write_text(
        "成交时间,证券代码,证券名称,操作,成交数量,成交价格,成交金额,手续费,印花税,过户费\n"
        "2026-01-02 09:35:00,600519,贵州茅台,买入,100,1700,170000,5,0,0.1\n"
        "2026-01-08 10:00:00,600519,贵州茅台,卖出,100,1800,180000,5,180,0.1\n",
        encoding="utf-8",
    )
    fmt, records = parse_file(csv)
    assert fmt == "tonghuashun"
    assert records[0].symbol == "600519.SH"  # qualified
    assert records[0].side == "buy"
    assert records[1].side == "sell"
    # fee = 手续费 + 印花税 + 过户费
    assert records[1].fee == pytest.approx(5 + 180 + 0.1)


def test_parse_file_unknown_raises(tmp_path: Path) -> None:
    csv = tmp_path / "weird.csv"
    csv.write_text("foo,bar\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Unrecognized"):
        parse_file(csv)


# --------------------------------------------------------------------------
# FIFO pairing
# --------------------------------------------------------------------------


def test_fifo_single_roundtrip_pnl() -> None:
    rts = pair_trades_fifo(
        _df(
            [
                _rec("2026-01-01 10:00:00", "600519.SH", "buy", 100, 10),
                _rec("2026-01-11 10:00:00", "600519.SH", "sell", 100, 12),
            ]
        )
    )
    assert len(rts) == 1
    trip = rts[0]
    assert trip["pnl"] == 200.0  # (12-10)*100
    assert trip["pnl_pct"] == 0.2  # 200 / (10*100)
    assert trip["hold_days"] == 10.0
    assert trip["qty"] == 100


def test_fifo_fee_allocation() -> None:
    rts = pair_trades_fifo(
        _df(
            [
                _rec("2026-01-01 10:00:00", "X.SH", "buy", 100, 10, fee=10),
                _rec("2026-01-02 10:00:00", "X.SH", "sell", 100, 12, fee=6),
            ]
        )
    )
    # gross 200 - buy_fee 10 - sell_fee 6 = 184
    assert rts[0]["pnl"] == 184.0


def test_fifo_partial_fill_splits_into_two_roundtrips() -> None:
    rts = pair_trades_fifo(
        _df(
            [
                _rec("2026-01-01 10:00:00", "X.SH", "buy", 100, 10),
                _rec("2026-01-02 10:00:00", "X.SH", "buy", 100, 20),
                _rec("2026-01-03 10:00:00", "X.SH", "sell", 150, 30),
            ]
        )
    )
    # FIFO: 100 @10 fully, then 50 @20.
    assert len(rts) == 2
    assert rts[0]["qty"] == 100
    assert rts[0]["pnl"] == 2000.0  # (30-10)*100
    assert rts[1]["qty"] == 50
    assert rts[1]["pnl"] == 500.0  # (30-20)*50


def test_fifo_unmatched_sell_ignored() -> None:
    rts = pair_trades_fifo(
        _df([_rec("2026-01-01 10:00:00", "X.SH", "sell", 100, 12)])
    )
    assert rts == []


# --------------------------------------------------------------------------
# Profile / behavior
# --------------------------------------------------------------------------


def test_compute_profile_win_rate_and_pnl() -> None:
    profile = _compute_profile(
        _df(
            [
                _rec("2026-01-01 10:00:00", "A.SH", "buy", 100, 10),
                _rec("2026-01-05 10:00:00", "A.SH", "sell", 100, 12),  # +200 win
                _rec("2026-01-02 10:00:00", "B.SH", "buy", 100, 50),
                _rec("2026-01-06 10:00:00", "B.SH", "sell", 100, 45),  # -500 loss
            ]
        )
    )
    assert profile["total_roundtrips"] == 2
    assert profile["win_rate"] == 0.5
    assert profile["total_pnl"] == -300.0  # 200 - 500


def test_compute_profile_empty() -> None:
    assert _compute_profile(records_to_dataframe([])) == {"error": "empty trade journal"}


def test_disposition_effect_flags_holding_losers_longer() -> None:
    rts_df = pd.DataFrame(
        [
            {"pnl": 100.0, "hold_days": 2.0},  # winner held 2d
            {"pnl": -80.0, "hold_days": 10.0},  # loser held 10d
        ]
    )
    out = _disposition_effect(rts_df)
    assert out["ratio_loss_to_win_hold"] == 5.0  # 10 / 2
    assert out["severity"] == "high"


def test_disposition_effect_insufficient_data() -> None:
    only_wins = pd.DataFrame([{"pnl": 10.0, "hold_days": 1.0}])
    assert _disposition_effect(only_wins)["severity"] == "low"


def test_compute_behavior_returns_all_four_diagnostics() -> None:
    behavior = _compute_behavior(
        _df(
            [
                _rec("2026-01-01 10:00:00", "A.SH", "buy", 100, 10),
                _rec("2026-01-05 10:00:00", "A.SH", "sell", 100, 12),
            ]
        )
    )
    assert set(behavior) == {
        "disposition_effect",
        "overtrading",
        "chasing_momentum",
        "anchoring",
    }


# --------------------------------------------------------------------------
# _apply_filter
# --------------------------------------------------------------------------


def _filter_df() -> pd.DataFrame:
    return _df(
        [
            _rec("2026-01-02 10:00:00", "600519.SH", "buy", 100, 10),
            _rec("2026-02-15 10:00:00", "AAPL", "buy", 10, 180),
            _rec("2026-03-20 10:00:00", "600519.SH", "sell", 100, 12),
        ]
    )


def test_apply_filter_date_range() -> None:
    out = _apply_filter(_filter_df(), "2026-02-01 to 2026-02-28")
    assert len(out) == 1
    assert out.iloc[0]["symbol"] == "AAPL"


def test_apply_filter_symbol_equals() -> None:
    out = _apply_filter(_filter_df(), "symbol=600519.SH")
    assert len(out) == 2
    assert set(out["symbol"]) == {"600519.SH"}


def test_apply_filter_empty_expr_is_noop() -> None:
    df = _filter_df()
    assert len(_apply_filter(df, "")) == len(df)


# --------------------------------------------------------------------------
# analyze_trade_journal dispatch + error paths
# --------------------------------------------------------------------------


def test_analyze_missing_file(allow_tmp: Path) -> None:
    result = json.loads(analyze_trade_journal(str(allow_tmp / "does_not_exist_12345.csv")))
    assert result["status"] == "error"
    assert "not found" in result["error"].lower()


def test_analyze_unsupported_extension(allow_tmp: Path) -> None:
    bad = allow_tmp / "trades.txt"
    bad.write_text("whatever", encoding="utf-8")
    result = json.loads(analyze_trade_journal(str(bad)))
    assert result["status"] == "error"
    assert "extension" in result["error"].lower()


def _write_full_journal(tmp_path: Path) -> Path:
    csv = tmp_path / "full.csv"
    csv.write_text(
        "datetime,symbol,side,quantity,price\n"
        "2026-01-02 09:35:00,600519.SH,buy,100,10\n"
        "2026-01-09 14:00:00,600519.SH,sell,100,12\n",
        encoding="utf-8",
    )
    return csv


def test_analyze_full_includes_profile_and_behavior(allow_tmp: Path) -> None:
    result = json.loads(analyze_trade_journal(str(_write_full_journal(allow_tmp))))
    assert result["status"] == "ok"
    assert result["total_records"] == 2
    assert "profile" in result
    assert "behavior" in result
    assert result["profile"]["total_pnl"] == 200.0


def test_analyze_strategy_is_pending_placeholder(allow_tmp: Path) -> None:
    result = json.loads(
        analyze_trade_journal(str(_write_full_journal(allow_tmp)), analysis_type="strategy")
    )
    assert result["status"] == "ok"
    assert result["strategy_features"]["status"] == "pending"
    # profile/behavior should not be attached for a strategy-only request.
    assert "profile" not in result
    assert "behavior" not in result


def test_analyze_profile_only(allow_tmp: Path) -> None:
    result = json.loads(
        analyze_trade_journal(str(_write_full_journal(allow_tmp)), analysis_type="profile")
    )
    assert result["status"] == "ok"
    assert "profile" in result
    assert "behavior" not in result


def test_analyze_with_filter(allow_tmp: Path) -> None:
    csv = allow_tmp / "multi.csv"
    csv.write_text(
        "datetime,symbol,side,quantity,price\n"
        "2026-01-02 09:35:00,600519.SH,buy,100,10\n"
        "2026-02-09 14:00:00,AAPL,buy,10,180\n",
        encoding="utf-8",
    )
    result = json.loads(
        analyze_trade_journal(str(csv), filter_expr="symbol=AAPL")
    )
    assert result["status"] == "ok"
    assert result["total_records"] == 1
    assert result["filter_applied"] == "symbol=AAPL"
