from __future__ import annotations

from typing import Dict, Optional

import pandas as pd

from tradingagents.utils.logging_manager import get_logger

logger = get_logger('agents')


def _safe_float(x) -> Optional[float]:
    try:
        if x is None:
            return None
        v = float(x)
        if pd.isna(v):
            return None
        return v
    except Exception:
        return None


def _get_tushare_snapshot(symbol: str) -> Dict[str, Optional[float]]:
    try:
        from .providers.china.tushare import get_tushare_provider
        provider = get_tushare_provider()
        if not getattr(provider, 'connected', False):
            return {}
        # 先取 ts_code
        info = provider.get_stock_info(symbol)
        ts_code = info.get('ts_code') if isinstance(info, dict) else None
        if not ts_code:
            return {}
        # daily_basic 拿 pe/pb/total_mv
        api = provider.api
        if api is None:
            return {}
        db = api.daily_basic(ts_code=ts_code, fields='ts_code,trade_date,pe,pb,total_mv')
        pe = pb = mv = None
        if db is not None and not db.empty:
            db = db.sort_values('trade_date').iloc[-1]
            pe = _safe_float(db.get('pe'))
            pb = _safe_float(db.get('pb'))
            mv = _safe_float(db.get('total_mv'))
        # roe 通过 fina_indicator（若不可用则忽略）
        roe = None
        try:
            fi = api.fina_indicator(ts_code=ts_code, fields='ts_code,end_date,roe')
            if fi is not None and not fi.empty:
                fi = fi.sort_values('end_date').iloc[-1]
                roe = _safe_float(fi.get('roe'))
        except Exception:
            pass
        return {
            'pe': pe,
            'pb': pb,
            'market_cap': mv,  # 单位：万元
            'roe': roe,
        }
    except Exception as e:
        logger.debug(f"[fund_snapshot] tushare snapshot failed: {e}")
        return {}


def get_cn_fund_snapshot(symbol: str) -> Dict[str, Optional[float]]:
    """
    获取A股基础基本面快照（pe/pb/roe/market_cap）。
    优先Tushare，失败则返回空字典（后续可扩展AKShare/东方财富等）。
    """
    snap = _get_tushare_snapshot(symbol)
    if snap:
        return snap
    return {}

