"""
新闻过滤集成模块
将新闻过滤器集成到现有的新闻获取流程中
"""

import pandas as pd
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

def integrate_news_filtering(original_get_stock_news_em):
    """
    装饰器：为get_stock_news_em函数添加新闻过滤功能
    
    Args:
        original_get_stock_news_em: 原始的get_stock_news_em函数
        
    Returns:
        包装后的函数，具有新闻过滤功能
    """
    def filtered_get_stock_news_em(symbol: str, enable_filter: bool = True, min_score: float = 30, 
                                  use_semantic: bool = False, use_local_model: bool = False) -> pd.DataFrame:
        """
        增强版get_stock_news_em，集成新闻过滤功能
        
        Args:
            symbol: 股票代码
            enable_filter: 是否启用新闻过滤
            min_score: 最低相关性评分阈值
            use_semantic: 是否使用语义相似度过滤
            use_local_model: 是否使用本地分类模型
            
        Returns:
            pd.DataFrame: 过滤后的新闻数据
        """
        logger.info(f"[新闻过滤集成] 开始获取 {symbol} 的新闻，过滤开关: {enable_filter}")
        
        # 调用原始函数获取新闻
        start_time = datetime.now()
        try:
            news_df = original_get_stock_news_em(symbol)
            fetch_time = (datetime.now() - start_time).total_seconds()
            
            if news_df.empty:
                logger.warning(f"[新闻过滤集成] 原始函数未获取到 {symbol} 的新闻数据")
                return news_df
            
            logger.info(f"[新闻过滤集成] 原始新闻获取成功: {len(news_df)}条，耗时: {fetch_time:.2f}秒")
            
            # 如果不启用过滤，直接返回原始数据
            if not enable_filter:
                logger.info(f"[新闻过滤集成] 过滤功能已禁用，返回原始新闻数据")
                return news_df
            
            # 启用新闻过滤
            filter_start_time = datetime.now()
            
            try:
                # 导入过滤器
                from tradingagents.utils.enhanced_news_filter import create_enhanced_news_filter
                
                # 创建过滤器
                news_filter = create_enhanced_news_filter(
                    symbol, 
                    use_semantic=use_semantic, 
                    use_local_model=use_local_model
                )
                
                # 执行过滤
                filtered_df = news_filter.filter_news_enhanced(news_df, min_score=min_score)
                
                filter_time = (datetime.now() - filter_start_time).total_seconds()
                
                # 记录过滤统计
                original_count = len(news_df)
                filtered_count = len(filtered_df)
                filter_rate = (original_count - filtered_count) / original_count * 100 if original_count > 0 else 0
                
                logger.info(f"[新闻过滤集成] 新闻过滤完成:")
                logger.info(f"  - 原始新闻: {original_count}条")
                logger.info(f"  - 过滤后新闻: {filtered_count}条")
                logger.info(f"  - 过滤率: {filter_rate:.1f}%")
                logger.info(f"  - 过滤耗时: {filter_time:.2f}秒")
                
                if not filtered_df.empty:
                    avg_score = filtered_df['final_score'].mean()
                    max_score = filtered_df['final_score'].max()
                    logger.info(f"  - 平均评分: {avg_score:.1f}")
                    logger.info(f"  - 最高评分: {max_score:.1f}")
                
                return filtered_df
                
            except Exception as filter_error:
                logger.error(f"[新闻过滤集成] 新闻过滤失败: {filter_error}")
                logger.error(f"[新闻过滤集成] 返回原始新闻数据作为备用")
                return news_df
                
        except Exception as fetch_error:
            logger.error(f"[新闻过滤集成] 原始新闻获取失败: {fetch_error}")
            return pd.DataFrame()  # 返回空DataFrame
    
    return filtered_get_stock_news_em


