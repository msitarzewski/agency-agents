"""
Unified model client – talks to Ollama (local) and Anthropic (supervisor).
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from .config import ModelSpec, ModelTier, PipelineConfig

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Ollama chat completion
# ---------------------------------------------------------------------------

def _ollama_chat(
    model: str,
    system: str,
    user_prompt: str,
    *,
    base_url: str,
    temperature: float = 0.4,
    max_tokens: int = 4096,
) -> str:
    """Call Ollama's /api/chat endpoint and return the assistant message."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    resp = httpx.post(
        f"{base_url}/api/chat",
        json=payload,
        timeout=300.0,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("message", {}).get("content", "")


# ---------------------------------------------------------------------------
# Anthropic chat completion  (used only for supervisor)
# ---------------------------------------------------------------------------

def _anthropic_chat(
    model: str,
    system: str,
    user_prompt: str,
    *,
    api_key: str,
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> str:
    """Call the Anthropic Messages API."""
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "system": system,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    resp = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=payload,
        timeout=120.0,
    )
    resp.raise_for_status()
    data = resp.json()
    # Extract text from content blocks
    blocks = data.get("content", [])
    return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")


# ---------------------------------------------------------------------------
# Unified dispatch
# ---------------------------------------------------------------------------

def call_model(
    spec: ModelSpec,
    system_prompt: str,
    user_prompt: str,
    config: PipelineConfig,
    *,
    temperature: float | None = None,
    max_tokens: int = 4096,
) -> str:
    """Route to the right provider and return the response text."""
    temp = temperature if temperature is not None else (
        0.3 if spec.tier == ModelTier.PAID_SUPERVISOR else 0.4
    )

    log.info(f"  ⚙ Calling {spec.provider}:{spec.name} (tier={spec.tier.value})")

    if spec.provider == "ollama":
        return _ollama_chat(
            spec.name,
            system_prompt,
            user_prompt,
            base_url=config.ollama_base_url,
            temperature=temp,
            max_tokens=max_tokens,
        )
    elif spec.provider == "anthropic":
        return _anthropic_chat(
            spec.name,
            system_prompt,
            user_prompt,
            api_key=config.anthropic_api_key,
            temperature=temp,
            max_tokens=max_tokens,
        )
    else:
        raise ValueError(f"Unknown provider: {spec.provider}")


# ---------------------------------------------------------------------------
# Model selection helpers
# ---------------------------------------------------------------------------

def pick_model(
    task_type: str,
    strength_map: dict[str, list[str]],
    models: list[ModelSpec],
    max_tier: ModelTier = ModelTier.FREE_HEAVY,
) -> ModelSpec:
    """
    Pick the cheapest model whose strengths overlap with the task.
    Never picks the paid supervisor tier unless explicitly allowed.
    """
    wanted = set(strength_map.get(task_type, ["general"]))
    # Sort by tier ordinal (cheapest first)
    tier_order = list(ModelTier)
    candidates = [m for m in models if tier_order.index(m.tier) <= tier_order.index(max_tier)]
    candidates.sort(key=lambda m: tier_order.index(m.tier))

    # Score by overlap
    best: ModelSpec | None = None
    best_score = -1
    for m in candidates:
        score = len(wanted & set(m.strengths))
        if score > best_score:
            best_score = score
            best = m
    return best or candidates[0]


def get_supervisor_model(models: list[ModelSpec]) -> ModelSpec:
    """Return the Claude Opus supervisor model."""
    for m in models:
        if m.tier == ModelTier.PAID_SUPERVISOR:
            return m
    raise RuntimeError("No supervisor model configured")
