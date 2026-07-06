"""
向后兼容导入模块
保持旧的导入路径可用，避免破坏现有代码

使用方法：
    # 旧代码仍然可以这样导入
    from tradingagents.dataflows.googlenews_utils import getNewsData
    from tradingagents.dataflows.cache_manager import StockDataCache
    
    # 新代码推荐使用新路径
    from tradingagents.dataflows.news import getNewsData
    from tradingagents.dataflows.cache import StockDataCache
"""

# 这个文件本身不导出任何内容
# 它的存在是为了提醒开发者使用新的导入路径

__all__ = []