def patch_akshare_utils():
    """
    为akshare_utils模块的get_stock_news_em函数添加过滤功能

    ⚠️ 已废弃：akshare_utils 模块已被移除，此函数保留仅为向后兼容
    """
    logger.warning("[新闻过滤集成] ⚠️ patch_akshare_utils 已废弃：akshare_utils 模块已被移除")


def create_filtered_realtime_news_function():
    """
    创建增强版的实时新闻获取函数
    """
    def get_filtered_realtime_stock_news(ticker: str, curr_date: str, hours_back: int = 6, 
                                       enable_filter: bool = True, min_score: float = 30) -> str:
        """
        增强版实时新闻获取函数，集成新闻过滤
        
        Args:
            ticker: 股票代码
            curr_date: 当前日期
            hours_back: 回溯小时数
            enable_filter: 是否启用新闻过滤
            min_score: 最低相关性评分阈值
            
        Returns:
            str: 格式化的新闻报告
        """
        logger.info(f"[增强实时新闻] 开始获取 {ticker} 的过滤新闻")
        
        try:
            # 导入原始函数
            from tradingagents.dataflows.news.realtime_news import get_realtime_stock_news

            # 调用原始函数获取新闻
            original_report = get_realtime_stock_news(ticker, curr_date, hours_back)
            
            if not enable_filter:
                logger.info(f"[增强实时新闻] 过滤功能已禁用，返回原始报告")
                return original_report
            
            # 如果启用过滤且是A股，尝试重新获取并过滤
            if any(suffix in ticker for suffix in ['.SH', '.SZ', '.SS', '.XSHE', '.XSHG']) or \
               (not '.' in ticker and ticker.isdigit()):
                
                logger.info(f"[增强实时新闻] 检测到A股代码，尝试使用过滤版东方财富新闻")
                
                try:
                    # 注意：akshare_utils 已废弃，使用 AKShareProvider 替代
                    from tradingagents.dataflows.providers.china.akshare import get_akshare_provider

                    # 清理股票代码
                    clean_ticker = ticker.replace('.SH', '').replace('.SZ', '').replace('.SS', '')\
                                    .replace('.XSHE', '').replace('.XSHG', '')

                    # 使用 AKShareProvider 获取新闻（如果有相应方法）
                    provider = get_akshare_provider()
                    # TODO: 需要实现 get_stock_news 方法
                    # original_news_df = provider.get_stock_news(clean_ticker)
                    # 暂时跳过，返回原始报告
                    logger.warning(f"[增强实时新闻] AKShare新闻功能暂未实现，返回原始报告")
                    return original_report
                        
                except Exception as filter_error:
                    logger.error(f"[增强实时新闻] 新闻过滤失败: {filter_error}")
                    return original_report
            else:
                logger.info(f"[增强实时新闻] 非A股代码，返回原始报告")
                return original_report
                
        except Exception as e:
            logger.error(f"[增强实时新闻] 增强新闻获取失败: {e}")
            return f"❌ 新闻获取失败: {str(e)}"
    
    return get_filtered_realtime_stock_news


# 自动应用补丁
def apply_news_filtering_patches():
    """
    自动应用新闻过滤补丁
    """
    logger.info("[新闻过滤集成] 开始应用新闻过滤补丁...")
    
    # 1. 增强akshare_utils
    patch_akshare_utils()
    
    # 2. 创建增强版实时新闻函数
    enhanced_function = create_filtered_realtime_news_function()
    
    logger.info("[新闻过滤集成] ✅ 新闻过滤补丁应用完成")
    
    return enhanced_function


if __name__ == "__main__":
    # 测试集成功能
    print("=== 测试新闻过滤集成 ===")
    
    # 应用补丁
    enhanced_news_function = apply_news_filtering_patches()
    
    # 测试增强版函数
    test_result = enhanced_news_function(
        ticker="600036",
        curr_date="2024-07-28",
        enable_filter=True,
        min_score=30
    )
    
    print(f"测试结果长度: {len(test_result)} 字符")
    print(f"测试结果预览: {test_result[:200]}...")