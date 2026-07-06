#!/usr/bin/env python3
"""
App 缓存读取适配器（TradingAgents -> app MongoDB 集合）
- 基本信息集合：stock_basic_info
- 行情集合：market_quotes

当启用 ta_use_app_cache 时，作为优先数据源；未命中部分由上层继续回退到直连数据源。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime

import pandas as pd
import logging

_logger = logging.getLogger('dataflows')

try:
    from tradingagents.config.database_manager import get_mongodb_client
except Exception:  # pragma: no cover - 弱依赖
    get_mongodb_client = None  # type: ignore


BASICS_COLLECTION = "stock_basic_info"
QUOTES_COLLECTION = "market_quotes"


def get_basics_from_cache(stock_code: Optional[str] = None) -> Optional[Dict[str, Any] | List[Dict[str, Any]]]:
    """从 app 的 stock_basic_info 读取基础信息。"""
    if get_mongodb_client is None:
        return None
    client = get_mongodb_client()
    if not client:
        return None
    try:
        # 数据库名取自 DatabaseManager 内部配置
        db_name = None
        try:
            # 访问 DatabaseManager 暴露的配置
            from tradingagents.config.database_manager import get_database_manager  # type: ignore
            db_name = get_database_manager().mongodb_config.get("database", "tradingagents")
        except Exception:
            db_name = "tradingagents"
        db = client[db_name]
        coll = db[BASICS_COLLECTION]
        if stock_code:
            code6 = str(stock_code).zfill(6)
            try:
                _logger.debug(f"[app_cache] 查询基础信息 | db={db_name} coll={BASICS_COLLECTION} code={code6}")
            except Exception:
                pass
            # 同时查询 symbol 和 code 字段，确保兼容新旧数据格式
            doc = coll.find_one({"$or": [{"symbol": code6}, {"code": code6}]})
            if not doc:
                try:
                    _logger.debug(f"[app_cache] 基础信息未命中 | db={db_name} coll={BASICS_COLLECTION} code={code6}")
                except Exception:
                    pass
            return doc or None
        else:
            cursor = coll.find({})
            docs = list(cursor)
            return docs or None
    except Exception as e:
        try:
            _logger.debug(f"[app_cache] 基础信息读取异常（忽略）: {e}")
        except Exception:
            pass
        return None


def get_market_quote_dataframe(symbol: str) -> Optional[pd.DataFrame]:
    """从 app 的 market_quotes 读取单只股票的最新一条快照，并转为 DataFrame。"""
    if get_mongodb_client is None:
        return None
    client = get_mongodb_client()
    if not client:
        return None
    try:
        # 获取数据库
        from tradingagents.config.database_manager import get_database_manager  # type: ignore
        db_name = get_database_manager().mongodb_config.get("database", "tradingagents")
        db = client[db_name]
        coll = db[QUOTES_COLLECTION]
        code = str(symbol).zfill(6)
        try:
            _logger.debug(f"[app_cache] 查询行情 | db={db_name} coll={QUOTES_COLLECTION} code={code}")
        except Exception:
            pass
        doc = coll.find_one({"code": code})
        if not doc:
            try:
                _logger.debug(f"[app_cache] 行情未命中 | db={db_name} coll={QUOTES_COLLECTION} code={code}")
            except Exception:
                pass
            return None
        # 构造 DataFrame，字段对齐 tushare 标准化映射
        row = {
            "code": code,
            "date": doc.get("trade_date"),  # YYYYMMDD
            "open": doc.get("open"),
            "high": doc.get("high"),
            "low": doc.get("low"),
            "close": doc.get("close"),
            "volume": doc.get("volume"),
            "amount": doc.get("amount"),
            "pct_chg": doc.get("pct_chg"),
            "change": None,
        }
        df = pd.DataFrame([row])
        return df
    except Exception as e:
        try:
            _logger.debug(f"[app_cache] 行情读取异常（忽略）: {e}")
        except Exception:
            pass
        return None

