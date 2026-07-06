#!/usr/bin/env python3
"""
Tushare数据源演示脚本
展示如何使用Tushare获取中国A股数据
"""

import os
import sys
from datetime import datetime, timedelta

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('default')

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def demo_basic_usage():
    """演示基本用法"""
    logger.info(f"🎯 Tushare基本用法演示")
    logger.info(f"=")
    
    try:
        from tradingagents.dataflows.tushare_adapter import get_tushare_adapter
        
        # 获取适配器实例
        adapter = get_tushare_adapter()
        
        if not adapter.provider or not adapter.provider.connected:
            logger.error(f"❌ Tushare未连接，请检查配置")
            return
        
        logger.info(f"✅ Tushare连接成功")
        
        # 1. 获取股票基本信息
        logger.info(f"\n📊 获取股票基本信息")
        logger.info(f"-")
        
        stock_info = adapter.get_stock_info("000001")
        if stock_info:
            logger.info(f"股票代码: {stock_info.get('symbol')}")
            logger.info(f"股票名称: {stock_info.get('name')}")
            logger.info(f"所属行业: {stock_info.get('industry')}")
            logger.info(f"所属地区: {stock_info.get('area')}")
        
        # 2. 获取历史数据
        logger.info(f"\n📈 获取历史数据")
        logger.info(f"-")
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        stock_data = adapter.get_stock_data("000001", start_date, end_date)
        if not stock_data.empty:
            logger.info(f"数据期间: {start_date} 至 {end_date}")
            logger.info(f"数据条数: {len(stock_data)}条")
            logger.info(f"\n最新5条数据:")
            print(stock_data.tail(5)[['date', 'open', 'high', 'low', 'close', 'volume']].to_string(index=False))
        
        # 3. 搜索股票
        logger.debug(f"\n🔍 搜索股票")
        logger.info(f"-")
        
        search_results = adapter.search_stocks("银行")
        if not search_results.empty:
            logger.info(f"搜索'银行'找到 {len(search_results)} 只股票")
            logger.info(f"\n前5个结果:")
            for idx, row in search_results.head(5).iterrows():
                logger.info(f"  {row['symbol']} - {row['name']} ({row.get('industry', '未知')})")
        
    except Exception as e:
        logger.error(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()


def demo_interface_functions():
    """演示接口函数"""
    logger.info(f"\n🎯 Tushare接口函数演示")
    logger.info(f"=")
    
    try:
        from tradingagents.dataflows.interface import (
            get_china_stock_data_tushare,
            search_china_stocks_tushare,
            get_china_stock_info_tushare,
            get_china_stock_fundamentals_tushare
        )
        
        # 1. 获取股票数据
        logger.info(f"\n📊 获取股票数据")
        logger.info(f"-")
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        
        data_result = get_china_stock_data_tushare("000001", start_date, end_date)
        print(data_result[:500] + "..." if len(data_result) > 500 else data_result)
        
        # 2. 搜索股票
        logger.debug(f"\n🔍 搜索股票")
        logger.info(f"-")
        
        search_result = search_china_stocks_tushare("平安")
        print(search_result[:500] + "..." if len(search_result) > 500 else search_result)
        
        # 3. 获取股票信息
        logger.info(f"\n📋 获取股票信息")
        logger.info(f"-")
        
        info_result = get_china_stock_info_tushare("000001")
        print(info_result)
        
        # 4. 获取基本面数据
        logger.info(f"\n💰 获取基本面数据")
        logger.info(f"-")
        
        fundamentals_result = get_china_stock_fundamentals_tushare("000001")
        print(fundamentals_result[:800] + "..." if len(fundamentals_result) > 800 else fundamentals_result)
        
    except Exception as e:
        logger.error(f"❌ 接口函数演示失败: {e}")
        import traceback
        traceback.print_exc()


def demo_batch_operations():
    """演示批量操作"""
    logger.info(f"\n🎯 Tushare批量操作演示")
    logger.info(f"=")
    
    try:
        from tradingagents.dataflows.tushare_adapter import get_tushare_adapter
        import time
        
        adapter = get_tushare_adapter()
        
        if not adapter.provider or not adapter.provider.connected:
            logger.error(f"❌ Tushare未连接，请检查配置")
            return
        
        # 批量获取多只股票信息
        symbols = ["000001", "000002", "600036", "600519", "000858"]
        
        logger.info(f"📊 批量获取 {len(symbols)} 只股票信息")
        logger.info(f"-")
        
        for i, symbol in enumerate(symbols, 1):
            try:
                stock_info = adapter.get_stock_info(symbol)
                if stock_info:
                    logger.info(f"{i}. {symbol} - {stock_info.get('name')} ({stock_info.get('industry', '未知')})")
                else:
                    logger.error(f"{i}. {symbol} - 获取失败")
                
                # 避免API频率限制
                if i < len(symbols):
                    time.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"{i}. {symbol} - 错误: {e}")
        
        logger.info(f"\n✅ 批量操作完成")
        
    except Exception as e:
        logger.error(f"❌ 批量操作演示失败: {e}")
        import traceback
        traceback.print_exc()


