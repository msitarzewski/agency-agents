"""Shadow Account — extract a user's profitable pattern as a re-runnable shadow.

Public API (for tools/tests/external callers):
    extract_shadow_profile: journal → ShadowProfile
    ShadowProfile / ShadowRule / ShadowBacktestResult / AttributionBreakdown
    storage: save_profile / load_profile / find_by_journal_hash
"""

from src.shadow_account.backtester import (
    SUPPORTED_MARKETS,
    run_shadow_backtest,
    select_multi_market_codes,
)
from src.shadow_account.codegen import (
    render_config,
    render_signal_engine,
    validate_generated,
    write_run_dir,
)
from src.shadow_account.extractor import extract_shadow_profile
from src.shadow_account.reporter import render_shadow_report
from src.shadow_account.models import (
    AttributionBreakdown,
    ShadowBacktestResult,
    ShadowProfile,
    ShadowRule,
)
from src.shadow_account.storage import (
    find_by_journal_hash,
    load_profile,
    new_shadow_id,
    save_profile,
)

__all__ = [
    "AttributionBreakdown",
    "SUPPORTED_MARKETS",
    "ShadowBacktestResult",
    "ShadowProfile",
    "ShadowRule",
    "extract_shadow_profile",
    "find_by_journal_hash",
    "load_profile",
    "new_shadow_id",
    "render_config",
    "render_shadow_report",
    "render_signal_engine",
    "run_shadow_backtest",
    "save_profile",
    "select_multi_market_codes",
    "validate_generated",
    "write_run_dir",
]
