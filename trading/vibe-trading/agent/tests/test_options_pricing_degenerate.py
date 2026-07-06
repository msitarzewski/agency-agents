"""Regression tests for P06 — analyze_options/options_pricing must not return
confident `status:"ok"` numbers for degenerate or invalid inputs.

Pre-fix: invalid inputs (σ≤0, spot/strike≤0, negative expiry, bad type) and
T=0 all returned `status:"ok"`; NaN could leak into the JSON. Post-fix:
invalid inputs are rejected with an error envelope, T=0 is flagged
`status:"degenerate"` with a warning (intrinsic value still returned), and
the normal path is numerically unchanged.
"""

from __future__ import annotations

import json

import pytest

from src.tools.options_pricing_tool import OptionsPricingTool


def _run(**kw):
    return json.loads(OptionsPricingTool().execute(**kw))


def test_normal_path_unchanged_status_ok():
    """ATM call 30d, r=0.05, σ=0.25 — authoritative BS reference values.
    Guards against any regression in the happy path."""
    out = _run(spot=100, strike=100, expiry_days=30, risk_free_rate=0.05, volatility=0.25, option_type="call")
    assert out["status"] == "ok"
    assert out["price"] == pytest.approx(3.0626, abs=1e-3)
    assert out["delta"] == pytest.approx(0.537118, abs=1e-4)
    assert out["gamma"] == pytest.approx(0.055421, abs=1e-4)
    assert out["vega"] == pytest.approx(0.113878, abs=1e-4)


def test_expiry_zero_is_degenerate_not_ok():
    out = _run(spot=100, strike=100, expiry_days=0, risk_free_rate=0.05, volatility=0.25, option_type="call")
    assert out["status"] == "degenerate"
    assert out["degenerate"] is True
    assert "warning" in out
    assert out["price"] == 0.0  # ATM intrinsic at expiry — still correct


def test_in_the_money_expiry_returns_intrinsic_degenerate():
    out = _run(spot=120, strike=100, expiry_days=0, risk_free_rate=0.05, volatility=0.25, option_type="call")
    assert out["status"] == "degenerate"
    assert out["price"] == pytest.approx(20.0, abs=1e-9)


@pytest.mark.parametrize(
    "kw",
    [
        {"spot": 100, "strike": 100, "expiry_days": 30, "volatility": 0.0, "option_type": "call"},
        {"spot": 100, "strike": 100, "expiry_days": 30, "volatility": -0.2, "option_type": "call"},
        {"spot": 0, "strike": 100, "expiry_days": 30, "volatility": 0.25, "option_type": "call"},
        {"spot": 100, "strike": 0, "expiry_days": 30, "volatility": 0.25, "option_type": "call"},
        {"spot": 100, "strike": 100, "expiry_days": -5, "volatility": 0.25, "option_type": "call"},
        {"spot": 100, "strike": 100, "expiry_days": 30, "volatility": 0.25, "option_type": "straddle"},
    ],
)
def test_invalid_inputs_rejected_with_error(kw):
    out = _run(risk_free_rate=0.05, **kw)
    assert out["status"] == "error"
    assert "error" in out and out["error"]


@pytest.mark.parametrize(
    "kw",
    [
        {"spot": 100, "strike": 100, "expiry_days": 30, "volatility": float("nan"), "option_type": "call"},
        {"spot": float("inf"), "strike": 100, "expiry_days": 30, "volatility": 0.25, "option_type": "call"},
        {
            "spot": 100,
            "strike": 100,
            "expiry_days": 30,
            "volatility": 0.25,
            "risk_free_rate": float("nan"),
            "option_type": "call",
        },
    ],
)
def test_non_finite_inputs_rejected_with_error(kw):
    """G2: NaN/Inf in any numeric input is rejected before pricing."""
    kw.setdefault("risk_free_rate", 0.05)
    out = _run(**kw)
    assert out["status"] == "error"
    assert "error" in out and out["error"]
    assert "finite" in out["error"]


def test_output_is_strict_json_no_nan():
    # json.loads already enforces strict JSON; assert it parses for all branches.
    for kw in (
        dict(spot=100, strike=100, expiry_days=30, volatility=0.25, option_type="put"),
        dict(spot=100, strike=100, expiry_days=0, volatility=0.25, option_type="put"),
    ):
        raw = OptionsPricingTool().execute(risk_free_rate=0.03, **kw)
        assert "NaN" not in raw and "Infinity" not in raw
        json.loads(raw)  # must not raise
