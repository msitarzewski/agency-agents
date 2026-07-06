from __future__ import annotations

import sys
from types import SimpleNamespace

import pandas as pd
import pytest

from backtest.loaders.tushare_fundamentals import (
    SchemaValidationError,
    TushareFundamentalProvider,
    UnknownTableError,
    enrich_price_frames_with_fundamentals,
)


class _FakeTushareApi:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    def income(self, **kwargs: object) -> pd.DataFrame:
        self.calls.append(("income", kwargs))
        return pd.DataFrame(
            [
                {
                    "ts_code": kwargs["ts_code"],
                    "end_date": "20231231",
                    "ann_date": "20240401",
                    "f_ann_date": "20240402",
                    "total_revenue": 100.0,
                },
                {
                    "ts_code": kwargs["ts_code"],
                    "end_date": "20240331",
                    "ann_date": "20240425",
                    "f_ann_date": "20240506",
                    "total_revenue": 120.0,
                },
            ]
        )


def test_provider_exposes_first_milestone_financial_table_metadata() -> None:
    provider = TushareFundamentalProvider(api=_FakeTushareApi())

    assert provider.list_tables() == ["balancesheet", "cashflow", "fina_indicator", "income"]

    schema = provider.describe_table("income")
    assert schema.api_name == "income"
    assert schema.point_in_time_column == "f_ann_date"
    assert {"ts_code", "end_date", "ann_date", "f_ann_date", "total_revenue"} <= {
        column.name for column in schema.columns
    }


def test_default_constructor_uses_project_tushare_token_env(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    fake_api = _FakeTushareApi()

    def pro_api(token: str = "") -> _FakeTushareApi:
        calls.append(token)
        return fake_api

    monkeypatch.setenv("TUSHARE_TOKEN", "ts-secret-token")
    monkeypatch.setitem(sys.modules, "tushare", SimpleNamespace(pro_api=pro_api))

    provider = TushareFundamentalProvider()

    assert provider.api is fake_api
    assert calls == ["ts-secret-token"]


def test_query_fundamentals_returns_pit_safe_dataframe() -> None:
    api = _FakeTushareApi()
    provider = TushareFundamentalProvider(api=api)

    result = provider.query_fundamentals(
        "income",
        ["000001.SZ", "600000.SH"],
        as_of="2024-04-30",
        periods=["20231231", "20240331"],
        fields=["total_revenue"],
    )

    assert list(result["ts_code"]) == ["000001.SZ", "600000.SH"]
    assert list(result["end_date"]) == ["20231231", "20231231"]
    assert list(result["f_ann_date"]) == ["20240402", "20240402"]
    assert list(result["total_revenue"]) == [100.0, 100.0]
    assert api.calls == [
        ("income", {"ts_code": "000001.SZ", "period": None}),
        ("income", {"ts_code": "600000.SH", "period": None}),
    ]


def test_query_fundamentals_falls_back_to_ann_date_per_row() -> None:
    class SparseDisclosureApi:
        def balancesheet(self, **kwargs: object) -> pd.DataFrame:
            return pd.DataFrame(
                [
                    {
                        "ts_code": kwargs["ts_code"],
                        "end_date": "20231231",
                        "ann_date": "20240401",
                        "f_ann_date": None,
                        "total_assets": 100.0,
                    },
                    {
                        "ts_code": kwargs["ts_code"],
                        "end_date": "20240331",
                        "ann_date": "20240420",
                        "f_ann_date": "20240506",
                        "total_assets": 110.0,
                    },
                ]
            )

    provider = TushareFundamentalProvider(api=SparseDisclosureApi())

    result = provider.query_fundamentals(
        "balancesheet",
        ["000001.SZ"],
        as_of="2024-04-30",
        fields=["total_assets"],
    )

    assert list(result["end_date"]) == ["20231231"]
    assert list(result["total_assets"]) == [100.0]


def test_query_fundamentals_rejects_unknown_tables() -> None:
    provider = TushareFundamentalProvider(api=_FakeTushareApi())

    with pytest.raises(UnknownTableError):
        provider.query_fundamentals("daily_basic", ["000001.SZ"], as_of="2024-04-30")


def test_query_fundamentals_validates_required_schema_columns() -> None:
    class BadApi:
        def fina_indicator(self, **kwargs: object) -> pd.DataFrame:
            return pd.DataFrame([{"ts_code": kwargs["ts_code"], "ann_date": "20240401"}])

    provider = TushareFundamentalProvider(api=BadApi())

    with pytest.raises(SchemaValidationError, match="end_date"):
        provider.query_fundamentals("fina_indicator", ["000001.SZ"], as_of="2024-04-30")


def test_enrich_price_frames_with_fundamentals_respects_point_in_time_dates() -> None:
    class StatementApi:
        def income(self, **kwargs: object) -> pd.DataFrame:
            return pd.DataFrame(
                [
                    {
                        "ts_code": kwargs["ts_code"],
                        "end_date": "20231231",
                        "ann_date": "20240401",
                        "f_ann_date": "20240402",
                        "total_revenue": 80.0,
                        "n_income": 8.0,
                    },
                    {
                        "ts_code": kwargs["ts_code"],
                        "end_date": "20240331",
                        "ann_date": "20240425",
                        "f_ann_date": "20240506",
                        "total_revenue": 120.0,
                        "n_income": 12.0,
                    },
                ]
            )

    dates = pd.to_datetime(["2024-04-01", "2024-04-03", "2024-05-07"])
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
    provider = TushareFundamentalProvider(api=StatementApi())

    enriched = enrich_price_frames_with_fundamentals(
        {"000001.SZ": bars},
        provider,
        {"income": ["total_revenue", "n_income"]},
        as_of="2024-05-31",
    )

    result = enriched["000001.SZ"]
    assert pd.isna(result.loc[pd.Timestamp("2024-04-01"), "income_total_revenue"])
    assert result.loc[pd.Timestamp("2024-04-03"), "income_total_revenue"] == 80.0
    assert result.loc[pd.Timestamp("2024-05-07"), "income_total_revenue"] == 120.0
    assert result.loc[pd.Timestamp("2024-05-07"), "income_end_date"] == "20240331"
