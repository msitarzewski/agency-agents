"""Content-filter resilience helpers shared by AgentLoop and swarm worker.

When an LLM provider blocks a response via content moderation
(``finish_reason == "content_filter"``), the caller skips that iteration
and continues instead of breaking on empty/garbage content.  These
helpers centralise threshold parsing, the warning-string format, and the
consecutive-skip circuit breaker so both the agent loop and the swarm
worker stay in sync.
"""

from __future__ import annotations

import os

CONTENT_FILTER_WARNING_THRESHOLD_ENV = "CONTENT_FILTER_WARNING_THRESHOLD"
DEFAULT_CONTENT_FILTER_THRESHOLD = 0.05

# Circuit breaker: when this many *consecutive* LLM responses are blocked
# by content moderation, stop skipping and end the run early instead of
# burning the whole iteration budget on a provider that is clearly refusing
# every request.
MAX_CONSECUTIVE_CONTENT_FILTER_SKIPS = 10

# System message injected after a content-filter hit, telling the model to
# move on to the next item instead of retrying the blocked content.
CONTENT_FILTER_SKIP_MESSAGE = (
    "[SYSTEM] The previous response was blocked by content "
    "moderation. Skip the current item and continue with the "
    "next one. Do not retry the same content."
)

# Gemini surfaces content moderation via uppercase FinishReason enum values
# (SAFETY, RECITATION, BLOCKLIST, ...) instead of OpenAI's lowercase
# "content_filter". Google's OpenAI-compatible endpoint passes these through
# unmapped, so the detector must recognise both vocabularies. See issue #307.
GEMINI_SAFETY_FINISH_REASONS = frozenset({
    "SAFETY",
    "RECITATION",
    "BLOCKLIST",
    "PROHIBITED_CONTENT",
    "SPII",
    "IMAGE_SAFETY",
    "IMAGE_PROHIBITED_CONTENT",
    "IMAGE_RECITATION",
})


def is_content_filter_triggered(finish_reason: object) -> bool:
    """Return True when ``finish_reason`` indicates content moderation blocked the response.

    Recognises both OpenAI's ``"content_filter"`` and Gemini's uppercase
    safety FinishReason enum (``"SAFETY"``, ``"RECITATION"``, ...). The
    comparison is case-insensitive on the Gemini side so a provider that
    lowercases the value still matches. Non-string values (None, missing)
    return False.
    """
    if not isinstance(finish_reason, str):
        return False
    if finish_reason == "content_filter":
        return True
    return finish_reason.upper() in GEMINI_SAFETY_FINISH_REASONS


def get_content_filter_threshold() -> float:
    """Return the configured content-filter warning threshold.

    Reads ``CONTENT_FILTER_WARNING_THRESHOLD`` (default 0.05 = 5%).
    Invalid values fall back to the default instead of crashing the run.
    """
    raw = os.getenv(
        CONTENT_FILTER_WARNING_THRESHOLD_ENV,
        str(DEFAULT_CONTENT_FILTER_THRESHOLD),
    )
    try:
        return float(raw)
    except (TypeError, ValueError):
        return DEFAULT_CONTENT_FILTER_THRESHOLD


def compute_content_filter_warnings(
    content_filter_count: int,
    total_iterations: int,
) -> list[str]:
    """Compute content-filter warnings based on the hit ratio.

    Args:
        content_filter_count: Number of LLM responses blocked by content
            moderation during the run.
        total_iterations: Total number of LLM iterations executed.

    Returns:
        A list with one warning string when the ratio exceeds the
        configured threshold, otherwise an empty list.
    """
    if content_filter_count == 0:
        return []
    denominator = max(1, total_iterations)
    ratio = content_filter_count / denominator
    threshold = get_content_filter_threshold()
    if ratio > threshold:
        return [
            f"{content_filter_count}/{denominator} LLM responses"
            f" ({ratio:.0%}) were blocked by content moderation."
            " Consider switching to a provider with less aggressive"
            " filtering for event-driven analysis."
        ]
    return []
