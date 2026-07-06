"""
美股数据提供器
包含 Finnhub, Yahoo Finance 等美股数据源
"""

# 导入 Finnhub 工具
try:
    from .finnhub import get_data_in_range
    FINNHUB_AVAILABLE = True
except ImportError:
    get_data_in_range = None
    FINNHUB_AVAILABLE = False

# 导入 Yahoo Finance 工具
try:
    from .yfinance import YFinanceUtils
    YFINANCE_AVAILABLE = True
except ImportError:
    YFinanceUtils = None
    YFINANCE_AVAILABLE = False

# 导入优化的美股数据提供器
try:
    from .optimized import OptimizedUSDataProvider
    OPTIMIZED_US_AVAILABLE = True
except ImportError:
    OptimizedUSDataProvider = None
    OPTIMIZED_US_AVAILABLE = False

# 默认使用优化的提供器
DefaultUSProvider = OptimizedUSDataProvider

__all__ = [
    # Finnhub
    'get_data_in_range',
    'FINNHUB_AVAILABLE',

    # Yahoo Finance
    'YFinanceUtils',
    'YFINANCE_AVAILABLE',

    # 优化的提供器
    'OptimizedUSDataProvider',
    'OPTIMIZED_US_AVAILABLE',
    'DefaultUSProvider',
]

