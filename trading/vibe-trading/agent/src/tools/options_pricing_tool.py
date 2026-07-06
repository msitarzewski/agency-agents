"""Options pricing tool: Black-Scholes theoretical price and Greeks."""

from __future__ import annotations

import json
import math
from typing import Any

import numpy as np
from scipy.stats import norm

from src.agent.tools import BaseTool


def _validate_inputs(
    spot: float, strike: float, expiry_days: float, sigma: float, r: float, option_type: str
) -> str | None:
    """Reject genuinely invalid inputs at the boundary (P06).

    T == 0 is a *valid* expiry (handled downstream as intrinsic value), so
    it is intentionally NOT rejected here — only invalid inputs are.
    """
    if option_type not in ("call", "put"):
        return f"option_type must be 'call' or 'put', got {option_type!r}"
    for _name, _val in (
        ("spot", spot),
        ("strike", strike),
        ("expiry_days", expiry_days),
        ("volatility", sigma),
        ("risk_free_rate", r),
    ):
        if not math.isfinite(_val):
            return f"{_name} must be a finite number, got {_val}"
    if spot <= 0:
        return f"spot must be positive, got {spot}"
    if strike <= 0:
        return f"strike must be positive, got {strike}"
    if sigma <= 0:
        return f"volatility must be positive, got {sigma}"
    if expiry_days < 0:
        return f"expiry_days must be non-negative, got {expiry_days}"
    return None


def _bs_price_and_greeks(
    spot: float,
    strike: float,
    T: float,
    r: float,
    sigma: float,
    option_type: str,
) -> dict:
    """Compute Black-Scholes price and Greeks.

    Args:
        spot: Current underlying price.
        strike: Strike price.
        T: Time to expiry in years.
        r: Risk-free rate.
        sigma: Annualised volatility.
        option_type: "call" or "put".

    Returns:
        Dict containing price, delta, gamma, theta, vega.
    """
    if T <= 0 or sigma <= 0:
        if option_type == "call":
            price = max(spot - strike, 0.0)
            delta = 1.0 if spot > strike else 0.0
        else:
            price = max(strike - spot, 0.0)
            delta = -1.0 if spot < strike else 0.0
        return {"price": price, "delta": delta, "gamma": 0.0, "theta": 0.0, "vega": 0.0}

    sqrt_T = np.sqrt(T)
    d1 = (np.log(spot / strike) + (r + sigma**2 / 2) * T) / (sigma * sqrt_T)
    d2 = d1 - sigma * sqrt_T
    nd1_pdf = float(norm.pdf(d1))

    if option_type == "call":
        price = float(spot * norm.cdf(d1) - strike * np.exp(-r * T) * norm.cdf(d2))
        delta = float(norm.cdf(d1))
    else:
        price = float(strike * np.exp(-r * T) * norm.cdf(-d2) - spot * norm.cdf(-d1))
        delta = float(norm.cdf(d1) - 1.0)

    gamma = float(nd1_pdf / (spot * sigma * sqrt_T))

    theta_common = -(spot * nd1_pdf * sigma) / (2 * sqrt_T)
    if option_type == "call":
        theta = theta_common - r * strike * np.exp(-r * T) * norm.cdf(d2)
    else:
        theta = theta_common + r * strike * np.exp(-r * T) * norm.cdf(-d2)
    theta = float(theta / 365.0)

    vega = float(spot * nd1_pdf * sqrt_T / 100.0)

    return {
        "price": round(price, 6),
        "delta": round(delta, 6),
        "gamma": round(gamma, 6),
        "theta": round(theta, 6),
        "vega": round(vega, 6),
    }


class OptionsPricingTool(BaseTool):
    """Options pricing tool: Black-Scholes theoretical price and Greeks."""

    name = "options_pricing"
    description = "Options pricing: compute theoretical price and Greeks using the Black-Scholes model."
    parameters = {
        "type": "object",
        "properties": {
            "spot": {"type": "number", "description": "Current underlying price"},
            "strike": {"type": "number", "description": "Strike price"},
            "expiry_days": {"type": "number", "description": "Days to expiry"},
            "risk_free_rate": {"type": "number", "description": "Risk-free rate", "default": 0.05},
            "volatility": {"type": "number", "description": "Annualised volatility"},
            "option_type": {"type": "string", "enum": ["call", "put"], "description": "Option type"},
        },
        "required": ["spot", "strike", "expiry_days", "volatility", "option_type"],
    }

    def execute(self, **kwargs: Any) -> str:
        """Run options pricing calculation.

        Args:
            **kwargs: Must include spot, strike, expiry_days, volatility, option_type.
                     Optional risk_free_rate.

        Returns:
            JSON string containing price, delta, gamma, theta, vega.
        """
        spot = float(kwargs["spot"])
        strike = float(kwargs["strike"])
        expiry_days = float(kwargs["expiry_days"])
        r = float(kwargs.get("risk_free_rate", 0.05))
        sigma = float(kwargs["volatility"])
        option_type = kwargs["option_type"]

        err = _validate_inputs(spot, strike, expiry_days, sigma, r, option_type)
        if err is not None:
            return json.dumps(
                {"status": "error", "tool": "options_pricing", "error": err},
                ensure_ascii=False,
            )

        T = expiry_days / 365.0

        result = _bs_price_and_greeks(spot, strike, T, r, sigma, option_type)
        result["inputs"] = {
            "spot": spot,
            "strike": strike,
            "expiry_days": expiry_days,
            "risk_free_rate": r,
            "volatility": sigma,
            "option_type": option_type,
            "T_years": round(T, 6),
        }
        nonfinite = any(
            k not in result or not math.isfinite(float(result[k])) for k in ("price", "delta", "gamma", "theta", "vega")
        )
        if T == 0.0 or nonfinite:
            result["status"] = "degenerate"
            result["degenerate"] = True
            result["warning"] = (
                "option at expiry (T=0): Greeks are singular; intrinsic value returned"
                if T == 0.0
                else "non-finite result (extreme inputs); values unreliable"
            )
        else:
            result["status"] = "ok"

        try:
            return json.dumps(result, ensure_ascii=False, allow_nan=False)
        except ValueError as exc:
            return json.dumps(
                {"status": "error", "tool": "options_pricing", "error": f"non-serializable numeric result: {exc}"},
                ensure_ascii=False,
            )
