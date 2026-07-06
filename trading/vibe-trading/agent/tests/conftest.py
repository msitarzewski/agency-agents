"""Shared fixtures and sys.path setup for all tests."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure agent/ is on sys.path so imports like `backtest.*` and `src.*` work.
AGENT_DIR = Path(__file__).resolve().parent.parent
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))