def demo_cache_performance():
    """演示缓存性能"""
    logger.info(f"\n🎯 Tushare缓存性能演示")
    logger.info(f"=")
    
    try:
        from tradingagents.dataflows.tushare_adapter import get_tushare_adapter
        import time
        
        adapter = get_tushare_adapter()
        
        if not adapter.provider or not adapter.provider.connected:
            logger.error(f"❌ Tushare未连接，请检查配置")
            return
        
        if not adapter.enable_cache:
            logger.warning(f"⚠️ 缓存未启用，无法演示缓存性能")
            return
        
        symbol = "000001"
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d')
        
        # 第一次获取（从API）
        logger.info(f"🔄 第一次获取数据（从API）...")
        start_time = time.time()
        data1 = adapter.get_stock_data(symbol, start_date, end_date)
        time1 = time.time() - start_time
        
        if not data1.empty:
            logger.info(f"✅ 获取成功: {len(data1)}条数据，耗时: {time1:.2f}秒")
        else:
            logger.error(f"❌ 获取失败")
            return
        
        # 第二次获取（从缓存）
        logger.info(f"🔄 第二次获取数据（从缓存）...")
        start_time = time.time()
        data2 = adapter.get_stock_data(symbol, start_date, end_date)
        time2 = time.time() - start_time
        
        if not data2.empty:
            logger.info(f"✅ 获取成功: {len(data2)}条数据，耗时: {time2:.2f}秒")
            
            # 性能对比
            if time2 < time1:
                speedup = time1 / time2
                logger.info(f"🚀 缓存加速: {speedup:.1f}倍")
            else:
                logger.warning(f"⚠️ 缓存性能未体现明显优势")
        else:
            logger.error(f"❌ 获取失败")
        
    except Exception as e:
        logger.error(f"❌ 缓存性能演示失败: {e}")
        import traceback
        traceback.print_exc()


def check_environment():
    """检查环境配置"""
    logger.info(f"🔧 检查Tushare环境配置")
    logger.info(f"=")
    
    # 检查Tushare库
    try:
        import tushare as ts
        logger.info(f"✅ Tushare库: v{ts.__version__}")
    except ImportError:
        logger.error(f"❌ Tushare库未安装")
        return False
    
    # 检查Token
    token = os.getenv('TUSHARE_TOKEN')
    if token:
        logger.info(f"✅ API Token: 已设置 ({len(token)}字符)")
    else:
        logger.error(f"❌ API Token: 未设置")
        logger.info(f"💡 请在.env文件中设置: TUSHARE_TOKEN=your_token_here")
        return False
    
    # 检查缓存
    try:
        from tradingagents.dataflows.cache_manager import get_cache

        cache = get_cache()
        logger.info(f"✅ 缓存管理器: 可用")
    except Exception as e:
        logger.warning(f"⚠️ 缓存管理器: 不可用 ({e})")
    
    return True


def main():
    """主函数"""
    logger.info(f"🎯 Tushare数据源演示")
    logger.info(f"=")
    logger.info(f"本演示将展示Tushare数据源的各种功能")
    logger.info(f"=")
    
    # 检查环境
    if not check_environment():
        logger.error(f"\n❌ 环境配置不完整，请先配置Tushare环境")
        return
    
    # 运行演示
    demo_basic_usage()
    demo_interface_functions()
    demo_batch_operations()
    demo_cache_performance()
    
    logger.info(f"\n🎉 Tushare演示完成！")
    logger.info(f"\n📚 更多信息:")
    logger.info(f"   - 文档: docs/data/tushare-integration.md")
    logger.info(f"   - 测试: tests/test_tushare_integration.py")
    logger.info(f"   - 配置: config/tushare_config.example.env")
    
    input("\n按回车键退出...")


if __name__ == "__main__":
    main()
