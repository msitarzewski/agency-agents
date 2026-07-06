"""
技术指标计算模块
提供各种技术分析指标的计算功能
"""

# 导入 stockstats
try:
    from .stockstats import StockstatsUtils
    STOCKSTATS_AVAILABLE = True
except ImportError:
    StockstatsUtils = None
    STOCKSTATS_AVAILABLE = False

__all__ = [
    'StockstatsUtils',
    'STOCKSTATS_AVAILABLE',
]

